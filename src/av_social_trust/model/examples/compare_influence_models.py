"""Run the same car and situations through both social-influence models.

Run from the project root:
    python src/av_social_trust/model/examples/compare_influence_models.py

The decision-influence model applies DeGroot after private opinions form. The
cognition-influence model applies DeGroot to cognition first, after which every
occupant forms an individual opinion and decision. Only the driver's resulting
decision controls the vehicle in either model.

All values in this example are synthetic and cycles are not calibrated seconds.
"""

from statistics import mean

import av_social_trust as av
from av_social_trust.decision import cognitive_to_opinion


def _make_comparison_car() -> av.Car:
    """Create occupants who favor automation for different cognitive reasons.

    The driver initially perceives low risk, while the passenger initially has
    high automation trust. Their opposed trust/risk profiles make the difference
    between averaging decisions and averaging cognition easy to see.
    """
    car = av.Car()
    car.add_driver(
        agent_id=0,
        self_trust=0.5,
        cognitive_state=av.CognitiveState(
            automation_trust=0.1,
            perceived_risk=0.1,
            workload=0.0,
        ),
        self_trust_learning_rate=0.1,
    )
    car.add_passenger(
        agent_id=1,
        self_trust=0.5,
        cognitive_state=av.CognitiveState(
            automation_trust=0.9,
            perceived_risk=0.9,
            workload=0.0,
        ),
        self_trust_learning_rate=0.1,
    )
    car.connect_agents(
        agent_from_id=0,
        agent_to_id=1,
        trust=0.5,
        trust_learning_rate=0.2,
        homophilic_normative_tradeoff=0.5,
    )
    car.connect_agents(
        agent_from_id=1,
        agent_to_id=0,
        trust=0.5,
        trust_learning_rate=0.2,
        homophilic_normative_tradeoff=0.5,
    )
    return car


def _private_cognition_opinion(record: dict, agent_index: int) -> float:
    """Return the opinion implied by cognition before cognitive influence."""
    cognition = av.CognitiveState(
        **record["private_cognitive_states"][agent_index]
    )
    return cognitive_to_opinion(cognition)


def _mode(enabled: bool) -> str:
    return "ON" if enabled else "OFF"


def main(number_of_cycles: int = 8) -> None:
    situations = [
        av.Situation(task_complexity=1, automation_available=True)
        for _ in range(number_of_cycles)
    ]

    # Each constructor takes an independent snapshot of the same car. Both
    # models then receive the exact same ordered Situation objects.
    car = _make_comparison_car()
    decision_model = av.Model(car)
    cognition_model = av.CognitionInfluenceModel(car)
    decision_model.run(situations)
    cognition_model.run(situations)

    print("Comparison using the same occupants, trust, and situations")
    print("DI = decision-level influence; CI = cognition-level influence")
    print("Before -> after shows the driver's opinion around social influence.\n")
    print(
        "The driver initially favors automation because perceived risk is low;\n"
        "the passenger favors it because automation trust is high. All cycles\n"
        "use high task complexity with automation available.\n"
    )
    print(
        "Cycle  Situation       DI before -> after  Mode   "
        "CI before -> after  Driver decision  Mode"
    )

    different_modes = 0
    for decision_record, cognition_record in zip(
        decision_model.history, cognition_model.history
    ):
        situation = decision_record["situation"]
        complexity = "high" if situation["task_complexity"] else "low"
        availability = "available" if situation["automation_available"] else "unavailable"

        decision_before = decision_record["private_opinion_vector"][0]
        decision_after = decision_record["state"]["opinion_vector"][0]

        cognition_before = _private_cognition_opinion(cognition_record, 0)
        cognition_after = cognition_record["individual_opinion_vector"][0]
        cognition_decision = cognition_record["individual_decision_vector"][0]

        decision_mode = decision_record["state"]["automation_on"]
        cognition_mode = cognition_record["state"]["automation_on"]
        different_modes += decision_mode != cognition_mode

        print(
            f"{decision_record['cycle']:5}  {complexity:4}/{availability:11}  "
            f"{decision_before:+.3f} -> {decision_after:+.3f}   "
            f"{_mode(decision_mode):3}    "
            f"{cognition_before:+.3f} -> {cognition_after:+.3f}   "
            f"{str(cognition_decision):15}  {_mode(cognition_mode):3}"
        )

    decision_on = sum(
        record["state"]["automation_on"] for record in decision_model.history
    )
    cognition_on = sum(
        record["state"]["automation_on"] for record in cognition_model.history
    )
    final_decision_opinions = decision_model.state["opinion_vector"]
    final_cognition_opinions = cognition_model.state["opinion_vector"]

    print("\nSummary")
    print(f"  DI automation-ON cycles: {decision_on}/{number_of_cycles}")
    print(f"  CI automation-ON cycles: {cognition_on}/{number_of_cycles}")
    print(f"  Cycles with different executed modes: {different_modes}")
    print(
        "  Final mean occupant opinion: "
        f"DI={mean(final_decision_opinions):+.3f}, "
        f"CI={mean(final_cognition_opinions):+.3f}"
    )
    print("  Final raw trust matrix (DI):", decision_model.state["trust_matrix"])
    print("  Final raw trust matrix (CI):", cognition_model.state["trust_matrix"])
    print("\nDetailed intermediate values remain available in each model's history.")


if __name__ == "__main__":
    main()
