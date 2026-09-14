from av_social_trust.situation import SituationGenerator


generator = SituationGenerator(
    rng_seed=42,
    task_complexity_probability=0.6,
    automation_availability_probability=0.6,
    task_complexity_persistence=0.3,
    automation_availability_persistence=0.3,
)


if __name__ == "__main__":
    situations = generator.generate_series(10)
    for step, situation in enumerate(situations):
        print(
            f"Step {step}:"
            f"  Complexity={situation.task_complexity}",
            f"  Available={situation.automation_available}",
        )