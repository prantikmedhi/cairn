from __future__ import annotations

from typing import Any

from cairnforge.models import StateDefinition

from .base import BasePlugin
from .core_handlers import execute_core_handler


class BuiltinFallbackPlugin(BasePlugin):
    def __init__(self, name: str) -> None:
        self.name = name

    def execute_state(self, state: StateDefinition, resolved_inputs: dict[str, Any], runtime_context: dict[str, Any]) -> dict[str, Any]:
        return execute_core_handler(self.name, state, resolved_inputs, runtime_context)

    def get_metadata(self) -> dict[str, Any]:
        return {"plugin": self.name, "runtime_mode": "builtin-fallback"}
