"""Counterexamples for matching, weighting, influence direction and interpretation."""
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from experiment.analysis.shared.paired import matched_tracks, balanced_weights, correlation
from experiment.analysis.track_social_effects.run import summarize
from experiment.analysis.network_dynamics.metrics import network_measures, residualize, opposing_weight
from experiment.analysis.network_dynamics.run import choose_sample, conditional_curve, extract


class PairedTrackTests(unittest.TestCase):
    def test_missing_track_and_reordered_rows_never_create_false_pairs(self):
        table = dict(driver=np.array([0,0,0,0,0]), track=np.array([1,0,1,0,0]),
                     composition=np.array([2,1,1,2,3]), start=np.zeros(5,int),
                     _tracks=['a','b'])
        matched = matched_tracks(table)
        np.testing.assert_array_equal(table['composition'][matched], [[1,1],[2,2]])
        np.testing.assert_array_equal(table['track'][matched], [[0,1],[0,1]])

    def test_weights_do_not_let_large_quotas_or_many_cars_dominate(self):
        driver = np.array([0,0,0,0,1])
        count = np.array([1,2,2,2,1])
        weight = balanced_weights(driver,count)
        self.assertAlmostEqual(weight.sum(),1)
        self.assertAlmostEqual(weight[:4].sum(),.5)
        self.assertAlmostEqual(weight[0],.25)
        self.assertAlmostEqual(weight[1:4].sum(),.25)

    def test_track_contrast_is_zero_when_each_car_has_only_its_own_constant_effect(self):
        tracks = [f'{d}_{p}' for d in ('low','normal','high') for p in (.3,.6,.9)]
        table = dict(driver=np.repeat([0,1],9), track=np.tile(np.arange(9),2),
                     composition=np.ones(18,int), start=np.zeros(18,int),
                     passenger_count=np.ones(18,int), _tracks=tracks)
        for pair in ('decision','cognition','cross'):
            table[f'{pair}_mismatch_cycles'] = np.repeat([10,70],9)
            table[f'{pair}_delta_automation_fraction'] = np.zeros(18)
        manifest = dict(tracks=[dict(name=name,difficulty=name.split('_')[0],persistence=float(name.split('_')[1]),
                                    mean_complexity=.5,complexity_switches=5) for name in tracks])
        result,_ = summarize(table,manifest,100)
        for contrast in result['contrasts']:
            np.testing.assert_allclose(contrast['mean_pp'],0)
        np.testing.assert_allclose(result['shared_track_share_of_within_car_variation'],0)
        for row in result['grid']:
            np.testing.assert_allclose(row['balanced_changed_percent'],[40]*3)

    def test_network_sampling_keeps_the_same_car_keys_on_every_track(self):
        table = dict(driver=np.zeros(24,int),track=np.tile([0,1,2],8),
                     composition=np.repeat(np.arange(1,5),6),start=np.tile(np.repeat([0,1],3),4),
                     passenger_count=np.ones(24,int),_tracks=['a','b','c'])
        sample = choose_sample(table,compositions=2,starts=1,seed=32)
        self.assertEqual(sample.shape,(2,3))
        for name in ('driver','composition','start'):
            self.assertTrue((table[name][sample] == table[name][sample[:,:1]]).all())


class NetworkMeasureTests(unittest.TestCase):
    def test_left_stationary_influence_identifies_the_person_everyone_listens_to(self):
        # Identical listener rows: driver receives .8 of everyone's attention.
        w = np.array([[[.8,.2],[.8,.2]]])
        m = network_measures(w)
        np.testing.assert_allclose(m['self_weight'],.8)
        np.testing.assert_allclose(m['passenger_attention'],.8)
        np.testing.assert_allclose(m['relative_influence'],1.6)
        # Right eigenvector would incorrectly imply equal influence.

    def test_incoming_attention_and_keeping_own_view_can_go_in_opposite_directions(self):
        w = np.array([[[.1,.9],[.9,.1]]])
        m = network_measures(w)
        self.assertAlmostEqual(m['self_weight'][0],.1)
        self.assertAlmostEqual(m['passenger_attention'][0],.9)
        self.assertAlmostEqual(m['relative_influence'][0],1)

    def test_effective_weights_respect_number_of_discussion_rounds(self):
        w = np.array([[[.8,.2],[.1,.9]]])
        self.assertAlmostEqual(network_measures(w,2)['self_weight'][0],.66)
        self.assertAlmostEqual(network_measures(w,0)['self_weight'][0],1)
        with self.assertRaises(ValueError):
            network_measures(np.array([np.eye(2)]))

    def test_majority_own_weight_protects_both_binary_choices(self):
        random = np.random.default_rng(81)
        for n in (2,3,6):
            rows = random.dirichlet(np.ones(n),size=200)
            rows[:,0] = .50001
            rows[:,1:] *= .49999/rows[:,1:].sum(axis=1,keepdims=True)
            for own in (-1,1):
                votes = np.full((len(rows),n),-own)
                votes[:,0] = own
                self.assertTrue(((np.sum(rows*votes,axis=1)>0) == (own>0)).all())

    def test_opposing_weight_distinguishes_same_count_with_different_influence(self):
        weights = np.array([[[.2,.7,.1],[.2,.7,.1],[.2,.7,.1]]]*2)
        choices = np.array([[True,False,True],[True,True,False]])
        np.testing.assert_allclose(opposing_weight(weights,choices),[.7,.1])

    def test_group_adjustment_removes_a_pure_group_confound(self):
        # Both network feature and behavior differ ONLY between groups.
        x = np.array([.1,.1,.9,.9])
        y = np.array([0.,0.,1.,1.])
        groups = np.array([[0],[0],[1],[1]])
        np.testing.assert_allclose(residualize(x,groups),0,atol=1e-12)
        rows = conditional_curve(x,y,groups,[0,.5,1],np.ones(4)/4)
        np.testing.assert_allclose([r['within_group_difference_pp'] for r in rows],0)
        self.assertEqual(correlation(np.ones(5),np.arange(5)),None)


class ExtractionTests(unittest.TestCase):
    def test_pre_influence_weights_are_used_and_checkpoint_can_resume(self):
        from experiment.tests.test_pipeline import PipelineTests
        from experiment.results import ResultStore
        from experiment.design import Composition
        fixture = PipelineTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        store = ResultStore(fixture.directory,fixture.definition)
        solo = [0,1,0,1]
        cognition = [0,1,1,0]
        for variant,on in (('baseline',solo),('decision',solo),('cognition',cognition)):
            composition = Composition('P01',(),0) if variant=='baseline' else Composition('P01',('P02',),1)
            meta,arrays = fixture.fixture(composition,0,variant,on)
            if variant!='baseline':
                arrays['influence_matrix'] = np.array([[[.7,.3],[.2,.8]]]*4)
                # Deliberately different post-update weights; using them would
                # reverse the interpretation of retained driver influence.
                arrays['trust'] = np.array([[[.1,.9],[.8,.2]]]*4)
                private = solo if variant=='decision' else [0,1,1,1]
                arrays['private_decisions'] = np.column_stack([private, np.logical_not(private)]).astype(bool)
                arrays['final_decisions'] = np.column_stack([on, np.logical_not(on)]).astype(bool)
            store.save(composition,0,variant,'low_0',meta,arrays)
        store.close()
        table = dict(driver=np.array([0]),track=np.array([0]),composition=np.array([1]),start=np.array([0]),
                     passenger_count=np.array([1]),_drivers=['P01'],_tracks=['low_0'],
                     decision_mismatch_cycles=np.array([0]),cognition_mismatch_cycles=np.array([2]),
                     cross_mismatch_cycles=np.array([2]))
        output = Path(fixture.temp.name)/'analysis'
        output.mkdir()
        settings = fixture.definition['parameters']
        first = extract(table,np.array([[0]]),fixture.directory,output,'fixture',settings)
        np.testing.assert_allclose(first['self_weight'],.7)
        np.testing.assert_array_equal(first['changed'].sum(axis=2),[[0,2,2]])
        np.testing.assert_allclose(first['opposing_weight'],.3)
        # All expensive network calculations must be bypassed on resume.
        with patch('experiment.analysis.network_dynamics.run.network_measures',side_effect=AssertionError('recomputed')):
            second = extract(table,np.array([[0]]),fixture.directory,output,'fixture',settings)
        np.testing.assert_array_equal(first['changed'],second['changed'])
        table['cognition_mismatch_cycles'][0] = 0
        with self.assertRaisesRegex(ValueError,'disagrees with the comparison cache'):
            extract(table,np.array([[0]]),fixture.directory,output,'changed-comparison-key',settings)


if __name__ == '__main__':
    unittest.main()
