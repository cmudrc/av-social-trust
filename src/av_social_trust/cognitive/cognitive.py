from dataclasses import dataclass


@dataclass
class CognitiveState:
    """A person's automation trust, perceived risk, and workload on [0, 1]."""

    automation_trust: float
    perceived_risk: float
    workload: float

    def __post_init__(self):
        for name in ("automation_trust", "perceived_risk", "workload"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1, got {value}.")

    @property
    def opinion(self) -> float:
        """Private usage preference using the decision rule's synthetic defaults.

        Socially updated opinions are stored separately in the model state.
        """
        from av_social_trust.decision import cognitive_to_opinion

        return cognitive_to_opinion(self)


if __name__ == "__main__":
    cognitive_state = CognitiveState(
        automation_trust=0.75,
        perceived_risk=0.6,
        workload=0.4,
    )
    print(cognitive_state)
    print(f"Opinion: {cognitive_state.opinion}")
