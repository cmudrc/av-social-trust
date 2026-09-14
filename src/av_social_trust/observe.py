"""Personal cognitive update boundary for the future individual model."""

from dataclasses import asdict

from av_social_trust.cognitive import CognitiveState
from av_social_trust.situation import Situation


def observe(cognitive_state: CognitiveState, situation: Situation) -> CognitiveState:
    """
    Return an independent, unchanged cognitive state for now.

    The driving situation is shared, but this function is called separately
    for each person. Task complexity has no cognitive effect until an individual
    update is supplied. No measurements or participant coefficients are invented.
    """
    if not isinstance(cognitive_state, CognitiveState):
        raise TypeError("cognitive_state must be a CognitiveState instance.")
    if not isinstance(situation, Situation):
        raise TypeError("situation must be a Situation instance.")
    situation.validate()
    next_state = CognitiveState(**asdict(cognitive_state))

    # TODO: Connect Sibi's forward cognitive update once his code, participant
    # coefficients, input units, timestep, and boundary handling are available.
    # Proposed interface only; this is not a supplied API:
    # next_state = individual_model.advance_cognition(
    #     cognition=next_state,
    #     context=situation,
    #     parameters=participant_parameters,
    # )
    return next_state


if __name__ == "__main__":
    cognition = CognitiveState(automation_trust=0.75, perceived_risk=0.6, workload=0.4)
    print(observe(cognition, Situation(task_complexity=1)))
