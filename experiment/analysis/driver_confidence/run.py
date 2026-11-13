"""Track driver self-trust: what updates it and what its changes immediately affect."""
from pathlib import Path
from contextlib import closing
import io
import inspect
import json
import sqlite3
import sys
import time
if __package__ in (None, ''):
    root = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(root), str(root/'src')]
import numpy as np
from experiment.config import RUNS_DIR, DATA_DIR, TRACKS_DIR
from experiment.design import digest, canonical
from experiment.participants import load_participants
from experiment.tracks.generate_tracks import file_hash
from experiment.analysis.shared.output import result_directory, write_results, comparison_directory
from experiment.analysis.shared.paired import balanced_weights, correlation, archive_definition
from experiment.analysis.shared.table import cache_key
from experiment.analysis.network_dynamics.run import source_signature, conditional_curve
from experiment.analysis.network_dynamics.metrics import residualize
from experiment.analysis.driver_confidence import metrics

NAME = 'driver_confidence'
MODES = ('baseline', 'decision', 'cognition')
LEVELS = np.array([0, .25, .5, .75, 1.])
FIELDS = ('confidence_before','confidence_after','incoming_before','incoming_after','outgoing_sum',
          'own_weight','passenger_agreement','group_alignment','incoming_target','confidence_gain',
          'confidence_update_error','incoming_update_error')


def extract(sample, runs, output, definition, participants, track_values):
    settings = definition['parameters']
    n, steps = len(sample['driver']), settings['steps']
    data = {name:sample[name].copy() for name in ('driver','track','composition','start','passenger_count')}
    data.update({name:np.full((n,3,steps),np.nan) for name in FIELDS})
    for name in ('choice','private_choice','changed_solo','changed_private','switched'):
        data[name] = np.zeros((n,3,steps),dtype=bool)
    data['intervention_choices'] = np.zeros((n,2,len(LEVELS),steps),dtype=bool)
    data['intervention_own_weight'] = np.zeros((n,2,len(LEVELS),steps),dtype=np.float32)
    data['observed_replay_mismatches'] = np.zeros((n,2),dtype=np.int16)
    folder = output/'sample_archives'
    folder.mkdir(parents=True,exist_ok=True)
    fingerprint = digest(dict(extract=inspect.getsource(extract),metrics=Path(metrics.__file__).read_text(),
                              participants=definition['inputs']['participant_export'],levels=LEVELS.tolist(),
                              comparison_key=str(sample['_comparison_key']),numpy=np.__version__))
    archive_code = data['driver']*len(sample['_tracks'])+data['track']
    reported = time.monotonic()
    codes = np.unique(archive_code)
    for done,code in enumerate(codes,1):
        positions = np.flatnonzero(archive_code==code)
        person = str(sample['_drivers'][data['driver'][positions[0]]])
        track = str(sample['_tracks'][data['track'][positions[0]]])
        path = Path(runs)/f'{person}_{track}.sqlite'
        keys = np.stack([data['composition'][positions],data['start'][positions]],axis=1)
        signature = digest(dict(source=source_signature(path),keys=keys.tolist(),fingerprint=fingerprint))
        cached = folder/f'{path.stem}.npz'
        part = None
        if cached.exists():
            with np.load(cached,allow_pickle=False) as saved:
                if str(saved['_signature'])==signature:
                    part={name:saved[name] for name in saved.files if not name.startswith('_')}
        if part is None:
            part={name:values[positions].copy() for name,values in data.items() if values.ndim>=2}
            with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
                archived=json.loads(db.execute("SELECT value FROM metadata WHERE key='definition'").fetchone()[0])
                if canonical(archived)!=canonical(definition):
                    raise ValueError(f'Definition differs across sample archives: {path}')
                def read(composition,start,variant):
                    row=db.execute('SELECT trajectory FROM results WHERE composition=? AND start=? AND variant=?',
                                   (int(composition),int(start),variant)).fetchone()
                    if row is None:
                        raise ValueError(f'Missing complete run {person}, {track}, {composition}, {start}, {variant}')
                    with np.load(io.BytesIO(row[0]),allow_pickle=False) as saved:
                        return {name:saved[name] for name in ('initial_trust','trust','connection_mask','alpha','private_opinions',
                            'private_decisions','private_cognition','final_decisions','influence_matrix','initial_cognition')}
                baselines={start:read(0,start,'baseline') for start in np.unique(keys[:,1])}
                available=track_values[track]['available']
                for j,(composition,start) in enumerate(keys):
                    baseline=baselines[start]
                    base_choice=baseline['final_decisions'][:,0]
                    initial=None
                    for m,mode in enumerate(MODES):
                        model=baseline if m==0 else read(composition,start,mode)
                        if not np.array_equal(model['initial_cognition'][0],baseline['initial_cognition'][0]) or model['initial_trust'][0,0]!=baseline['initial_trust'][0,0]:
                            raise ValueError('Driver initialization does not match solo')
                        if m:
                            if initial is None:
                                initial=(model['initial_trust'],model['initial_cognition'])
                            elif any(not np.array_equal(a,b) for a,b in zip(initial,(model['initial_trust'],model['initial_cognition']))):
                                raise ValueError('Influence models do not have the same initialization')
                        before,fields=metrics.confidence_measures(model['initial_trust'],model['trust'],model['connection_mask'],
                            model['alpha'],model['private_opinions'],settings['self_learning_rate'],settings['interpersonal_learning_rate'])
                        if not np.allclose(metrics.normalize_batch(before),model['influence_matrix'],rtol=0,atol=1e-12):
                            raise ValueError('Reconstructed trust is not aligned with the archived influence weights')
                        for name,value in fields.items():
                            part[name][j,m]=value
                        choice=model['final_decisions'][:,0].astype(bool)
                        private=model['private_decisions'][:,0].astype(bool)&available
                        part['choice'][j,m]=choice
                        part['private_choice'][j,m]=private
                        part['changed_solo'][j,m]=choice!=base_choice
                        part['changed_private'][j,m]=choice!=private
                        part['switched'][j,m,1:]=choice[1:]!=choice[:-1]
                        if m:
                            expected=sample['changed'][positions[j],m-1]
                            if not np.array_equal(part['changed_solo'][j,m],expected):
                                raise ValueError('Confidence outcomes disagree with sampled network data')
                            replay,_=metrics.replay(before,model['private_cognition'],model['private_opinions'],
                                participants[person]['tree'],mode,settings['discussion_rounds'],available)
                            part['observed_replay_mismatches'][j,m-1]=np.count_nonzero(replay!=choice)
                            intervention,own_weight=metrics.intervene(before,model['private_cognition'],model['private_opinions'],
                                participants[person]['tree'],mode,settings['discussion_rounds'],available,LEVELS)
                            part['intervention_choices'][j,m-1]=intervention
                            part['intervention_own_weight'][j,m-1]=own_weight
            temporary=cached.with_suffix('.tmp.npz')
            np.savez_compressed(temporary,_signature=np.array(signature),**part)
            temporary.replace(cached)
        for name,values in part.items():
            data[name][positions]=values
        if time.monotonic()-reported>=5:
            print(f'  Confidence trajectories: {done}/{len(codes)} archives',flush=True)
            reported=time.monotonic()
    if np.nanmax(np.abs(data['confidence_update_error']))>1e-12 or np.nanmax(np.abs(data['incoming_update_error']))>1e-12:
        raise ValueError('Archived trust changes do not follow the expected update rules')
    data['_drivers'],data['_tracks']=sample['_drivers'],sample['_tracks']
    data['_comparison_key']=sample['_comparison_key']
    data['_settings']=np.array(json.dumps(settings))
    data['_levels']=LEVELS
    np.savez_compressed(output/'cycles.npz',**data)
    return data


def average(values,weights):
    return float(np.average(values,weights=weights))


def summarize(data,track_values):
    n,_,steps=data['choice'].shape
    weights=balanced_weights(data['driver'],data['passenger_count'])
    groups=np.stack([data['driver'],data['track'],data['passenger_count']],axis=1)
    confidence=data['confidence_before']
    change=data['confidence_after'][:,:,-1]-confidence[:,:,0]
    base_keys=np.rec.fromarrays([data[k] for k in ('driver','composition','start')],names='driver,composition,start')
    keys,inverse=np.unique(base_keys,return_inverse=True)
    ids=np.repeat(inverse,steps)
    cycle_weights=np.repeat(weights/steps,steps)
    stages=np.tile(np.minimum(np.arange(steps)*3//steps,2),n)
    strata=np.column_stack([np.repeat(groups,steps,axis=0),stages])
    result=dict(definition='Driver confidence = raw self-trust, on the 0–1 model scale; it is not a calibrated probability of being correct.',
        sampled_car_tracks=n,sampled_base_cars=len(keys),drivers=len(np.unique(data['driver'])),steps=steps,
        weighting='Equal drivers and passenger counts; same sampled cars on every track; persistence averaged for complexity figures.',
        interpretation='Update relationships are verified model rules. Observed associations are descriptive. Interventions change only confidence in fixed cycle snapshots; they are not new full-drive trajectories or real-world causal estimates.',
        self_learning_rate=json.loads(str(data['_settings']))['self_learning_rate'],
        overall={},profiles={},complexity_profiles={},by_passengers={},associations=[],confidence_curves={},
        update_curve={},interventions={},by_initial_confidence={},
        checks=dict(max_self_update_error=float(np.nanmax(np.abs(data['confidence_update_error']))),
                    max_incoming_update_error=float(np.nanmax(np.abs(data['incoming_update_error']))),
                    observed_replay_mismatches=data['observed_replay_mismatches'].sum(axis=0).astype(int).tolist()))
    for m,mode in enumerate(MODES):
        initial=confidence[:,m,0]
        result['overall'][mode]=dict(initial=average(initial,weights),final=average(data['confidence_after'][:,m,-1],weights),
            change=average(change[:,m],weights),fraction_increasing=average((change[:,m]>1e-6).astype(float),weights),
            fraction_decreasing=average((change[:,m]<-1e-6).astype(float),weights),
            final_quartiles=np.quantile(data['confidence_after'][:,m,-1],[.25,.5,.75]).tolist())
        result['profiles'][mode]=dict(confidence=np.einsum('i,it->t',weights,confidence[:,m]).tolist(),
            confidence_after=np.einsum('i,it->t',weights,data['confidence_after'][:,m]).tolist())
        if m:
            for field in ('incoming_before','own_weight','outgoing_sum'):
                result['profiles'][mode][field]=np.einsum('i,it->t',weights,data[field][:,m]).tolist()
        result['complexity_profiles'][mode]={}
        for complexity in ('low','normal','high'):
            keep=np.isin(data['track'],[i for i,name in enumerate(data['_tracks']) if track_values[str(name)]['difficulty']==complexity])
            w=weights[keep]/weights[keep].sum()
            result['complexity_profiles'][mode][complexity]=dict(
                confidence=np.einsum('i,it->t',w,confidence[keep,m]).tolist(),
                final=average(data['confidence_after'][keep,m,-1],w),change=average(change[keep,m],w))
        result['by_passengers'][mode]=[dict(passengers=int(k),initial=average(initial[keep],weights[keep]),
            final=average(data['confidence_after'][keep,m,-1],weights[keep]),change=average(change[keep,m],weights[keep]))
            for k in np.unique(data['passenger_count']) for keep in [data['passenger_count']==k]]
        initial_bins=np.clip(np.searchsorted([0,.2,.4,.6,.8,1],initial,side='right')-1,0,4)
        result['by_initial_confidence'][mode]=[dict(lo=.2*b,hi=.2*(b+1),cars=int(keep.sum()),
            profile=np.einsum('i,it->t',weights[keep]/weights[keep].sum(),confidence[keep,m]).tolist())
            for b in range(5) for keep in [initial_bins==b] if keep.any()]
        if not m:
            continue
        predictors={label:values for label,values in (
            ('Initial confidence',initial),
            ('Initial passengers’ trust in driver',data['incoming_before'][:,m,0]),
            ('Initial driver trust in passengers',data['outgoing_sum'][:,m,0]/data['passenger_count']),
            ('Passengers agreeing with driver (drive average)',data['passenger_agreement'][:,m].mean(axis=1)),
            ('Driver agrees with group (drive average)',data['group_alignment'][:,m].mean(axis=1)))}
        for label,x in predictors.items():
            result['associations'].append(dict(mode=mode,predictor=label,outcome='Confidence change over drive',
                spearman=correlation(x,change[:,m]),within_driver_track_count=correlation(residualize(x,groups),residualize(change[:,m],groups))))
        for label,x,y in (
            ('Initial confidence',initial,data['changed_solo'][:,m].mean(axis=1)),
            ('Early confidence',confidence[:,m,:min(20,steps)].mean(axis=1),data['changed_solo'][:,m,-min(20,steps):].mean(axis=1))):
            result['associations'].append(dict(mode=mode,predictor=label,outcome='Different decisions from solo (whole drive)' if label.startswith('Initial') else 'Different decisions from solo (late drive)',
                spearman=correlation(x,y),within_driver_track_count=correlation(residualize(x,groups),residualize(y,groups))))
        c=confidence[:,m].ravel()
        result['confidence_curves'][mode]={outcome:conditional_curve(c,data[field][:,m].ravel(),strata,
            [0,.2,.4,.6,.8,1],cycle_weights,ids) for outcome,field in
            (('different_from_solo','changed_solo'),('different_from_private','changed_private'),('decision_switches','switched'))}
        gap=data['incoming_before'][:,m]-confidence[:,m]
        result['update_curve'][mode]=conditional_curve(gap.ravel(),data['confidence_gain'][:,m].ravel(),strata,
            [-1,-.6,-.3,-.1,0,.1,.3,.6,1],cycle_weights,ids)
        choices=data['intervention_choices'][:,m-1]
        private=data['private_choice'][:,m]
        baseline=data['choice'][:,0]
        result['interventions'][mode]=dict(levels=data['_levels'].tolist(),
            own_weight=np.einsum('i,ilt->l',weights,data['intervention_own_weight'][:,m-1]/steps).tolist(),
            different_from_private_percent=(100*np.einsum('i,ilt->l',weights,(choices!=private[:,None])/steps)).tolist(),
            different_from_solo_percent=(100*np.einsum('i,ilt->l',weights,(choices!=baseline[:,None])/steps)).tolist(),
            automation_percent=(100*np.einsum('i,ilt->l',weights,choices/steps)).tolist(),
            low_to_high_choice_change_percent=float(100*np.average((choices[:,0]!=choices[:,-1]).mean(axis=1),weights=weights)))
    result['checks']['solo_max_confidence_change']=float(np.max(np.abs(change[:,0])))
    result['checks']['initial_confidence_max_mode_difference']=float(np.max(np.abs(confidence[:,1:,0]-confidence[:,:1,0])))
    return result


def markdown(result):
    from experiment.analysis.shared.stats import markdown_table
    lines=[result['definition'],'',f"**{result['sampled_base_cars']:,} sampled cars on nine tracks**, {result['sampled_car_tracks']:,} car–track comparisons.",'',
           result['weighting'],'',result['interpretation'],'',
           '### Track confidence through the drive','',
           '![Confidence trajectories](results/figures/confidence_trajectories.png)','',
           markdown_table(['Method','Initial confidence','Final confidence','Mean change'],
               [[mode,f"{row['initial']:.3f}",f"{row['final']:.3f}",f"{row['change']:+.3f}"] for mode,row in result['overall'].items()]),'',
           '![Different starting confidence](results/figures/starting_confidence.png)','',
           '### What affects confidence?','',
           f"The exact update is: next confidence = current confidence + {result['self_learning_rate']:g} × "
           '(passengers’ mean raw trust in the driver − current confidence). Confidence rises when passengers’ trust exceeds it, '
           'falls when it is lower, and remains constant when driving alone. This relationship is built into the model, not an empirical discovery.','',
           '![Confidence update](results/figures/confidence_update.png)','',
           '![Confidence by complexity](results/figures/confidence_by_complexity.png)','',
           '![Confidence by passengers](results/figures/confidence_by_passengers.png)','',
           'Opinions update passengers’ trust after the cycle. That updated appraisal changes confidence in the following cycle’s trust update. '
           'Track complexity and occupant disagreement therefore act indirectly through opinions and trust.','',
           '### What does confidence affect?','',
           'With one discussion round, the driver’s own weight is raw self-trust divided by '
           '(raw self-trust + total driver trust in passengers). High confidence alone does not ensure high own weight.','',
           '![Confidence and observed decisions](results/figures/observed_confidence.png)','',
           'Observed binned rates are descriptive and can reflect other changing conditions.','',
           '![Changing only confidence](results/figures/confidence_intervention.png)','',
           'For each recorded cycle, the intervention sets only driver self-trust to 0, 0.25, 0.5, 0.75 or 1. '
           'All other trust entries, private opinions, cognitive states and automation availability stay fixed. '
           'Discussion and the driver’s decision are recomputed. Outputs are not carried forward to later cycles. '
           'This isolates the immediate effect of confidence within the model, not the full effect on a future drive.','',
           'Cognition-mode comparisons with the current private decision distinguish immediate influence from changes already carried in cognition. '
           'The solo decision is an additional reference, not a new starting state for these interventions.','',
           '### Numerical checks and associations','',
           f"Maximum confidence-update error: {result['checks']['max_self_update_error']:.2e}; "
           f"maximum passenger-trust-update error: {result['checks']['max_incoming_update_error']:.2e}. "
           f"Replaying the observed snapshots disagreed on {result['checks']['observed_replay_mismatches']} decisions "
           '(decision, cognition; near-boundary rounding is reported rather than hidden).','',
           markdown_table(['Method','Predictor','Outcome','Rank association','Within comparable groups'],
               [[r['mode'],r['predictor'],r['outcome'], '—' if r['spearman'] is None else f"{r['spearman']:+.3f}",
                 '—' if r['within_driver_track_count'] is None else f"{r['within_driver_track_count']:+.3f}"] for r in result['associations']]),'',
           'Within comparable groups means subtracting averages within driver × track × passenger count before calculating the rank association. '
           'No independent-cycle significance tests are used. Full measurements and identifiers are saved in cycles.npz.']
    return '\n'.join(lines)


def run(output=None,runs=RUNS_DIR,network_directory=None):
    output=Path(output) if output else result_directory(NAME)
    output.mkdir(parents=True,exist_ok=True)
    network_directory=Path(network_directory) if network_directory else result_directory('network_dynamics')
    with np.load(network_directory/'cycles.npz',allow_pickle=False) as saved:
        sample={name:saved[name] for name in ('driver','track','composition','start','passenger_count','changed',
                                             '_drivers','_tracks','_comparison_key')}
    if str(sample['_comparison_key'])!=cache_key(comparison_directory()/'comparisons.sqlite'):
        raise ValueError('Network sample is stale; rerun network_dynamics first')
    definition=archive_definition(runs,str(sample['_drivers'][0]),str(sample['_tracks'][0]))
    if file_hash(DATA_DIR/'combined_models.mat')!=definition['inputs']['participant_export']:
        raise ValueError('Participant models differ from archived inputs')
    participants=load_participants()
    manifest=json.loads((TRACKS_DIR/'manifest.json').read_text())
    track_values={}
    for track in manifest['tracks']:
        path=TRACKS_DIR/f"{track['name']}.csv"
        if file_hash(path)!=definition['inputs']['tracks'][track['name']]:
            raise ValueError('Track differs from archived inputs')
        values=np.genfromtxt(path,delimiter=',',names=True)
        track_values[track['name']]=dict(difficulty=track['difficulty'],available=values['automation_available'].astype(bool))
    print(f"Reading self-trust for {len(sample['driver']):,} matched car–track cases; resumable by archive.",flush=True)
    data=extract(sample,runs,output,definition,participants,track_values)
    result=summarize(data,track_values)
    write_results(NAME,result,markdown(result),output=output)
    from experiment.analysis.driver_confidence.plot import render
    render(output)
    print(f'Saved {output}; confidence tracked and immediate interventions complete.',flush=True)
    return result

if __name__=='__main__':
    run()
