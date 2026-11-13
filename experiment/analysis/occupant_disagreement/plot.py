"""Draw the pressure figures from results/summary.json and pressure_change.npz; edit freely and rerun."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

import numpy as np

from experiment.analysis.shared import figures
from experiment.analysis.shared.output import read_results

NAME="occupant_disagreement"
PRESSURES=dict(solo_outvoted_cycles="Outvoted cycles (equal-weight vote)",
               solo_cognitive_pull_cycles="Cognitive-pull cycles (mean cognition)")


def binned_means(result,directory):
    figure,(left,right)=figures.figure(2,figures.DOUBLE_COLUMN,2.9)
    for axis,key,title in ((left,"by_outvoted","Equal-weight vote overrules the driver"),
                           (right,"by_cognitive_pull","Mean cognition flips the driver's tree")):
        groups=result[key]
        x=[g["pressure"] for g in groups]
        axis.plot([0,100],[0,100],color=figures.COLORS["reference"],linewidth=1,linestyle="--")
        figures.line(axis,x,[g["decision"] for g in groups],"decision","Decision")
        figures.line(axis,x,[g["cognition"] for g in groups],"cognition","Cognition")
        axis.set(xlim=(0,100),ylim=(0,100),xlabel="Pressure cycles (solo counterfactual)",ylabel="Changed cycles vs solo")
        axis.set_title(title,fontsize=9)
    return figures.save(figure,directory,"change_vs_pressure.png")


def heatmaps(result,directory):
    from matplotlib.colors import LogNorm
    saved=np.load(directory/"pressure_change.npz")
    figure,axes=figures.figure(2,figures.DOUBLE_COLUMN,5.6,rows=2,sharex=True,sharey=True)
    cycles=np.arange(101)
    images=[]
    for row,mode in enumerate(("decision","cognition")):
        for column,pressure in enumerate(PRESSURES):
            axis=axes[row,column]
            counts=saved[f"{mode}__{pressure}"]
            axis.grid(False)
            image=axis.imshow(np.ma.masked_equal(counts.T,0),origin="lower",cmap=figures.CMAPS[mode],
                              norm=LogNorm(vmin=1,vmax=counts.max()),extent=(-0.5,100.5,-0.5,100.5),aspect="auto")
            total=counts.sum(axis=1)
            mean=np.divide(counts@cycles,total,out=np.full(101,np.nan),where=total>=200)
            axis.plot(cycles,mean,color=figures.INK["primary"],linewidth=1.3,label="Mean change")
            axis.plot([0,100],[0,100],color=figures.COLORS["reference"],linewidth=0.9,linestyle="--",label="Change = pressure")
            rho=result["correlations"][pressure][mode]
            axis.text(3,94,f"ρ = {rho:.2f}",fontsize=8,color=figures.INK["primary"],va="top")
            if row==1:
                axis.set_xlabel(PRESSURES[pressure],fontsize=8)
            if column==0:
                axis.set_ylabel(f"{figures.MODE_NAMES[mode]}:\ncycles changed vs solo",fontsize=8)
        images.append(image)
    handles,labels=axes[0,0].get_legend_handles_labels()
    figure.legend(handles,labels,loc="lower center",ncol=2,frameon=False,fontsize=7)
    figure.subplots_adjust(left=0.1,right=0.88,bottom=0.13,top=0.97,hspace=0.12,wspace=0.08)
    for row,image in enumerate(images):
        box=axes[row,1].get_position()
        colorbar=figure.colorbar(image,cax=figure.add_axes((box.x1+0.015,box.y0,0.015,box.height)))
        colorbar.set_label("Cars",fontsize=7)
        colorbar.ax.tick_params(labelsize=7)
    return figures.save(figure,directory,"pressure_heatmaps.png",tight=False)


def render(output=None):
    result,directory=read_results(NAME,output)
    paths=[binned_means(result,directory)]
    if (directory/"pressure_change.npz").exists():
        paths.append(heatmaps(result,directory))
    print("Drew "+", ".join(paths),flush=True)
    return paths


if __name__=="__main__":
    render()
