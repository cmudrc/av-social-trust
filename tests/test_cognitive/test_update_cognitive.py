import unittest
from dataclasses import asdict, fields, replace
from itertools import product

from av_social_trust import CognitiveState, Situation
from av_social_trust.cognitive import update_cognitive_state
from av_social_trust.cognitive.update import CognitiveParameters, SYNTHETIC_PARAMETERS


class UpdateCognitiveStateTests(unittest.TestCase):
    def test_synthetic_affine_updates_use_previous_state_and_complexity(self):
        original = CognitiveState(0.75, 0.6, 0.4)
        for complexity, expected in ((0, (0.755, 0.56, 0.38)), (1, (0.705, 0.61, 0.43))):
            for available in (False, True):
                result = update_cognitive_state(original, Situation(complexity, available))
                for actual, value in zip(asdict(result).values(), expected):
                    self.assertAlmostEqual(actual, value)
                self.assertIsNot(result, original)
                result.automation_trust = 0.9
                self.assertEqual(original, CognitiveState(0.75, 0.6, 0.4))

    def test_state_evolves_across_cycles(self):
        state = CognitiveState(0.75, 0.6, 0.4)
        for _ in range(2):
            state = update_cognitive_state(state, Situation(task_complexity=1))
        for actual, expected in zip(asdict(state).values(), (0.6645, 0.619, 0.457)):
            self.assertAlmostEqual(actual, expected)

    def test_custom_participant_coefficients(self):
        parameters = CognitiveParameters(
            a_trust=0.5, b_trust=0.1, c_trust=0.2,
            a_risk=0.4, b_risk=0.2, c_risk=0.1,
            a_workload=0.8, b_workload=-0.1, c_workload=0.05,
        )
        result = update_cognitive_state(
            CognitiveState(0.3, 0.6, 0.7), Situation(1), parameters=parameters
        )
        for actual, expected in zip(asdict(result).values(), (0.45, 0.54, 0.51)):
            self.assertAlmostEqual(actual, expected)

    def test_synthetic_defaults_remain_bounded_and_approach_targets(self):
        for initial in product((0.0, 1.0), repeat=3):
            for complexity, target in ((0, (0.8, 0.2, 0.2)), (1, (0.3, 0.7, 0.7))):
                state = CognitiveState(*initial)
                for _ in range(200):
                    state = update_cognitive_state(state, Situation(complexity))
                for actual, expected in zip(asdict(state).values(), target):
                    self.assertAlmostEqual(actual, expected)

    def test_invalid_coefficients_and_out_of_range_predictions_are_rejected(self):
        for field in fields(CognitiveParameters):
            for value in (float("nan"), float("inf"), True, "0.5"):
                with self.subTest(field=field.name, value=value):
                    with self.assertRaises(ValueError):
                        replace(SYNTHETIC_PARAMETERS, **{field.name: value})
        for offset in (-2.0, 2.0):
            with self.assertRaises(ValueError):
                update_cognitive_state(
                    CognitiveState(0.5, 0.5, 0.5), Situation(),
                    parameters=replace(SYNTHETIC_PARAMETERS, c_trust=offset),
                )

    def test_invalid_and_mutated_inputs_are_rejected(self):
        cognition = CognitiveState(0.3, 0.6, 0.7)
        situation = Situation()
        # Deliberately violate annotations to test runtime validation.
        with self.assertRaises(TypeError):
            update_cognitive_state(cognition, {})  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            update_cognitive_state({}, situation)  # type: ignore[arg-type]
        situation.task_complexity = 2
        with self.assertRaises(ValueError):
            update_cognitive_state(cognition, situation)
        cognition.workload = float("nan")
        with self.assertRaises(ValueError):
            update_cognitive_state(cognition, Situation())


if __name__ == "__main__":
    unittest.main()
