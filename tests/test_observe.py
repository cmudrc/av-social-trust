import unittest

from av_social_trust import CognitiveState, Situation
from av_social_trust.observe import observe


class ObserveTests(unittest.TestCase):
    def test_placeholder_preserves_cognition_for_every_situation(self):
        original = CognitiveState(0.3, 0.6, 0.7)
        for complexity in (0, 1):
            for available in (False, True):
                result = observe(original, Situation(complexity, available))
                self.assertEqual(result, original)
                self.assertIsNot(result, original)
                result.automation_trust = 0.9
                self.assertEqual(original.automation_trust, 0.3)

    def test_invalid_and_mutated_inputs_are_rejected(self):
        cognition = CognitiveState(0.3, 0.6, 0.7)
        situation = Situation()
        with self.assertRaises(TypeError):
            observe(cognition, {})
        with self.assertRaises(TypeError):
            observe({}, situation)
        situation.task_complexity = 2
        with self.assertRaises(ValueError):
            observe(cognition, situation)
        cognition.workload = float("nan")
        with self.assertRaises(ValueError):
            observe(cognition, Situation())


if __name__ == "__main__":
    unittest.main()
