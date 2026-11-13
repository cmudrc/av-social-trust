"""Does the driver's changing network influence predict agreement among methods?"""
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
    sys.path[:0] = [str(root), str(root / 'src')]
import numpy as np
from experiment.config import RUNS_DIR
from experiment.design import digest, canonical
from experiment.analysis.shared.output import result_directory, write_results, comparison_directory
from experiment.analysis.shared.table import cache_key
from experiment.analysis.shared.paired import (selected_columns, matched_tracks, balanced_weights,
                                               archive_definition, correlation)
from experiment.analysis.shared.stats import markdown_table
from experiment.analysis.network_dynamics.metrics import network_measures, residualize, group_bins, opposing_weight
from experiment.analysis.network_dynamics import metrics as network_metrics

NAME = 'network_dynamics'
SEED = 291
COMPOSITIONS_PER_DRIVER_COUNT = 2
STARTS_PER_COMPOSITION = 3
EXTRACTION_VERSION = 2
METRICS = dict(self_weight='How much the driver keeps their own view',
               passenger_attention='How much passengers listen to the driver',
               relative_influence='Driver’s relative influence if the network were held fixed')
EDGES = dict(self_weight=[0, .2, .4, .6, .8, 1],
             passenger_attention=[0, .1, .2, .3, .4, .6, 1],
             relative_influence=[0, .5, .8, 1, 1.2, 1.5, 2, 6])
MODE_NAMES = ['Decision-level', 'Cognition-level']


def choose_sample(table, compositions=COMPOSITIONS_PER_DRIVER_COUNT, starts=STARTS_PER_COMPOSITION, seed=SEED):
    """Sample cars once, reuse their exact composition/start on every track."""
    matched = matched_tracks(table)
    first = matched[:, 0]
    driver, count = table['driver'][first], table['passenger_count'][first]
    composition, start = table['composition'][first], table['start'][first]
    random = np.random.default_rng(seed)
    selected = []
    for d in np.unique(driver):
        for k in np.unique(count[driver == d]):
            mask = (driver == d) & (count == k)
            options = np.unique(composition[mask])
            for c in np.sort(random.choice(options, min(compositions, len(options)), replace=False)):
                rows = np.flatnonzero(mask & (composition == c))
                # Sample distinct start identifiers, including cognitive and social starts.
                rows = rows[np.argsort(start[rows])]
                selected.extend(random.choice(rows, min(starts, len(rows)), replace=False).tolist())
    return matched[np.sort(selected)]


def source_signature(path):
    return [(p.name, p.stat().st_size, p.stat().st_mtime_ns)
            for p in (path, Path(str(path) + '-wal')) if p.exists()]


def extract(table, sample, runs, output, comparison_key, settings):
    rows = sample.ravel()
    n, steps = len(rows), settings['steps']
    arrays = {name: table[name][rows] for name in ('driver', 'track', 'composition', 'start', 'passenger_count')}
    arrays['changed'] = np.zeros((n, 3, steps), dtype=bool)
    arrays['private_changed'] = np.zeros((n, 2, steps), dtype=bool)
    arrays['opposition'] = np.zeros((n, 2, steps), dtype=np.float32)
    arrays['opposing_weight'] = np.zeros((n, 2, steps), dtype=np.float64)
    for name in METRICS:
        arrays[name] = np.zeros((n, 2, steps), dtype=np.float32)
    rounds = settings['discussion_rounds']
    extraction_source = digest(dict(extract=inspect.getsource(extract),
                                    metrics=Path(network_metrics.__file__).read_text(), numpy=np.__version__))
    folder = output / 'sample_archives'
    folder.mkdir(parents=True, exist_ok=True)
    started = reported = time.monotonic()
    archive_codes = arrays['driver'] * len(table['_tracks']) + arrays['track']
    for done, code in enumerate(np.unique(archive_codes), 1):
        positions = np.flatnonzero(archive_codes == code)
        d, t = int(arrays['driver'][positions[0]]), int(arrays['track'][positions[0]])
        person, track = table['_drivers'][d], table['_tracks'][t]
        path = Path(runs) / f'{person}_{track}.sqlite'
        keys = np.stack([arrays['composition'][positions], arrays['start'][positions]], axis=1)
        signature = digest(dict(version=EXTRACTION_VERSION, source=source_signature(path), keys=keys.tolist(),
                                discussion_rounds=rounds, comparison_key=comparison_key,
                                extraction_source=extraction_source))
        cached = folder / f'{path.stem}.npz'
        part = None
        if cached.exists():
            with np.load(cached, allow_pickle=False) as z:
                if str(z['_signature']) == signature:
                    part = {name: z[name] for name in z.files if not name.startswith('_')}
        if part is None:
            part = {name: value[positions].copy() for name, value in arrays.items() if value.ndim == 3}
            with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
                definition = json.loads(db.execute("SELECT value FROM metadata WHERE key='definition'").fetchone()[0])
                if canonical(definition['parameters']) != canonical(settings):
                    raise ValueError(f'Archive settings differ: {path}')
                solo = {}
                for start, blob, trajectory in db.execute("SELECT start,automation_on,trajectory FROM results WHERE composition=0 AND variant='baseline'"):
                    with np.load(io.BytesIO(trajectory)) as z:
                        solo[start] = (np.unpackbits(np.frombuffer(blob, dtype=np.uint8))[:steps].astype(bool),
                                       z['initial_cognition'][0], z['initial_trust'][0, 0])
                for j, (composition, start) in enumerate(keys):
                    base, base_initial, base_self = solo[int(start)]
                    modes, initials, metadata = [], [], []
                    for m, variant in enumerate(('decision', 'cognition')):
                        row = db.execute('SELECT metadata,trajectory FROM results WHERE composition=? AND start=? AND variant=?',
                                         (int(composition), int(start), variant)).fetchone()
                        if row is None:
                            raise ValueError(f'Missing sampled model: {path}, {composition}, {start}, {variant}')
                        metadata.append(json.loads(row[0]))
                        with np.load(io.BytesIO(row[1]), allow_pickle=False) as z:
                            weights, private, final = z['influence_matrix'], z['private_decisions'], z['final_decisions']
                            if len(weights) != steps or final.shape != private.shape:
                                raise ValueError('Sample trajectory has unexpected length/occupants')
                            initials.append((z['initial_cognition'], z['initial_trust']))
                            if not np.array_equal(z['initial_cognition'][0], base_initial) or z['initial_trust'][0, 0] != base_self:
                                raise ValueError('Solo and social driver initialization differ')
                        if private.shape[1] - 1 != int(arrays['passenger_count'][positions[j]]):
                            raise ValueError('Archived passenger count differs from comparison cache')
                        for name, value in network_measures(weights, rounds).items():
                            part[name][j, m] = value
                        modes.append(final[:, 0].astype(bool))
                        part['private_changed'][j, m] = private[:, 0] != base
                        part['opposition'][j, m] = (private[:, 1:] != private[:, :1]).mean(axis=1)
                        part['opposing_weight'][j, m] = opposing_weight(weights, private, rounds)
                        part['changed'][j, m] = modes[-1] != base
                    if metadata[0]['features'] != metadata[1]['features'] or metadata[0]['passengers'] != metadata[1]['passengers']:
                        raise ValueError('Decision and cognition models are not matched')
                    if any(not np.array_equal(a, b) for a, b in zip(initials[0], initials[1])):
                        raise ValueError('Social models have different initial conditions')
                    part['changed'][j, 2] = modes[0] != modes[1]
                    if part['private_changed'][j, 0].any():
                        raise ValueError('Decision-mode private choices unexpectedly differ from solo')
                    # Check the extracted bits against all three cached comparisons.
                    position = rows[positions[j]]
                    for m, prefix in enumerate(('decision', 'cognition', 'cross')):
                        if part['changed'][j, m].sum() != table[f'{prefix}_mismatch_cycles'][position]:
                            raise ValueError('Sampled trajectory disagrees with the comparison cache')
            temporary = cached.with_suffix('.tmp.npz')
            np.savez_compressed(temporary, _signature=np.array(signature), **part)
            temporary.replace(cached)
        for name, value in part.items():
            arrays[name][positions] = value
        if time.monotonic() - reported >= 5:
            print(f'  Network sample: {done}/{len(np.unique(archive_codes))} archives; {time.monotonic()-started:.0f}s', flush=True)
            reported = time.monotonic()
    arrays['_drivers'], arrays['_tracks'] = np.array(table['_drivers']), np.array(table['_tracks'])
    arrays['_comparison_key'] = np.array(comparison_key)
    arrays['_settings'] = np.array(json.dumps(settings))
    np.savez_compressed(output / 'cycles.npz', **arrays)
    return arrays


def conditional_curve(x, outcome, strata, edges, car_weights, car_ids=None):
    """Bin rates after removing group baselines.

    Each car-cycle retains its design weight. Group demeaning asks whether the
    association remains within driver × track × passenger-count × drive-stage
    groups. A second version adds the amount of current passenger disagreement.
    These are descriptive associations, not controlled interventions.
    """
    code = group_bins(x, edges)
    _, group = np.unique(strata, axis=0, return_inverse=True)
    count = np.bincount(group, weights=car_weights)
    means = np.bincount(group, weights=car_weights * outcome) / count
    baseline = np.average(outcome, weights=car_weights)
    adjusted = outcome - means[group] + baseline
    rows = []
    for b in range(len(edges) - 1):
        mask = code == b
        if not mask.any():
            continue
        rows.append(dict(lo=edges[b], hi=edges[b + 1], cycles=int(mask.sum()),
                         sampled_base_cars=int(len(np.unique(car_ids[mask]))) if car_ids is not None else None,
                         mean_x=float(np.average(x[mask], weights=car_weights[mask])),
                         raw_changed_percent=float(100*np.average(outcome[mask], weights=car_weights[mask])),
                         within_group_difference_pp=float(100*np.average(adjusted[mask]-baseline, weights=car_weights[mask]))))
    return rows


def summarize(data):
    n, _, steps = data['changed'].shape
    driver, track, count = (data[k] for k in ('driver', 'track', 'passenger_count'))
    weights = balanced_weights(driver, count)
    # Every sampled base car is repeated on all nine tracks, so balancing these
    # rows also balances tracks. Missing archive reads fail rather than vanish.
    groups = np.stack([driver, track, count], axis=1)
    changed = data['changed'].mean(axis=2)
    all_agree = ~data['changed'].any(axis=1)
    summary = dict(sampled_car_tracks=n, sampled_base_cars=n//len(data['_tracks']),
                   drivers=len(np.unique(driver)), tracks=data['_tracks'].tolist(), steps=steps,
                   seed=SEED, compositions_per_driver_count=COMPOSITIONS_PER_DRIVER_COUNT,
                   starts_per_composition=STARTS_PER_COMPOSITION,
                   sampling='Fixed random passenger compositions and starts within every driver and passenger count; identical cars on every track.',
                   interpretation='Descriptive associations in a balanced sample. Trust evolves from opinions, so changing centrality and changing behavior can share a cause. No causal claim or independent-cycle significance test.',
                   mean_changed_percent=(100*np.einsum('i,im->m', weights, changed)).tolist(),
                   all_three_agree_percent=float(100*np.average(all_agree.mean(axis=1), weights=weights)),
                   correlations=[], cycle_curves={}, opposition_curves={}, weighted_opposition={}, early_late=[],
                   thresholds=dict(high_self_weight=.5), checks={})
    phase = np.repeat(np.minimum(np.arange(steps)*3//steps, 2)[None, :], n, axis=0)
    strata = np.stack([np.repeat(driver, steps), np.repeat(track, steps), np.repeat(count, steps), phase.ravel()], axis=1)
    cycle_weights = np.repeat(weights / steps, steps)
    base_keys = np.rec.fromarrays([driver, data['composition'], data['start']], names='driver,composition,start')
    unique, inverse = np.unique(base_keys, return_inverse=True)
    cycle_car_ids = np.repeat(inverse, steps)
    windows = min(20, max(1, steps//2))
    summary['window_cycles'] = windows
    for m, mode in enumerate(('decision', 'cognition')):
        own = data['changed'][:, m]
        cross = data['changed'][:, 2]
        opposition = data['opposition'][:, m]
        opposition_code = np.where(opposition == 0, 0, np.where(opposition <= .5, 1, 2))
        strata_opposition = np.column_stack([strata, opposition_code.ravel()])
        for metric, label in METRICS.items():
            x = data[metric][:, m]
            for when, car_value, response in (
                ('initial', x[:, 0], changed[:, m]),
                ('drive_average', x.mean(axis=1), changed[:, m]),
                ('early_predicts_late', x[:, :windows].mean(axis=1), own[:, -windows:].mean(axis=1)),
                ('early_to_late_change', x[:, -windows:].mean(axis=1)-x[:, :windows].mean(axis=1),
                 own[:, -windows:].mean(axis=1)-own[:, :windows].mean(axis=1))):
                summary['correlations'].append(dict(mode=mode, metric=metric, label=label, timing=when,
                    spearman=correlation(car_value, response),
                    within_driver_track_count_spearman=correlation(residualize(car_value, groups), residualize(response, groups))))
            edges = EDGES[metric]
            summary['cycle_curves'][f'{mode}__{metric}'] = dict(label=label, mode=mode,
                versus_solo=conditional_curve(x.ravel(), own.ravel(), strata, edges, cycle_weights, cycle_car_ids),
                versus_solo_with_disagreement=conditional_curve(x.ravel(), own.ravel(), strata_opposition, edges, cycle_weights, cycle_car_ids),
                methods_differ=conditional_curve(x.ravel(), cross.ravel(), strata, edges, cycle_weights, cycle_car_ids))
        x = data['self_weight'][:, m]
        opposition_rows = []
        for group, label in enumerate(('Passengers agree with driver', 'Up to half disagree', 'More than half disagree')):
            for high in (False, True):
                mask = (opposition_code == group) & ((x > .5) == high)
                if mask.any():
                    w = np.broadcast_to(weights[:, None]/steps, mask.shape)[mask]
                    opposition_rows.append(dict(opposition=label, high_own_weight=high, cycles=int(mask.sum()),
                        versus_solo_percent=float(100*np.average(own[mask], weights=w)),
                        versus_private_percent=float(100*np.average((own != data['private_changed'][:, m])[mask], weights=w))))
        summary['opposition_curves'][mode] = opposition_rows
        exposure = data['opposing_weight'][:, m]
        summary['weighted_opposition'][mode] = dict(
            versus_solo=conditional_curve(exposure.ravel(), own.ravel(), strata,
                                          [0,.1,.2,.3,.4,.5,.6,.7,.8,1], cycle_weights, cycle_car_ids),
            versus_current_private=conditional_curve(exposure.ravel(),
                (own != data['private_changed'][:, m]).ravel(), strata,
                [0,.1,.2,.3,.4,.5,.6,.7,.8,1], cycle_weights, cycle_car_ids))
        for t, name in enumerate(data['_tracks']):
            mask = track == t
            for stage, cut in (('early', slice(0, windows)), ('late', slice(-windows, None))):
                w = weights[mask] / weights[mask].sum()
                row = dict(mode=mode, track=str(name), stage=stage,
                           changed_percent=float(100*np.average(own[mask, cut].mean(axis=1), weights=w)),
                           private_changed_percent=float(100*np.average(data['private_changed'][mask, m, cut].mean(axis=1), weights=w)))
                row.update({metric:float(np.average(data[metric][mask, m, cut].mean(axis=1), weights=w)) for metric in METRICS})
                summary['early_late'].append(row)
    # This is an exact implication of binary voting with >0 threshold: with
    # more than half the effective weight on itself the driver cannot be outvoted.
    protected = data['self_weight'][:, 0] > .5 + 1e-6
    summary['checks']['decision_changes_with_more_than_half_own_weight'] = int(data['changed'][:, 0][protected].sum())
    summary['checks']['decision_cycles_with_more_than_half_own_weight'] = int(protected.sum())
    summary['checks']['initial_network_difference_max'] = float(max(np.max(np.abs(data[k][:, 0, 0]-data[k][:, 1, 0])) for k in METRICS))
    if summary['checks']['decision_changes_with_more_than_half_own_weight']:
        raise ValueError('Decision influence violates the own-weight protection check')
    summary['profiles'] = {}
    for mode in ('decision', 'cognition'):
        m = ('decision', 'cognition').index(mode)
        summary['profiles'][mode] = {metric:np.einsum('i,it->t', weights, data[metric][:, m]).tolist() for metric in METRICS}
        summary['profiles'][mode]['changed_percent'] = (100*np.einsum('i,it->t', weights, data['changed'][:, m])).tolist()
    # Sample-size sensitivity uses half the sampled base cars (all their tracks).
    # It is a repeatability check, not a confidence interval.
    keep_keys = np.random.default_rng(SEED+1).choice(len(unique), max(1, len(unique)//2), replace=False)
    keep = np.isin(inverse, keep_keys)
    half_weights = balanced_weights(driver[keep], count[keep])
    summary['sample_sensitivity'] = dict(half_sample_base_cars=len(keep_keys),
        half_mean_changed_percent=(100*np.einsum('i,im->m', half_weights, changed[keep])).tolist())
    summary['sample_sensitivity']['initial_and_dynamic_correlations'] = []
    for m, mode in enumerate(('decision','cognition')):
        for metric in METRICS:
            x = data[metric][:,m]
            for timing, feature, outcome in (
                ('initial', x[:,0], changed[:,m]),
                ('early_to_late_change', x[:,-windows:].mean(axis=1)-x[:,:windows].mean(axis=1),
                 data['changed'][:,m,-windows:].mean(axis=1)-data['changed'][:,m,:windows].mean(axis=1))):
                summary['sample_sensitivity']['initial_and_dynamic_correlations'].append(dict(
                    mode=mode, metric=metric, timing=timing,
                    half_spearman=correlation(feature[keep],outcome[keep]),
                    half_within_group_spearman=correlation(residualize(feature[keep],groups[keep]),residualize(outcome[keep],groups[keep]))))
    return summary


def markdown(result):
    lines = [f"**{result['sampled_base_cars']:,} sampled cars × {len(result['tracks'])} tracks = {result['sampled_car_tracks']:,} car–track comparisons.**", '',
             result['sampling'], '', result['interpretation'], '',
             'The three network measures are evaluated on the weights used **before** each cycle’s social influence. '
             'Passengers listening to the driver is different from the driver listening to passengers. '
             'Relative frozen-network influence equals 1 for an equal-share driver; above 1 means greater influence. '
             'It describes repeated discussion with the current weights held fixed, not the actual long-run drive.', '',
             '### Does a strong starting position predict less change?', '',
             '![Starting network](results/figures/starting_network.png)', '',
             markdown_table(['Mode', 'Starting measure', 'Rank association', 'Within driver / track / passenger count'],
                 [[r['mode'], r['label'], '—' if r['spearman'] is None else f"{r['spearman']:+.3f}",
                   '—' if r['within_driver_track_count_spearman'] is None else f"{r['within_driver_track_count_spearman']:+.3f}"]
                  for r in result['correlations'] if r['timing']=='initial']), '',
             'Negative association means larger starting values accompany fewer changed cycles; positive means more.', '',
             '### Does greater influence during the drive accompany agreement?', '',
             '![Network and behavior](results/figures/network_associations.png)', '',
             'The top row gives raw changed-cycle rates. The bottom row subtracts the usual rate within '
             'driver × track × passenger-count × drive-stage × current-disagreement groups. '
             'Zero means no difference from that group’s usual rate. These differences are associations, not causal effects. '
             'Bins with fewer than 100 sampled cycles or 10 distinct sampled cars are omitted from the figure. Points use observed mean weights within bins.', '',
             '### When do the two social methods agree with each other?', '',
             f"All three methods agree on **{result['all_three_agree_percent']:.1f}%** of sampled car–cycles (balanced weighting).", '',
             '![Agreement between social methods](results/figures/methods_agreement.png)', '',
             'Each line uses the indicated method’s own evolving network. The networks begin identically but can differ later. '
             'The outcome here is disagreement between decision-level and cognition-level choices, rather than disagreement with solo driving.', '',
             '### Does the driver’s own weight matter when passengers disagree?', '',
             '![Own weight and disagreement](results/figures/own_weight_disagreement.png)', '',
             f"Decision mode: **{result['checks']['decision_changes_with_more_than_half_own_weight']:,} changed cycles** among "
             f"{result['checks']['decision_cycles_with_more_than_half_own_weight']:,} cycles where the driver retains more than half the weight. "
             'Binary weighted voting makes the driver impossible to overrule above this point. Cognition mixing has no equivalent protection: '
             'a small cognitive change can cross a decision-tree threshold. In cognition mode, agreement among current private votes '
             'does not imply agreement with solo driving, because prior influence has already changed cognition.', '',
             '### Do network influence and behavior move together over time?', '',
             '![Network over time](results/figures/network_over_time.png)', '',
             '![Early and late changes](results/figures/early_late.png)', '',
             '### Is disagreement coming from influential passengers?', '',
             '![Weighted disagreement](results/figures/weighted_disagreement.png)', '',
             'The horizontal axis counts how much of the driver’s influence weight belongs to passengers whose current private vote opposes the driver. '
             'In decision mode, more than half this weight flips the vote; in cognition mode, mixing states is a different mechanism. '
             'The two panels distinguish changing the driver’s current private choice from changing the solo trajectory.', '',
             'Full outputs include early-network / late-behavior associations, early-to-late changes, cross-method disagreement, '
             'and a half-sample stability check. Use these as additional descriptive questions; social trust learns from opinions, '
             'so a time trend alone cannot identify what causes what.']
    return '\n'.join(lines)


def run(directory=None, output=None, runs=RUNS_DIR):
    output = Path(output) if output else result_directory(NAME)
    output.mkdir(parents=True, exist_ok=True)
    names = ['driver', 'track', 'composition', 'start', 'passenger_count']
    names += [f'{p}_mismatch_cycles' for p in ('decision', 'cognition', 'cross')]
    table = selected_columns(names, directory)
    sample = choose_sample(table)
    key = cache_key(comparison_directory(directory) / 'comparisons.sqlite')
    settings = archive_definition(runs, table['_drivers'][0], table['_tracks'][0])['parameters']
    print(f'Reading network trajectories for {sample.size:,} matched car–track pairs; resumable by archive.', flush=True)
    data = extract(table, sample, runs, output, key, settings)
    print('Summarizing initial positions, changing positions and passenger disagreement...', flush=True)
    result = summarize(data)
    write_results(NAME, result, markdown(result), output=output)
    from experiment.analysis.network_dynamics.plot import render
    render(output)
    print(f'Saved {output}; README updated.', flush=True)
    return result

if __name__ == '__main__':
    run()
