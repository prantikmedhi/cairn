from __future__ import annotations

from typing import Any

from cairnforge.models import StateDefinition

from .base import BasePlugin


class LangChainPlugin(BasePlugin):
    """
    Phase 1 proof-of-concept plugin.

    This does not depend on external LangChain objects yet. It gives Cairn a
    stable target named "langchain" so loops can be validated and executed
    end-to-end while plugin contract stays small.
    """

    name = "langchain"

    def execute_state(self, state: StateDefinition, resolved_inputs: dict[str, Any], runtime_context: dict[str, Any]) -> dict[str, Any]:
        handler = state.handler or ""
        if handler in {"core.collect", "core.set", "langchain.collect"}:
            return dict(resolved_inputs)
        if handler in {"core.template", "langchain.prompt"}:
            return dict(resolved_inputs)
        if handler == "core.condition":
            condition = runtime_context.get("current_condition")
            return {"passed": bool(condition)}
        if handler == "core.echo":
            return {"value": resolved_inputs}
        if handler == "core.fail":
            message = resolved_inputs.get("message", state.raw.get("message", "State requested failure"))
            raise RuntimeError(str(message))
        raise RuntimeError(f"Unsupported handler '{handler}' for target '{self.name}'")
