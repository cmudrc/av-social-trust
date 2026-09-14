import unittest

import numpy as np

import av_social_trust as av
from av_social_trust.trust import (
    trust_step,
    update_interpersonal_trust,
    update_self_trust,
)


class TrustTests(unittest.TestCase):
    def test_self_trust_uses_incoming_raw_trust(self):
        trust = np.array([[0.8, 0.1, 0.3], [0.6, 0.4, 0.7], [0.2, 0.9, 0.5]])
        original = trust.copy()
        rates = np.diag([0.5, 1.0, 0.0])
        updated = update_self_trust(trust, rates)
        np.testing.assert_allclose(np.diag(updated), [0.6, 0.5, 0.5])
        off_diagonal = ~np.eye(3, dtype=bool)
        np.testing.assert_equal(updated[off_diagonal], trust[off_diagonal])
        np.testing.assert_equal(trust, original)

    def test_existing_zero_appraisal_counts_but_absent_connection_does_not(self):
        trust = [[0.8, 0.0, 0.0], [0.0, 0.5, 0.0], [0.6, 0.0, 0.2]]
        mask = np.eye(3, dtype=bool)
        mask[1, 0] = True
        mask[2, 0] = True
        updated = update_self_trust(trust, np.eye(3), mask)
        np.testing.assert_allclose(np.diag(updated), [0.3, 0.5, 0.2])
        mask[1, 0] = False
        updated = update_self_trust(trust, np.eye(3), mask)
        np.testing.assert_allclose(np.diag(updated), [0.6, 0.5, 0.2])

    def test_lone_agent_preserves_self_trust(self):
        np.testing.assert_equal(update_self_trust([[0.7]], [[1.0]]), [[0.7]])

    def test_self_rate_endpoints_and_bounds(self):
        trust = [[0.0, 1.0], [0.0, 1.0]]
        np.testing.assert_equal(update_self_trust(trust, np.zeros((2, 2))), trust)
        np.testing.assert_equal(update_self_trust(trust, np.ones((2, 2))), trust)

    def test_invalid_inputs(self):
        for trust in ([], [[1, 0]], [[np.nan]], [[np.inf]], [[-0.1]], [[1.1]]):
            with self.subTest(trust=trust):
                with self.assertRaises(ValueError):
                    update_self_trust(trust, [[0.5]])
        for rates in ([[0.2]], [[np.nan, 0], [0, 1]], [[1.1, 0], [0, 1]]):
            with self.subTest(rates=rates):
                with self.assertRaises(ValueError):
                    update_self_trust(np.eye(2), rates)
        for mask in ([[True]], [[1, 0], [0, 1]]):
            with self.subTest(mask=mask):
                with self.assertRaises(ValueError):
                    update_self_trust(np.eye(2), np.eye(2), mask)

    def test_homophilic_and_normative_targets(self):
        trust = np.diag([0.2, 0.3, 0.4])
        opinions = [-1.0, 0.0, 1.0]
        rates = np.ones((3, 3))
        homophilic = update_interpersonal_trust(opinions, trust, rates, rates)
        np.testing.assert_allclose(
            homophilic, [[0.2, 0.5, 0.0], [0.5, 0.3, 0.5], [0.0, 0.5, 0.4]]
        )
        normative = update_interpersonal_trust(opinions, trust, rates, np.zeros((3, 3)))
        np.testing.assert_allclose(
            normative, [[0.2, 1.0, 0.5], [0.5, 0.3, 0.5], [0.5, 1.0, 0.4]]
        )

    def test_directed_rates_tradeoffs_and_masks(self):
        trust = np.array([[0.8, 0.2, 0.0], [0.6, 0.5, 0.0], [0.0, 0.0, 0.4]])
        mask = np.eye(3, dtype=bool)
        mask[0, 1] = mask[1, 0] = mask[1, 2] = True
        rates = np.full((3, 3), 0.5)
        rates[1, 2] = 0.0
        tradeoffs = np.zeros((3, 3))
        tradeoffs[0, 1] = 0.25
        updated = update_interpersonal_trust([-1, 0, 1], trust, rates, tradeoffs, mask)
        # 0 -> 1 target: 0.25 * 0.5 + 0.75 * 1 = 0.875.
        # 1 -> 0 target: normative agreement of agent 0 = 0.5.
        np.testing.assert_allclose(
            updated, [[0.8, 0.5375, 0.0], [0.55, 0.5, 0.0], [0.0, 0.0, 0.4]]
        )

    def test_simultaneous_update_uses_old_appraisals_and_ignores_tradeoff_diagonal(self):
        trust = [[0.8, 0.2], [0.6, 0.4]]
        result = trust_step([0.0, 0.0], trust, np.ones((2, 2)), np.zeros((2, 2)))
        # Interpersonal trust becomes 1, but self-trust uses old incoming values.
        np.testing.assert_allclose(result, [[0.6, 1.0], [1.0, 0.2]])
        changed_diagonal = trust_step(
            [0.0, 0.0], trust, np.ones((2, 2)), np.eye(2)
        )
        np.testing.assert_equal(changed_diagonal, result)

    def test_car_state_integration_preserves_inputs_and_does_not_use_attention(self):
        car = av.Car()
        car.add_driver(10, 0.8, -1.0, 1.0, 0.5)
        car.add_passenger(20, 0.4, 1.0, 0.0, 0.5)
        car.connect_agents(10, 20, 0.0, 1.0, 0.0)
        state = car.to_state()
        result = trust_step(
            state["opinion_vector"],
            state["trust_matrix"],
            state["learning_rate_matrix"],
            state["homophilic_normative_tradeoff_matrix"],
            state["connection_mask_matrix"],
        )
        np.testing.assert_allclose(result, [[0.8, 0.5], [0.0, 0.2]])
        self.assertEqual(car.to_state(), state)
        car.G.nodes[20]["attention"] = 1.0
        new_state = car.to_state()
        new_result = trust_step(
            new_state["opinion_vector"], new_state["trust_matrix"],
            new_state["learning_rate_matrix"],
            new_state["homophilic_normative_tradeoff_matrix"],
            new_state["connection_mask_matrix"],
        )
        np.testing.assert_equal(new_result, result)

    def test_repeated_updates_remain_bounded_without_mutating_arrays(self):
        opinions = np.array([-1.0, 0.2, 1.0])
        trust = np.array([[0.8, 0.2, 0.0], [0.6, 0.4, 0.9], [1.0, 0.0, 0.5]])
        rates = np.full((3, 3), 0.3)
        tradeoffs = np.full((3, 3), 0.6)
        mask = np.ones((3, 3), dtype=bool)
        inputs = [opinions, trust, rates, tradeoffs, mask]
        copies = [value.copy() for value in inputs]
        result = trust_step(*inputs)
        for value, original in zip(inputs, copies):
            np.testing.assert_equal(value, original)
        for _ in range(100):
            result = trust_step(opinions, result, rates, tradeoffs, mask)
            self.assertTrue(np.all((result >= 0) & (result <= 1)))

    def test_interpersonal_invalid_inputs(self):
        for opinions in ([0.0], [[0.0], [0.0]], [np.nan, 0], [np.inf, 0], [-1.1, 0]):
            with self.subTest(opinions=opinions):
                with self.assertRaises(ValueError):
                    update_interpersonal_trust(opinions, np.eye(2), np.eye(2), np.eye(2))
        for tradeoffs in ([[0.5]], [[0, np.nan], [0, 0]], [[0, 1.1], [0, 0]]):
            with self.subTest(tradeoffs=tradeoffs):
                with self.assertRaises(ValueError):
                    trust_step([0.0, 0.0], np.eye(2), np.eye(2), tradeoffs)


if __name__ == "__main__":
    unittest.main()
