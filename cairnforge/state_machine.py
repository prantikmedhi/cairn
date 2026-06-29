from __future__ import annotations

from typing import Iterable

from .expression import resolve_condition
from .models import LoopDefinition, StateDefinition, TransitionDefinition


def get_start_state(loop: LoopDefinition) -> StateDefinition:
    if not loop.states:
        raise ValueError("Loop must define at least one state")
    return loop.states[0]


def iter_transitions(loop: LoopDefinition, state: StateDefinition) -> Iterable[TransitionDefinition]:
    for transition in loop.transitions:
        if transition.from_state == state.id:
            yield transition
    for transition in state.transitions:
        if transition.from_state == state.id:
            yield transition


def choose_next_state(loop: LoopDefinition, state: StateDefinition, context: dict[str, object]) -> str | None:
    for transition in iter_transitions(loop, state):
        if transition.condition is None:
            return transition.to_state
        result = resolve_condition(transition.condition, context)
        if bool(result):
            return transition.to_state
    return None
