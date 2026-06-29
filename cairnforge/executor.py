from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .budget import BudgetExceededError, BudgetTracker
from .checkpoint import load_checkpoint, save_checkpoint
from .expression import render_value, resolve_condition
from .models import ExecutionResult, LoopDefinition, StateResult
from .plugins import LangChainPlugin
from .state_machine import choose_next_state, get_start_state
from .validator import validate_loop_definition


PLUGIN_REGISTRY = {
    "langchain": LangChainPlugin(),
}


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
                if current_state.loop_ref:
                    outputs = _execute_subloop(loop, current_state.loop_ref, runtime_inputs, target)
                else:
                    outputs = plugin.execute_state(
                        current_state,
                        runtime_inputs,
                        {
                            "loop": asdict(loop),
                            "inputs": resolved_inputs,
                            "states": state_outputs,
                            "current_condition": runtime_condition,
                        },
                    )
            else:
                outputs = {"skipped": True}

            state_outputs[current_state.id] = outputs
            state_results.append(StateResult(state_id=current_state.id, outputs=outputs, skipped=not should_run))
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
            metadata={"target": target, "iterations": tracker.iterations, "budget_exceeded": True, **plugin.get_metadata()},
        )
    except Exception as exc:
        hook_outputs = _run_hook(loop.on_error, plugin, loop, resolved_inputs, state_outputs, str(exc), tracker)
        return ExecutionResult(
            loop_id=loop.id,
            success=False,
            final_outputs=hook_outputs,
            state_results=state_results,
            error=str(exc),
            metadata={"target": target, "iterations": tracker.iterations, **plugin.get_metadata()},
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
