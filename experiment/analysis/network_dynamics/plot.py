"""Paper-oriented network figures, redrawn from summary.json only."""
from pathlib import Path
import sys
if __package__ in (None, ''):
    root = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(root), str(root / 'src')]
import numpy as np
from experiment.analysis.shared import figures
from experiment.analysis.shared.output import read_results
from experiment.analysis.network_dynamics.run import METRICS

SHORT = dict(self_weight='Driver keeps own view', passenger_attention='Weight passengers give\nto the driver',
             relative_influence='Driver’s relative influence\n(current network held fixed)')
COLORS = figures.COLORS
MIN_CYCLES = 100
MIN_CARS = 10


def supported(rows):
    return [p for p in rows if p['cycles'] >= MIN_CYCLES and (p.get('sampled_base_cars') or 0) >= MIN_CARS]


def render(output=None):
    result, output = read_results('network_dynamics', output)
    metrics = list(METRICS)
    fig, axes = figures.figure(columns=2, width=8, height=3.2)
    for m, mode in enumerate(('decision', 'cognition')):
        ax = axes[m]
        for j, metric in enumerate(metrics):
            row = next(r for r in result['correlations'] if r['mode']==mode and r['metric']==metric and r['timing']=='initial')
            for offset, name, alpha in ((-.14, 'spearman', .45), (.14, 'within_driver_track_count_spearman', 1)):
                if row[name] is not None:
                    ax.barh(j+offset, row[name], height=.25, color=COLORS[mode], alpha=alpha,
                            label=('Across sampled cars' if alpha<1 else 'Within comparable groups') if j==0 else None)
        ax.axvline(0, color='#666', lw=.8)
        ax.set(yticks=range(3), yticklabels=[SHORT[k] for k in metrics] if m==0 else [],
               title=f'{mode.capitalize()}-level vs solo', xlabel='Rank association with changed-cycle fraction', xlim=(-.3, .3))
        ax.invert_yaxis()
        ax.legend(fontsize=6, loc='lower left')
    figures.save(fig, output, 'starting_network')
    fig, axes = figures.figure(columns=3, rows=2, width=9, height=5.5)
    for j, metric in enumerate(metrics):
        for mode in ('decision', 'cognition'):
            row = result['cycle_curves'][f'{mode}__{metric}']
            for r, name, field in ((0, 'versus_solo', 'raw_changed_percent'),
                                   (1, 'versus_solo_with_disagreement', 'within_group_difference_pp')):
                points = supported(row[name])
                if not points:
                    continue
                x = [p['mean_x'] for p in points]
                y = [p[field] for p in points]
                axes[r,j].plot(x, y, color=COLORS[mode], marker='o', ms=4, label=f'{mode.capitalize()}-level')
                axes[r,j].set_xlabel(SHORT[metric])
        axes[0,j].set(title=SHORT[metric], ylim=(0, 100))
        axes[1,j].axhline(0, color='#666', lw=.8)
        if metric == 'relative_influence':
            for ax in axes[:,j]:
                ax.axvline(1, color='#666', lw=.7, ls='--')
    axes[0,0].set_ylabel('Cycles different from solo (%)')
    axes[1,0].set_ylabel('Difference from comparable\ngroup’s usual rate (pp)')
    axes[0,-1].legend(fontsize=6)
    figures.save(fig, output, 'network_associations')
    # Cross-method disagreement is evaluated against EACH method's network.
    fig, axes = figures.figure(columns=3, width=9, height=3.2)
    for j, metric in enumerate(metrics):
        for mode in ('decision', 'cognition'):
            rows = result['cycle_curves'][f'{mode}__{metric}']['methods_differ']
            points = supported(rows)
            axes[j].plot([p['mean_x'] for p in points], [p['raw_changed_percent'] for p in points],
                         marker='o', ms=3, color=COLORS[mode], label=f'{mode.capitalize()} network')
        axes[j].set(xlabel=SHORT[metric], ylim=(0, 100), title='Decision vs cognition')
    axes[0].set_ylabel('Cycles where methods differ (%)')
    axes[-1].legend(fontsize=6)
    figures.save(fig, output, 'methods_agreement')
    fig, axes = figures.figure(columns=2, width=8, height=3.8)
    labels = ['None', 'Up to half', 'More than half']
    for m, mode in enumerate(('decision', 'cognition')):
        for high in (False, True):
            rows = [r for r in result['opposition_curves'][mode] if r['high_own_weight']==high]
            x = [(['Passengers agree with driver','Up to half disagree','More than half disagree'].index(r['opposition'])) for r in rows]
            axes[m].bar(np.array(x)+(.18 if high else -.18), [r['versus_solo_percent'] for r in rows], width=.32,
                        color=COLORS[mode], alpha=1 if high else .4,
                        label='Driver keeps > half' if high else 'Driver keeps ≤ half')
        axes[m].set(xticks=range(3), xticklabels=labels, ylim=(0, 100), xlabel='Passengers disagreeing with current driver view',
                    title=f'{mode.capitalize()}-level vs solo')
        axes[m].legend(fontsize=6)
    axes[0].set_ylabel('Cycles different from solo (%)')
    figures.save(fig, output, 'own_weight_disagreement')
    fig, axes = figures.figure(columns=4, width=10, height=3)
    for j, metric in enumerate([*metrics, 'changed_percent']):
        for mode in ('decision', 'cognition'):
            y = result['profiles'][mode][metric]
            axes[j].plot(np.arange(1, len(y)+1), y, color=COLORS[mode], label=f'{mode.capitalize()}-level')
        axes[j].set(xlabel='Steps', title=SHORT.get(metric, 'Cycles different from solo (%)'))
    axes[-1].legend(fontsize=6)
    figures.save(fig, output, 'network_over_time')
    fig, axes = figures.figure(columns=2, width=8, height=3.8)
    for m, mode in enumerate(('decision', 'cognition')):
        for track in result['tracks']:
            early = next(r for r in result['early_late'] if r['mode']==mode and r['track']==track and r['stage']=='early')
            late = next(r for r in result['early_late'] if r['mode']==mode and r['track']==track and r['stage']=='late')
            color = dict(low='#5c9b72', normal='#9b8b4e', high='#ba6574')[track.split('_')[0]]
            axes[m].annotate('', xy=(late['self_weight'],late['changed_percent']),
                             xytext=(early['self_weight'],early['changed_percent']),
                             arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
            axes[m].plot(early['self_weight'],early['changed_percent'],'o',color=color, ms=4)
            # Include endpoints in autoscaling: annotations alone do not extend
            # axis limits and would hide arrows ending outside the early range.
            axes[m].plot(late['self_weight'],late['changed_percent'],'s',color=color, ms=3)
            axes[m].annotate(track, (late['self_weight'],late['changed_percent']), xytext=(3,3),
                             textcoords='offset points', fontsize=6, color=color)
        axes[m].set(xlabel='Driver keeps own view (weight)', ylabel='Cycles different from solo (%)' if m==0 else '',
                    title=f"{mode.capitalize()}-level: first → last {result['window_cycles']} cycles")
    figures.save(fig, output, 'early_late')
    fig, axes = figures.figure(columns=2, width=7.16, height=3.2)
    for j, key in enumerate(('versus_current_private', 'versus_solo')):
        for mode in ('decision','cognition'):
            rows = supported(result['weighted_opposition'][mode][key])
            axes[j].plot([r['mean_x'] for r in rows], [r['raw_changed_percent'] for r in rows],
                         marker='o', ms=4, color=COLORS[mode], label=f'{mode.capitalize()}-level')
        axes[j].axvline(.5, color='#666', ls='--', lw=.8)
        axes[j].set(xlabel='Driver weight on opposing passengers', ylim=(0,100),
                    title='Different from current private choice' if j==0 else 'Different from solo driving')
    axes[0].set_ylabel('Cycles with different decisions (%)')
    axes[-1].legend(fontsize=6)
    figures.save(fig, output, 'weighted_disagreement')

if __name__ == '__main__':
    render()
