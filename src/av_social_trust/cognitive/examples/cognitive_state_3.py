"""Synthetic cognitive state with low automation trust and high perceived risk."""

from av_social_trust.car import CognitiveState


cognitive_state = CognitiveState(
    automation_trust=0.25,
    perceived_risk=0.8,
    workload=0.7,
)


if __name__ == "__main__":
    print(cognitive_state)
