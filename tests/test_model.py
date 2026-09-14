import unittest
from copy import deepcopy

import numpy as np

import av_social_trust as av


def make_car():
    car = av.Car()
    car.add_passenger(20, 0.75, av.CognitiveState(1.0, 1.0, 0.0), 0.0, 1.0)
    car.add_driver(10, 0.75, av.CognitiveState(0.0, 1.0, 0.0), 1.0, 1.0)
    car.connect_agents(10, 20, 0.25, 1.0, 1.0)
    car.connect_agents(20, 10, 0.25, 1.0, 1.0)
    return car


class ModelTests(unittest.TestCase):
    def test_cycle_uses_old_trust_and_private_opinions(self):
        car = make_car()
        original = car.to_state()
        model = av.Model(car)
        result = model.step()

        # Private opinions [-0.5, 0.5] are mixed with 75% self-influence.
        np.testing.assert_allclose(result["opinion_vector"], [-0.25, 0.25])
        self.assertEqual(result["cognitive_states"], original["cognitive_states"])
        self.assertFalse(result["automation_on"])
        # Private disagreement gives homophilic trust 0.5, rather than 0.75
        # from the social opinions. Self-trust uses OLD incoming trust 0.25.
        np.testing.assert_allclose(result["trust_matrix"], [[0.25, 0.5], [0.5, 0.25]])
        self.assertEqual(result["agents"], [10, 20])
        self.assertEqual(car.to_state(), original)
        self.assertEqual(model.cycle, 1)
        self.assertEqual(model.history[0]["private_opinion_vector"], [-0.5, 0.5])

        # Fresh private opinions remain [-0.5, 0.5]; new social trust now puts
        # more weight on the other person and flips the driver's decision.
        result = model.step()
        np.testing.assert_allclose(
            model.history[1]["influence_matrix"], [[1 / 3, 2 / 3], [2 / 3, 1 / 3]]
        )
        self.assertEqual(model.history[1]["private_opinion_vector"], [-0.5, 0.5])
        np.testing.assert_allclose(result["opinion_vector"], [1 / 6, -1 / 6])
        self.assertTrue(result["automation_on"])
        self.assertEqual(result["cognitive_states"], original["cognitive_states"])
        np.testing.assert_allclose(result["trust_matrix"], [[0.5, 0.5], [0.5, 0.5]])

    def test_solo_driver_is_unchanged_without_personal_update(self):
        car = av.Car()
        car.add_driver(7, 0.8, av.CognitiveState(0.65, 0.6, 0.4), 1.0, 0.5)
        model = av.Model(car)
        expected = car.to_state()
        expected["automation_on"] = True
        self.assertEqual(model.run(3), expected)
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
        situation = av.Situation(task_complexity=1)
        result = model.step(situation)
        saved = deepcopy(model.history[0])
        situation.task_complexity = 0
        result["opinion_vector"][0] = 0.9
        result["trust_matrix"][0][0] = 0.9
        result["agents"][0] = 999
        result["cognitive_states"][0]["automation_trust"] = 0.9
        self.assertEqual(model.state["opinion_vector"], [-0.25, 0.25])
        self.assertEqual(model.state["trust_matrix"][0][0], 0.25)
        self.assertEqual(model.state["agents"], [10, 20])
        self.assertEqual(model.state["cognitive_states"][0]["automation_trust"], 0.0)
        self.assertEqual(model.history[0]["situation"]["task_complexity"], 1)
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

    def test_availability_overrides_social_preference_without_changing_it(self):
        available = av.Model(make_car())
        unavailable = av.Model(make_car())
        available.step()
        unavailable.step()
        enabled = available.step(av.Situation(1, True))
        context = {"task_complexity": 1, "automation_available": False}
        disabled = unavailable.step(context)
        context["automation_available"] = True
        self.assertTrue(enabled["automation_on"])
        self.assertFalse(disabled["automation_on"])
        self.assertEqual(enabled["opinion_vector"], disabled["opinion_vector"])
        self.assertEqual(enabled["cognitive_states"], disabled["cognitive_states"])
        self.assertFalse(unavailable.history[-1]["situation"]["automation_available"])

    def test_workload_drives_private_preference_and_zero_is_off(self):
        car = av.Car()
        car.add_driver(1, 1.0, av.CognitiveState(0.1, 0.9, 0.8), 1.0, 0.0)
        model = av.Model(car)
        self.assertTrue(model.step()["automation_on"])
        model.state["cognitive_states"][0] = dict(
            automation_trust=0.5, perceived_risk=0.5, workload=0.5
        )
        result = model.step()
        self.assertEqual(result["opinion_vector"], [0.0])
        self.assertFalse(result["automation_on"])

    def test_invalid_situation_does_not_commit(self):
        model = av.Model(make_car())
        original = deepcopy(model.state)
        for situation in ({"task_complexity": 2}, {"automation_available": "false"}, 1):
            with self.subTest(situation=situation):
                with self.assertRaises((TypeError, ValueError)):
                    model.step(situation)
                self.assertEqual(model.state, original)
                self.assertEqual(model.cycle, 0)
                self.assertEqual(model.history, [])


if __name__ == "__main__":
    unittest.main()
