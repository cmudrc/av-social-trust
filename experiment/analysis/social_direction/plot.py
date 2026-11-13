"""Draw net change in automation use against the passengers' lean from results/summary.json; edit freely and rerun.

x: passengers' solo automation use minus the driver's solo use (percentage points).
y: driver's automation use with passengers minus driving alone (percentage points).
On the diagonal the driver ends up using automation as much as the passengers
would alone; on the zero line the passengers change nothing.
"""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(root), str(root/"src")]


from experiment.analysis.shared import figures
from experiment.analysis.shared.output import read_results

NAME = "social_direction"
MODES = ("decision", "cognition")
MIN_SHARE = 0.01  # Hide bins holding less than 1% of the cars at that complexity.
LIMIT = 70


def render(output=None):
    result, directory = read_results(NAME, output)
    fig, axes = figures.figure(3, figures.DOUBLE_COLUMN, 2.9, sharey=True)
    for i, (axis, complexity) in enumerate(zip(axes, result["complexities"])):
        rows = [r for r in complexity["by_lean"] if r["share_of_cars"] >= MIN_SHARE and "mean_lean" in r]
        x = [100*r["mean_lean"] for r in rows]
        axis.plot([-LIMIT, LIMIT], [-LIMIT, LIMIT], color=figures.COLORS["reference"], linewidth=1, linestyle=":",
                  label="Driver matches passengers' solo use")
        axis.axhline(0, color=figures.COLORS["reference"], linewidth=0.9, linestyle="--", label="No change from driving alone")
        for mode in MODES:
            figures.line(axis, x, [r[f"{mode}_net_pp"] for r in rows], mode, label=figures.MODE_NAMES[mode], end_label=False)
        axis.set(xlim=(-LIMIT, LIMIT), ylim=(-50, 40))
        axis.set_xticks([-60, -30, 0, 30, 60])
        axis.set_title(f"{complexity['label']} complexity")
        if i == 1:
            axis.set_xlabel("Passengers' lean: their solo automation use minus the driver's (percentage points)")
        axis.text(LIMIT-2, -48, "passengers use\nautomation more →", ha="right", va="bottom", fontsize=6.5,
                  color=figures.INK["secondary"])
    axes[0].set_ylabel("Driver's change in automation use\n(percentage points vs driving alone)")
    handles, labels = axes[0].get_legend_handles_labels()
    order = [2, 3, 0, 1]
    fig.legend([handles[k] for k in order], [labels[k] for k in order], loc="upper center", ncol=4,
               frameon=False, bbox_to_anchor=(0.5, 1.01))
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    return figures.save(fig, directory, "net_change_by_lean", tight=False)


if __name__ == "__main__":
    render()
