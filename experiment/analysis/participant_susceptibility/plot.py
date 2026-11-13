"""Draw this question's figure from results/summary.json; edit freely and rerun (no analysis is repeated)."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

import numpy as np

from experiment.analysis.shared import figures
from experiment.analysis.shared.output import read_results

NAME="participant_susceptibility"


def save_figure(result,output):
    figure,axes=figures.figure(2,figures.DOUBLE_COLUMN,3.3)
    for axis,mode,x_key,y_key,xlabel in ((axes[0],"decision","outvoted","decision_change","Mean outvoted cycles"),
                                         (axes[1],"cognition","cognitive_pull","cognition_change","Mean cognitive-pull cycles")):
        rows=result["rows"]
        x,y=np.array([r[x_key] for r in rows]),np.array([r[y_key] for r in rows])
        top=max(x.max(),y.max())*1.08
        axis.plot([0,top],[0,top],color=figures.COLORS["reference"],linewidth=1,linestyle="--")
        axis.scatter(x,y,s=36,color=figures.COLORS[mode],edgecolors="white",linewidths=1.5,zorder=3)
        # Label the most affected participants and those furthest from "change equals pressure".
        for i in sorted(set(np.argsort(-y)[:3])|set(np.argsort(-np.abs(y-x))[:3])):
            axis.annotate(rows[i]["participant"],(x[i],y[i]),xytext=(5,-3),textcoords="offset points",fontsize=7,color=figures.INK["secondary"])
        axis.set(xlim=(0,top),ylim=(0,top),xlabel=xlabel,ylabel="Mean changed cycles as driver")
        axis.set_title(f"{mode.title()}-level influence",fontsize=9)
    return figures.save(figure,output,"participants.png")


def render(output=None):
    result,directory=read_results(NAME,output)
    path=save_figure(result,directory)
    print(f"Drew {path}",flush=True)
    return path


if __name__=="__main__":
    render()
