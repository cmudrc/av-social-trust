"""Cognitive-update parameter data, independent of the update implementation.

Defaults are synthetic, per-cycle settings for sanity checks. Replace them
with fitted participant coefficients only after checking their timestep and
state scaling. No Sibi data loader or file format is assumed here.
"""

from dataclasses import dataclass, fields
from math import isfinite
from numbers import Real


@dataclass(frozen=True)
class CognitiveParameters:
    """Nine coefficients for three independent updates: next = a*x + b*d + c.

    Synthetic defaults move trust toward 0.8 under low complexity and 0.3
    under high complexity. Risk and workload move toward 0.2 and 0.7,
    respectively. Each cycle closes 10% of the gap to these target values.
    These directions and speeds are illustrative modeling choices.
    """

    a_trust: float = 0.9
    b_trust: float = -0.05
    c_trust: float = 0.08
    a_risk: float = 0.9
    b_risk: float = 0.05
    c_risk: float = 0.02
    a_workload: float = 0.9
    b_workload: float = 0.05
    c_workload: float = 0.02

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
                raise ValueError(f"{field.name} must be a finite real number.")


SYNTHETIC_PARAMETERS = CognitiveParameters()
