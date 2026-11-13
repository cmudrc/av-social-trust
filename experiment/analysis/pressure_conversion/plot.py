"""Draw this question's figure from results/summary.json; edit freely and rerun (no analysis is repeated)."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

import numpy as np

from experiment.analysis.shared import figures
from experiment.analysis.shared.output import read_results

NAME="pressure_conversion"


def save_figure(result,output):
    figure,(left,right)=figures.figure(2,figures.DOUBLE_COLUMN,2.9)
    for axis,name,xlabel in ((left,"passenger_count","Passengers"),(right,"alpha_outbound_mean","Driver's homophily toward passengers (alpha)")):
        groups=result["features"][name]["groups"]
        x=np.arange(len(groups))
        figures.line(axis,x,[g["decision_conversion"] for g in groups],"decision","Decision")
        figures.line(axis,x,[g["cognition_conversion"] for g in groups],"cognition","Cognition")
        axis.axhline(1,color=figures.COLORS["reference"],linewidth=1,linestyle="--")
        axis.set_xticks(x,[g["group"] for g in groups])
        axis.set(ylim=(0,1.3),xlim=(-0.3,len(groups)-0.2),xlabel=xlabel,ylabel="Changed / pressure cycles")
    left.set_title("Changed cycles relative to equal-weight pressure",fontsize=9)
    return figures.save(figure,output,"conversion.png")


def render(output=None):
    result,directory=read_results(NAME,output)
    path=save_figure(result,directory)
    print(f"Drew {path}",flush=True)
    return path


if __name__=="__main__":
    render()
