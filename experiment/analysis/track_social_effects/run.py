"""How much do the nine shared tracks change the effect of social influence?"""
from pathlib import Path
import json
import sys
if __package__ in (None, ''):
    root = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(root), str(root / 'src')]
import numpy as np
from experiment.config import RUNS_DIR, TRACKS_DIR
from experiment.analysis.shared.output import result_directory, write_results
from experiment.analysis.shared.paired import (PAIRS, PAIR_LABELS, selected_columns, matched_tracks,
                                               balanced_weights, archive_definition)
from experiment.analysis.shared.stats import markdown_table
from experiment.tracks.generate_tracks import file_hash

NAME = 'track_social_effects'


def summarize(table, manifest, steps):
    matched = matched_tracks(table)
    driver = table['driver'][matched[:, 0]]
    counts = table['passenger_count'][matched[:, 0]]
    weights = balanced_weights(driver, counts)
    records = {t['name']: t for t in manifest['tracks']}
    tracks = [records[name] for name in table['_tracks']]
    effect = np.stack([100 * table[f'{p}_mismatch_cycles'][matched].astype(float) / steps for p in PAIRS], axis=2)
    # Both the signed automation change and changes in either direction matter.
    signed = np.stack([100 * table[f'{p}_delta_automation_fraction'][matched] for p in PAIRS], axis=2)
    means = np.einsum('i,itm->tm', weights, effect)
    driver_means = np.stack([effect[driver == d].mean(axis=0) for d in np.unique(driver)])
    count_means = np.stack([effect[counts == k].mean(axis=0) for k in np.unique(counts)])
    grid = [dict(track=t['name'], difficulty=t['difficulty'], persistence=t['persistence'],
                 realized_complexity=t['mean_complexity'], complexity_switches=t['complexity_switches'],
                 balanced_changed_percent=means[i].tolist(), raw_changed_percent=effect[:, i].mean(axis=0).tolist(),
                 balanced_net_automation_pp=np.einsum('i,im->m', weights, signed[:, i]).tolist())
            for i, t in enumerate(tracks)]
    difficulties = [d for d in ('low', 'normal', 'high') if any(t['difficulty'] == d for t in tracks)]
    persistences = sorted(set(t['persistence'] for t in tracks))
    cells = {}
    for d in difficulties:
        for p in persistences:
            ix = [i for i, t in enumerate(tracks) if t['difficulty'] == d and t['persistence'] == p]
            if not ix:
                raise ValueError(f'Missing track cell {d}, {p}')
            cells[d, p] = effect[:, ix].mean(axis=1)
    def contrast(label, delta):
        per_driver = []
        for d in np.unique(driver):
            mask = driver == d
            per_driver.append(np.einsum('i,im->m', weights[mask] / weights[mask].sum(), delta[mask]))
        return dict(question=label, mean_pp=np.einsum('i,im->m', weights, delta).tolist(),
                              median_pp=np.median(delta, axis=0).tolist(),
                              car_quartiles_pp=np.quantile(delta, [.25, .75], axis=0).tolist(),
                              share_cars_increasing=np.einsum('i,im->m', weights, delta > 0).tolist(),
                              driver_means_pp=np.array(per_driver).tolist(),
                              driver_range_pp=[np.min(per_driver, axis=0).tolist(), np.max(per_driver, axis=0).tolist()])
    complexity_effect = {d: np.mean([cells[d, p] for p in persistences], axis=0) for d in difficulties}
    complexity_groups = [dict(complexity=d, label={'low':'Low','normal':'Medium','high':'High'}[d],
                             balanced_changed_percent=np.einsum('i,im->m', weights, complexity_effect[d]).tolist())
                         for d in difficulties]
    complexity_contrasts = [contrast(f"{complexity_groups[j]['label']} minus {complexity_groups[i]['label']} complexity",
                                     complexity_effect[difficulties[j]]-complexity_effect[difficulties[i]])
                           for i,j in ((0,1),(0,2),(1,2)) if j<len(difficulties)]
    contrasts = []
    for p in persistences:
        contrasts.append(contrast(f'High minus low complexity, persistence {p:g}', cells[difficulties[-1], p] - cells[difficulties[0], p]))
    for d in difficulties:
        contrasts.append(contrast(f"Higher minus lower persistence, {dict(low='low',normal='medium',high='high')[d]} complexity", cells[d, persistences[-1]] - cells[d, persistences[0]]))
    contrasts.append(contrast('Does persistence change the high–low difference?',
             (cells[difficulties[-1], persistences[-1]] - cells[difficulties[0], persistences[-1]])
             - (cells[difficulties[-1], persistences[0]] - cells[difficulties[0], persistences[0]])))
    # Repeated-car variance: remove each car's average, then see how much of
    # the remaining variation is shared by all cars on the same named track.
    residual = effect - effect.mean(axis=1, keepdims=True)
    track_pattern = np.einsum('i,itm->tm', weights, residual)
    total = np.einsum('i,itm->m', weights, residual ** 2) / len(tracks)
    explained = np.mean(track_pattern ** 2, axis=0)
    shares = np.divide(explained, total, out=np.zeros_like(total), where=total > 0)
    sensitivity = []
    for threshold in (1, 5, 10, 25):
        rates = np.einsum('i,itm->tm', weights, effect >= threshold)
        sensitivity.append(dict(at_least_percent=threshold, track_shares=rates.tolist()))
    result = dict(comparison_rows=len(table['driver']), complete_cars=len(matched),
                  excluded_comparison_rows=len(table['driver']) - matched.size,
                  tracks=len(tracks), drivers=len(np.unique(driver)), steps=steps,
                  weighting='Equal drivers, equal passenger counts within driver, equal cars within each cell.',
                  interpretation='Exact paired comparisons on the realized tracks. Driver ranges show heterogeneity, not confidence intervals. One realization per track cell cannot establish a general difficulty or persistence effect.',
                  pair_labels=list(PAIR_LABELS), grid=grid, contrasts=contrasts,
                  complexity_groups=complexity_groups, complexity_contrasts=complexity_contrasts,
                  complexity_aggregation='Average each matched car across persistence levels, then balance drivers and passenger counts.',
                  shared_track_share_of_within_car_variation=shares.tolist(), threshold_sensitivity=sensitivity)
    arrays = dict(track_names=np.array(table['_tracks']), driver_means=driver_means,
                  passenger_counts=np.unique(counts), count_means=count_means,
                  # Histograms retain the distribution without exporting millions of rows.
                  distribution_edges=np.arange(0, 102, 2),
                  distribution=np.stack([[np.histogram(effect[:, t, m], bins=np.arange(0, 102, 2), weights=weights)[0]
                                          for m in range(3)] for t in range(len(tracks))]))
    return result, arrays


def markdown(result):
    labels = ['Decision-level influence compared with solo driving',
              'Cognition-level influence compared with solo driving']
    lines = [f"**{result['complete_cars']:,} matched cars across {result['tracks']} tracks**, {result['drivers']} drivers.", '',
             'Each percentage is the average fraction of cycles with different driver automation decisions: '
             '100 × (number of differing cycles / number of cycles). For example, 18.3% means about '
             '18 of 100 decisions differ from the matched solo run, on average. It is neither a percentage '
             'of cars nor a percentage increase in automation use.', '',
             result['weighting'], '', result['complexity_aggregation'], '', result['interpretation'], '',
             '### Main result: complexity and differences from solo driving', '',
             '![Complexity effects](results/figures/complexity_effects.png)', '',
             markdown_table(['Track complexity', *labels],
                            [[g['label'], *[f'{v:.1f}%' for v in g['balanced_changed_percent'][:2]]]
                             for g in result['complexity_groups']]), '',
             'Persistence is averaged over for this presentation; this is not evidence that persistence has no effect.', '',
             '### Compare complexity while keeping the car fixed', '',
             'Positive differences mean more changed decisions at the higher complexity. Dots show balanced averages; '
             'bars span the driver averages, not confidence intervals. Persistence is averaged over within each car.', '',
             '![Paired complexity differences](results/figures/paired_contrasts.png)', '',
             markdown_table(['Comparison', *labels], [[g['question'], *[f'{v:+.2f} percentage points' for v in g['mean_pp'][:2]]]
                                                    for g in result['complexity_contrasts']]), '',
             '### Optional separate question: does the location of influence matter?', '',
             '![Difference between influence methods](results/figures/method_difference.png)', '',
             'This compares decision-level with cognition-level influence. It describes sensitivity to where '
             'social influence is modeled; it is not required to establish that either social model differs from solo driving. '
             'Neither method is validated as more accurate by this comparison.', '',
             '### Supplementary checks', '',
             '![Passenger counts](results/figures/by_passengers.png)', '',
             '![Threshold sensitivity](results/figures/threshold_sensitivity.png)', '',
             '![Persistence checks](results/figures/track_grid.png)', '',
             'The persistence grid remains available as a supplementary check. All figures use complexity categories, '
             'with no internal track identifiers. Thresholds are exploratory checks, not definitions of importance. '
             'summary.json also retains persistence contrasts, raw weighting, signed changes, paired quartiles, '
             'driver ranges and the shared track share of within-car variation.']
    return '\n'.join(lines)


def run(directory=None, output=None, runs=RUNS_DIR, tracks_directory=TRACKS_DIR):
    names = ['driver', 'track', 'composition', 'start', 'passenger_count']
    names += [f'{p}_{m}' for p in PAIRS for m in ('mismatch_cycles', 'delta_automation_fraction')]
    table = selected_columns(names, directory)
    manifest = json.loads((Path(tracks_directory) / 'manifest.json').read_text())
    definition = archive_definition(runs, table['_drivers'][0], table['_tracks'][0])
    if manifest['parameters'] != {k: definition['parameters'][k] for k in manifest['parameters']}:
        raise ValueError('Track manifest does not match archived experiment settings')
    for track in manifest['tracks']:
        archived_hash = definition['inputs']['tracks'].get(track['name'])
        if archived_hash != track['sha256'] or file_hash(Path(tracks_directory) / f"{track['name']}.csv") != archived_hash:
            raise ValueError(f"Track sequence differs from archived inputs: {track['name']}")
    result, arrays = summarize(table, manifest, definition['parameters']['steps'])
    output = Path(output) if output else result_directory(NAME)
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output / 'plots.npz', **arrays)
    write_results(NAME, result, markdown(result), output=output)
    from experiment.analysis.track_social_effects.plot import render
    render(output)
    print(f'Saved {output}: {result["complete_cars"]:,} complete cars.', flush=True)
    return result

if __name__ == '__main__':
    run()
