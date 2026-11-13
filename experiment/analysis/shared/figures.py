"""Static figures with one consistent look: decision mode is blue, cognition mode orange.

Each question computes its data in run.py and draws it in plot.py, so figures can be
restyled and redrawn from saved results in seconds. Figures are saved as PNG (for the
README) and PDF (vector, for the paper). Widths follow common two-column papers.
"""

import os
from pathlib import Path
import tempfile

COLORS = dict(decision="#2a78d6",cognition="#eb6834",solo="#52514e",passenger="#a8a7a1",reference="#8a8984")
CMAPS = dict(decision="Blues",cognition="Oranges")
INK = dict(primary="#0b0b0b",secondary="#52514e",grid="#e4e3df")
SINGLE_COLUMN = 3.5   # inches
DOUBLE_COLUMN = 7.16  # inches
MODE_NAMES = dict(solo="Driver alone",decision="Decision-level",cognition="Cognition-level")


def style(axis):
    axis.spines[["top","right"]].set_visible(False)
    axis.spines[["left","bottom"]].set_color(INK["secondary"])
    axis.tick_params(colors=INK["secondary"])
    axis.grid(axis="y",color=INK["grid"],linewidth=0.8)
    axis.set_axisbelow(True)


def figure(columns=1, width=6.4, height=3.8, rows=1, **grid):
    os.environ.setdefault("MPLCONFIGDIR",str(Path(tempfile.gettempdir())/"av-social-trust-matplotlib"))
    import matplotlib
    matplotlib.rcParams.update({"axes.labelsize":8,"axes.titlesize":9,"legend.fontsize":7,
                                "xtick.labelsize":7,"ytick.labelsize":7,"font.size":8})
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    result = Figure(figsize=(width,height),dpi=200)
    FigureCanvasAgg(result)
    axes = result.subplots(rows,columns,squeeze=False,**grid)
    for axis in axes.ravel():
        style(axis)
    return result,(axes[0] if rows==1 else axes)


def line(axis, x, y, mode, label=None, end_label=True):
    axis.plot(x,y,color=COLORS[mode],linewidth=2,marker="o",markersize=5,
              markeredgecolor="white",markeredgewidth=1,label=label)
    if end_label and label and len(x):
        axis.annotate(label,(x[-1],y[-1]),xytext=(6,0),textcoords="offset points",
                      va="center",fontsize=8,color=INK["primary"])


def save(result, output, name, tight=True):
    """Save name.png and name.pdf in results/figures and return the README path of the PNG."""
    folder = Path(output)/"figures"
    folder.mkdir(parents=True,exist_ok=True)
    if tight:
        result.tight_layout()
    stem = Path(name).stem
    result.savefig(folder/f"{stem}.png")
    result.savefig(folder/f"{stem}.pdf")
    return f"results/figures/{stem}.png"
