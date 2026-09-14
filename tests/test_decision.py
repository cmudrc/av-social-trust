import unittest
from copy import deepcopy
from itertools import product

from av_social_trust.cognitive import CognitiveState
from av_social_trust.consensus import degroot_step
from av_social_trust.decision import cognitive_to_opinion, decide_automation


class DecisionTests(unittest.TestCase):
    def test_private_decision_matches_threshold_or_rule(self):
        thresholds = dict(trust_threshold=0.6, risk_threshold=0.3, workload_threshold=0.8)
        for trust, risk, workload in product((0.0, 0.3, 0.6, 0.8, 1.0), repeat=3):
            with self.subTest(trust=trust, risk=risk, workload=workload):
                cognition = CognitiveState(trust, risk, workload)
                original = deepcopy(cognition)
                opinion = cognitive_to_opinion(cognition, **thresholds)
                self.assertGreaterEqual(opinion, -1.0)
                self.assertLessEqual(opinion, 1.0)
                self.assertEqual(
                    decide_automation(opinion),
                    trust > 0.6 or risk < 0.3 or workload > 0.8,
                )
                self.assertEqual(cognition, original)

    def test_equality_is_off_and_workload_can_outweigh_low_trust(self):
        self.assertEqual(cognitive_to_opinion(CognitiveState(0.5, 0.5, 0.5)), 0.0)
        self.assertFalse(decide_automation(0.0))
        self.assertAlmostEqual(cognitive_to_opinion(CognitiveState(0.2, 0.8, 0.9)), 0.4)

    def test_social_opinion_controls_decision_without_changing_cognition(self):
        driver = CognitiveState(0.2, 0.8, 0.2)
        passenger = CognitiveState(0.9, 0.8, 0.2)
        private = [cognitive_to_opinion(driver), cognitive_to_opinion(passenger)]
        social = degroot_step(private, [[0.25, 0.75], [0.0, 1.0]])
        self.assertFalse(decide_automation(private[0]))
        self.assertTrue(decide_automation(social[0]))
        self.assertFalse(decide_automation(social[0], automation_available=False))
        self.assertEqual(driver.automation_trust, 0.2)

    def test_invalid_inputs(self):
        cognition = CognitiveState(0.5, 0.5, 0.5)
        for name in ("trust_threshold", "risk_threshold", "workload_threshold"):
            for value in (-0.1, 1.1, float("nan"), float("inf"), True, "0.5"):
                with self.subTest(name=name, value=value):
                    with self.assertRaises(ValueError):
                        cognitive_to_opinion(cognition, **{name: value})
        for opinion in (-1.1, 1.1, float("nan"), float("inf"), True, "0.5"):
            with self.subTest(opinion=opinion):
                with self.assertRaises(ValueError):
                    decide_automation(opinion)
        with self.assertRaises(TypeError):
            decide_automation(0.5, automation_available="false")
        with self.assertRaises(TypeError):
            cognitive_to_opinion([0.5, 0.5, 0.5])
        cognition.workload = float("nan")
        with self.assertRaises(ValueError):
            cognitive_to_opinion(cognition)


if __name__ == "__main__":
    unittest.main()
