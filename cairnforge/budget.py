from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .models import BudgetDefinition


class BudgetExceededError(RuntimeError):
    """Raised when loop budget is exceeded."""


def parse_duration_seconds(value: str | None) -> int | None:
    if value is None:
        return None
    text = value.strip().lower()
    if text.endswith("ms"):
        return max(1, int(text[:-2]) // 1000)
    units = {"s": 1, "m": 60, "h": 3600}
    suffix = text[-1]
    if suffix not in units:
        raise ValueError(f"Unsupported duration format: {value}")
    return int(float(text[:-1]) * units[suffix])


@dataclass(slots=True)
class BudgetTracker:
    definition: BudgetDefinition
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    iterations: int = 0
    cost_usd: float = 0.0

    def tick(self) -> None:
        self.iterations += 1
        self.assert_within_limits()

    def add_cost(self, amount: float) -> None:
        self.cost_usd += amount
        self.assert_within_limits()

    def assert_within_limits(self) -> None:
        if self.definition.max_iterations is not None and self.iterations > self.definition.max_iterations:
            raise BudgetExceededError("Loop exceeded max_iterations budget")
        if self.definition.max_cost_usd is not None and self.cost_usd > float(self.definition.max_cost_usd):
            raise BudgetExceededError("Loop exceeded max_cost_usd budget")
        max_duration = parse_duration_seconds(self.definition.max_duration)
        if max_duration is not None:
            elapsed = (datetime.now(timezone.utc) - self.started_at).total_seconds()
            if elapsed > max_duration:
                raise BudgetExceededError("Loop exceeded max_duration budget")
