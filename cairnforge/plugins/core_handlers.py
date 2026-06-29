from __future__ import annotations

from typing import Any

from cairnforge.models import StateDefinition


def execute_core_handler(target: str, state: StateDefinition, resolved_inputs: dict[str, Any], runtime_context: dict[str, Any]) -> dict[str, Any]:
    handler = state.handler or ""
    if handler in {"core.collect", "core.set", f"{target}.collect"}:
        return dict(resolved_inputs)
    if handler in {"core.template", f"{target}.prompt"}:
        return dict(resolved_inputs)
    if handler == "core.condition":
        condition = runtime_context.get("current_condition")
        return {"passed": bool(condition)}
    if handler == "core.echo":
        return {"value": resolved_inputs}
    if handler == "core.fail":
        message = resolved_inputs.get("message", state.raw.get("message", "State requested failure"))
        raise RuntimeError(str(message))
    if handler == "core.flaky":
        attempt = int(runtime_context.get("attempt", 1))
        fail_until = int(resolved_inputs.get("fail_until_attempt", 0))
        if attempt <= fail_until:
            message = resolved_inputs.get("message", f"Flaky state failed on attempt {attempt}")
            raise RuntimeError(str(message))
        payload = dict(resolved_inputs)
        payload["attempt"] = attempt
        payload["recovered"] = True
        return payload
    raise RuntimeError(f"Unsupported handler '{handler}' for target '{target}'")
