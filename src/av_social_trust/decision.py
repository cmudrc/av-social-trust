"""
Form a private automation-use opinion, then decide after social influence.

The maximum threshold margin is a proposed continuous extension of Sibi's
binary OR rule, not a fitted probability or an automation-trust value.
"""

from numbers import Real

from av_social_trust.cognitive import CognitiveState


def _validate_range(value: float, name: str, lower: float, upper: float) -> None:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a real number.")
    if not lower <= value <= upper:
        raise ValueError(f"{name} must be between {lower} and {upper}.")


def cognitive_to_opinion(
    cognitive_state: CognitiveState,
    *,
    trust_threshold: float = 0.5,
    risk_threshold: float = 0.5,
    workload_threshold: float = 0.5,
) -> float:
    """
    Return a private usage preference in [-1, 1] without changing cognition.

    A positive opinion means at least one condition holds: high automation
    trust, low perceived risk, or high workload relative to its threshold.
    Equality alone does not activate automation. The 0.5 defaults are synthetic
    sanity-check thresholds; fitted participant thresholds can be supplied.

    All inputs must lie in [0, 1]. Comparing their margins assumes comparable
    scales. Pass the resulting opinions to DeGroot before deciding actual use.
    """
    if not isinstance(cognitive_state, CognitiveState):
        raise TypeError("cognitive_state must be a CognitiveState instance.")

    for name, value in (
        ("automation_trust", cognitive_state.automation_trust),
        ("perceived_risk", cognitive_state.perceived_risk),
        ("workload", cognitive_state.workload),
        ("trust_threshold", trust_threshold),
        ("risk_threshold", risk_threshold),
        ("workload_threshold", workload_threshold),
    ):
        _validate_range(value, name, 0.0, 1.0)

    return float(max(
        cognitive_state.automation_trust - trust_threshold,
        risk_threshold - cognitive_state.perceived_risk,
        cognitive_state.workload - workload_threshold,
    ))


def decide_automation(opinion: float, *, automation_available: bool = True) -> bool:
    """Turn automation on only for an available system and a positive opinion.

    Use the driver's socially updated opinion. Zero and negative opinions
    select manual operation. Availability constrains use, not private opinion.
    """
    _validate_range(opinion, "opinion", -1.0, 1.0)
    if not isinstance(automation_available, bool):
        raise TypeError("automation_available must be a bool.")
    return bool(automation_available and opinion > 0.0)


if __name__ == "__main__":
    cognitive_state = CognitiveState(
        automation_trust=0.3,
        perceived_risk=0.7,
        workload=0.8,
    )
    opinion = cognitive_to_opinion(cognitive_state)
    print(f"Private opinion: {opinion:.2f}")
    # With no social influence, the private opinion is also the final opinion.
    print(f"Automation on: {decide_automation(opinion)}")
