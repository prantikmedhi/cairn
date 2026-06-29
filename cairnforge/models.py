from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


JsonMap = dict[str, Any]


@dataclass(slots=True)
class InputField:
    type: str = "string"
    required: bool = False
    description: str = ""
    default: Any = None
    properties: JsonMap = field(default_factory=dict)


@dataclass(slots=True)
class BudgetDefinition:
    max_cost_usd: float | None = None
    max_duration: str | None = None
    max_iterations: int | None = None


@dataclass(slots=True)
class TransitionDefinition:
    from_state: str
    to_state: str
    condition: str | None = None


@dataclass(slots=True)
class HookDefinition:
    handler: str
    inputs: JsonMap = field(default_factory=dict)
    message: str | None = None


@dataclass(slots=True)
class ImportDefinition:
    name: str
    source: str
    resolved_path: str | None = None
    loop: "LoopDefinition | None" = None


@dataclass(slots=True)
class StateDefinition:
    id: str
    name: str | None = None
    handler: str | None = None
    loop_ref: str | None = None
    inputs: JsonMap = field(default_factory=dict)
    condition: str | None = None
    timeout: str | None = None
    transitions: list[TransitionDefinition] = field(default_factory=list)
    raw: JsonMap = field(default_factory=dict)


@dataclass(slots=True)
class LoopDefinition:
    cairn_version: str
    id: str
    name: str
    version: str
    description: str = ""
    inputs: dict[str, InputField] = field(default_factory=dict)
    outputs: JsonMap = field(default_factory=dict)
    budget: BudgetDefinition = field(default_factory=BudgetDefinition)
    imports: list[ImportDefinition] = field(default_factory=list)
    states: list[StateDefinition] = field(default_factory=list)
    transitions: list[TransitionDefinition] = field(default_factory=list)
    on_error: HookDefinition | None = None
    on_budget_exceeded: HookDefinition | None = None
    source_path: str | None = None
    raw: JsonMap = field(default_factory=dict)


@dataclass(slots=True)
class StateResult:
    state_id: str
    outputs: JsonMap
    skipped: bool = False


@dataclass(slots=True)
class ExecutionResult:
    loop_id: str
    success: bool
    final_outputs: JsonMap
    state_results: list[StateResult]
    error: str | None = None
    metadata: JsonMap = field(default_factory=dict)
