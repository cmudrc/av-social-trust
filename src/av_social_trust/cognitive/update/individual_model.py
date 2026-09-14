"""Affine cognitive dynamics following Sibi's hybrid-model structure.

Equations 3-5: https://arxiv.org/html/2512.05845v1#S2
Only the equation structure comes from the paper. Coefficients are supplied
separately; this module does not generate situations or choose parameters.
"""

from dataclasses import asdict

from av_social_trust.cognitive.state import CognitiveState
from av_social_trust.cognitive.update.parameters import CognitiveParameters
from av_social_trust.situation import Situation


def advance_cognition(
    *,
    cognition: CognitiveState,
    context: Situation,
    parameters: CognitiveParameters,
) -> CognitiveState:
    """
    Advance one cycle without mutating inputs or applying social influence.

    All three updates use the previous cognitive state and task complexity.
    Availability does not enter these equations. Our interface is an adapter
    design, not an API supplied by Sibi. His fitted coefficients require their
    original timestep (one second in the paper).

    Defaults preserve [0, 1]. Custom coefficients producing out-of-range states
    raise ValueError through CognitiveState validation; no clipping is applied.
    """
    if not isinstance(cognition, CognitiveState):
        raise TypeError("cognition must be a CognitiveState instance.")
    if not isinstance(context, Situation):
        raise TypeError("context must be a Situation instance.")
    if not isinstance(parameters, CognitiveParameters):
        raise TypeError("parameters must be a CognitiveParameters instance.")
    context.validate()
    previous = CognitiveState(**asdict(cognition))
    complexity = context.task_complexity

    return CognitiveState(
        automation_trust=(
            parameters.a_trust * previous.automation_trust
            + parameters.b_trust * complexity + parameters.c_trust
        ),
        perceived_risk=(
            parameters.a_risk * previous.perceived_risk
            + parameters.b_risk * complexity + parameters.c_risk
        ),
        workload=(
            parameters.a_workload * previous.workload
            + parameters.b_workload * complexity + parameters.c_workload
        ),
    )
