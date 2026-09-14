import unittest
from unittest.mock import Mock

import numpy as np

from av_social_trust.situation.generator import SituationGenerator


class SituationGeneratorTests(unittest.TestCase):
    def test_seeded_series_continues_across_calls(self):
        first = SituationGenerator(rng_seed=42, automation_availability_probability=0.8)
        second = SituationGenerator(rng_seed=42, automation_availability_probability=0.8)
        self.assertEqual(
            first.generate_series(30),
            second.generate_series(10) + [second.generate()] + second.generate_series(19),
        )

    def test_previous_conditions_affect_next_sample(self):
        generator = SituationGenerator(
            task_complexity_probability=0.2,
            automation_availability_probability=0.8,
        )
        generator.rng = Mock()
        generator.rng.random.side_effect = (
            np.array([0.1, 0.9]),  # Start with high complexity, unavailable.
            np.array([0.5, 0.5]),  # Persist; independent draws would flip both.
            np.array([0.99, 0.01]),  # Switch both conditions.
            np.array([0.5, 0.5]),  # Persist in the new conditions.
        )
        series = generator.generate_series(4)
        self.assertEqual([s.task_complexity for s in series], [1, 1, 0, 0])
        self.assertEqual([s.automation_available for s in series], [False, False, True, True])

    def test_zero_persistence_matches_independent_draws(self):
        generator = SituationGenerator(
            rng_seed=7,
            task_complexity_probability=0.3,
            automation_availability_probability=0.7,
            task_complexity_persistence=0.0,
            automation_availability_persistence=0.0,
        )
        draws = np.random.default_rng(7).random((20, 2))
        series = generator.generate_series(20)
        self.assertEqual([s.task_complexity for s in series], (draws[:, 0] < 0.3).astype(int).tolist())
        self.assertEqual([s.automation_available for s in series], (draws[:, 1] < 0.7).tolist())

    def test_full_persistence_and_independent_returned_objects(self):
        generator = SituationGenerator(
            rng_seed=7,
            automation_availability_probability=0.5,
            task_complexity_persistence=1.0,
            automation_availability_persistence=1.0,
        )
        first = generator.generate()
        expected = (first.task_complexity, first.automation_available)
        first.task_complexity = 1 - first.task_complexity
        first.automation_available = not first.automation_available
        for situation in generator.generate_series(20):
            self.assertEqual((situation.task_complexity, situation.automation_available), expected)
            self.assertIsNot(situation, first)

    def test_probability_endpoints_and_native_types(self):
        for complexity in (0, 1):
            for available in (False, True):
                generator = SituationGenerator(
                    rng_seed=42,
                    task_complexity_probability=complexity,
                    automation_availability_probability=float(available),
                )
                for situation in generator.generate_series(5):
                    self.assertEqual(situation.task_complexity, complexity)
                    self.assertIs(situation.automation_available, available)
                    self.assertIs(type(situation.task_complexity), int)

    def test_invalid_configuration_and_series_lengths(self):
        for name in (
            "task_complexity_probability", "automation_availability_probability",
            "task_complexity_persistence", "automation_availability_persistence",
        ):
            for value in (-0.1, 1.1, float("nan"), float("inf"), True, "0.5"):
                with self.subTest(name=name, value=value):
                    with self.assertRaises(ValueError):
                        SituationGenerator(**{name: value})
        generator = SituationGenerator(rng_seed=42)
        self.assertEqual(generator.generate_series(0), [])
        for steps in (-1, 0.5, True):
            with self.assertRaises(ValueError):
                generator.generate_series(steps)
        self.assertEqual(generator.generate(), SituationGenerator(rng_seed=42).generate())


if __name__ == "__main__":
    unittest.main()
