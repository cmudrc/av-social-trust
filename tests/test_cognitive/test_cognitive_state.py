import unittest

from av_social_trust import Car, CognitiveState


class CognitiveStateTests(unittest.TestCase):
    def test_private_opinion_uses_all_three_cognitive_components(self):
        for trust, opinion in ((0.0, -0.5), (0.5, 0.0), (1.0, 0.5)):
            with self.subTest(trust=trust):
                self.assertEqual(CognitiveState(trust, 1.0, 0.0).opinion, opinion)
        self.assertAlmostEqual(CognitiveState(0.0, 0.2, 0.0).opinion, 0.3)
        self.assertAlmostEqual(CognitiveState(0.0, 1.0, 0.9).opinion, 0.4)

    def test_invalid_cognitive_values(self):
        for name in ("automation_trust", "perceived_risk", "workload"):
            for value in (-0.1, 1.1, float("nan"), float("inf")):
                values = dict(automation_trust=0.5, perceived_risk=0.5, workload=0.5)
                values[name] = value
                with self.subTest(name=name, value=value):
                    with self.assertRaises(ValueError):
                        CognitiveState(**values)

    def test_each_node_and_snapshot_owns_its_cognitive_state(self):
        cognition = CognitiveState(0.75, 1.0, 0.0)
        car = Car()
        car.add_passenger(20, 0.8, cognition, 0.2)
        car.add_driver(10, 0.9, cognition, 0.1)
        cognition.automation_trust = 0.0
        self.assertEqual(car.to_state()["opinion_vector"], [0.25, 0.25])

        car.G.nodes[20]["cognitive_state"].automation_trust = 0.25
        snapshot = car.to_state()
        self.assertEqual(snapshot["agents"], [10, 20])
        self.assertEqual(snapshot["opinion_vector"], [0.25, -0.25])
        self.assertEqual(snapshot["cognitive_states"][0]["automation_trust"], 0.75)
        self.assertEqual(snapshot["cognitive_states"][1]["automation_trust"], 0.25)
        snapshot["cognitive_states"][0]["perceived_risk"] = 0.0
        self.assertEqual(car.G.nodes[10]["cognitive_state"].perceived_risk, 1.0)

    def test_car_requires_cognitive_state_and_one_driver(self):
        car = Car()
        # Deliberately violate the annotation to test runtime validation.
        with self.assertRaises(TypeError):
            car.add_driver(10, 0.9, 0.5, 0.1)  # type: ignore[arg-type]
        cognition = CognitiveState(0.75, 0.6, 0.4)
        car.add_driver(10, 0.9, cognition, 0.1)
        with self.assertRaisesRegex(Exception, "Driver already exists"):
            car.add_driver(20, 0.9, cognition, 0.1)


if __name__ == "__main__":
    unittest.main()
