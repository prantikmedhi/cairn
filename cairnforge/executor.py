from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from .budget import BudgetExceededError, BudgetTracker
from .checkpoint import load_checkpoint, save_checkpoint
from .expression import render_value, resolve_condition
from .models import ExecutionResult, LoopDefinition, StateResult
from .plugins import get_builtin_plugins
from .state_machine import choose_next_state, get_start_state
from .validator import validate_loop_definition

PLUGIN_REGISTRY = get_builtin_plugins()


class CircuitBreakerOpenError(RuntimeError):
    """Raised when repeated failures open the circuit breaker."""


def execute_loop(loop: LoopDefinition, inputs: dict[str, Any] | None = None, target: str = "langchain") -> ExecutionResult:
    validate_loop_definition(loop)
    return _execute_loop(loop, inputs=inputs, target=target)


def _execute_loop(
    loop: LoopDefinition,
    inputs: dict[str, Any] | None = None,
    target: str = "langchain",
    checkpoint_path: str | Path | None = None,
    resume_from: str | Path | None = None,
    max_steps: int | None = None,
) -> ExecutionResult:
    if target not in PLUGIN_REGISTRY:
        raise ValueError(f"Unknown target '{target}'")

    plugin = PLUGIN_REGISTRY[target]
    states_by_id = {state.id: state for state in loop.states}
    step_count = 0
    consecutive_failures = 0
    circuit_breaker_limit = _get_circuit_breaker_limit(loop)
    started_at = perf_counter()
    retry_events = 0

    if resume_from is not None:
        checkpoint = load_checkpoint(resume_from)
        if checkpoint["loop_id"] != loop.id:
            raise ValueError(f"Checkpoint loop_id '{checkpoint['loop_id']}' does not match '{loop.id}'")
        if checkpoint["target"] != target:
            raise ValueError(f"Checkpoint target '{checkpoint['target']}' does not match '{target}'")
        resolved_inputs = checkpoint["inputs"]
        tracker = BudgetTracker(loop.budget)
        tracker.iterations = int(checkpoint.get("iterations", 0))
        tracker.cost_usd = float(checkpoint.get("cost_usd", 0.0))
        current_state_id = checkpoint.get("next_state_id")
        current_state = states_by_id.get(current_state_id) if current_state_id else None
        state_results = [StateResult(**item) for item in checkpoint.get("state_results", [])]
        state_outputs = checkpoint.get("state_outputs", {})
        last_outputs = checkpoint.get("last_outputs", {})
    else:
        resolved_inputs = _materialize_inputs(loop, inputs or {})
        tracker = BudgetTracker(loop.budget)
        current_state = get_start_state(loop)
        state_results = []
        state_outputs = {}
        last_outputs = {}

    try:
        while current_state is not None:
            if max_steps is not None and step_count >= max_steps:
                _persist_checkpoint(checkpoint_path, loop, target, resolved_inputs, state_results, state_outputs, last_outputs, tracker, current_state.id, False)
                return ExecutionResult(
                    loop_id=loop.id,
                    success=False,
                    final_outputs=_safe_render_outputs(loop, resolved_inputs, state_outputs, tracker),
                    state_results=state_results,
                    error=None,
                    metadata={
                        "target": target,
                        "paused": True,
                        "next_state_id": current_state.id,
                        "iterations": tracker.iterations,
                        **plugin.get_metadata(),
                    },
                )

            tracker.tick()
            step_count += 1
            current_context = _build_context(loop, resolved_inputs, state_outputs, last_outputs, tracker)
            should_run = True
            if current_state.condition and current_state.handler != "core.condition":
                should_run = bool(resolve_condition(current_state.condition, current_context))

            if should_run:
                runtime_inputs = render_value(current_state.inputs, current_context)
                runtime_condition = None
                if "condition" in current_state.raw:
                    runtime_condition = render_value(current_state.raw["condition"], current_context)
                outputs = _execute_state_with_guards(
                    loop=loop,
                    state=current_state,
                    plugin=plugin,
                    target=target,
                    runtime_inputs=runtime_inputs,
                    resolved_inputs=resolved_inputs,
                    state_outputs=state_outputs,
                    runtime_condition=runtime_condition,
                )
                retry_events += max(0, outputs.pop("__retry_attempts__", 1) - 1)
                consecutive_failures = 0
            else:
                outputs = {"skipped": True}

            state_outputs[current_state.id] = outputs
            state_results.append(StateResult(state_id=current_state.id, outputs=outputs, skipped=not should_run))
            if should_run and current_state.raw.get("parallel"):
                parallel_results = _execute_parallel_states(
                    loop=loop,
                    parent_state=current_state,
                    states_by_id=states_by_id,
                    plugin=plugin,
                    target=target,
                    resolved_inputs=resolved_inputs,
                    state_outputs=state_outputs,
                    current_outputs=outputs,
                    tracker=tracker,
                )
                retry_events += sum(max(0, item["outputs"].pop("__retry_attempts__", 1) - 1) for item in parallel_results)
                for item in parallel_results:
                    state_outputs[item["state_id"]] = item["outputs"]
                    state_results.append(
                        StateResult(state_id=item["state_id"], outputs=item["outputs"], skipped=item["skipped"])
                    )
            last_outputs = outputs
            current_context = _build_context(loop, resolved_inputs, state_outputs, outputs, tracker)
            next_state_id = choose_next_state(loop, current_state, current_context)
            _persist_checkpoint(checkpoint_path, loop, target, resolved_inputs, state_results, state_outputs, last_outputs, tracker, next_state_id, False)
            current_state = states_by_id.get(next_state_id) if next_state_id else None

        _persist_checkpoint(checkpoint_path, loop, target, resolved_inputs, state_results, state_outputs, last_outputs, tracker, None, True)
        return ExecutionResult(
            loop_id=loop.id,
            success=True,
            final_outputs=_render_declared_outputs(loop, resolved_inputs, state_outputs, tracker),
            state_results=state_results,
            metadata={
                "target": target,
                "iterations": tracker.iterations,
                "cost_usd": tracker.cost_usd,
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                "retry_events": retry_events,
                **plugin.get_metadata(),
            },
        )
    except BudgetExceededError as exc:
        hook_outputs = _run_hook(loop.on_budget_exceeded, plugin, loop, resolved_inputs, state_outputs, str(exc), tracker)
        return ExecutionResult(
            loop_id=loop.id,
            success=False,
            final_outputs=hook_outputs,
            state_results=state_results,
            error=str(exc),
            metadata={
                "target": target,
                "iterations": tracker.iterations,
                "budget_exceeded": True,
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                "retry_events": retry_events,
                **plugin.get_metadata(),
            },
        )
    except Exception as exc:
        consecutive_failures += 1
        if circuit_breaker_limit is not None and consecutive_failures >= circuit_breaker_limit:
            exc = CircuitBreakerOpenError(
                f"Circuit breaker opened after {consecutive_failures} consecutive failure(s): {exc}"
            )
        hook_outputs = _run_hook(loop.on_error, plugin, loop, resolved_inputs, state_outputs, str(exc), tracker)
        return ExecutionResult(
            loop_id=loop.id,
            success=False,
            final_outputs=hook_outputs,
            state_results=state_results,
            error=str(exc),
            metadata={
                "target": target,
                "iterations": tracker.iterations,
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                "retry_events": retry_events,
                **plugin.get_metadata(),
            },
        )


def _materialize_inputs(loop: LoopDefinition, provided: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for name, config in loop.inputs.items():
        if name in provided:
            values[name] = provided[name]
        elif config.default is not None:
            values[name] = config.default
        elif config.required:
            raise ValueError(f"Missing required input '{name}'")
        else:
            values[name] = None
    for name, value in provided.items():
        if name not in values:
            values[name] = value
    return values


def _build_context(
    loop: LoopDefinition,
    inputs: dict[str, Any],
    state_outputs: dict[str, dict[str, Any]],
    current_outputs: dict[str, Any],
    tracker: BudgetTracker,
) -> dict[str, Any]:
    return {
        "inputs": inputs,
        "states": {state_id: {"outputs": outputs} for state_id, outputs in state_outputs.items()},
        "outputs": current_outputs,
        "budget": {
            "iterations": tracker.iterations,
            "cost_usd": tracker.cost_usd,
            "max_iterations": loop.budget.max_iterations,
            "max_cost_usd": loop.budget.max_cost_usd,
            "max_duration": loop.budget.max_duration,
        },
        "loop": {"id": loop.id, "name": loop.name, "version": loop.version},
    }


def _render_declared_outputs(
    loop: LoopDefinition,
    inputs: dict[str, Any],
    state_outputs: dict[str, dict[str, Any]],
    tracker: BudgetTracker,
) -> dict[str, Any]:
    context = _build_context(loop, inputs, state_outputs, {}, tracker)
    result: dict[str, Any] = {}
    for name, config in loop.outputs.items():
        if isinstance(config, dict) and "value" in config:
            result[name] = render_value(config["value"], context)
        else:
            result[name] = config
    if not result and state_outputs:
        last_state_id = next(reversed(state_outputs))
        result["result"] = state_outputs[last_state_id]
    return result


def _run_hook(
    hook,
    plugin,
    loop: LoopDefinition,
    inputs: dict[str, Any],
    state_outputs: dict[str, dict[str, Any]],
    error_message: str,
    tracker: BudgetTracker,
) -> dict[str, Any]:
    if hook is None:
        return {}
    context = _build_context(loop, inputs, state_outputs, {"error": error_message}, tracker)
    hook_inputs = render_value(hook.inputs, context)
    if hook.message is not None and "message" not in hook_inputs:
        hook_inputs["message"] = hook.message
    pseudo_state = loop.states[0].__class__(
        id="hook",
        handler=hook.handler,
        inputs=hook_inputs,
        raw={"message": hook.message or error_message},
    )
    return plugin.execute_state(pseudo_state, hook_inputs, {"inputs": inputs, "states": state_outputs, "current_condition": None})


def _execute_subloop(loop: LoopDefinition, loop_ref: str, inputs: dict[str, Any], target: str) -> dict[str, Any]:
    for imported in loop.imports:
        if imported.name != loop_ref:
            continue
        if imported.loop is None:
            raise RuntimeError(f"Sub-loop '{loop_ref}' is not resolved")
        result = execute_loop(imported.loop, inputs=inputs, target=target)
        if not result.success:
            raise RuntimeError(f"Sub-loop '{loop_ref}' failed: {result.error or 'execution failed'}")
        return result.final_outputs
    raise RuntimeError(f"Unknown sub-loop '{loop_ref}'")


def _execute_parallel_states(
    loop: LoopDefinition,
    parent_state,
    states_by_id: dict[str, Any],
    plugin,
    target: str,
    resolved_inputs: dict[str, Any],
    state_outputs: dict[str, dict[str, Any]],
    current_outputs: dict[str, Any],
    tracker: BudgetTracker,
) -> list[dict[str, Any]]:
    parallel_state_ids = list(parent_state.raw.get("parallel", []))
    if not parallel_state_ids:
        return []

    base_context = _build_context(loop, resolved_inputs, state_outputs, current_outputs, tracker)

    def run_parallel(state_id: str) -> dict[str, Any]:
        tracker.tick()
        branch_state = states_by_id[state_id]
        should_run = True
        if branch_state.condition and branch_state.handler != "core.condition":
            should_run = bool(resolve_condition(branch_state.condition, base_context))
        if not should_run:
            return {"state_id": state_id, "outputs": {"skipped": True}, "skipped": True}

        runtime_inputs = render_value(branch_state.inputs, base_context)
        runtime_condition = None
        if "condition" in branch_state.raw:
            runtime_condition = render_value(branch_state.raw["condition"], base_context)
        outputs = _execute_state_with_guards(
            loop=loop,
            state=branch_state,
            plugin=plugin,
            target=target,
            runtime_inputs=runtime_inputs,
            resolved_inputs=resolved_inputs,
            state_outputs=state_outputs,
            runtime_condition=runtime_condition,
        )
        return {"state_id": state_id, "outputs": outputs, "skipped": False}

    with ThreadPoolExecutor(max_workers=len(parallel_state_ids)) as executor:
        futures = [executor.submit(run_parallel, state_id) for state_id in parallel_state_ids]
        return [future.result() for future in futures]


def _execute_state_with_guards(
    loop: LoopDefinition,
    state,
    plugin,
    target: str,
    runtime_inputs: dict[str, Any],
    resolved_inputs: dict[str, Any],
    state_outputs: dict[str, dict[str, Any]],
    runtime_condition: Any,
) -> dict[str, Any]:
    guard = state.raw.get("guard", {}) if isinstance(state.raw, dict) else {}
    retries = int(guard.get("retry", 0) or 0)
    attempts = retries + 1
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            runtime_context = {
                "loop": asdict(loop),
                "inputs": resolved_inputs,
                "states": state_outputs,
                "current_condition": runtime_condition,
                "attempt": attempt,
                "max_attempts": attempts,
                "backoff": guard.get("backoff"),
            }
            if state.loop_ref:
                result = _execute_subloop(loop, state.loop_ref, runtime_inputs, target)
            else:
                result = plugin.execute_state(state, runtime_inputs, runtime_context)
            result["__retry_attempts__"] = attempt
            return result
        except Exception as exc:
            last_error = exc
            if attempt == attempts:
                break
    if last_error is None:
        raise RuntimeError(f"State '{state.id}' failed without error detail")
    if attempts == 1:
        raise last_error
    raise RuntimeError(
        f"State '{state.id}' failed after {attempts} attempt(s): {last_error}"
    )


def execute_loop_with_runtime_controls(
    loop: LoopDefinition,
    inputs: dict[str, Any] | None = None,
    target: str = "langchain",
    checkpoint_path: str | Path | None = None,
    resume_from: str | Path | None = None,
    max_steps: int | None = None,
) -> ExecutionResult:
    validate_loop_definition(loop)
    return _execute_loop(
        loop,
        inputs=inputs,
        target=target,
        checkpoint_path=checkpoint_path,
        resume_from=resume_from,
        max_steps=max_steps,
    )


def _persist_checkpoint(
    checkpoint_path: str | Path | None,
    loop: LoopDefinition,
    target: str,
    inputs: dict[str, Any],
    state_results: list[StateResult],
    state_outputs: dict[str, dict[str, Any]],
    last_outputs: dict[str, Any],
    tracker: BudgetTracker,
    next_state_id: str | None,
    completed: bool,
) -> None:
    if checkpoint_path is None:
        return
    save_checkpoint(
        checkpoint_path,
        {
            "loop_id": loop.id,
            "target": target,
            "inputs": inputs,
            "state_results": [
                {"state_id": item.state_id, "outputs": item.outputs, "skipped": item.skipped}
                for item in state_results
            ],
            "state_outputs": state_outputs,
            "last_outputs": last_outputs,
            "iterations": tracker.iterations,
            "cost_usd": tracker.cost_usd,
            "next_state_id": next_state_id,
            "completed": completed,
        },
    )


def _safe_render_outputs(
    loop: LoopDefinition,
    inputs: dict[str, Any],
    state_outputs: dict[str, dict[str, Any]],
    tracker: BudgetTracker,
) -> dict[str, Any]:
    try:
        return _render_declared_outputs(loop, inputs, state_outputs, tracker)
    except Exception:
        return {}


def _get_circuit_breaker_limit(loop: LoopDefinition) -> int | None:
    raw_loop = loop.raw.get("loop", {}) if isinstance(loop.raw, dict) else {}
    runtime = raw_loop.get("runtime", {}) if isinstance(raw_loop, dict) else {}
    limit = runtime.get("circuit_breaker_max_failures")
    if limit is None:
        return None
    return int(limit)
