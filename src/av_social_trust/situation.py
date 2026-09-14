"""Shared driving conditions for a simulation cycle.

Sibi's hybrid model uses one external input, task complexity d(k). Its
experiment uses 0 for low complexity and 1 for high complexity (construction).
Automation availability is an additional constraint for our decision layer,
not the driver's engagement decision or another cognitive state.

Reference: https://arxiv.org/html/2512.05845v1, Sections II and III.
"""

from dataclasses import dataclass
from numbers import Integral


@dataclass
class Situation:
    """Binary task complexity and automation availability shared by all agents."""

    task_complexity: int = 0
    automation_available: bool = True

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        """Validate current values, including changes made after construction."""
        if (
            isinstance(self.task_complexity, bool)
            or not isinstance(self.task_complexity, Integral)
            or self.task_complexity not in (0, 1)
        ):
            raise ValueError("task_complexity must be 0 (low) or 1 (high).")
        if not isinstance(self.automation_available, bool):
            raise TypeError("automation_available must be a bool.")


if __name__ == "__main__":
    situation = Situation(task_complexity=1, automation_available=True)
    print(situation)
