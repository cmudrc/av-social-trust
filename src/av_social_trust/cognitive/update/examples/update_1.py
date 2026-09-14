"""Drive cognitive updates with a reproducible synthetic situation series."""

from av_social_trust.cognitive import CognitiveState, update_cognitive_state
from av_social_trust.cognitive.update import SYNTHETIC_PARAMETERS
from av_social_trust.situation import SituationGenerator


def main() -> None:
    # The situation source is outside the cognitive model. Later it can read
    # recorded driving conditions while returning the same Situation objects.
    generator = SituationGenerator(
        rng_seed=7,
        task_complexity_probability=0.4,
        automation_availability_probability=0.8,
        task_complexity_persistence=0.8,
    )
    cognition = CognitiveState(automation_trust=0.75, perceived_risk=0.6, workload=0.4)
    participant_parameters = SYNTHETIC_PARAMETERS

    for cycle, situation in enumerate(generator.generate_series(20), start=1):
        cognition = update_cognitive_state(
            cognition, situation, parameters=participant_parameters
        )
        print(
            f"Cycle {cycle:2}: complexity={situation.task_complexity}, "
            f"available={situation.automation_available}, "
            f"trust={cognition.automation_trust:.3f}, "
            f"risk={cognition.perceived_risk:.3f}, "
            f"workload={cognition.workload:.3f}"
        )


if __name__ == "__main__":
    main()
