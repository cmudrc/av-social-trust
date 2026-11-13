"""Draw trust-learning interventions from their saved summaries."""
from pathlib import Path
import sys
if __package__ in (None, ''):
    root = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(root), str(root / 'src')]
import numpy as np
from experiment.analysis.shared import figures
from experiment.analysis.shared.output import read_results


def render(output=None):
    result, output = read_results('trust_learning', output)
    curves = {k: np.asarray(v) for k, v in result['curves'].items()}
    x = np.arange(1, result['cycles'] + 1)
    for name, field, conditions, labels, multiplier in (
        ('weak_ties', 'changed', (0, 2, 3), ('Original trust + learning', 'Weak ties + learning', 'Weak ties, fixed trust'), 100),
        ('weight_recovery', 'self_weight', (0, 2, 3), ('Original trust + learning', 'Weak ties + learning', 'Weak ties, fixed trust'), 100),
        ('uniform_scaling', 'changed', (0, 4, 1, 5), ('Original trust + learning', 'All trust reduced + learning', 'Original trust, fixed', 'All trust reduced, fixed'), 100),
    ):
        fig, axes = figures.figure(columns=2, width=7.16, height=3.6, sharey=True)
        for m, ax in enumerate(axes):
            for k, (condition, label) in enumerate(zip(conditions, labels)):
                ax.plot(x, multiplier * curves[field][condition, m], label=label,
                        color=('#7755a2' if k == 0 else '#111' if k == 1 else '#999' if k == 2 else '#2a78d6'),
                        linewidth=(2 if k < 2 else 1.5), linestyle=('-' if k < 2 else '--' if k == 2 else ':'),
                        alpha=(1 if k < 2 else .9))
            ax.set(xlabel='Steps', title=('Decision-level influence', 'Cognition-level influence')[m],
                   xlim=(1, 100), ylim=(0, 105) if field == 'self_weight' else (0, 40))
        axes[0].set_ylabel('Weight given to driver’s\nown judgment (%)' if field == 'self_weight' else 'Driver decisions different\nfrom solo driving (%)')
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='lower center', ncol=2, frameon=False, fontsize=7)
        fig.tight_layout(rect=(0, .14, 1, 1))
        figures.save(fig, output, name, tight=False)


if __name__ == '__main__':
    render()
