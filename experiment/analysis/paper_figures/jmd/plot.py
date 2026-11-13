"""Paper versions of the vehicle (AV) figures for the JMD manuscript.

Each figure is drawn at the size it is printed in the paper, so the font sizes
in FONT are the printed sizes (LaTeX does not rescale them). Figures shown
together share margins, so their plotting areas line up.

Only saved analysis results are read (summary.json and .npz files); no
simulations are rerun. Run the source analyses first if their results are missing.

  name                             source analysis       place in the paper
  complexity_effects               track_social_effects  Results, panel (a), 0.43\\textwidth
  by_passengers                    track_social_effects  Results, panel (b), 0.53\\textwidth
  net_change_by_lean               social_direction      Results, 1.0\\textwidth
  step_blocks_by_complexity        influence_timing      Appendix, 1.0\\columnwidth
  inbound_trust_by_starting_trust  driver_confidence     Appendix, panel (a), 0.48\\textwidth
  starting_confidence              driver_confidence     Appendix, panel (b), 0.48\\textwidth
  example_cases_simple             example_cases         Appendix, 0.8\\textwidth

Outputs: paper_figures/jmd/figures/{name}.pdf and .png. With COPY_TO_PAPER, the
PDFs are also copied into the manuscript's figures folder.

Run: python3 experiment/analysis/paper_figures/jmd/plot.py
"""

from pathlib import Path
import shutil
import sys

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[4]
    sys.path[:0] = [str(root), str(root / "src")]

import numpy as np

from experiment.analysis.shared import figures
from experiment.analysis.shared.output import read_results
from experiment.analysis.track_social_effects.plot import complexity_average
from experiment.analysis.influence_timing.plot import step_blocks, LEVEL_COLORS
from experiment.analysis.driver_confidence.plot import starting_categories

# =========================
# Settings
# =========================
OUTPUT = Path(__file__).resolve().parent
PAPER_FIGURES = Path(__file__).resolve().parents[3] / "assets" / "ASME_JMD_Trust_and_Adoption" / "figures"
COPY_TO_PAPER = True

TEXT_WIDTH = 7.0      # inches, asmejour \textwidth
COLUMN_WIDTH = 3.375  # inches, asmejour \columnwidth

# Printed font sizes (pt)
FONT = dict(tick=7.5, label=8, legend=7.5, panel=8.5, title=9.5, value=7, note=7)

# Margins (inches) around the plotting area, shared by figures shown together
LEFT, RIGHT = 0.62, 0.14
TOP = 0.46        # figure title + panel titles
BOTTOM = 0.70     # tick labels + axis label + legend row
PANEL_GAP = 0.10  # between panels that share a y-axis
TIME_PANEL_GAP = 0.20  # wider, so the 100 and 0 step labels of neighboring panels do not touch

YMAX_CHANGED = 35  # y-limit for "driver decisions different from solo driving (%)"

MODES = ("decision", "cognition")
MODE_LABELS = dict(decision="Decision-level", cognition="Cognition-level")
MODE_STYLES = dict(decision="-", cognition="--")
LEVELS = ("Low", "Medium", "High")
START_COLORS = ("#1f77b4", "#ff7f0e", "#2ca02c")  # Low, Medium, High starting value
CHANGED_LABEL = "Driver decisions different\nfrom solo driving (%)"


# =========================
# Shared layout helpers
# =========================
def new_figure(width, height, columns=1, gap=PANEL_GAP, left=LEFT, right=RIGHT, top=TOP, bottom=BOTTOM):
    """Figure with margins fixed in inches, so panels line up across figures."""
    fig, axes = figures.figure(columns, width, height, sharey=columns > 1)
    panel = (width - left - right - gap * (columns - 1)) / columns
    fig.subplots_adjust(left=left / width, right=1 - right / width, top=1 - top / height,
                        bottom=bottom / height, wspace=gap / panel)
    for axis in axes:
        axis.tick_params(labelsize=FONT["tick"])
    fig._paper_margins = (left, right)
    return fig, list(axes)


def _center(fig):
    """Horizontal center of the plotting area, as a figure fraction."""
    left, right = fig._paper_margins
    width = fig.get_size_inches()[0]
    return (left + width - right) / 2 / width


def title(fig, text):
    height = fig.get_size_inches()[1]
    fig.suptitle(text, x=_center(fig), y=1 - 0.03 / height, va="top", fontsize=FONT["title"])


def bottom_legend(fig, handles, ncol, heading=None):
    """One legend row under the plotting area; an optional text-only heading leads the row."""
    from matplotlib.legend_handler import HandlerBase
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    handler_map = {}
    if heading:
        class TextOnly(HandlerBase):
            def create_artists(self, legend, handle, xdescent, ydescent, width, height, fontsize, trans):
                return [Line2D([], [], linestyle="none", transform=trans)]

        lead = Patch(visible=False, label=heading)
        handles = [lead, *handles]
        handler_map[lead] = TextOnly()
        ncol += 1
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(_center(fig), 0.0), ncol=ncol,
               frameon=False, fontsize=FONT["legend"], handlelength=1.5, handletextpad=0.4,
               columnspacing=0.9, borderaxespad=0.15, handler_map=handler_map)


def mode_handles(marker=True):
    from matplotlib.lines import Line2D
    return [Line2D([], [], color=figures.COLORS[mode], linestyle=MODE_STYLES[mode], linewidth=1.8,
                   marker="o" if marker else None, markersize=4, label=MODE_LABELS[mode])
            for mode in MODES]


def color_handles(colors):
    from matplotlib.lines import Line2D
    return [Line2D([], [], color=color, linewidth=1.8, label=label) for label, color in zip(LEVELS, colors)]


def save(fig, name):
    figures.save(fig, OUTPUT, name, tight=False)
    return OUTPUT / "figures" / f"{name}.pdf"


# =========================
# Results: size of the effect, panels (a) and (b)
# =========================
PAIR_HEIGHT = 2.5


def complexity_effects():
    result, _ = read_results("track_social_effects")
    means = np.array([g["balanced_changed_percent"] for g in result["complexity_groups"]])
    fig, (axis,) = new_figure(0.43 * TEXT_WIDTH, PAIR_HEIGHT)
    x = np.arange(3)
    for m, mode in enumerate(MODES):
        color = figures.COLORS[mode]
        axis.plot(x, means[:, m], color=color, linestyle=MODE_STYLES[mode], linewidth=1.8,
                  marker="o", markersize=4)
        for i, value in enumerate(means[:, m]):
            axis.annotate(f"{value:.1f}%", (i, value), xytext=(0, 6), textcoords="offset points",
                          ha="center", fontsize=FONT["value"], color=color)
    axis.set(xticks=x, xticklabels=LEVELS, xlim=(-0.3, 2.3), ylim=(0, YMAX_CHANGED))
    axis.set_xlabel("Track complexity", fontsize=FONT["label"])
    axis.set_ylabel(CHANGED_LABEL, fontsize=FONT["label"])
    title(fig, "By track complexity")
    bottom_legend(fig, mode_handles(), ncol=2)
    return save(fig, "complexity_effects")


def by_passengers():
    result, directory = read_results("track_social_effects")
    with np.load(directory / "plots.npz", allow_pickle=False) as z:
        count_means = complexity_average(z["count_means"], result["grid"])
        counts = z["passenger_counts"]
    fig, axes = new_figure(0.53 * TEXT_WIDTH, PAIR_HEIGHT, columns=3)
    for i, axis in enumerate(axes):
        for m, mode in enumerate(MODES):
            axis.plot(counts, count_means[:, i, m], color=figures.COLORS[mode], linestyle=MODE_STYLES[mode],
                      linewidth=1.8, marker="o", markersize=4)
        axis.set(xticks=counts, xlim=(counts.min() - 0.4, counts.max() + 0.4), ylim=(0, YMAX_CHANGED))
        axis.set_title(LEVELS[i], fontsize=FONT["panel"], pad=3)
    axes[0].set_ylabel(CHANGED_LABEL, fontsize=FONT["label"])
    axes[1].set_xlabel("Number of passengers", fontsize=FONT["label"])
    title(fig, "By number of passengers")
    bottom_legend(fig, mode_handles(), ncol=2)
    return save(fig, "by_passengers")


# =========================
# Results: direction of the effect
# =========================
LEAN_LIMIT = 70
LEAN_MIN_SHARE = 0.01  # hide lean bins holding less than 1% of the cars at that complexity


def net_change_by_lean():
    from matplotlib.lines import Line2D
    result, _ = read_results("social_direction")
    fig, axes = new_figure(TEXT_WIDTH, 2.9, columns=3, gap=0.18)
    reference = figures.COLORS["reference"]
    for axis, complexity in zip(axes, result["complexities"]):
        rows = [r for r in complexity["by_lean"] if r["share_of_cars"] >= LEAN_MIN_SHARE and "mean_lean" in r]
        x = [100 * r["mean_lean"] for r in rows]
        axis.plot([-LEAN_LIMIT, LEAN_LIMIT], [-LEAN_LIMIT, LEAN_LIMIT], color=reference, linewidth=1, linestyle=":")
        axis.axhline(0, color=reference, linewidth=0.9, linestyle="--")
        for mode in MODES:
            figures.line(axis, x, [r[f"{mode}_net_pp"] for r in rows], mode, end_label=False)
        axis.set(xlim=(-LEAN_LIMIT, LEAN_LIMIT), ylim=(-50, 40), xticks=[-60, -30, 0, 30, 60])
        axis.set_title(f"{complexity['label']} complexity", fontsize=FONT["panel"], pad=3)
        axis.text(LEAN_LIMIT - 2, -48, "passengers use\nautomation more →", ha="right", va="bottom",
                  fontsize=FONT["note"], color=figures.INK["secondary"])
    axes[0].set_ylabel("Driver's change in automation use\n(percentage points vs driving alone)",
                       fontsize=FONT["label"])
    axes[1].set_xlabel("Passengers' lean (percentage points)", fontsize=FONT["label"])
    title(fig, "Change in the driver's automation use by the passengers' lean")
    handles = [Line2D([], [], color=figures.COLORS[mode], linewidth=2, marker="o", markersize=5,
                      markeredgecolor="white", markeredgewidth=1, label=MODE_LABELS[mode]) for mode in MODES]
    handles += [Line2D([], [], color=reference, linewidth=1, linestyle=":", label="Driver matches passengers' solo use"),
                Line2D([], [], color=reference, linewidth=0.9, linestyle="--", label="No change from driving alone")]
    bottom_legend(fig, handles, ncol=4)
    return save(fig, "net_change_by_lean")


# =========================
# Appendix: timing and relationships
# =========================
APPENDIX_HEIGHT = 2.6
TIME_TICKS = [0, 50, 100]


def step_blocks_by_complexity():
    _, directory = read_results("influence_timing")
    with np.load(directory / "cycles.npz", allow_pickle=False) as z:
        levels = z["difficulties"].astype(str).tolist()
        blocks = {mode: step_blocks(z[f"{mode}_change"]) for mode in MODES}
    fig, axes = new_figure(COLUMN_WIDTH, APPENDIX_HEIGHT, columns=2, gap=TIME_PANEL_GAP)
    for axis, mode in zip(axes, MODES):
        x, values, _ = blocks[mode]
        for i, level in enumerate(levels):
            axis.plot(x, 100 * values[i], color=LEVEL_COLORS[level], linewidth=1.6, marker="o", markersize=3)
        axis.set(xlim=(0, 100), ylim=(0, YMAX_CHANGED), xticks=TIME_TICKS)
        axis.set_title(MODE_LABELS[mode], fontsize=FONT["panel"], pad=3)
        axis.set_xlabel("Steps", fontsize=FONT["label"])
    axes[0].set_ylabel(CHANGED_LABEL, fontsize=FONT["label"])
    title(fig, "Change over the drive")
    colors = [LEVEL_COLORS[level] for level in ("low", "normal", "high")]
    bottom_legend(fig, color_handles(colors), ncol=3, heading="Track complexity:")
    return save(fig, "step_blocks_by_complexity")


def _driver_confidence_data():
    _, directory = read_results("driver_confidence")
    fields = ("driver", "passenger_count", "confidence_before", "confidence_after", "incoming_before", "incoming_after")
    with np.load(directory / "cycles.npz", allow_pickle=False) as z:
        return {k: z[k] for k in fields}


def _starting_figure(profiles, name, figure_title, ylabel, heading):
    fig, axes = new_figure(0.48 * TEXT_WIDTH, APPENDIX_HEIGHT, columns=2, gap=TIME_PANEL_GAP)
    for axis, mode in zip(axes, MODES):
        for row in profiles[mode]:
            color = START_COLORS[LEVELS.index(row["label"])]
            axis.plot(np.arange(len(row["profile"])), row["profile"], color=color, linewidth=1.6)
        axis.set(xlim=(0, 100), ylim=(0, 1), xticks=TIME_TICKS, yticks=np.arange(0, 1.01, 0.2))
        axis.set_title(MODE_LABELS[mode], fontsize=FONT["panel"], pad=3)
        axis.set_xlabel("Steps", fontsize=FONT["label"])
    axes[0].set_ylabel(ylabel, fontsize=FONT["label"])
    title(fig, figure_title)
    bottom_legend(fig, color_handles(START_COLORS), ncol=3, heading=heading)
    return save(fig, name)


def inbound_trust_by_starting_trust(data):
    profiles = starting_categories(data, value_field="incoming", group_field="incoming")
    return _starting_figure(profiles, "inbound_trust_by_starting_trust", "Passengers' trust in the driver",
                            "Mean trust in driver", "Initial level:")


def starting_confidence(data):
    profiles = starting_categories(data)
    return _starting_figure(profiles, "starting_confidence", "Driver's confidence (self-trust)",
                            "Driver confidence", "Initial level:")


# =========================
# Appendix: example drives
# =========================
EXAMPLE_HEIGHT = 2.1
EXAMPLE_TITLES = dict(agree="(a)  Peer influence has little effect",
                      disagree="(b)  The three ways of driving diverge")


def example_cases_simple():
    """Same drawing as example_cases/plot.py, at its printed width so the text prints larger."""
    from experiment.analysis.example_cases.plot import simple_case
    result, directory = read_results("example_cases")
    cases = result["cases"]
    fig, axes = new_figure(0.8 * TEXT_WIDTH, EXAMPLE_HEIGHT, columns=len(cases), gap=0.3,
                           left=0.82, top=0.40, bottom=0.68)
    with np.load(directory / "cases.npz", allow_pickle=False) as saved:
        for axis, (label, info) in zip(axes, cases.items()):
            data = {key.split("__", 1)[1]: saved[key] for key in saved.files if key.startswith(f"{label}__")}
            complexity = simple_case(axis, info, data, EXAMPLE_TITLES.get(label, label))
            axis.tick_params(labelsize=FONT["tick"])
            axis.xaxis.label.set_size(FONT["label"])
    handles, _ = axes[0].get_legend_handles_labels()
    bottom_legend(fig, [*handles, complexity], ncol=4)
    return save(fig, "example_cases_simple")


# =========================
# Main
# =========================
def main():
    data = _driver_confidence_data()
    paths = [complexity_effects(), by_passengers(), net_change_by_lean(), step_blocks_by_complexity(),
             inbound_trust_by_starting_trust(data), starting_confidence(data), example_cases_simple()]
    for path in paths:
        print(f"Saved {path}")
    if COPY_TO_PAPER:
        PAPER_FIGURES.mkdir(parents=True, exist_ok=True)
        for path in paths:
            shutil.copyfile(path, PAPER_FIGURES / path.name)
        print(f"Copied {len(paths)} PDFs to {PAPER_FIGURES}")


if __name__ == "__main__":
    main()
