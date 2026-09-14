"""Synthetic cognitive state with high automation trust and low workload."""

from av_social_trust.cognitive import CognitiveState


cognitive_state = CognitiveState(
    automation_trust=0.8,
    perceived_risk=0.3,
    workload=0.2,
)


if __name__ == "__main__":
    print(cognitive_state)
