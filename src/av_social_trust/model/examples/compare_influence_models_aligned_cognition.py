"""Compare both models when occupants have aligned cognitive profiles.

Run from the project root:
    python src/av_social_trust/model/examples/compare_influence_models_aligned_cognition.py

Unlike ``compare_influence_models.py``, this example gives both occupants the
same dominant reason for favoring automation and relatively high self-weight.
It demonstrates conditions under which decision-level and cognition-level
influence produce similar results.

All values are synthetic and cycles are not calibrated seconds.
"""

from statistics import mean

import av_social_trust as av
from av_social_trust.decision import cognitive_to_opinion


def _make_aligned_car() -> av.Car:
    car = av.Car()
    car.add_driver(
        agent_id=0,
        self_trust=0.8,
        cognitive_state=av.CognitiveState(
            automation_trust=0.65,
            perceived_risk=0.65,
            workload=0.20,
        ),
        self_trust_learning_rate=0.1,
    )
    car.add_passenger(
        agent_id=1,
        self_trust=0.8,
        cognitive_state=av.CognitiveState(
            automation_trust=0.75,
            perceived_risk=0.70,
            workload=0.25,
        ),
        self_trust_learning_rate=0.1,
    )
    car.connect_agents(
        agent_from_id=0,
        agent_to_id=1,
        trust=0.2,
        trust_learning_rate=0.1,
        homophilic_normative_tradeoff=0.5,
    )
    car.connect_agents(
        agent_from_id=1,
        agent_to_id=0,
        trust=0.2,
        trust_learning_rate=0.1,
        homophilic_normative_tradeoff=0.5,
    )
    return car


def _private_cognition_opinion(record: dict, agent_index: int) -> float:
    cognition = av.CognitiveState(
        **record["private_cognitive_states"][agent_index]
    )
    return cognitive_to_opinion(cognition)


def _mode(enabled: bool) -> str:
    return "ON" if enabled else "OFF"


def main(discussion_rounds: int = 1) -> None:
    complexities = [0, 0, 1, 1, 0, 1, 0, 0, 1, 0]
    situations = [
        av.Situation(task_complexity=value, automation_available=True)
        for value in complexities
    ]

    car = _make_aligned_car()
    decision_model = av.Model(car, discussion_rounds=discussion_rounds)
    cognition_model = av.CognitionInfluenceModel(
        car, discussion_rounds=discussion_rounds
    )
    decision_model.run(situations)
    cognition_model.run(situations)

    print("Low-divergence comparison using aligned cognitive profiles")
    print("DI = decision-level influence; CI = cognition-level influence")
    print(f"DeGroot discussion rounds per cycle: {discussion_rounds}")
    print(
        "Both occupants primarily favor automation because automation trust is\n"
        "above its threshold. Each initially assigns 80% of social weight to\n"
        "themselves and 20% to the other occupant.\n"
    )
    print(
        "Cycle  Complexity  DI before -> after  Mode   "
        "CI before -> after  Mode   |after difference|"
    )

    differences = []
    different_modes = 0
    for decision_record, cognition_record in zip(
        decision_model.history, cognition_model.history
    ):
        situation = decision_record["situation"]
        complexity = "high" if situation["task_complexity"] else "low"

        decision_before = decision_record["private_opinion_vector"][0]
        decision_after = decision_record["state"]["opinion_vector"][0]
        cognition_before = _private_cognition_opinion(cognition_record, 0)
        cognition_after = cognition_record["individual_opinion_vector"][0]

        decision_mode = decision_record["state"]["automation_on"]
        cognition_mode = cognition_record["state"]["automation_on"]
        difference = abs(decision_after - cognition_after)
        differences.append(difference)
        different_modes += decision_mode != cognition_mode

        print(
            f"{decision_record['cycle']:5}  {complexity:10}  "
            f"{decision_before:+.3f} -> {decision_after:+.3f}   "
            f"{_mode(decision_mode):3}    "
            f"{cognition_before:+.3f} -> {cognition_after:+.3f}   "
            f"{_mode(cognition_mode):3}       {difference:.4f}"
        )

    print("\nSummary")
    print(f"  Cycles with different executed modes: {different_modes}")
    print(f"  Mean absolute driver-opinion difference: {mean(differences):.4f}")
    print(f"  Maximum absolute driver-opinion difference: {max(differences):.4f}")
    print("  Final raw trust matrix (DI):", decision_model.state["trust_matrix"])
    print("  Final raw trust matrix (CI):", cognition_model.state["trust_matrix"])


if __name__ == "__main__":
    main()
