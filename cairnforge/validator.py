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


def validate_loop_definition(loop: LoopDefinition, seen_paths: set[str] | None = None) -> None:
    schema = load_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(loop.raw), key=lambda item: list(item.path))
    if errors:
        error = errors[0]
        path = ".".join(str(part) for part in error.path) or "<root>"
        raise CairnValidationError(f"Schema validation failed at {path}: {error.message}")

    seen_paths = set(seen_paths or set())
    if loop.source_path:
        if loop.source_path in seen_paths:
            raise CairnValidationError(f"Circular sub-loop import detected for {loop.source_path}")
        seen_paths.add(loop.source_path)

    if not loop.id:
        raise CairnValidationError("Loop id is required")
    if not loop.name:
        raise CairnValidationError("Loop name is required")
    if not loop.states:
        raise CairnValidationError("Loop must contain at least one state")

    import_names: list[str] = []
    for imported in loop.imports:
        if not imported.name:
            raise CairnValidationError("Import name is required")
        if imported.name in import_names:
            raise CairnValidationError(f"Duplicate import name '{imported.name}'")
        import_names.append(imported.name)
        if imported.loop is None and imported.resolved_path is None:
            raise CairnValidationError(
                f"Import '{imported.name}' uses unsupported source '{imported.source}'. "
                "Phase 2 currently supports local file imports only."
            )

    state_ids: list[str] = []
    for state in loop.states:
        if not state.id:
            raise CairnValidationError("Every state requires id")
        if state.id in state_ids:
            raise CairnValidationError(f"Duplicate state id '{state.id}'")
        state_ids.append(state.id)
        if bool(state.handler) == bool(state.loop_ref):
            raise CairnValidationError(f"State '{state.id}' must define exactly one of handler or loop")
        if state.loop_ref and state.loop_ref not in import_names:
            raise CairnValidationError(f"State '{state.id}' references unknown sub-loop '{state.loop_ref}'")
        for parallel_state_id in state.raw.get("parallel", []) if isinstance(state.raw, dict) else []:
            if parallel_state_id not in state_ids and parallel_state_id not in [item.id for item in loop.states]:
                raise CairnValidationError(f"State '{state.id}' references unknown parallel state '{parallel_state_id}'")

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

    for imported in loop.imports:
        if imported.loop is not None:
            validate_loop_definition(imported.loop, seen_paths=seen_paths)
