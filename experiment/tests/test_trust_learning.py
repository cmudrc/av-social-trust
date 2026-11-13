"""Check full-drive controls used to interpret weak-network interventions."""
import unittest
import numpy as np
from av_social_trust.consensus import normalize_trust_matrix
from av_social_trust.situation import Situation
from experiment.config import Settings
from experiment.model import run_model
from experiment.analysis.trust_learning.run import intervention, choose_sample, SCALE
from experiment.tests.test_social_layer import person


class TrustLearningTests(unittest.TestCase):
    def setUp(self):
        self.people = {key: person(.5) for key in ('P01', 'P02')}
        # Constant private cognition keeps driver/passenger disagreement fixed,
        # so a later decision change is attributable to evolving trust weights.
        for p in self.people.values():
            p.update(A=np.eye(3), B=np.zeros(3), c=np.zeros(3))
        self.initial = dict(agents=list(self.people), cognition=np.array([[.8,.5,.5],[.2,.5,.5]]),
                            trust=np.array([[.8,.4],[.4,.8]]), rates=np.full((2,2),.1),
                            alpha=np.zeros((2,2)), mask=np.ones((2,2),bool))
        self.settings = Settings(steps=40)
        self.track = [Situation(0, True)] * self.settings.steps

    def test_uniform_scale_preserves_full_frozen_behavior_in_both_modes(self):
        for mode in ('decision', 'cognition'):
            original = run_model(intervention(self.initial, 'original_fixed'), self.people, self.settings, mode, self.track)
            scaled = run_model(intervention(self.initial, 'all_small_fixed'), self.people, self.settings, mode, self.track)
            np.testing.assert_array_equal(original['automation_on'], scaled['automation_on'])
            np.testing.assert_array_equal(original['influence_matrix'], scaled['influence_matrix'])
            np.testing.assert_array_equal(original['social_cognition'], scaled['social_cognition'])

    def test_weak_ties_protect_initial_vote_but_learning_can_change_it(self):
        frozen = run_model(intervention(self.initial, 'weak_fixed'), self.people, self.settings, 'decision', self.track)
        learned = run_model(intervention(self.initial, 'weak_learning'), self.people, self.settings, 'decision', self.track)
        self.assertTrue(frozen['automation_on'].all())
        self.assertTrue(learned['automation_on'][0])
        self.assertFalse(learned['automation_on'][-1])
        np.testing.assert_array_equal(frozen['private_decisions'], learned['private_decisions'])
        self.assertGreater(frozen['influence_matrix'][0,0,0], .99)
        self.assertLess(learned['influence_matrix'][-1,0,0], .5)
        np.testing.assert_array_equal(frozen['trust'], np.broadcast_to(frozen['initial_trust'], frozen['trust'].shape))

    def test_interventions_preserve_source_and_distinguish_self_from_social_ties(self):
        before = self.initial['trust'].copy()
        weak = intervention(self.initial, 'weak_learning')
        scaled = intervention(self.initial, 'all_small_learning')
        np.testing.assert_array_equal(self.initial['trust'], before)
        np.testing.assert_array_equal(np.diag(weak['trust']), np.diag(before))
        self.assertEqual(weak['trust'][0,1], before[0,1]*SCALE)
        np.testing.assert_array_equal(normalize_trust_matrix(scaled['trust']), normalize_trust_matrix(before))

    def test_sampling_keeps_exact_same_car_on_every_track(self):
        rows = [(d,t,c,s,k) for d in range(2) for t in range(3) for k in (1,2)
                for c,s in ((k*10,0),(k*10+1,1))]
        data = dict(zip(('driver','track','composition','start','passenger_count'), np.array(rows).T))
        data['_tracks'] = np.array(['low','medium','high'])
        selected = choose_sample(data)
        self.assertEqual(len(selected), 12)
        keys = [set(zip(data['driver'][selected][data['track'][selected]==t],
                        data['composition'][selected][data['track'][selected]==t],
                        data['start'][selected][data['track'][selected]==t])) for t in range(3)]
        self.assertEqual(keys[0], keys[1])
        self.assertEqual(keys[1], keys[2])


if __name__ == '__main__':
    unittest.main()
