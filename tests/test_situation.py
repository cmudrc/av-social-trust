import unittest

from av_social_trust import Situation
from av_social_trust.generator import generate_situations


class SituationTests(unittest.TestCase):
    def test_situation_validation(self):
        self.assertEqual(Situation(), Situation(0, True))
        for value in (-1, 2, 0.5, True, "1", float("nan")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    Situation(task_complexity=value)
        for value in (0, 1, "false", None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    Situation(automation_available=value)

    def test_synthetic_sequence_is_reproducible_and_independent(self):
        sequence = list(generate_situations(6, block_size=2, unavailable_steps=1))
        self.assertEqual([s.task_complexity for s in sequence], [0, 0, 1, 1, 0, 0])
        self.assertEqual([s.automation_available for s in sequence], [False] + [True] * 5)
        self.assertEqual(sequence, list(generate_situations(6, block_size=2, unavailable_steps=1)))
        sequence[0].task_complexity = 1
        self.assertEqual(sequence[1].task_complexity, 0)
        self.assertEqual(list(generate_situations(0)), [])

    def test_generator_rejects_invalid_counts(self):
        for name in ("steps", "block_size", "unavailable_steps"):
            for value in (-1, True, 1.5):
                kwargs = dict(steps=2, block_size=1, unavailable_steps=0)
                kwargs[name] = value
                with self.subTest(name=name, value=value):
                    with self.assertRaises(ValueError):
                        list(generate_situations(**kwargs))
        with self.assertRaises(ValueError):
            list(generate_situations(2, block_size=0))


if __name__ == "__main__":
    unittest.main()
