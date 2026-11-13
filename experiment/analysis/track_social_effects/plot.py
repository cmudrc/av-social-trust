"""Complexity figures for the paper; persistence remains a supplementary check."""
from pathlib import Path
import sys
if __package__ in (None, ''):
    root = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(root), str(root / 'src')]
import numpy as np
from experiment.analysis.shared import figures
from experiment.analysis.shared.output import read_results

COLORS = [figures.COLORS['decision'], figures.COLORS['cognition'], '#7755a2']
COMPARISONS = ['Decision-level influence\ncompared with solo driving',
               'Cognition-level influence\ncompared with solo driving',
               'Decision-level compared with\ncognition-level influence']
LEVELS = ['low', 'normal', 'high']
LABELS = ['Low', 'Medium', 'High']


def passenger_line_labels(ax, endpoints, counts, colors):
    """Keep labels legible without moving the plotted observations."""
    order = np.argsort(endpoints, kind='stable')
    positions = np.asarray(endpoints, dtype=float)[order].copy()
    gap = 2.4
    for i in range(1, len(positions)):
        positions[i] = max(positions[i], positions[i-1] + gap)
    positions -= np.mean(positions - np.asarray(endpoints)[order])
    if positions[0] < 1.5:
        positions += 1.5 - positions[0]
    for k, y in zip(order, positions):
        ax.plot([2.02, 2.18], [endpoints[k], y], color=colors[k], linewidth=.7)
        ax.text(2.22, y, f'{counts[k]} passenger'+('s' if counts[k]!=1 else ''),
                color=colors[k], fontsize=7, va='center')


def complexity_average(values, grid):
    """Average named tracks within each complexity; preserve all other axes."""
    return np.stack([np.asarray(values)[..., [i for i,g in enumerate(grid) if g['difficulty']==d], :].mean(axis=-2)
                     for d in LEVELS], axis=-2)


def draw_complexity_effects(result, output):
    means = np.array([g['balanced_changed_percent'] for g in result['complexity_groups']])
    x = np.arange(3)
    fig, axes = figures.figure(width=7.16 * .7, height=3.8)
    ax = axes[0]
    for m, label in enumerate(('Decision-level influence', 'Cognition-level influence')):
        ax.plot(x, means[:,m], color=COLORS[m], marker='o', linewidth=2, label=label)
        for i,v in enumerate(means[:,m]):
            ax.annotate(f'{v:.1f}%', (i,v), xytext=(0,8), textcoords='offset points', ha='center', color=COLORS[m])
    ax.set(xticks=x, xticklabels=LABELS, xlabel='Track complexity',
           ylabel='Driver decisions different\nfrom solo driving (%)', ylim=(0,40), xlim=(-.2,2.2))
    ax.legend(loc='upper right')
    figures.save(fig, output, 'complexity_effects')


def draw_by_passengers(result, data, output):
    """Separate complexity panels keep all counts with only two curves per panel."""
    count_means = complexity_average(data['count_means'], result['grid'])
    counts = data['passenger_counts']
    fig, axes = figures.figure(columns=3, width=7.16, height=3.4, sharey=True)
    from matplotlib.lines import Line2D
    names = ('Decision-level influence', 'Cognition-level influence')
    for i, ax in enumerate(axes):
        for m, linestyle in enumerate(('-', '--')):
            ax.plot(counts, count_means[:, i, m], color=COLORS[m],
                    linestyle=linestyle, linewidth=1.8, marker='o', markersize=3)
        ax.set(xticks=counts, xlabel='Number of passengers',
               title=f'{LABELS[i]} complexity', ylim=(0, 35),
               xlim=(min(counts)-.2, max(counts)+.2))
    axes[0].set_ylabel('Driver decisions different\nfrom solo driving (%)')
    fig.legend(handles=[Line2D([], [], color=COLORS[m], linestyle=style,
                              marker='o', markersize=3, label=names[m])
                        for m, style in enumerate(('-', '--'))],
               loc='lower center', ncol=2, frameon=False)
    fig.tight_layout(rect=(0, .13, 1, 1))
    figures.save(fig, output, 'by_passengers', tight=False)


def render(output=None):
    result, output = read_results('track_social_effects', output)
    with np.load(output / 'plots.npz') as z:
        data = {name: z[name] for name in z.files}
    means = np.array([g['balanced_changed_percent'] for g in result['complexity_groups']])
    x = np.arange(3)
    draw_complexity_effects(result, output)
    fig, axes = figures.figure(width=3.5, height=3.1)
    ax = axes[0]
    ax.plot(x, means[:,2], color=COLORS[2], marker='o', linewidth=2)
    for i,v in enumerate(means[:,2]):
        ax.annotate(f'{v:.1f}%', (i,v), xytext=(0,7), textcoords='offset points', ha='center')
    ax.set(xticks=x, xticklabels=LABELS, xlabel='Track complexity', ylim=(0,45), xlim=(-.2,2.2),
           ylabel='Driver decisions different\nbetween influence methods (%)')
    figures.save(fig, output, 'method_difference')
    fig, axes = figures.figure(columns=2, width=7.16, height=3.4)
    rows = result['complexity_contrasts']
    limit = max(abs(v) for row in rows for end in row['driver_range_pp'] for v in end[:2]) * 1.15
    for m,ax in enumerate(axes):
        for i,row in enumerate(rows):
            lo,hi = [end[m] for end in row['driver_range_pp']]
            ax.plot([lo,hi],[i,i],color=COLORS[m],alpha=.5,linewidth=3)
            ax.plot(row['mean_pp'][m],i,'o',color=COLORS[m])
        ax.axvline(0,color='#666',linewidth=.8)
        ax.set(yticks=range(len(rows)), yticklabels=[r['question'].replace(' complexity','') for r in rows] if m==0 else [],
               xlabel='Difference in changed decisions\n(percentage points)', title=COMPARISONS[m], xlim=(-limit,limit))
        ax.invert_yaxis()
    figures.save(fig, output, 'paired_contrasts')
    persistences = sorted(set(g['persistence'] for g in result['grid']))
    fig,axes = figures.figure(columns=3,width=9,height=3.5)
    vmax = max(max(g['balanced_changed_percent']) for g in result['grid'])
    for m,ax in enumerate(axes):
        matrix = np.full((3,len(persistences)),np.nan)
        for g in result['grid']:
            matrix[LEVELS.index(g['difficulty']),persistences.index(g['persistence'])] = g['balanced_changed_percent'][m]
        ax.grid(False)
        im=ax.imshow(matrix,vmin=0,vmax=vmax,cmap='YlOrRd',aspect='auto')
        ax.set(xticks=range(len(persistences)),xticklabels=persistences,yticks=range(3),yticklabels=LABELS,
               title=COMPARISONS[m],xlabel='Track persistence')
        for (i,j),v in np.ndenumerate(matrix):
            ax.text(j,i,f'{v:.1f}%',ha='center',va='center',fontsize=10,color='white' if v>.6*vmax else '#111')
    axes[0].set_ylabel('Track complexity')
    fig.colorbar(im,ax=list(axes),fraction=.025,pad=.025,label='Cycles with different driver decisions (%)')
    fig.subplots_adjust(left=.07,right=.87,bottom=.2,top=.82,wspace=.4)
    figures.save(fig,output,'track_grid',tight=False)
    draw_by_passengers(result, data, output)
    fig,axes=figures.figure(columns=2,width=7.16,height=3.5)
    for m,ax in enumerate(axes):
        for row in result['threshold_sensitivity']:
            rates=complexity_average(np.array(row['track_shares']),result['grid'])
            ax.plot(x,100*rates[:,m],marker='o',markersize=3,label=f"At least {row['at_least_percent']}% of decisions differ")
        ax.set(xticks=x,xticklabels=LABELS,xlabel='Track complexity',title=COMPARISONS[m],ylim=(0,100),xlim=(-.15,2.15))
    axes[0].set_ylabel('Cars meeting threshold (%)')
    axes[-1].legend(fontsize=6)
    figures.save(fig,output,'threshold_sensitivity')

if __name__ == '__main__':
    render()
