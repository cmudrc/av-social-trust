import unittest
from copy import deepcopy
from dataclasses import asdict

import numpy as np

import av_social_trust as av
from av_social_trust.cognitive import update_cognitive_state
from av_social_trust.decision import cognitive_to_opinion, decide_automation
from av_social_trust.model.model_cognition_influence import Model as CognitionModel
from av_social_trust.model.model_decision_influence import Model as DecisionModel


def make_car():
    car = av.Car()
    car.add_passenger(20, 0.75, av.CognitiveState(1.0, 1.0, 0.0), 1.0)
    car.add_driver(10, 0.75, av.CognitiveState(0.0, 1.0, 0.0), 1.0)
    car.connect_agents(10, 20, 0.25, 1.0, 1.0)
    car.connect_agents(20, 10, 0.25, 1.0, 1.0)
    return car


class DriverDecisionTests(unittest.TestCase):
    def test_driver_decision_controls_action_despite_passenger_majority(self):
        for model_class in (DecisionModel, CognitionModel):
            for driver_on in (False, True):
                with self.subTest(model=model_class.__module__, driver_on=driver_on):
                    car = av.Car()
                    # Add passengers first to verify driver-first exported ordering.
                    passenger_state = (
                        av.CognitiveState(0.0, 1.0, 0.0)
                        if driver_on else av.CognitiveState(1.0, 0.0, 1.0)
                    )
                    for agent_id in (20, 30, 40):
                        car.add_passenger(agent_id, 1.0, passenger_state, 0.0)
                    driver_state = (
                        av.CognitiveState(1.0, 0.0, 1.0)
                        if driver_on else av.CognitiveState(0.0, 1.0, 0.0)
                    )
                    car.add_driver(10, 1.0, driver_state, 0.0)
                    model = model_class(car)
                    result = model.step(av.Situation())

                    self.assertEqual(result["agents"], [10, 20, 30, 40])
                    self.assertEqual(
                        model.history[-1]["individual_decision_vector"],
                        [driver_on, *([not driver_on] * 3)],
                    )
                    self.assertIs(result["automation_on"], driver_on)

    def test_final_driver_decision_follows_influence_and_availability(self):
        for model_class in (DecisionModel, CognitionModel):
            for available in (False, True):
                with self.subTest(model=model_class.__module__, available=available):
                    model = model_class(make_car())
                    first = model.step(av.Situation())
                    self.assertLess(first["opinion_vector"][0], 0.0)
                    self.assertEqual(
                        model.history[-1]["individual_decision_vector"], [False, True]
                    )
                    self.assertFalse(first["automation_on"])

                    # Social influence now flips the driver's opinion to positive.
                    result = model.step(av.Situation(automation_available=available))
                    decisions = model.history[-1]["individual_decision_vector"]
                    self.assertGreater(result["opinion_vector"][0], 0.0)
                    self.assertEqual(decisions, [available, False])
                    self.assertIs(result["automation_on"], decisions[0])
                    self.assertIs(model.state["automation_on"], decisions[0])
                    self.assertIs(
                        model.history[-1]["state"]["automation_on"], decisions[0]
                    )


class ModelTests(unittest.TestCase):
    def test_default_model_preserves_decision_influence_model(self):
        self.assertIs(av.Model, DecisionModel)
        self.assertIs(av.CognitionInfluenceModel, CognitionModel)

    def test_cycle_uses_old_trust_and_private_opinions(self):
        car = make_car()
        original = car.to_state()
        model = av.Model(car)
        result = model.step(av.Situation())

        # Synthetic cognition produces private opinions [-0.42, 0.48].
        # Old social trust still supplies 75% self-influence in this cycle.
        np.testing.assert_allclose(result["opinion_vector"], [-0.195, 0.255])
        np.testing.assert_allclose(
            [list(state.values()) for state in result["cognitive_states"]],
            [[0.08, 0.92, 0.02], [0.98, 0.92, 0.02]],
        )
        self.assertFalse(result["automation_on"])
        # Private disagreement gives homophilic trust 0.55, rather than 0.775
        # from social opinions. Self-trust uses OLD incoming trust 0.25.
        np.testing.assert_allclose(result["trust_matrix"], [[0.25, 0.55], [0.55, 0.25]])
        self.assertEqual(result["agents"], [10, 20])
        self.assertEqual(car.to_state(), original)
        self.assertEqual(model.cycle, 1)
        np.testing.assert_allclose(model.history[0]["private_opinion_vector"], [-0.42, 0.48])

        # The next cognitive update uses prior COGNITION, not social opinion.
        # New social trust now flips the driver's decision.
        result = model.step(av.Situation())
        np.testing.assert_allclose(
            model.history[1]["influence_matrix"], [[0.3125, 0.6875], [0.6875, 0.3125]]
        )
        np.testing.assert_allclose(model.history[1]["private_opinion_vector"], [-0.348, 0.462])
        np.testing.assert_allclose(result["opinion_vector"], [0.208875, -0.094875])
        self.assertTrue(result["automation_on"])
        np.testing.assert_allclose(
            [list(state.values()) for state in result["cognitive_states"]],
            [[0.152, 0.848, 0.038], [0.962, 0.848, 0.038]],
        )
        np.testing.assert_allclose(result["trust_matrix"], [[0.55, 0.595], [0.595, 0.55]])

    def test_multiple_decision_discussion_rounds_apply_matrix_power(self):
        model = av.Model(make_car(), discussion_rounds=3)
        result = model.step(av.Situation())
        record = model.history[0]
        weights = np.asarray(record["influence_matrix"])
        expected = np.linalg.matrix_power(weights, 3) @ np.asarray(
            record["private_opinion_vector"]
        )

        np.testing.assert_allclose(result["opinion_vector"], expected)
        self.assertEqual(record["discussion_rounds"], 3)

    def test_solo_driver_matches_individual_model(self):
        car = av.Car()
        car.add_driver(7, 0.8, av.CognitiveState(0.65, 0.6, 0.4), 0.5)
        model = av.Model(car)
        expected = car.to_state()
        cognition = av.CognitiveState(**expected["cognitive_states"][0])
        for _ in range(3):
            cognition = update_cognitive_state(cognition, av.Situation())
        expected["cognitive_states"] = [asdict(cognition)]
        expected["opinion_vector"] = [cognitive_to_opinion(cognition)]
        expected["automation_on"] = decide_automation(expected["opinion_vector"][0])
        self.assertEqual(model.run([av.Situation() for _ in range(3)]), expected)
        self.assertEqual(model.cycle, 3)
        self.assertEqual([entry["cycle"] for entry in model.history], [1, 2, 3])

    def test_run_continues_from_current_state(self):
        car = make_car()
        model = av.Model(car)
        manual = av.Model(car)
        situations = [
            av.Situation(0, True), av.Situation(1, False),
            av.Situation(1, True), av.Situation(0, False), av.Situation(1, True),
        ]
        original_situations = deepcopy(situations)
        model.run(situations[:2])
        result = model.run(situations[2:])
        for situation in situations:
            expected = manual.step(situation)
        self.assertEqual(result, expected)
        self.assertEqual(model.cycle, 5)
        self.assertEqual(len(model.history), 5)
        self.assertEqual(model.history, manual.history)
        self.assertEqual([record["situation"] for record in model.history],
                         [asdict(situation) for situation in situations])
        self.assertEqual(situations, original_situations)
        self.assertEqual(model.run([]), result)
        self.assertEqual(model.cycle, 5)
        result["cognitive_states"][0]["automation_trust"] = -1
        situations[0].task_complexity = 1
        self.assertEqual(model.state, manual.state)
        self.assertEqual(model.history, manual.history)

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
        self.assertEqual(model.state, saved["state"])
        self.assertEqual(model.state["trust_matrix"][0][0], 0.25)
        self.assertEqual(model.state["agents"], [10, 20])
        self.assertEqual(model.history[0]["situation"]["task_complexity"], 1)
        model.step(av.Situation())
        self.assertEqual(model.history[0], saved)

    def test_empty_run_and_invalid_lists(self):
        model = av.Model(make_car())
        original = deepcopy(model.state)
        result = model.run([])
        self.assertEqual(result, original)
        result["opinion_vector"][0] = 0.0
        self.assertEqual(model.state, original)
        for situations in (3, None, True, (av.Situation(),), [av.Situation(), {}]):
            with self.subTest(situations=situations):
                with self.assertRaises(TypeError):
                    model.run(situations)  # type: ignore[arg-type]
        invalid = av.Situation()
        invalid.task_complexity = 2
        with self.assertRaises(ValueError):
            model.run([av.Situation(), invalid])
        self.assertEqual(model.state, original)
        self.assertEqual(model.cycle, 0)
        self.assertEqual(model.history, [])

    def test_failed_update_does_not_partially_commit_cycle(self):
        model = av.Model(make_car())
        model.state["learning_rate_matrix"][0][0] = 2.0
        original = deepcopy(model.state)
        with self.assertRaises(ValueError):
            model.step(av.Situation())
        self.assertEqual(model.state, original)
        self.assertEqual(model.cycle, 0)
        self.assertEqual(model.history, [])

    def test_availability_overrides_social_preference_without_changing_it(self):
        available = av.Model(make_car())
        unavailable = av.Model(make_car())
        available.step(av.Situation())
        unavailable.step(av.Situation())
        enabled = available.step(av.Situation(1, True))
        context = av.Situation(task_complexity=1, automation_available=False)
        disabled = unavailable.step(context)
        context.automation_available = True
        self.assertTrue(enabled["automation_on"])
        self.assertFalse(disabled["automation_on"])
        self.assertEqual(enabled["opinion_vector"], disabled["opinion_vector"])
        self.assertEqual(enabled["cognitive_states"], disabled["cognitive_states"])
        self.assertFalse(unavailable.history[-1]["situation"]["automation_available"])

    def test_workload_drives_private_preference_even_with_low_trust(self):
        car = av.Car()
        car.add_driver(1, 1.0, av.CognitiveState(0.1, 0.9, 0.8), 0.0)
        model = av.Model(car)
        self.assertTrue(model.step(av.Situation())["automation_on"])
        model.state["cognitive_states"][0] = dict(
            automation_trust=0.1, perceived_risk=0.9, workload=0.0
        )
        result = model.step(av.Situation())
        self.assertLess(result["opinion_vector"][0], 0.0)
        self.assertFalse(result["automation_on"])

    def test_invalid_situation_does_not_commit(self):
        model = av.Model(make_car())
        original = deepcopy(model.state)
        invalid = av.Situation()
        invalid.task_complexity = 2
        for situation in (None, {"task_complexity": 0}, 1, invalid):
            with self.subTest(situation=situation):
                with self.assertRaises((TypeError, ValueError)):
                    model.step(situation)  # type: ignore[arg-type]
                self.assertEqual(model.state, original)
                self.assertEqual(model.cycle, 0)
                self.assertEqual(model.history, [])


class CognitionInfluenceModelTests(unittest.TestCase):
    def test_social_influence_changes_cognition_before_individual_decisions(self):
        car = make_car()
        original = car.to_state()
        model = av.CognitionInfluenceModel(car)
        result = model.step(av.Situation())

        np.testing.assert_allclose(
            [
                list(state.values())
                for state in model.history[0]["private_cognitive_states"]
            ],
            [[0.08, 0.92, 0.02], [0.98, 0.92, 0.02]],
        )
        np.testing.assert_allclose(
            [list(state.values()) for state in result["cognitive_states"]],
            [[0.305, 0.92, 0.02], [0.755, 0.92, 0.02]],
        )
        np.testing.assert_allclose(result["opinion_vector"], [-0.195, 0.255])
        self.assertEqual(
            model.history[0]["individual_decision_vector"], [False, True]
        )
        self.assertFalse(result["automation_on"])

        # Trust uses the individual opinions formed after cognitive influence.
        np.testing.assert_allclose(
            result["trust_matrix"], [[0.25, 0.775], [0.775, 0.25]]
        )
        self.assertEqual(car.to_state(), original)

    def test_next_private_update_starts_from_social_cognition(self):
        model = av.CognitionInfluenceModel(make_car())
        first = model.step(av.Situation())
        model.step(av.Situation())

        expected_private = [
            update_cognitive_state(av.CognitiveState(**state), av.Situation())
            for state in first["cognitive_states"]
        ]
        np.testing.assert_allclose(
            [
                list(state.values())
                for state in model.history[1]["private_cognitive_states"]
            ],
            [list(asdict(state).values()) for state in expected_private],
        )

    def test_multiple_cognitive_discussion_rounds_apply_matrix_power(self):
        model = av.CognitionInfluenceModel(make_car(), discussion_rounds=3)
        result = model.step(av.Situation())
        record = model.history[0]
        weights = np.asarray(record["influence_matrix"])
        private_cognition = np.asarray([
            list(state.values()) for state in record["private_cognitive_states"]
        ])
        expected = np.linalg.matrix_power(weights, 3) @ private_cognition

        np.testing.assert_allclose(
            [list(state.values()) for state in result["cognitive_states"]],
            expected,
        )
        self.assertEqual(record["discussion_rounds"], 3)

    def test_solo_driver_reduces_to_individual_model(self):
        car = av.Car()
        car.add_driver(7, 0.8, av.CognitiveState(0.65, 0.6, 0.4), 0.5)
        model = av.CognitionInfluenceModel(car)
        expected_cognition = av.CognitiveState(**car.to_state()["cognitive_states"][0])

        for _ in range(3):
            expected_cognition = update_cognitive_state(
                expected_cognition, av.Situation()
            )

        result = model.run([av.Situation() for _ in range(3)])
        self.assertEqual(result["cognitive_states"], [asdict(expected_cognition)])
        self.assertEqual(
            result["opinion_vector"], [cognitive_to_opinion(expected_cognition)]
        )
        self.assertEqual(
            result["automation_on"],
            decide_automation(result["opinion_vector"][0]),
        )

    def test_availability_constrains_final_decisions_without_changing_opinions(self):
        model = av.CognitionInfluenceModel(make_car())
        result = model.step(av.Situation(automation_available=False))

        self.assertFalse(result["automation_on"])
        self.assertEqual(
            model.history[0]["individual_decision_vector"], [False, False]
        )
        self.assertEqual(
            model.history[0]["individual_opinion_vector"], result["opinion_vector"]
        )

    def test_discussion_round_validation_and_zero_rounds(self):
        for model_class in (av.Model, av.CognitionInfluenceModel):
            for value in (-1, 1.5, True, None):
                with self.subTest(model=model_class.__module__, value=value):
                    with self.assertRaises(ValueError):
                        model_class(make_car(), discussion_rounds=value)

        old_model = av.Model(make_car(), discussion_rounds=0)
        old_result = old_model.step(av.Situation())
        np.testing.assert_allclose(
            old_result["opinion_vector"],
            old_model.history[0]["private_opinion_vector"],
        )

        new_model = av.CognitionInfluenceModel(make_car(), discussion_rounds=0)
        new_result = new_model.step(av.Situation())
        self.assertEqual(
            new_result["cognitive_states"],
            new_model.history[0]["private_cognitive_states"],
        )


if __name__ == "__main__":
    unittest.main()
