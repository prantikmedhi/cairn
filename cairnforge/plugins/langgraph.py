from __future__ import annotations

import importlib
from typing import Any

from cairnforge.compiler import compile_state
from cairnforge.models import StateDefinition

from .base import BasePlugin
from .core_handlers import execute_core_handler


class LangGraphPlugin(BasePlugin):
    name = "langgraph"

    def execute_state(self, state: StateDefinition, resolved_inputs: dict[str, Any], runtime_context: dict[str, Any]) -> dict[str, Any]:
        state_graph = self._load_state_graph()
        if state_graph is None:
            return self._execute_builtin(state, resolved_inputs, runtime_context)

        try:
            return self._execute_via_langgraph(state, resolved_inputs, runtime_context, state_graph)
        except Exception:
            return self._execute_builtin(state, resolved_inputs, runtime_context)

    def get_metadata(self) -> dict[str, Any]:
        runtime_mode = "langgraph-native" if self._load_state_graph() is not None else "builtin-fallback"
        return {"plugin": self.name, "runtime_mode": runtime_mode}

    def _execute_builtin(self, state: StateDefinition, resolved_inputs: dict[str, Any], runtime_context: dict[str, Any]) -> dict[str, Any]:
        return execute_core_handler(self.name, state, resolved_inputs, runtime_context)

    def _execute_via_langgraph(
        self,
        state: StateDefinition,
        resolved_inputs: dict[str, Any],
        runtime_context: dict[str, Any],
        graph_module,
    ) -> dict[str, Any]:
        compiled = compile_state(state, target=self.name, runtime="langgraph-native")
        state_graph_cls = getattr(graph_module, "StateGraph")
        start = getattr(graph_module, "START", "__start__")
        end = getattr(graph_module, "END", "__end__")

        def run(payload: dict[str, Any]) -> dict[str, Any]:
            outputs = self._execute_builtin(state, resolved_inputs, runtime_context)
            return {"outputs": outputs, "compiled_state": compiled.state_id, "payload": payload}

        graph = state_graph_cls(dict)
        graph.add_node(compiled.state_id, run)
        graph.add_edge(start, compiled.state_id)
        graph.add_edge(compiled.state_id, end)
        result = graph.compile().invoke({"inputs": resolved_inputs, "state": compiled.state_id})
        if isinstance(result, dict) and "outputs" in result and isinstance(result["outputs"], dict):
            return result["outputs"]
        if isinstance(result, dict):
            return result
        raise RuntimeError(f"LangGraph state '{state.id}' returned non-dict output")

    @staticmethod
    def _load_state_graph():
        try:
            return importlib.import_module("langgraph.graph")
        except ImportError:
            return None
