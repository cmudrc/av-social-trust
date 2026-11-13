"""Confidence timing, raw-versus-normalized trust, and fixed-snapshot interventions."""
import unittest
import numpy as np
from av_social_trust.trust import trust_step
from experiment.analysis.driver_confidence.metrics import confidence_measures, intervene, normalize_batch, replay
from experiment.model import run_model
from experiment.config import Settings
from experiment.tests.test_social_layer import person
from av_social_trust.situation import Situation


class ConfidenceTests(unittest.TestCase):
    def initial(self):
        return np.array([[.5,.2],[.2,.5]])

    def parameters(self):
        return np.full((2,2),.1), np.full((2,2),.5), np.ones((2,2),dtype=bool)

    def test_confidence_uses_incoming_raw_trust_with_one_update_delay(self):
        before=self.initial()
        rates,alpha,mask=self.parameters()
        agree=trust_step([1,1],before,rates,alpha,mask)
        disagree=trust_step([1,-1],before,rates,alpha,mask)
        self.assertAlmostEqual(agree[0,0],.47)
        self.assertAlmostEqual(disagree[0,0],.47)
        # The current opinions change appraisals now, not self-trust now.
        self.assertGreater(agree[1,0],disagree[1,0])
        agree_next=trust_step([1,1],agree,rates,alpha,mask)
        disagree_next=trust_step([1,-1],disagree,rates,alpha,mask)
        self.assertGreater(agree_next[0,0],disagree_next[0,0])
        raw,fields=confidence_measures(before,np.stack([agree,agree_next]),mask,alpha,
                                      np.array([[1,1],[1,1]]),.1,.1)
        np.testing.assert_allclose(raw[1],agree)
        np.testing.assert_allclose(fields['confidence_update_error'],0,atol=1e-15)
        np.testing.assert_allclose(fields['incoming_update_error'],0,atol=1e-15)
        self.assertNotAlmostEqual(fields['confidence_before'][0],fields['own_weight'][0])

    def test_solo_confidence_does_not_change_even_with_zero_initial_self_trust(self):
        initial=np.zeros((1,1))
        raw,fields=confidence_measures(initial,np.zeros((3,1,1)),np.ones((1,1),bool),np.zeros((1,1)),
                                      np.ones((3,1)),.1,.1)
        np.testing.assert_array_equal(fields['confidence_gain'],0)
        np.testing.assert_array_equal(fields['own_weight'],1)
        self.assertTrue(np.isnan(fields['incoming_before']).all())

    def test_snapshot_intervention_changes_only_confidence(self):
        trust=np.array([[[.7,.5],[.3,.6]]])
        original=trust.copy()
        states=np.array([[[.8,.5,.5],[.2,.5,.5]]])
        opinions=np.array([[1.,-1.]])
        tree=person(.55)['tree']
        for mode in ('decision','cognition'):
            choices,weights=intervene(trust,states,opinions,tree,mode,1,np.ones(1,bool),[0,.5,1])
            self.assertFalse(choices[0,0])
            self.assertTrue(choices[-1,0])
            self.assertTrue((np.diff(weights[:,0])>0).all())
        np.testing.assert_array_equal(trust,original)
        # With no discussion confidence has no immediate effect on the choice.
        for mode in ('decision','cognition'):
            choices,_=intervene(trust,states,opinions,tree,mode,0,np.ones(1,bool),[0,1])
            np.testing.assert_array_equal(choices,True)

    def test_observed_replay_matches_model_and_respects_automation_availability(self):
        settings=Settings(steps=4,cognitive_starts=1,social_starts=1)
        rates,alpha,mask=self.parameters()
        initial=dict(agents=['P01','P02'],cognition=np.array([[.8,.5,.5],[.2,.5,.5]]),
                     trust=self.initial(),rates=rates,alpha=alpha,mask=mask)
        people={'P01':person(.55),'P02':person(.4)}
        situations=[Situation(i%2,i!=2) for i in range(4)]
        available=np.array([s.automation_available for s in situations])
        for mode in ('decision','cognition'):
            arrays=run_model(initial,people,settings,mode,situations)
            raw,fields=confidence_measures(arrays['initial_trust'],arrays['trust'],arrays['connection_mask'],arrays['alpha'],
                                          arrays['private_opinions'],settings.self_learning_rate,settings.interpersonal_learning_rate)
            np.testing.assert_allclose(normalize_batch(raw),arrays['influence_matrix'])
            choices,_=replay(raw,arrays['private_cognition'],arrays['private_opinions'],people['P01']['tree'],mode,1,available)
            np.testing.assert_array_equal(choices,arrays['automation_on'])
            np.testing.assert_allclose(fields['confidence_update_error'],0,atol=1e-15)
            self.assertFalse(choices[2])

if __name__=='__main__':
    unittest.main()
