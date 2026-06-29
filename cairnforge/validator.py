from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from .budget import parse_duration_seconds
from .models import LoopDefinition


class CairnValidationError(ValueError):
    """Raised when loop definition is invalid."""


def load_schema() -> dict:
    schema_path = Path(__file__).resolve().parent.parent / "cairnlang" / "schema" / "cairn-1.0.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_loop_definition(loop: LoopDefinition) -> None:
    schema = load_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(loop.raw), key=lambda item: list(item.path))
    if errors:
        error = errors[0]
        path = ".".join(str(part) for part in error.path) or "<root>"
        raise CairnValidationError(f"Schema validation failed at {path}: {error.message}")

    if not loop.id:
        raise CairnValidationError("Loop id is required")
    if not loop.name:
        raise CairnValidationError("Loop name is required")
    if not loop.states:
        raise CairnValidationError("Loop must contain at least one state")

    state_ids: list[str] = []
    for state in loop.states:
        if not state.id:
            raise CairnValidationError("Every state requires id")
        if state.id in state_ids:
            raise CairnValidationError(f"Duplicate state id '{state.id}'")
        state_ids.append(state.id)
        if not state.handler:
            raise CairnValidationError(f"State '{state.id}' requires handler")

    known_states = set(state_ids)
    transitions = list(loop.transitions)
    for state in loop.states:
        transitions.extend(state.transitions)

    for transition in transitions:
        if transition.from_state not in known_states:
            raise CairnValidationError(f"Transition source '{transition.from_state}' does not exist")
        if transition.to_state not in known_states:
            raise CairnValidationError(f"Transition target '{transition.to_state}' does not exist")

    budget = loop.budget
    if budget.max_iterations is not None and int(budget.max_iterations) < 1:
        raise CairnValidationError("budget.max_iterations must be >= 1")
    if budget.max_cost_usd is not None and float(budget.max_cost_usd) < 0:
        raise CairnValidationError("budget.max_cost_usd must be >= 0")
    parse_duration_seconds(budget.max_duration)
