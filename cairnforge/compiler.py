from __future__ import annotations

from dataclasses import dataclass

from .models import LoopDefinition, StateDefinition


@dataclass(slots=True)
class CompiledLoop:
    loop_id: str
    state_order: list[str]
    transition_count: int
    target: str = "core"


@dataclass(slots=True)
class CompiledState:
    state_id: str
    handler: str
    target: str
    runtime: str


def compile_loop(loop: LoopDefinition, target: str = "core") -> CompiledLoop:
    """Create small execution plan for introspection and debugging."""

    inline_transitions = sum(len(state.transitions) for state in loop.states)
    return CompiledLoop(
        loop_id=loop.id,
        state_order=[state.id for state in loop.states],
        transition_count=len(loop.transitions) + inline_transitions,
        target=target,
    )


def compile_state(state: StateDefinition, target: str = "core", runtime: str = "builtin") -> CompiledState:
    return CompiledState(
        state_id=state.id,
        handler=state.handler or "",
        target=target,
        runtime=runtime,
    )
