import unittest

from av_social_trust import Situation
from av_social_trust.situation import SituationGenerator


class SituationTests(unittest.TestCase):
    def test_situation_validation(self):
        self.assertEqual(Situation(), Situation(0, True))
        for value in (-1, 2, 0.5, True, "1", float("nan")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    Situation(task_complexity=value)  # type: ignore[arg-type]
        for value in (0, 1, "false", None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    Situation(automation_available=value)  # type: ignore[arg-type]

    def test_synthetic_sequence_is_reproducible_with_independent_snapshots(self):
        generator = SituationGenerator(rng_seed=7, automation_availability_probability=0.8)
        reference = SituationGenerator(rng_seed=7, automation_availability_probability=0.8)
        sequence = generator.generate_series(6)
        expected = reference.generate_series(6)
        self.assertEqual(len(sequence), 6)
        self.assertEqual(sequence, expected)
        for situation in sequence:
            self.assertIsInstance(situation, Situation)
            situation.validate()

        # Snapshots are independent even though the time series is correlated.
        sequence[0].task_complexity = 1 - sequence[0].task_complexity
        sequence[0].automation_available = not sequence[0].automation_available
        self.assertEqual(sequence[1:], expected[1:])
        sequence[-1].task_complexity = 1 - sequence[-1].task_complexity
        sequence[-1].automation_available = not sequence[-1].automation_available
        self.assertEqual(generator.generate(), reference.generate())

    def test_generator_rejects_invalid_counts(self):
        generator = SituationGenerator(rng_seed=42)
        self.assertEqual(generator.generate_series(0), [])
        for steps in (-1, True, 1.5):
            with self.subTest(steps=steps):
                with self.assertRaises(ValueError):
                    generator.generate_series(steps)  # type: ignore[arg-type]
        # Empty and rejected requests must not advance the random series.
        self.assertEqual(generator.generate(), SituationGenerator(rng_seed=42).generate())


if __name__ == "__main__":
    unittest.main()
