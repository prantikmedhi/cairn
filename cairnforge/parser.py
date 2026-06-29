from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import (
    BudgetDefinition,
    HookDefinition,
    ImportDefinition,
    InputField,
    LoopDefinition,
    StateDefinition,
    TransitionDefinition,
)


class CairnParseError(ValueError):
    """Raised when a loop file cannot be parsed."""


def load_loop_file(path: str | Path) -> LoopDefinition:
    return _load_loop_file(Path(path), visited=set())


def _load_loop_file(path: Path, visited: set[Path]) -> LoopDefinition:
    path = Path(path)
    resolved = path.resolve()
    if resolved in visited:
        raise CairnParseError(f"Circular import detected while loading {path}")
    visited = set(visited)
    visited.add(resolved)
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise CairnParseError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise CairnParseError(f"{path} must contain mapping at document root")
    return parse_loop_document(payload, source_path=path, visited=visited)


def parse_loop_document(payload: dict[str, Any], source_path: Path | None = None, visited: set[Path] | None = None) -> LoopDefinition:
    if "cairn" not in payload:
        raise CairnParseError("Missing top-level 'cairn' version")
    if "loop" not in payload or not isinstance(payload["loop"], dict):
        raise CairnParseError("Missing top-level 'loop' object")

    loop = payload["loop"]
    states = [_parse_state(item) for item in loop.get("states", [])]
    transitions = [_parse_transition(item) for item in loop.get("transitions", [])]
    imports = [_parse_import(item, source_path, visited or set()) for item in loop.get("imports", [])]
    inputs = {
        name: InputField(
            type=str(config.get("type", "string")),
            required=bool(config.get("required", False)),
            description=str(config.get("description", "")),
            default=config.get("default"),
            properties=dict(config.get("properties", {})),
        )
        for name, config in dict(loop.get("inputs", {})).items()
    }

    return LoopDefinition(
        cairn_version=str(payload["cairn"]),
        id=str(loop.get("id", "")),
        name=str(loop.get("name", "")),
        version=str(loop.get("version", "0.1.0")),
        description=str(loop.get("description", "")),
        inputs=inputs,
        outputs=dict(loop.get("outputs", {})),
        budget=_parse_budget(loop.get("budget", {})),
        imports=imports,
        states=states,
        transitions=transitions,
        on_error=_parse_hook(loop.get("on_error")),
        on_budget_exceeded=_parse_hook(loop.get("on_budget_exceeded")),
        source_path=str(source_path) if source_path else None,
        raw=payload,
    )


def _parse_state(item: dict[str, Any]) -> StateDefinition:
    if not isinstance(item, dict):
        raise CairnParseError("Each state must be an object")
    return StateDefinition(
        id=str(item.get("id", "")),
        name=item.get("name"),
        handler=item.get("handler"),
        loop_ref=item.get("loop"),
        inputs=dict(item.get("inputs", {})),
        condition=item.get("condition"),
        timeout=item.get("timeout"),
        transitions=[_parse_transition(transition, default_from=item.get("id")) for transition in item.get("transitions", [])],
        raw=item,
    )


def _parse_transition(item: dict[str, Any], default_from: str | None = None) -> TransitionDefinition:
    if not isinstance(item, dict):
        raise CairnParseError("Each transition must be an object")
    from_state = item.get("from", default_from)
    return TransitionDefinition(
        from_state=str(from_state or ""),
        to_state=str(item.get("to", "")),
        condition=item.get("condition") or item.get("if"),
    )


def _parse_budget(item: Any) -> BudgetDefinition:
    if not isinstance(item, dict):
        return BudgetDefinition()
    return BudgetDefinition(
        max_cost_usd=item.get("max_cost_usd"),
        max_duration=item.get("max_duration"),
        max_iterations=item.get("max_iterations"),
    )


def _parse_import(item: Any, source_path: Path | None, visited: set[Path]) -> ImportDefinition:
    if not isinstance(item, dict):
        raise CairnParseError("Each import must be an object")
    name = str(item.get("name", ""))
    source = str(item.get("source", ""))
    if not name or not source:
        raise CairnParseError("Each import requires 'name' and 'source'")

    import_def = ImportDefinition(name=name, source=source)
    if "://" in source or source.startswith("cairnhub.com/"):
        return import_def
    if source_path is None:
        raise CairnParseError(f"Cannot resolve local import '{source}' without source path")
    resolved_path = (source_path.parent / source).resolve()
    import_def.resolved_path = str(resolved_path)
    import_def.loop = _load_loop_file(resolved_path, visited=visited)
    return import_def


def _parse_hook(item: Any) -> HookDefinition | None:
    if item is None:
        return None
    if not isinstance(item, dict):
        raise CairnParseError("Hooks must be objects")
    handler = item.get("handler")
    if not handler:
        raise CairnParseError("Hooks require 'handler'")
    return HookDefinition(
        handler=str(handler),
        inputs=dict(item.get("inputs", {})),
        message=item.get("message"),
    )
