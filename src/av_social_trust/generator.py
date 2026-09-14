"""Deterministic synthetic driving inputs for exercising the simulation.

These are invented situations, not participant data or a fitted cognitive model.
"""

from collections.abc import Iterator
from numbers import Integral

from av_social_trust.situation import Situation


def generate_situations(
    steps: int,
    *,
    block_size: int = 5,
    unavailable_steps: int = 0,
) -> Iterator[Situation]:
    """Alternate low/high complexity blocks, with optional initial unavailability.

    Every yielded Situation is independent. Counts refer to simulation cycles,
    not seconds. The sequence is reproducible without a random seed.
    """
    for name, value, minimum in (
        ("steps", steps, 0),
        ("block_size", block_size, 1),
        ("unavailable_steps", unavailable_steps, 0),
    ):
        if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}.")

    for cycle in range(steps):
        yield Situation(
            task_complexity=(cycle // block_size) % 2,
            automation_available=cycle >= unavailable_steps,
        )


if __name__ == "__main__":
    for situation in generate_situations(6, block_size=2, unavailable_steps=1):
        print(situation)
