import unittest

import numpy as np

import av_social_trust as av
from av_social_trust.consensus import (
    degroot_step,
    normalize_trust_matrix,
    run_degroot,
    validate_row_stochastic,
)


class ConsensusTests(unittest.TestCase):
    def test_exported_state_preserves_raw_trust_and_agent_order(self):
        car = av.Car()
        car.add_passenger(20, 0.5, av.CognitiveState(0.0, 1.0, 0.0), 1.0, 0.1)
        car.add_driver(10, 0.2, av.CognitiveState(1.0, 1.0, 0.0), 1.0, 0.1)
        car.connect_agents(10, 20, 0.6, 0.1, 0.5)
        state = car.to_state()
        weights = normalize_trust_matrix(state["trust_matrix"])

        self.assertEqual(state["agents"], [10, 20])
        np.testing.assert_allclose(weights, [[0.25, 0.75], [0.0, 1.0]])
        np.testing.assert_allclose(
            degroot_step(state["opinion_vector"], weights), [-0.25, -0.5]
        )
        self.assertEqual(state["trust_matrix"], [[0.2, 0.6], [0.0, 0.5]])
        self.assertEqual(state["opinion_vector"], [0.5, -0.5])

    def test_zero_trust_retains_opinion(self):
        weights = normalize_trust_matrix([[0.0, 0.0], [0.4, 0.6]])
        np.testing.assert_allclose(weights, [[1.0, 0.0], [0.4, 0.6]])
        np.testing.assert_allclose(degroot_step([0.8, -0.2], weights), [0.8, 0.2])
        np.testing.assert_equal(normalize_trust_matrix([[0.0]]), [[1.0]])

    def test_updates_are_synchronous_and_do_not_mutate_inputs(self):
        weights = np.array([[0.0, 1.0], [1.0, 0.0]])
        opinions = np.array([-0.7, 0.9])
        updated = degroot_step(opinions, weights)
        np.testing.assert_allclose(updated, [0.9, -0.7])
        np.testing.assert_equal(opinions, [-0.7, 0.9])
        np.testing.assert_equal(weights, [[0.0, 1.0], [1.0, 0.0]])
        np.testing.assert_allclose(degroot_step(updated, weights), opinions)

    def test_repeated_averaging_and_roundoff(self):
        weights = np.array([[0.75, 0.25], [0.25, 0.75]])
        opinions = np.array([-1.0, 1.0])
        for _ in range(30):
            opinions = degroot_step(opinions, weights)
        np.testing.assert_allclose(opinions, [0.0, 0.0], atol=1e-8)

        weights = [[0.5, 0.5 + 1e-12], [0.5, 0.5 - 1e-12]]
        for _ in range(10):
            np.testing.assert_allclose(degroot_step([1.0, 1.0], weights), [1.0, 1.0])

    def test_invalid_matrices(self):
        for matrix in ([], [1.0], [[1.0, 0.0]], [[np.nan]], [[np.inf]], [[-0.1]]):
            for operation in (normalize_trust_matrix, validate_row_stochastic):
                with self.subTest(matrix=matrix, operation=operation.__name__):
                    with self.assertRaises(ValueError):
                        operation(matrix)
        for matrix in ([[0.0]], [[0.9]], [[1.0 + 1e-7]], [[1.1, -0.1], [0.0, 1.0]]):
            with self.subTest(matrix=matrix):
                with self.assertRaises(ValueError):
                    validate_row_stochastic(matrix)

    def test_invalid_opinions(self):
        for opinions in ([], [0.0], [[0.0], [0.0]], [np.nan, 0.0], [np.inf, 0.0], [1.1, 0.0]):
            with self.subTest(opinions=opinions):
                with self.assertRaises(ValueError):
                    degroot_step(opinions, np.eye(2))

    def test_extreme_finite_weights_normalize(self):
        weights = normalize_trust_matrix([[1e308, 1e308], [1e-300, 1e-300]])
        np.testing.assert_allclose(weights, [[0.5, 0.5], [0.5, 0.5]])
        validate_row_stochastic(weights)

    def test_fixed_steps_match_matrix_power_without_early_stopping(self):
        weights = np.array([[0.75, 0.25], [0.25, 0.75]])
        opinions = np.array([-1.0, 1.0])
        result = run_degroot(opinions, weights, steps=5)
        np.testing.assert_allclose(
            result["opinion_vector"], np.linalg.matrix_power(weights, 5) @ opinions
        )
        self.assertEqual(result["steps"], 5)
        self.assertFalse(result["converged"])
        self.assertEqual(result["max_change"], 0.03125)
        np.testing.assert_equal(opinions, [-1.0, 1.0])
        np.testing.assert_equal(weights, [[0.75, 0.25], [0.25, 0.75]])
        stable = run_degroot([0.4, 0.4], weights, steps=5)
        self.assertEqual(stable["steps"], 5)
        self.assertTrue(stable["converged"])

    def test_stop_at_change_threshold(self):
        result = run_degroot(
            [-1.0, 1.0], [[0.75, 0.25], [0.25, 0.75]], tol=0.01, max_steps=100
        )
        self.assertEqual(result["steps"], 7)
        self.assertTrue(result["converged"])
        self.assertLessEqual(result["max_change"], 0.01)
        self.assertFalse(result["consensus_reached"])
        np.testing.assert_allclose(result["opinion_vector"], [-1 / 128, 1 / 128])

    def test_oscillation_stops_at_limit_without_claiming_convergence(self):
        result = run_degroot([-1.0, 1.0], [[0.0, 1.0], [1.0, 0.0]], max_steps=5)
        self.assertEqual(result["steps"], 5)
        self.assertFalse(result["converged"])
        self.assertFalse(result["consensus_reached"])
        np.testing.assert_equal(result["opinion_vector"], [1.0, -1.0])

    def test_stable_disagreement_is_not_consensus(self):
        result = run_degroot([-1.0, 1.0], np.eye(2))
        self.assertEqual(result["steps"], 1)
        self.assertTrue(result["converged"])
        self.assertFalse(result["consensus_reached"])
        self.assertEqual(result["max_change"], 0.0)
        solo = run_degroot([0.5], [[1.0]])
        self.assertTrue(solo["converged"])
        self.assertTrue(solo["consensus_reached"])

    def test_zero_steps_returns_independent_validated_input(self):
        opinions = np.array([-0.5, 0.5])
        result = run_degroot(opinions, np.eye(2), steps=0)
        self.assertEqual(result["steps"], 0)
        self.assertIsNone(result["max_change"])
        self.assertFalse(result["converged"])
        np.testing.assert_equal(result["opinion_vector"], opinions)
        result["opinion_vector"][0] = 0.0
        self.assertEqual(opinions[0], -0.5)
        with self.assertRaises(ValueError):
            run_degroot([0.0], [[0.5]], steps=0)
        with self.assertRaises(ValueError):
            run_degroot([np.nan], [[1.0]], steps=0)

    def test_invalid_run_controls(self):
        controls = [
            {"steps": -1}, {"steps": 1.5}, {"steps": True},
            {"max_steps": 0}, {"max_steps": -1}, {"max_steps": 1.5},
            {"max_steps": True}, {"tol": 0}, {"tol": -1},
            {"tol": np.nan}, {"tol": np.inf}, {"tol": True},
        ]
        for kwargs in controls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    run_degroot([0.0], [[1.0]], **kwargs)


if __name__ == "__main__":
    unittest.main()
