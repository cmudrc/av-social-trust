"""Synthetic cognitive state with moderately high automation trust."""

from av_social_trust import CognitiveState


cognitive_state = CognitiveState(
    automation_trust=0.75,
    perceived_risk=0.6,
    workload=0.4,
)


if __name__ == "__main__":
    print(cognitive_state)
