"""Preview a shared figure theme without overwriting the established figures.

Run: PYTHONPATH=src python3 experiment/analysis/theme_preview.py
Outputs: experiment/analysis/results/theme_preview/figures (PDF and PNG).
Only saved analysis outputs are read; no simulations or grouping rules change.
"""
from pathlib import Path
import sys
if __package__ in (None, ''):
    root = Path(__file__).resolve().parents[2]
    sys.path[:0] = [str(root), str(root / 'src')]
import numpy as np
from experiment.analysis.shared import figures
from experiment.analysis.shared.output import read_results
from experiment.analysis.track_social_effects.plot import complexity_average
from experiment.analysis.driver_confidence.plot import starting_categories
from experiment.analysis.influence_timing.plot import step_blocks

COMPLEXITY = {'Low': '#247db7', 'Medium': '#b59a35', 'High': '#c43c43'}
INITIAL = {'Low': '#248d91', 'Medium': '#7954a6', 'High': '#b16b35'}
PREVIEW_WIDTH = 7.16 * .67
MODES = ('decision', 'cognition')
NAMES = {'decision': 'Decision-level influence', 'cognition': 'Cognition-level influence'}
STYLES = {'decision': '-', 'cognition': '--'}
INK = '#222222'
OUTPUT = Path(__file__).resolve().parent / 'results' / 'theme_preview'


def legends(ax, palette=None, title=None):
    """Place category and mechanism keys below a compact plotting area."""
    from matplotlib.lines import Line2D
    fig = ax.figure
    if palette:
        handles = [Line2D([], [], color=color, linewidth=2, label=label)
                   for label, color in palette.items()]
        if title:
            # A text-only first entry keeps the category heading on the same row.
            from matplotlib.patches import Patch
            from matplotlib.legend_handler import HandlerBase

            class TextOnlyHandler(HandlerBase):
                def create_artists(self, legend, handle, xdescent, ydescent,
                                   width, height, fontsize, trans):
                    return [Line2D([], [], linestyle='none', transform=trans)]

            heading = Patch(visible=False, label=f'{title}:')
            handles.insert(0, heading)
            fig.legend(handles=handles, loc='lower center',
                       bbox_to_anchor=(.5,.055), ncol=4, frameon=False,
                       columnspacing=1.1, handlelength=1.5,
                       handler_map={heading: TextOnlyHandler()})
        else:
            fig.legend(handles=handles, loc='lower center',
                       bbox_to_anchor=(.5,.055), ncol=3, frameon=False)
    fig.legend(handles=[Line2D([], [], color=INK, linestyle=STYLES[mode],
                              linewidth=2, label=NAMES[mode]) for mode in MODES],
               loc='lower center', bbox_to_anchor=(.5,.005), ncol=2, frameon=False)
    fig.tight_layout(rect=(0,.10,1,1))


def draw_initial(data, value_field, group_field, name, ylabel, title):
    profiles = starting_categories(data, value_field=value_field, group_field=group_field)
    fig, (ax,) = figures.figure(width=PREVIEW_WIDTH, height=3.8)
    for mode in MODES:
        for row in profiles[mode]:
            ax.plot(np.arange(len(row['profile'])), row['profile'],
                    color=INITIAL[row['label']], linestyle=STYLES[mode], linewidth=1.9)
    ax.set(xlabel='Steps', ylabel=ylabel, xlim=(0,100), ylim=(0,1), yticks=np.arange(0,1.01,.2))
    legends(ax, INITIAL, title)
    figures.save(fig, OUTPUT, name, tight=False)


def render(include_examples=True):
    result, directory = read_results('track_social_effects')
    means = np.array([g['balanced_changed_percent'] for g in result['complexity_groups']])
    fig, (ax,) = figures.figure(width=7.16*.7, height=3.8)
    for m, mode in enumerate(MODES):
        ax.plot(np.arange(3), means[:,m], color=figures.COLORS[mode], linestyle=STYLES[mode],
                marker='o', linewidth=2, label=NAMES[mode])
        for i, value in enumerate(means[:,m]):
            ax.annotate(f'{value:.1f}%', (i,value), xytext=(0,8),
                        textcoords='offset points', ha='center', color=figures.COLORS[mode])
    ax.set(xticks=np.arange(3), xticklabels=list(COMPLEXITY), xlabel='Track complexity',
           ylabel='Driver decisions different\nfrom solo driving (%)', ylim=(0,40), xlim=(-.2,2.2))
    ax.legend(loc='upper right')
    figures.save(fig, OUTPUT, 'complexity_effects')
    with np.load(directory/'plots.npz', allow_pickle=False) as z:
        count_means = complexity_average(z['count_means'], result['grid'])
        counts = z['passenger_counts']
    fig, (ax,) = figures.figure(width=PREVIEW_WIDTH, height=3.8)
    for i, (label, color) in enumerate(COMPLEXITY.items()):
        for m, mode in enumerate(MODES):
            ax.plot(counts, count_means[:,i,m], color=color, linestyle=STYLES[mode],
                    marker='o', markersize=3, linewidth=1.8)
    ax.set(xlabel='Number of passengers', xticks=counts, xlim=(counts.min()-.15,counts.max()+.15),
           ylabel='Driver decisions different\nfrom solo driving (%)', ylim=(0,40))
    legends(ax, {f'{k} complexity':v for k,v in COMPLEXITY.items()})
    figures.save(fig, OUTPUT, 'by_passengers', tight=False)

    _, directory = read_results('driver_confidence')
    with np.load(directory/'cycles.npz', allow_pickle=False) as z:
        data = {k:z[k] for k in ('driver','passenger_count','confidence_before','confidence_after',
                                 'incoming_before','incoming_after')}
    draw_initial(data, 'confidence', 'confidence', 'starting_confidence',
                 'Driver confidence (self-trust)', 'Initial driver confidence')
    draw_initial(data, 'incoming', 'incoming', 'inbound_trust_by_starting_trust',
                 'Mean passenger trust in driver', 'Initial trust in driver')

    _, directory = read_results('influence_timing')
    fig, (ax,) = figures.figure(width=PREVIEW_WIDTH, height=3.8)
    with np.load(directory/'cycles.npz', allow_pickle=False) as z:
        for mode in MODES:
            x, values, _ = step_blocks(z[f'{mode}_change'])
            for i, level in enumerate(z['difficulties'].astype(str)):
                label = {'low':'Low','normal':'Medium','high':'High'}[level]
                ax.plot(x, 100*values[i], color=COMPLEXITY[label], linestyle=STYLES[mode],
                        marker='o', markersize=3, linewidth=1.8)
    ax.set(xlabel='Steps', ylabel='Driver decisions different\nfrom solo driving (%)',
           xlim=(0,100), ylim=(0,40))
    legends(ax, {f'{k} complexity':v for k,v in COMPLEXITY.items()})
    figures.save(fig, OUTPUT, 'step_blocks_by_complexity', tight=False)

    if not include_examples:
        print(f'Five preview figure pairs updated in {OUTPUT / "figures"}')
        return
    # Preserve the preferred original example, including blue/orange lines.
    from shutil import copyfile
    _, directory = read_results('example_cases')
    for extension in ('pdf', 'png'):
        copyfile(directory / 'figures' / f'example_cases_simple.{extension}',
                 OUTPUT / 'figures' / f'example_cases_simple.{extension}')
    print(f'Six preview figure pairs written to {OUTPUT / "figures"}')


if __name__ == '__main__':
    render()
