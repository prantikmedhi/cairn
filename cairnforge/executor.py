from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .budget import BudgetExceededError, BudgetTracker
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
    if target not in PLUGIN_REGISTRY:
        raise ValueError(f"Unknown target '{target}'")

    resolved_inputs = _materialize_inputs(loop, inputs or {})
    plugin = PLUGIN_REGISTRY[target]
    tracker = BudgetTracker(loop.budget)
    current_state = get_start_state(loop)
    states_by_id = {state.id: state for state in loop.states}
    state_results: list[StateResult] = []
    state_outputs: dict[str, dict[str, Any]] = {}
    last_outputs: dict[str, Any] = {}

    try:
        while current_state is not None:
            tracker.tick()
            current_context = _build_context(loop, resolved_inputs, state_outputs, last_outputs, tracker)
            should_run = True
            if current_state.condition and current_state.handler != "core.condition":
                should_run = bool(resolve_condition(current_state.condition, current_context))

            if should_run:
                runtime_inputs = render_value(current_state.inputs, current_context)
                runtime_condition = None
                if "condition" in current_state.raw:
                    runtime_condition = render_value(current_state.raw["condition"], current_context)
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
            current_state = states_by_id.get(next_state_id) if next_state_id else None

        return ExecutionResult(
            loop_id=loop.id,
            success=True,
            final_outputs=_render_declared_outputs(loop, resolved_inputs, state_outputs, tracker),
            state_results=state_results,
            metadata={
                "target": target,
                "iterations": tracker.iterations,
                "cost_usd": tracker.cost_usd,
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
            metadata={"target": target, "iterations": tracker.iterations, "budget_exceeded": True},
        )
    except Exception as exc:
        hook_outputs = _run_hook(loop.on_error, plugin, loop, resolved_inputs, state_outputs, str(exc), tracker)
        return ExecutionResult(
            loop_id=loop.id,
            success=False,
            final_outputs=hook_outputs,
            state_results=state_results,
            error=str(exc),
            metadata={"target": target, "iterations": tracker.iterations},
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
