from __future__ import annotations

import importlib
from typing import Any

from cairnforge.compiler import compile_state
from cairnforge.models import StateDefinition

from .base import BasePlugin


class LangChainPlugin(BasePlugin):
    """
    Phase 1 plugin target for LangChain.

    If `langchain-core` is installed, supported handlers run through
    `RunnableLambda` so Cairn executes via real LangChain runnable primitives.
    Otherwise the plugin falls back to built-in execution with same semantics.
    """

    name = "langchain"

    def execute_state(self, state: StateDefinition, resolved_inputs: dict[str, Any], runtime_context: dict[str, Any]) -> dict[str, Any]:
        runnable_lambda = self._load_runnable_lambda()
        if runnable_lambda is None:
            return self._execute_builtin(state, resolved_inputs, runtime_context)

        compiled = compile_state(state, target=self.name, runtime="langchain-core")

        def run(_: dict[str, Any]) -> dict[str, Any]:
            return self._execute_builtin(state, resolved_inputs, runtime_context)

        runnable = runnable_lambda(run)
        result = runnable.invoke(
            {
                "state": compiled.state_id,
                "handler": compiled.handler,
                "inputs": resolved_inputs,
                "runtime_context": runtime_context,
            }
        )
        if not isinstance(result, dict):
            raise RuntimeError(f"LangChain runnable for state '{state.id}' returned non-dict output")
        return result

    def get_metadata(self) -> dict[str, Any]:
        runtime_mode = "langchain-core" if self._load_runnable_lambda() is not None else "builtin-fallback"
        return {"plugin": self.name, "runtime_mode": runtime_mode}

    def _execute_builtin(self, state: StateDefinition, resolved_inputs: dict[str, Any], runtime_context: dict[str, Any]) -> dict[str, Any]:
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

    @staticmethod
    def _load_runnable_lambda():
        try:
            module = importlib.import_module("langchain_core.runnables")
        except ImportError:
            return None
        return getattr(module, "RunnableLambda", None)
