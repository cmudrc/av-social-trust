"""Draw this question's figure from results/summary.json; edit freely and rerun (no analysis is repeated)."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

import numpy as np

from experiment.analysis.shared import figures
from experiment.analysis.shared.output import read_results
from experiment.analysis.when_social_matters.run import EXPLANATIONS

NAME="when_social_matters"


def save_figure(result,output):
    figure,(axis,)=figures.figure(1,figures.DOUBLE_COLUMN,2.8)
    keys=list(EXPLANATIONS)
    y=np.arange(len(keys))[::-1]
    height=0.36
    for offset,(mode,data) in zip((height/2+0.02,-height/2-0.02),result["modes"].items()):
        bars=axis.barh(y+offset,[data["r2"][k] for k in keys],height=height,color=figures.COLORS[mode],label=data["label"])
        axis.bar_label(bars,labels=[f"{data['r2'][k]:.2f}" for k in keys],padding=3,fontsize=7,color=figures.INK["secondary"])
    axis.set_yticks(y,[EXPLANATIONS[k][0] for k in keys],fontsize=8)
    axis.set(xlim=(0,1),xlabel="Variance in changed cycles explained (R²)")
    axis.grid(axis="y",visible=False)
    axis.grid(axis="x",color=figures.INK["grid"],linewidth=0.8)
    axis.legend(frameon=False,fontsize=8,loc="upper right")
    axis.set_title("What explains when the social layer changes behavior",fontsize=9)
    return figures.save(figure,output,"explanations.png")


def render(output=None):
    result,directory=read_results(NAME,output)
    path=save_figure(result,directory)
    print(f"Drew {path}",flush=True)
    return path


if __name__=="__main__":
    render()
