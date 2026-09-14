import unittest
from copy import deepcopy

import numpy as np

import av_social_trust as av


def make_car():
    car = av.Car()
    car.add_passenger(20, 0.5, av.CognitiveState(1.0, 0.3, 0.2), 0.0, 1.0)
    car.add_driver(10, 0.5, av.CognitiveState(0.0, 0.6, 0.4), 1.0, 1.0)
    car.connect_agents(10, 20, 0.5, 1.0, 1.0)
    car.connect_agents(20, 10, 0.5, 1.0, 1.0)
    return car


class ModelTests(unittest.TestCase):
    def test_cycle_uses_old_trust_and_private_opinions(self):
        car = make_car()
        original = car.to_state()
        model = av.Model(car)
        result = model.step()

        # Old trust gives equal influence, so opposite opinions average to zero.
        np.testing.assert_allclose(result["opinion_vector"], [0.0, 0.0])
        self.assertEqual(result["cognitive_states"], [
            {"automation_trust": 0.5, "perceived_risk": 0.6, "workload": 0.4},
            {"automation_trust": 0.5, "perceived_risk": 0.3, "workload": 0.2},
        ])
        # Trust learning sees the PRIVATE disagreement, so off-diagonal trust
        # becomes zero. Learning from post-consensus opinions would produce one.
        np.testing.assert_allclose(result["trust_matrix"], [[0.5, 0.0], [0.0, 0.5]])
        self.assertEqual(result["agents"], [10, 20])
        self.assertEqual(car.to_state(), original)
        self.assertEqual(model.cycle, 1)
        self.assertEqual(model.history[0]["private_opinion_vector"], [-1.0, 1.0])

        # The next cycle uses the updated trust, now an identity influence matrix.
        model.step()
        np.testing.assert_equal(model.history[1]["influence_matrix"], np.eye(2))
        np.testing.assert_allclose(model.state["trust_matrix"], [[0.0, 1.0], [1.0, 0.0]])

    def test_solo_driver_is_unchanged_without_personal_update(self):
        car = av.Car()
        car.add_driver(7, 0.8, av.CognitiveState(0.65, 0.6, 0.4), 1.0, 0.5)
        model = av.Model(car)
        self.assertEqual(model.run(3), car.to_state())
        self.assertEqual(model.cycle, 3)
        self.assertEqual([entry["cycle"] for entry in model.history], [1, 2, 3])

    def test_run_continues_from_current_state(self):
        car = make_car()
        model = av.Model(car)
        manual = av.Model(car)
        model.run(2)
        result = model.run(3)
        for _ in range(5):
            expected = manual.step()
        self.assertEqual(result, expected)
        self.assertEqual(model.cycle, 5)
        self.assertEqual(len(model.history), 5)

    def test_snapshots_and_situation_do_not_alias(self):
        model = av.Model(make_car())
        situation = {"task_complexity": 1}
        result = model.step(situation)
        saved = deepcopy(model.history[0])
        situation["task_complexity"] = 0
        result["opinion_vector"][0] = 0.9
        result["trust_matrix"][0][0] = 0.9
        result["agents"][0] = 999
        result["cognitive_states"][0]["automation_trust"] = 0.9
        self.assertEqual(model.state["opinion_vector"], [0.0, 0.0])
        self.assertEqual(model.state["trust_matrix"][0][0], 0.5)
        self.assertEqual(model.state["agents"], [10, 20])
        self.assertEqual(model.state["cognitive_states"][0]["automation_trust"], 0.5)
        model.step()
        self.assertEqual(model.history[0], saved)

    def test_zero_steps_and_invalid_counts(self):
        model = av.Model(make_car())
        original = deepcopy(model.state)
        result = model.run(0)
        self.assertEqual(result, original)
        result["opinion_vector"][0] = 0.0
        self.assertEqual(model.state, original)
        for count in (-1, 1.5, True):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    model.run(count)
        self.assertEqual(model.cycle, 0)
        self.assertEqual(model.history, [])

    def test_failed_update_does_not_partially_commit_cycle(self):
        model = av.Model(make_car())
        model.state["learning_rate_matrix"][0][0] = 2.0
        original = deepcopy(model.state)
        with self.assertRaises(ValueError):
            model.step()
        self.assertEqual(model.state, original)
        self.assertEqual(model.cycle, 0)
        self.assertEqual(model.history, [])


if __name__ == "__main__":
    unittest.main()
