from __future__ import annotations

from dataclasses import dataclass

from .models import LoopDefinition


@dataclass(slots=True)
class CompiledLoop:
    loop_id: str
    state_order: list[str]
    transition_count: int


def compile_loop(loop: LoopDefinition) -> CompiledLoop:
    """Create small execution plan for introspection and debugging."""

    inline_transitions = sum(len(state.transitions) for state in loop.states)
    return CompiledLoop(
        loop_id=loop.id,
        state_order=[state.id for state in loop.states],
        transition_count=len(loop.transitions) + inline_transitions,
    )
