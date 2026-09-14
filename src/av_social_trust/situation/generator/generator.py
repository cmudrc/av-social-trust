"""
Synthetic, temporally correlated driving conditions for simulation checks.
"""

from numbers import Integral, Real

import numpy as np
from av_social_trust.situation.situation import Situation


class SituationGenerator:
    """
    Generate two independent binary Markov processes, one per situation field.

    Each probability p specifies a marginal probability: high complexity or
    available automation. The first sample uses p. Subsequent samples use
    P(next=1 | previous) = p + persistence * (previous - p).
    This preserves p as the stationary probability while creating runs of
    similar conditions. A finite series need not have exactly that proportion.

    Persistence 0 gives independent samples; 1 freezes the initial value.
    Intermediate values encourage longer runs as persistence increases.
    Durations are measured in calls/cycles, not seconds. These synthetic
    processes are not fitted to Sibi's data and do not model dependence
    between complexity and automation availability.
    """

    def __init__(
        self,
        rng_seed: int | None = None,
        automation_availability_probability: float = 1.0,
        task_complexity_probability: float = 0.2,
        *,
        task_complexity_persistence: float = 0.9,
        automation_availability_persistence: float = 0.9,
    ):
        for name, value in (
            ("automation_availability_probability", automation_availability_probability),
            ("task_complexity_probability", task_complexity_probability),
            ("task_complexity_persistence", task_complexity_persistence),
            ("automation_availability_persistence", automation_availability_persistence),
        ):
            if isinstance(value, bool) or not isinstance(value, Real) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be a real number between 0 and 1.")
        self.rng = np.random.default_rng(rng_seed)
        self.automation_availability_probability = automation_availability_probability
        self.task_complexity_probability = task_complexity_probability
        self.task_complexity_persistence = task_complexity_persistence
        self.automation_availability_persistence = automation_availability_persistence
        self._previous: tuple[int, bool] | None = None

    def generate(self) -> Situation:
        """
        Advance the time series by one cycle and return a fresh situation.
        """
        complexity_probability = self.task_complexity_probability
        availability_probability = self.automation_availability_probability
        if self._previous is not None:
            complexity, available = self._previous
            complexity_probability += self.task_complexity_persistence * (
                complexity - complexity_probability
            )
            availability_probability += self.automation_availability_persistence * (
                available - availability_probability
            )

        complexity_draw, availability_draw = self.rng.random(2)
        situation = Situation(
            task_complexity=int(complexity_draw < complexity_probability),
            automation_available=bool(availability_draw < availability_probability),
        )
        # Keep values separately so callers cannot alter the process by mutating
        # a previously returned Situation.
        self._previous = (situation.task_complexity, situation.automation_available)
        return situation

    def generate_series(self, steps: int) -> list[Situation]:
        """
        Return the next steps situations, continuing the existing series.
        """
        if isinstance(steps, bool) or not isinstance(steps, Integral) or steps < 0:
            raise ValueError("steps must be a nonnegative integer.")
        return [self.generate() for _ in range(steps)]


if __name__ == "__main__":
    generator = SituationGenerator(
        rng_seed=7,
        task_complexity_probability=0.4,
        automation_availability_probability=0.8,
        task_complexity_persistence=0.8,
        automation_availability_persistence=0.9,
    )
    for cycle, situation in enumerate(generator.generate_series(20), start=1):
        print(f"Cycle {cycle}: {situation}")
