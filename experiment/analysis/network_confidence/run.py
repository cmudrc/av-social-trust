"""Relate weighted driver centrality to confidence without rereading archives."""
from pathlib import Path
import json
import sys
if __package__ in (None,''):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/'src')]
import numpy as np
from experiment.analysis.shared.output import result_directory,write_results,comparison_directory
from experiment.analysis.shared.paired import balanced_weights,correlation
from experiment.analysis.shared.table import cache_key
from experiment.analysis.network_dynamics.metrics import residualize
from experiment.analysis.influence_timing.plot import step_blocks

NAME='network_confidence'


def weighted_quantiles(values,weights,probabilities=(.25,.5,.75)):
    values,weights=np.asarray(values),np.asarray(weights)
    if values.ndim!=1 or weights.shape!=values.shape or not len(values) or not np.isfinite(values).all() or not np.isfinite(weights).all() or (weights<0).any() or weights.sum()<=0:
        raise ValueError('Expected finite observations and nonnegative weights with positive total')
    keep=weights>0
    order=np.argsort(values[keep],kind='stable')
    v,w=values[keep][order],weights[keep][order]
    positions=(np.cumsum(w)-.5*w)/w.sum()
    return np.interp(probabilities,positions,v)


def matched_data(network,confidence):
    for key in ('driver','track','composition','start','passenger_count','_drivers','_tracks','_settings','_comparison_key'):
        if not np.array_equal(network[key],confidence[key]):
            raise ValueError(f'Network and confidence samples are not matched: {key}')
    if network['relative_influence'].shape!=confidence['confidence_before'][:,1:].shape:
        raise ValueError('Network and confidence step axes differ')


def summarize(network,confidence):
    matched_data(network,confidence)
    weights=balanced_weights(network['driver'],network['passenger_count'])
    groups=np.stack([network[k] for k in ('driver','track','passenger_count')],axis=1)
    result=dict(sampled_car_tracks=len(weights),sampled_base_cars=len(weights)//len(network['_tracks']),
                drivers=len(np.unique(network['driver'])),tracks=len(network['_tracks']),steps=network['relative_influence'].shape[-1],
                definition='Weighted centrality uses the left stationary distribution of the current row-normalized trust network, multiplied by occupant count. 1 is an equal share of influence. The network is held fixed only for calculating this measure, not in the simulation.',
                interpretation='Matched descriptive associations. Centrality includes self-trust through network weights and both evolve under the same trust rules, so their association is not an independent causal effect or a forecast of actual consensus.',
                weighting='Equal driver and passenger-count weights; the same sampled cars are reused on all nine tracks.',
                profiles={},associations=[],confidence_bins={},changes={},early_late={})
    for m,mode in enumerate(('decision','cognition')):
        centrality=network['relative_influence'][:,m]
        self_trust=confidence['confidence_before'][:,m+1]
        x,blocks,bounds=step_blocks(centrality)
        q=np.stack([weighted_quantiles(blocks[:,i],weights) for i in range(blocks.shape[1])],axis=1)
        result['profiles'][mode]=dict(steps=x.tolist(),blocks=bounds,lower=q[0].tolist(),median=q[1].tolist(),upper=q[2].tolist())
        avg_centrality,avg_confidence=centrality.mean(axis=1),self_trust.mean(axis=1)
        delta_centrality=centrality[:,-20:].mean(axis=1)-centrality[:,:20].mean(axis=1)
        delta_confidence=self_trust[:,-20:].mean(axis=1)-self_trust[:,:20].mean(axis=1)
        result['changes'][mode]=dict(centrality=delta_centrality.tolist(),confidence=delta_confidence.tolist())
        result['early_late'][mode]={phase:weighted_quantiles(centrality[:,sl].mean(axis=1),weights).tolist()
                                   for phase,sl in (('early',slice(0,20)),('late',slice(-20,None)))}
        for timing,a,b in (('Drive averages',avg_centrality,avg_confidence),
                           ('Early-to-late changes',delta_centrality,delta_confidence)):
            result['associations'].append(dict(mode=mode,timing=timing,spearman=correlation(a,b),
                within_driver_track_count=correlation(residualize(a,groups),residualize(b,groups))))
        codes=np.clip(np.searchsorted(np.linspace(0,1,6),avg_confidence,side='right')-1,0,4)
        result['confidence_bins'][mode]=[dict(cases=int(keep.sum()),confidence=float(np.average(avg_confidence[keep],weights=weights[keep])),
            centrality=float(np.average(avg_centrality[keep],weights=weights[keep]))) for b in range(5) for keep in [codes==b] if keep.any()]
    return result


def run(output=None):
    network_path=result_directory('network_dynamics')/'cycles.npz'
    confidence_path=result_directory('driver_confidence')/'cycles.npz'
    keys=('driver','track','composition','start','passenger_count','_drivers','_tracks','_settings','_comparison_key')
    with np.load(network_path,allow_pickle=False) as z:
        network={k:z[k] for k in (*keys,'relative_influence')}
    with np.load(confidence_path,allow_pickle=False) as z:
        confidence={k:z[k] for k in (*keys,'confidence_before')}
    if str(network['_comparison_key'])!=cache_key(comparison_directory()/'comparisons.sqlite'):
        raise ValueError('Saved trajectory sample is stale')
    result=summarize(network,confidence)
    output=Path(output) if output is not None else result_directory(NAME)
    output.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(output/'plots.npz',centrality=network['relative_influence'].mean(axis=2),
                        confidence=confidence['confidence_before'][:,1:].mean(axis=2))
    lines=[f"**{result['sampled_base_cars']} base cars on {result['tracks']} tracks ({result['sampled_car_tracks']:,} car–track cases).**",'',
           result['definition'],'',result['interpretation'],'',
           '![Centrality over time](results/figures/centrality_over_time.png)','',
           'Lines show the median and shading the central half of sampled car–track values, after averaging within ten-step blocks. The shaded range describes variation between cases; it is not a confidence interval.', '',
           '![Centrality and confidence](results/figures/centrality_confidence.png)','',
           'Each faint point is one car–track drive average; large points show means in five confidence bins. The horizontal reference is an equal share of network influence.', '',
           '| Method | Association of drive averages | Within driver / track / passenger count | Association of early-to-late changes |',
           '| --- | ---: | ---: | ---: |']
    for mode in ('decision','cognition'):
        a,b=[r for r in result['associations'] if r['mode']==mode]
        lines.append(f"| {mode.capitalize()} | {a['spearman']:.3f} | {a['within_driver_track_count']:.3f} | {b['spearman']:.3f} |")
    lines+=['','Early = steps 1–20; late = steps 81–100. Rank associations are descriptive. Repeated tracks and steps are not treated as independent replicates for significance tests.']
    write_results(NAME,result,'\n'.join(lines),output=output)
    from experiment.analysis.network_confidence.plot import render
    render(output)
    return result


if __name__=='__main__':
    run()
