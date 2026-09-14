from av_social_trust.situation import SituationGenerator


generator = SituationGenerator(
    rng_seed=42,
    task_complexity_probability=0.4,
    automation_availability_probability=0.8,
    task_complexity_persistence=0.8,
    automation_availability_persistence=0.9,
)


if __name__ == "__main__":
    step = 1
    for _ in range(10):
        situation = generator.generate()
        print(
            f"Step {step}:"
            f"  Complexity={situation.task_complexity}",
            f"  Available={situation.automation_available}",
        )
        step += 1