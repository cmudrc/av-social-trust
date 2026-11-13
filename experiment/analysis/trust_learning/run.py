"""Can a car that starts almost like solo driving become socially influenced?

Reuse archived occupants, cognition, trust, alpha and tracks. Rerun full drives,
changing only initial trust and whether trust learning is enabled. Source runs
are read-only; intervention outputs have separate, resumable checkpoints.
"""
from contextlib import closing
import io
import json
from pathlib import Path
import sqlite3
import sys
import time

if __package__ in (None, ''):
    root = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(root), str(root / 'src')]

import numpy as np
from av_social_trust.consensus import normalize_trust_matrix
from experiment.config import Settings, RUNS_DIR, DATA_DIR
from experiment.design import canonical, digest
from experiment.model import run_model
from experiment.participants import load_participants
from experiment.tracks.generate_tracks import load_tracks, file_hash
from experiment.analysis.network_dynamics.run import source_signature
from experiment.analysis.shared.output import result_directory, write_results, comparison_directory
from experiment.analysis.shared.paired import balanced_weights
from experiment.analysis.shared.table import cache_key
from experiment.analysis.shared.stats import markdown_table

NAME = 'trust_learning'
SEED = 837
SCALE = 2.0 ** -10  # Exact binary scaling avoids artificial tie flips from roundoff.
MODES = ('decision', 'cognition')
CONDITIONS = ('original_learning', 'original_fixed', 'weak_learning', 'weak_fixed',
              'all_small_learning', 'all_small_fixed')
LABELS = ('Original trust, learning', 'Original trust, fixed',
          'Weak passenger ties, learning', 'Weak passenger ties, fixed',
          'All trust reduced, learning', 'All trust reduced, fixed')


def intervention(initial, condition, scale=SCALE):
    if condition not in CONDITIONS or not 0 < scale <= 1:
        raise ValueError('Unknown condition or invalid scale')
    result = {k: v.copy() if isinstance(v, np.ndarray) else v for k, v in initial.items()}
    if condition.startswith('weak_'):
        mask = ~np.eye(len(result['trust']), dtype=bool)
        result['trust'][mask] *= scale
    elif condition.startswith('all_small_'):
        result['trust'] *= scale
    if condition.endswith('_fixed'):
        result['rates'][:] = 0
    return result


def choose_sample(data):
    """One of the six existing sampled base cars per driver/passenger count."""
    first = np.flatnonzero(data['track'] == 0)
    rng = np.random.default_rng(SEED)
    keys = []
    for d in np.unique(data['driver']):
        for k in np.unique(data['passenger_count'][data['driver'] == d]):
            options = first[(data['driver'][first] == d) & (data['passenger_count'][first] == k)]
            row = rng.choice(options)
            keys.append((d, data['composition'][row], data['start'][row]))
    selected = np.zeros(len(data['driver']), dtype=bool)
    for d, c, s in keys:
        selected |= (data['driver'] == d) & (data['composition'] == c) & (data['start'] == s)
    rows = np.flatnonzero(selected)
    if len(rows) != len(keys) * len(data['_tracks']):
        raise ValueError('Sample must contain the same cars on every track')
    return rows


def extract(output, runs=RUNS_DIR):
    sample_path = result_directory('network_dynamics') / 'cycles.npz'
    with np.load(sample_path, allow_pickle=False) as z:
        data = {k: z[k] for k in ('driver', 'track', 'composition', 'start', 'passenger_count',
                                 '_drivers', '_tracks', '_settings', '_comparison_key')}
    if str(data['_comparison_key']) != cache_key(comparison_directory() / 'comparisons.sqlite'):
        raise ValueError('Network sample is stale; run network_dynamics first')
    parameters = json.loads(str(data['_settings']))
    settings = Settings(**parameters)
    participants = load_participants()
    track_metadata, tracks = load_tracks(settings)
    root = Path(__file__).resolve().parents[3]
    code = {path: file_hash(root / path) for path in (
        'experiment/model.py', 'experiment/participants.py',
        'src/av_social_trust/trust.py', 'src/av_social_trust/consensus.py')}
    inputs = dict(code=code, participant_export=file_hash(DATA_DIR / 'combined_models.mat'),
                  tracks={t['name']: t['sha256'] for t in track_metadata})
    rows = choose_sample(data)
    arrays = {k: data[k][rows] for k in ('driver', 'track', 'composition', 'start', 'passenger_count')}
    shape = (len(rows), len(CONDITIONS), len(MODES), settings.steps)
    arrays['changed'] = np.zeros(shape, dtype=bool)
    arrays['choice'] = np.zeros(shape, dtype=bool)
    arrays['self_weight'] = np.zeros(shape)
    arrays['self_trust'] = np.zeros(shape)
    arrays['passenger_trust'] = np.zeros(shape)
    folder = output / 'checkpoints'
    folder.mkdir(parents=True, exist_ok=True)
    fingerprint = digest(dict(script=Path(__file__).read_text(), numpy=np.__version__,
                              inputs=inputs, seed=SEED, scale=SCALE, parameters=parameters))
    codes = arrays['driver'] * len(data['_tracks']) + arrays['track']
    started = reported = time.monotonic()
    for done, code_id in enumerate(np.unique(codes), 1):
        positions = np.flatnonzero(codes == code_id)
        d, t = (int(arrays[k][positions[0]]) for k in ('driver', 'track'))
        person, track = str(data['_drivers'][d]), str(data['_tracks'][t])
        path = Path(runs) / f'{person}_{track}.sqlite'
        keys = np.stack([arrays['composition'][positions], arrays['start'][positions]], axis=1)
        signature = digest(dict(source=source_signature(path), keys=keys.tolist(), fingerprint=fingerprint))
        cached = folder / f'{path.stem}.npz'
        part = None
        if cached.exists():
            with np.load(cached, allow_pickle=False) as z:
                if str(z['_signature']) == signature:
                    part = {k: z[k] for k in z.files if not k.startswith('_')}
        if part is None:
            part = {k: v[positions].copy() for k, v in arrays.items() if v.ndim == 4}
            with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
                definition = json.loads(db.execute("SELECT value FROM metadata WHERE key='definition'").fetchone()[0])
                old = definition['inputs']
                if canonical(definition['parameters']) != canonical(parameters) or any(
                    old['code'].get(k) != v for k, v in inputs['code'].items()
                ) or old['participant_export'] != inputs['participant_export'] or old['tracks'] != inputs['tracks']:
                    raise ValueError(f'Archived inputs differ from current simulation inputs: {path}')
                for j, (composition, start) in enumerate(keys):
                    blob = db.execute("SELECT automation_on FROM results WHERE composition=0 AND start=? AND variant='baseline'",
                                      (int(start),)).fetchone()[0]
                    solo = np.unpackbits(np.frombuffer(blob, dtype=np.uint8))[:settings.steps].astype(bool)
                    initial_pair = []
                    for m, mode in enumerate(MODES):
                        row = db.execute('SELECT metadata,trajectory FROM results WHERE composition=? AND start=? AND variant=?',
                                         (int(composition), int(start), mode)).fetchone()
                        metadata = json.loads(row[0])
                        with np.load(io.BytesIO(row[1]), allow_pickle=False) as z:
                            archived = {k: z[k] for k in ('initial_cognition', 'initial_trust', 'alpha', 'connection_mask',
                                                         'automation_on', 'private_cognition', 'trust')}
                        initial = dict(agents=[person, *metadata['passengers']], cognition=archived['initial_cognition'],
                                       trust=archived['initial_trust'], alpha=archived['alpha'], mask=archived['connection_mask'])
                        rates = initial['mask'].astype(float) * settings.interpersonal_learning_rate
                        np.fill_diagonal(rates, settings.self_learning_rate)
                        initial['rates'] = rates
                        initial_pair.append(initial)
                        trajectories = []
                        for c, condition in enumerate(CONDITIONS):
                            changed_initial = intervention(initial, condition)
                            result = run_model(changed_initial, participants, settings, mode, tracks[track])
                            trajectories.append(result)
                            if condition == 'original_learning':
                                for field in ('automation_on', 'private_cognition', 'trust'):
                                    if not np.array_equal(result[field], archived[field]):
                                        raise ValueError(f'Reference replay differs from archive: {path}, {field}')
                            before = np.concatenate([changed_initial['trust'][None], result['trust'][:-1]])
                            part['choice'][j, c, m] = result['automation_on']
                            part['changed'][j, c, m] = result['automation_on'] != solo
                            effective = np.linalg.matrix_power(result['influence_matrix'], settings.discussion_rounds)
                            part['self_weight'][j, c, m] = effective[:, 0, 0]
                            part['self_trust'][j, c, m] = before[:, 0, 0]
                            part['passenger_trust'][j, c, m] = before[:, 0, 1:].mean(axis=1)
                            if condition.endswith('_fixed') and not np.array_equal(result['trust'], np.broadcast_to(changed_initial['trust'], result['trust'].shape)):
                                raise ValueError('Frozen trust unexpectedly changed')
                        # Row normalization cancels uniform scaling; frozen runs must agree.
                        for field in ('automation_on', 'private_decisions'):
                            if not np.array_equal(trajectories[1][field], trajectories[5][field]):
                                raise ValueError(f'Uniformly scaled frozen trust changed behavior: {path}, composition={composition}, start={start}, mode={mode}, field={field}, cycles={np.flatnonzero(trajectories[1][field] != trajectories[5][field]).tolist()}')
                        if not np.allclose(trajectories[0]['influence_matrix'][0], trajectories[4]['influence_matrix'][0], atol=1e-14, rtol=0):
                            raise ValueError('Uniform scaling changed initial weights')
                    for field in ('agents', 'cognition', 'trust', 'alpha', 'mask', 'rates'):
                        if not np.array_equal(initial_pair[0][field], initial_pair[1][field]):
                            raise ValueError('Influence modes have unmatched initial conditions')
            temporary = cached.with_suffix('.tmp.npz')
            np.savez_compressed(temporary, _signature=np.array(signature), **part)
            temporary.replace(cached)
        for k, v in part.items():
            arrays[k][positions] = v
        if time.monotonic() - reported >= 5:
            print(f'  Trust interventions: {done}/234 archives; {time.monotonic()-started:.0f}s', flush=True)
            reported = time.monotonic()
    for k in ('_drivers', '_tracks', '_settings', '_comparison_key'):
        arrays[k] = data[k]
    arrays['_fingerprint'] = np.array(fingerprint)
    np.savez_compressed(output / 'cycles.npz', **arrays)
    return arrays


def summarize(data):
    weights = balanced_weights(data['driver'], data['passenger_count'])
    changed = data['changed']
    result = dict(sampled_car_tracks=len(weights), sampled_base_cars=len(weights)//len(data['_tracks']),
                  drivers=len(np.unique(data['driver'])), tracks=len(data['_tracks']), cycles=changed.shape[-1],
                  scale=SCALE, seed=SEED, conditions=list(CONDITIONS), rows=[], learning_contrasts=[],
                  sampling='One fixed random base car per driver/passenger count from the existing network sample, repeated on all nine tracks. Equal driver/passenger-count weight.',
                  interpretation='Paired full-drive interventions within the simulation. Weak ties reduce every interpersonal edge by 1,024 while retaining self-trust. All-small reduces self-trust too. Fixed conditions freeze both self-trust and interpersonal trust. Results are conditional on this small sampled set of initial states and the nine available tracks.',
                  checks=dict(reference_replay='Exact decisions, private cognition and trust match all archived references.',
                              frozen_trust='Unchanged at every cycle.', uniform_scaling='Frozen decisions unchanged in both modes; initial learned weights unchanged.'))
    result['curves'] = {k: np.einsum('i,icmt->cmt', weights, data[k]).tolist()
                        for k in ('changed', 'self_weight', 'self_trust', 'passenger_trust')}
    for c, condition in enumerate(CONDITIONS):
        for m, mode in enumerate(MODES):
            values = changed[:, c, m]
            result['rows'].append(dict(condition=condition, mode=mode,
                first_cycle_percent=float(100*np.average(values[:, 0], weights=weights)),
                early_percent=float(100*np.average(values[:, :20].mean(axis=1), weights=weights)),
                late_percent=float(100*np.average(values[:, -20:].mean(axis=1), weights=weights)),
                whole_percent=float(100*np.average(values.mean(axis=1), weights=weights)),
                any_change_percent=float(100*np.average(values.any(axis=1), weights=weights))))
    for learned, fixed in ((0, 1), (2, 3), (4, 5)):
        for m, mode in enumerate(MODES):
            per_car = (changed[:, learned, m, -20:].mean(axis=1).astype(float) -
                       changed[:, fixed, m, -20:].mean(axis=1)) * 100
            driver_means = [float(per_car[data['driver'] == d].mean()) for d in np.unique(data['driver'])]
            result['learning_contrasts'].append(dict(condition=CONDITIONS[learned], mode=mode,
                late_difference_pp=float(np.average(per_car, weights=weights)),
                driver_range_pp=[min(driver_means), max(driver_means)],
                changed_by_learning_percent=float(100*np.average(
                    (data['choice'][:, learned, m] != data['choice'][:, fixed, m]).mean(axis=1), weights=weights))))
    return result


def markdown(result):
    lines = [f"**{result['sampled_base_cars']} matched base cars × {result['tracks']} tracks = {result['sampled_car_tracks']:,} car–track cases.**",
             '', result['interpretation'], '',
             'Early = cycles 1–20; late = cycles 81–100. Percentages count driver decisions different from the matched solo run.', '',
             markdown_table(['Starting network / learning', 'Influence method', 'First cycle', 'Early', 'Late', 'Whole drive'],
                 [[LABELS[CONDITIONS.index(r['condition'])], r['mode'].capitalize(),
                   *[f"{r[k]:.1f}%" for k in ('first_cycle_percent', 'early_percent', 'late_percent', 'whole_percent')]]
                  for r in result['rows']]), '',
             '![Weak ties](results/figures/weak_ties.png)', '',
             '![Network weight](results/figures/weight_recovery.png)', '',
             '![Uniform scaling](results/figures/uniform_scaling.png)', '',
             'Uniformly reducing every trust value preserves initial influence weights. With learning frozen, it preserves decisions throughout the drive. Low absolute trust alone therefore does not imply solo-like behavior.', '',
             'Weak ties retains initial self-trust and reduces interpersonal trust, making the driver initially listen almost entirely to their own view. Learning can build interpersonal trust and also alter self-trust; this comparison estimates their joint effect, not either learning rule separately.', '',
             'The nine tracks are reused matched trajectories, not nine hundred independent track realizations. The sample uses one initial car per driver/count; it is a targeted mechanism experiment rather than the full parameter sweep.', '',
             'Checks: '+ ' '.join(result['checks'].values())]
    return '\n'.join(lines)


def run(output=None, runs=RUNS_DIR):
    output = Path(output) if output is not None else result_directory(NAME)
    output.mkdir(parents=True, exist_ok=True)
    result = summarize(extract(output, runs))
    write_results(NAME, result, markdown(result), output=output)
    from experiment.analysis.trust_learning.plot import render
    render(output)
    print(f'Saved {output}', flush=True)
    return result


if __name__ == '__main__':
    run()
