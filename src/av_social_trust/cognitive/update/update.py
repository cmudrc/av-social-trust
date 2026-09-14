"""Personal cognitive update using synthetic affine model parameters."""

from av_social_trust.cognitive.state import CognitiveState
from av_social_trust.situation import Situation

from av_social_trust.cognitive.update import individual_model
from av_social_trust.cognitive.update.parameters import CognitiveParameters, SYNTHETIC_PARAMETERS


def update_cognitive_state(
    cognitive_state: CognitiveState,
    situation: Situation,
    *,
    parameters: CognitiveParameters = SYNTHETIC_PARAMETERS,
) -> CognitiveState:
    """
    Return the next cognitive state using the affine equations in Sibi's paper.

    The driving situation is shared, but this function is called separately
    for each person. Defaults are explicitly synthetic coefficients, not fitted
    measurements. Supply participant-specific parameters when available. Cognitive
    state carries forward between cycles; social preferences do not overwrite it.
    """
    next_state = individual_model.advance_cognition(
        cognition=cognitive_state,
        context=situation,
        parameters=parameters,
    )
    return next_state


if __name__ == "__main__":
    cognition = CognitiveState(
        automation_trust=0.75,
        perceived_risk=0.6,
        workload=0.4
    )
    print("Initial:", cognition)
    for cycle in range(1, 6):
        cognition = update_cognitive_state(cognition, Situation(task_complexity=1))
        print(f"Cycle {cycle}:", cognition)
