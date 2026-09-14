"""Personal cognition, social usage preferences, trust learning, and reliance."""

from copy import deepcopy
from dataclasses import asdict
from numbers import Integral

from av_social_trust.car import Car
from av_social_trust.cognitive import CognitiveState
from av_social_trust.consensus import degroot_step, normalize_trust_matrix
from av_social_trust.decision import cognitive_to_opinion, decide_automation
from av_social_trust.cognitive import update_cognitive_state
from av_social_trust.situation import Situation
from av_social_trust.trust import trust_step


class Model:
    """
    Run a simulation using an independent copy of a Car's initial state.

    Each cycle updates personal cognition, forms private usage preferences,
    runs one discussion round, learns social trust, and decides driver reliance.
    Personal cognition follows affine dynamics with synthetic coefficients.
    Fitted participant parameters and attention effects are pending. Coefficients
    currently apply per cycle; cycles do not yet represent calibrated seconds.
    """

    def __init__(
        self,
        car: Car
    ):
        self.state = car.to_state()
        self.cycle = 0
        self.history = []

    def step(
            self,
            situation: Situation | dict | None = None
        ) -> dict:
        """
        Advance one cycle and return an independent copy of the new state.

        A missing situation means low complexity with automation available.
        Dictionaries are accepted for existing callers. Availability constrains
        the final decision; task complexity drives the synthetic personal update. The
        original Car is unchanged, and failed updates do not commit a cycle.
        """
        if situation is None:
            situation = Situation()
        elif isinstance(situation, dict):
            situation = Situation(**situation)
        elif isinstance(situation, Situation):
            situation = Situation(**asdict(situation))
        else:
            raise TypeError("situation must be a Situation, dict, or None.")

        old_trust = self.state["trust_matrix"]

        # Advance each person's cognition using synthetic affine dynamics.
        # TODO: Supply participant-specific coefficients once available.
        next_cognition = [
            update_cognitive_state(CognitiveState(**values), situation)
            for values in self.state["cognitive_states"]
        ]
        # Fresh private preferences use all three cognitive components. The
        # decision rule's default thresholds are synthetic sanity-check values.
        private_opinions = [cognitive_to_opinion(state) for state in next_cognition]

        # Discussion: update opinions through social influence using the OLD trust.
        influence_matrix = normalize_trust_matrix(old_trust)
        next_opinions = degroot_step(private_opinions, influence_matrix)

        # Trust learning: interpersonal and self-trust from the PRIVATE opinions.
        # These new trust values affect the next cycle, not the current one.
        next_trust = trust_step(
            opinion_vector=private_opinions,
            trust_matrix=old_trust,
            learning_rate_matrix=self.state["learning_rate_matrix"],
            homophilic_normative_tradeoff_matrix=self.state[
                "homophilic_normative_tradeoff_matrix"
            ],
            connection_mask_matrix=self.state["connection_mask_matrix"],
        )

        # Car snapshots are driver-first. Passengers influence the preference,
        # but only the driver decides the shared vehicle's automation mode.
        automation_on = decide_automation(
            next_opinions[0], automation_available=situation.automation_available
        )

        # Commit: adopt the new opinions and raw trust together.
        next_state = deepcopy(self.state)
        next_state["cognitive_states"] = [asdict(state) for state in next_cognition]
        next_state["opinion_vector"] = next_opinions.tolist()
        next_state["trust_matrix"] = next_trust.tolist()
        next_state["automation_on"] = automation_on
        self.state = next_state
        self.cycle += 1

        # History: save a snapshot so later cycles cannot overwrite earlier results.
        self.history.append({
            "cycle": self.cycle,
            "situation": asdict(situation),
            "private_opinion_vector": deepcopy(private_opinions),
            "influence_matrix": influence_matrix.tolist(),
            "state": deepcopy(self.state),
        })
        return deepcopy(self.state)

    def run(self, steps: int) -> dict:
        """
        Run exactly `steps` additional cycles and return the final state.

        History contains one record per completed cycle, starting at cycle 1.
        Use step(situation=...) directly when supplying changing conditions.
        """
        if isinstance(steps, bool) or not isinstance(steps, Integral) or steps < 0:
            raise ValueError("steps must be a nonnegative integer.")

        for _ in range(steps):
            self.step()

        return deepcopy(self.state)
