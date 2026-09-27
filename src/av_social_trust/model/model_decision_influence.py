"""Original model with social influence applied to usage opinions."""

from copy import deepcopy
from dataclasses import asdict

from av_social_trust.car import Car
from av_social_trust.cognitive import CognitiveState
from av_social_trust.consensus import degroot_step, normalize_trust_matrix
from av_social_trust.decision import cognitive_to_opinion, decide_automation
from av_social_trust.cognitive import update_cognitive_state
from av_social_trust.situation import Situation
from av_social_trust.trust import trust_step


class Model:
    """Run the original decision-level social-influence model.

    Each cycle updates personal cognition, forms private usage opinions, applies
    one DeGroot discussion round to those opinions, learns social trust from
    the private opinions, and lets the driver act on their influenced opinion.
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

        next_cognition = [
            update_cognitive_state(CognitiveState(**values), situation)
            for values in self.state["cognitive_states"]
        ]
        private_opinions = [cognitive_to_opinion(state) for state in next_cognition]

        influence_matrix = normalize_trust_matrix(old_trust)
        next_opinions = degroot_step(private_opinions, influence_matrix)

        next_trust = trust_step(
            opinion_vector=private_opinions,
            trust_matrix=old_trust,
            learning_rate_matrix=self.state["learning_rate_matrix"],
            homophilic_normative_tradeoff_matrix=self.state[
                "homophilic_normative_tradeoff_matrix"
            ],
            connection_mask_matrix=self.state["connection_mask_matrix"],
        )

        automation_on = decide_automation(
            next_opinions[0], automation_available=situation.automation_available
        )

        next_state = deepcopy(self.state)
        next_state["cognitive_states"] = [asdict(state) for state in next_cognition]
        next_state["opinion_vector"] = next_opinions.tolist()
        next_state["trust_matrix"] = next_trust.tolist()
        next_state["automation_on"] = automation_on
        self.state = next_state
        self.cycle += 1

        self.history.append({
            "cycle": self.cycle,
            "situation": asdict(situation),
            "private_opinion_vector": deepcopy(private_opinions),
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
