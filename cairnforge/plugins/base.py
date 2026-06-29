from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from cairnforge.models import StateDefinition


class BasePlugin(ABC):
    name: str

    def get_metadata(self) -> dict[str, Any]:
        return {"plugin": self.name}

    @abstractmethod
    def execute_state(self, state: StateDefinition, resolved_inputs: dict[str, Any], runtime_context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
