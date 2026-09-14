"""A simple simulation loop combining opinion consensus and trust learning."""

from copy import deepcopy
from numbers import Integral

from ..car import Car


class Model:
    """
    Run a simulation using an independent copy of a Car's initial state.

    Each cycle performs one social opinion update and one trust update.
    Personal experience, attention effects, and driving decisions are not
    implemented yet. Cycle numbers do not imply a physical timestep.
    """

    def __init__(
        self,
        car: Car
    ):
        self.state = car.to_state()
        self.cycle = 0
        self.history = []

    def step(self, situation: dict | None = None) -> dict:
        """
        Advance one cycle and return an independent copy of the new state.

        `situation` will supply driving conditions to the personal model.
        For now, it is only recorded in history. The original Car is unchanged.
        """
        from ..consensus import degroot_step, normalize_trust_matrix
        from ..trust import trust_step

        old_trust = self.state["trust_matrix"]

        # 1. Update personal opinions through driving experience.
        # TODO: Call Sibi's cognitive model here, using the situation and
        # each participant's state/parameters. Convert its automation trust
        # to our [-1, 1] opinion scale. For now, experience changes nothing.
        private_opinions = deepcopy(self.state["opinion_vector"])
        # private_opinions = update_personal_opinions(self.state, situation)

        # 2. Update opinions through social influence using the OLD trust.
        influence_matrix = normalize_trust_matrix(old_trust)
        next_opinions = degroot_step(private_opinions, influence_matrix)

        # 3. Learn interpersonal and self-trust from the PRIVATE opinions.
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

        # 4. Decide whether the DRIVER uses automation.
        # TODO: Apply Sibi's decision rule after social influence, using the
        # driver's updated automation trust, risk, and workload. Respect
        # automation availability. No driving decision is simulated yet.

        # 5. Commit the new opinions and raw trust together.
        next_state = deepcopy(self.state)
        next_state["opinion_vector"] = next_opinions.tolist()
        next_state["trust_matrix"] = next_trust.tolist()
        self.state = next_state
        self.cycle += 1

        # 6. Save a snapshot so later cycles cannot overwrite earlier results.
        self.history.append({
            "cycle": self.cycle,
            "situation": deepcopy(situation),
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
