"""Check grouping, temporal boundaries and matched network/confidence samples."""
import unittest
import numpy as np
from experiment.analysis.driver_confidence.plot import starting_categories
from experiment.analysis.influence_timing.plot import step_blocks
from experiment.analysis.network_confidence.run import weighted_quantiles,matched_data


class PaperSummaryTests(unittest.TestCase):
    def test_ten_step_blocks_cover_decisions_once_and_retain_partial_block(self):
        values=np.arange(1,24)
        x,means,bounds=step_blocks(values)
        self.assertEqual(bounds,[(1,10),(11,20),(21,23)])
        np.testing.assert_array_equal(x,[5.5,15.5,22])
        np.testing.assert_array_equal(means,[5.5,15.5,22])
        self.assertAlmostEqual(np.average(means,weights=[10,10,3]),values.mean())
        _,batch,_=step_blocks(np.stack([values,values+10]))
        np.testing.assert_array_equal(batch[1],means+10)

    def test_confidence_categories_keep_boundaries_and_final_updates(self):
        initial=np.array([.01,.2,.4,.6,.8,.99])
        before=np.broadcast_to(initial[:,None,None],(6,3,2)).copy()
        after=before+.001
        data=dict(driver=np.zeros(6,int),passenger_count=np.ones(6,int),confidence_before=before,confidence_after=after)
        three=starting_categories(data,3)['decision']
        self.assertEqual([r['label'] for r in three],['Low','Medium','High'])
        self.assertEqual([r['cars'] for r in three],[2,2,2])
        self.assertEqual(len(three[0]['profile']),3)
        self.assertAlmostEqual(three[0]['profile'][-1],three[0]['profile'][0]+.001)
        five=starting_categories(data,5)['decision']
        self.assertEqual([r['label'] for r in five],['Very low','Low','Medium','High','Very high'])
        self.assertEqual([r['cars'] for r in five],[1,1,1,1,2])
        self.assertAlmostEqual(five[3]['profile'][0],.6)

    def test_weighted_quantiles_ignore_zero_weight_and_are_scale_invariant(self):
        values=np.array([1,2,3,999]);weights=np.array([1,2,1,0])
        q=weighted_quantiles(values,weights)
        np.testing.assert_allclose(q,weighted_quantiles(values[:3],weights[:3]))
        np.testing.assert_allclose(q,weighted_quantiles(values,weights*1024))
        self.assertEqual(q[1],2)

    def test_join_rejects_reordered_cases_before_associations(self):
        keys=('driver','track','composition','start','passenger_count','_drivers','_tracks','_settings','_comparison_key')
        network={k:np.array([1,2]) for k in keys}
        confidence={k:v.copy() for k,v in network.items()}
        network['relative_influence']=np.ones((2,2,10))
        confidence['confidence_before']=np.ones((2,3,10))
        matched_data(network,confidence)
        confidence['composition']=np.array([2,1])
        with self.assertRaisesRegex(ValueError,'composition'):
            matched_data(network,confidence)


if __name__=='__main__':
    unittest.main()
