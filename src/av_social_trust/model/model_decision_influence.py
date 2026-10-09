"""Original model with social influence applied to usage opinions."""

from copy import deepcopy
from dataclasses import asdict
from numbers import Integral

from av_social_trust.car import Car
from av_social_trust.cognitive import CognitiveState
from av_social_trust.consensus import normalize_trust_matrix, run_degroot
from av_social_trust.decision import cognitive_to_opinion, decide_automation
from av_social_trust.cognitive import update_cognitive_state
from av_social_trust.situation import Situation
from av_social_trust.trust import trust_step


class Model:
    """
    Run the original decision-level social-influence model.

    Each cycle updates personal cognition, forms private usage opinions, applies
    one DeGroot discussion round to those opinions, learns social trust from
    the private opinions, and forms final decisions that account for automation
    availability. Only the driver's final decision controls automation use.
    """

    def __init__(self, car: Car, *, discussion_rounds: int = 1):
        if (
            isinstance(discussion_rounds, bool)
            or not isinstance(discussion_rounds, Integral)
            or discussion_rounds < 0
        ):
            raise ValueError("discussion_rounds must be a nonnegative integer.")
        self.state = car.to_state()
        self.discussion_rounds = int(discussion_rounds)
        self.cycle = 0
        self.history = []

    def step(self, situation: Situation) -> dict:
        """
        Advance one cycle and return an independent copy of the new state.
        """
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
        next_opinions = run_degroot(
            private_opinions,
            influence_matrix,
            steps=self.discussion_rounds,
        )["opinion_vector"]
        individual_decisions = [
            decide_automation(
                opinion, automation_available=situation.automation_available
            )
            for opinion in next_opinions
        ]

        next_trust = trust_step(
            opinion_vector=private_opinions,
            trust_matrix=old_trust,
            learning_rate_matrix=self.state["learning_rate_matrix"],
            homophilic_normative_tradeoff_matrix=self.state[
                "homophilic_normative_tradeoff_matrix"
            ],
            connection_mask_matrix=self.state["connection_mask_matrix"],
        )

        # Car exports occupants in driver-first order. Execute that final decision.
        automation_on = individual_decisions[0]

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
            "individual_decision_vector": deepcopy(individual_decisions),
            "influence_matrix": influence_matrix.tolist(),
            "discussion_rounds": self.discussion_rounds,
            "state": deepcopy(self.state),
        })
        return deepcopy(self.state)

    def run(self, situations: list[Situation]) -> dict:
        """
        Run one additional cycle per situation, in supplied list order.
        """
        if not isinstance(situations, list):
            raise TypeError("situations must be a list of Situation instances.")
        for index, situation in enumerate(situations):
            if not isinstance(situation, Situation):
                raise TypeError(f"situations[{index}] must be a Situation instance.")
            situation.validate()

        for situation in situations:
            self.step(situation)

        return deepcopy(self.state)
