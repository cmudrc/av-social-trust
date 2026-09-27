"""Model with social influence applied to cognition before individual decisions."""

from copy import deepcopy
from dataclasses import asdict

from av_social_trust.car import Car
from av_social_trust.cognitive import CognitiveState, update_cognitive_state
from av_social_trust.consensus import degroot_step, normalize_trust_matrix
from av_social_trust.decision import cognitive_to_opinion, decide_automation
from av_social_trust.situation import Situation
from av_social_trust.trust import trust_step


_COGNITIVE_COMPONENTS = (
    "automation_trust",
    "perceived_risk",
    "workload",
)


def _influence_cognitive_states(
    private_states: list[CognitiveState],
    influence_matrix,
) -> list[CognitiveState]:
    """Apply the same scalar DeGroot matrix to each cognitive component."""
    influenced_components = {
        component: degroot_step(
            [getattr(state, component) for state in private_states],
            influence_matrix,
        )
        for component in _COGNITIVE_COMPONENTS
    }
    return [
        CognitiveState(**{
            component: float(influenced_components[component][index])
            for component in _COGNITIVE_COMPONENTS
        })
        for index in range(len(private_states))
    ]


class Model:
    """Run cognition-level social influence with driver-specific authority.

    Each cycle advances private cognition, applies one DeGroot discussion round
    to every cognitive component, forms one individual opinion and decision per
    occupant, and executes only the driver's decision. The existing IDETC-style
    trust rules learn from the resulting individual opinions.
    """

    def __init__(self, car: Car):
        self.state = car.to_state()
        self.cycle = 0
        self.history = []

    def step(self, situation: Situation) -> dict:
        """Advance one cycle and return an independent copy of the new state."""
        if not isinstance(situation, Situation):
            raise TypeError("situation must be a Situation instance.")
        situation = Situation(**asdict(situation))

        old_trust = self.state["trust_matrix"]
        private_cognition = [
            update_cognitive_state(CognitiveState(**values), situation)
            for values in self.state["cognitive_states"]
        ]

        influence_matrix = normalize_trust_matrix(old_trust)
        social_cognition = _influence_cognitive_states(
            private_cognition, influence_matrix
        )

        individual_opinions = [
            cognitive_to_opinion(state) for state in social_cognition
        ]
        individual_decisions = [
            decide_automation(opinion) for opinion in individual_opinions
        ]

        next_trust = trust_step(
            opinion_vector=individual_opinions,
            trust_matrix=old_trust,
            learning_rate_matrix=self.state["learning_rate_matrix"],
            homophilic_normative_tradeoff_matrix=self.state[
                "homophilic_normative_tradeoff_matrix"
            ],
            connection_mask_matrix=self.state["connection_mask_matrix"],
        )

        automation_on = decide_automation(
            individual_opinions[0],
            automation_available=situation.automation_available,
        )

        next_state = deepcopy(self.state)
        next_state["cognitive_states"] = [
            asdict(state) for state in social_cognition
        ]
        next_state["opinion_vector"] = deepcopy(individual_opinions)
        next_state["trust_matrix"] = next_trust.tolist()
        next_state["automation_on"] = automation_on
        self.state = next_state
        self.cycle += 1

        self.history.append({
            "cycle": self.cycle,
            "situation": asdict(situation),
            "private_cognitive_states": [
                asdict(state) for state in private_cognition
            ],
            "social_cognitive_states": [
                asdict(state) for state in social_cognition
            ],
            "individual_opinion_vector": deepcopy(individual_opinions),
            "individual_decision_vector": deepcopy(individual_decisions),
            "influence_matrix": influence_matrix.tolist(),
            "state": deepcopy(self.state),
        })
        return deepcopy(self.state)

    def run(self, situations: list[Situation]) -> dict:
        """Run one additional cycle per situation, in supplied list order."""
        if not isinstance(situations, list):
            raise TypeError("situations must be a list of Situation instances.")
        for index, situation in enumerate(situations):
            if not isinstance(situation, Situation):
                raise TypeError(f"situations[{index}] must be a Situation instance.")
            situation.validate()

        for situation in situations:
            self.step(situation)

        return deepcopy(self.state)
