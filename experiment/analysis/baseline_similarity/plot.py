"""Draw the baseline-similarity figures from results/summary.json and agreement_map.npz; edit freely and rerun."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

import numpy as np

from experiment.analysis.shared import figures
from experiment.analysis.shared.output import read_results

NAME="baseline_similarity"
CATEGORY_COLORS={"both alike":"#1baf7a","only decision alike":figures.COLORS["decision"],
                 "only cognition alike":figures.COLORS["cognition"],"neither alike":"#a8a7a1"}
OUTCOMES=dict(decision_alike=("Decision-level alike","decision","Blues"),
              cognition_alike=("Cognition-level alike","cognition","Oranges"),
              both_alike=("Both alike","both","Greens"))


def agreement_map(result,directory):
    from matplotlib.colors import LogNorm
    counts=np.load(directory/"agreement_map.npz")["counts"]
    figure,(axis,)=figures.figure(1,figures.SINGLE_COLUMN+0.6,3.3)
    axis.grid(False)
    image=axis.imshow(np.ma.masked_equal(counts.T,0),origin="lower",cmap="Greys",norm=LogNorm(vmin=1,vmax=counts.max()),
                      extent=(-0.5,100.5,-0.5,100.5),aspect="equal")
    limit=100-result["alike_max_changed"]
    axis.axvline(limit-0.5,color=figures.INK["primary"],linewidth=0.8,linestyle="--")
    axis.axhline(limit-0.5,color=figures.INK["primary"],linewidth=0.8,linestyle="--")
    # The "alike" regions are thin strips along the top and right edges, so labels point into them.
    o=result["overall"]
    arrow=dict(arrowstyle="-",color=figures.INK["secondary"],linewidth=0.7)
    labels={"both alike":("Both alike",(97.5,97.5),(64,80)),
            "only cognition alike":("Only cognition alike",(35,97.5),(28,84)),
            "only decision alike":("Only decision alike",(97.5,30),(52,22))}
    for category,(text,point,place) in labels.items():
        axis.annotate(f"{text}  {100*o[category]:.0f}%",point,xytext=place,fontsize=7,color=figures.INK["primary"],
                      arrowprops=arrow,bbox=dict(boxstyle="round,pad=0.2",facecolor="white",edgecolor="none",alpha=0.85))
    axis.text(4,4,f"Neither alike  {100*o['neither alike']:.0f}%",fontsize=7,color=figures.INK["primary"],
              bbox=dict(boxstyle="round,pad=0.2",facecolor="white",edgecolor="none",alpha=0.85))
    axis.set(xlim=(-0.5,100.5),ylim=(-0.5,100.5),xlabel="Decision-level agreement with driving alone (%)",
             ylabel="Cognition-level agreement\nwith driving alone (%)")
    colorbar=figure.colorbar(image,ax=axis,fraction=0.046,pad=0.03)
    colorbar.set_label("Cars",fontsize=7)
    return figures.save(figure,directory,"agreement_map.png")


def pressure_plane(result,directory):
    plane=result["pressure_plane"]
    counts=np.array(plane["counts"],dtype=np.float64)
    total=counts.sum(axis=2)
    categories=result["categories"]
    maps=dict(decision_alike=counts[...,[categories.index("both alike"),categories.index("only decision alike")]].sum(axis=2),
              cognition_alike=counts[...,[categories.index("both alike"),categories.index("only cognition alike")]].sum(axis=2),
              both_alike=counts[...,categories.index("both alike")])
    figure,axes=figures.figure(3,figures.DOUBLE_COLUMN,2.9,sharey=True)
    for axis,(key,(title,_,cmap)) in zip(axes,OUTCOMES.items()):
        share=np.divide(maps[key],total,out=np.full_like(total,np.nan),where=total>0)
        axis.grid(False)
        axis.imshow(np.ma.masked_invalid(share),origin="lower",cmap=cmap,vmin=0,vmax=1,aspect="auto")
        for i in range(share.shape[0]):
            for j in range(share.shape[1]):
                if np.isfinite(share[i,j]):
                    axis.text(j,i,f"{100*share[i,j]:.0f}",ha="center",va="center",fontsize=6.5,
                              color="white" if share[i,j]>0.6 else figures.INK["primary"])
        axis.set_xticks(range(len(plane["cognitive_pull_bins"])),plane["cognitive_pull_bins"],rotation=45)
        axis.set_yticks(range(len(plane["outvoted_bins"])),plane["outvoted_bins"])
        axis.set_title(f"{title} (% of cars)",fontsize=8)
        axis.set_xlabel("Cognitive-pull cycles")
    axes[0].set_ylabel("Outvoted cycles")
    return figures.save(figure,directory,"pressure_plane.png")


def stacked(axis,groups,categories):
    y=np.arange(len(groups))[::-1]
    left=np.zeros(len(groups))
    for category in categories:
        widths=np.array([g[category] for g in groups])
        axis.barh(y,widths,left=left,color=CATEGORY_COLORS[category],height=0.7,edgecolor="white",linewidth=0.8,label=category)
        left+=widths
    axis.set_yticks(y,[g["group"] for g in groups])
    axis.set(xlim=(0,1))
    axis.xaxis.set_major_formatter(lambda value,_:f"{100*value:.0f}%")
    axis.grid(axis="y",visible=False)
    axis.grid(axis="x",color=figures.INK["grid"],linewidth=0.8)


def categories_by_condition(result,directory):
    keys=("passenger_count","track_difficulty","solo_regime")
    figure,axes=figures.figure(len(keys),figures.DOUBLE_COLUMN,2.4)
    for axis,key in zip(axes,keys):
        group=result["groups"][key]
        stacked(axis,group["groups"],result["categories"])
        axis.set_title('Solo baseline behavior' if key=='solo_regime' else 'Track complexity' if key=='track_difficulty' else group['label'],fontsize=8)
        if key=='track_difficulty':
            axis.set_yticklabels([{'low':'Low','normal':'Medium','high':'High'}.get(g['group'],g['group']) for g in group['groups']])
    handles,labels=axes[0].get_legend_handles_labels()
    clear_labels=['Both social models resemble solo','Only decision-level resembles solo',
                  'Only cognition-level resembles solo','Neither social model resembles solo']
    figure.legend(handles,clear_labels,loc="lower center",ncol=2,frameon=False,fontsize=6.5)
    figure.tight_layout(rect=(0,0.17,1,1))
    return figures.save(figure,directory,"categories_by_condition.png",tight=False)


def predictors(result,directory):
    rows=result["predictors"]
    figure,(axis,)=figures.figure(1,figures.DOUBLE_COLUMN,0.22*len(rows)+1.0)
    y=np.arange(len(rows))[::-1]
    axis.axvline(0.5,color=figures.COLORS["reference"],linewidth=0.9,linestyle="--")
    colors=dict(decision_alike=figures.COLORS["decision"],cognition_alike=figures.COLORS["cognition"],
                both_alike=CATEGORY_COLORS["both alike"])
    for offset,(key,(title,_,_)) in zip((0.2,0,-0.2),OUTCOMES.items()):
        axis.scatter([r[key] for r in rows],y+offset,s=22,color=colors[key],edgecolors="white",linewidths=0.8,label=title,zorder=3)
    axis.set_yticks(y,[r["label"] for r in rows])
    axis.grid(axis="y",visible=False)
    axis.grid(axis="x",color=figures.INK["grid"],linewidth=0.8)
    axis.set(xlim=(0,1),xlabel="AUC of the feature alone  (← lower values look alike · higher values look alike →)")
    axis.legend(frameon=False,fontsize=7,loc="lower right")
    axis.set_title("What predicts looking like driving alone",fontsize=9)
    return figures.save(figure,directory,"predictors.png")


def participants(result,directory):
    groups=sorted(result["groups"]["participant"]["groups"],key=lambda g:g["both alike"])
    figure,(axis,)=figures.figure(1,figures.SINGLE_COLUMN+0.6,4.4)
    stacked(axis,groups[::-1],result["categories"])
    axis.set_title("Participants as drivers",fontsize=9)
    axis.legend(loc="upper center",bbox_to_anchor=(0.45,-0.08),ncol=2,frameon=False,fontsize=7)
    return figures.save(figure,directory,"participants.png")


def render(output=None):
    result,directory=read_results(NAME,output)
    paths=[agreement_map(result,directory),pressure_plane(result,directory),categories_by_condition(result,directory),
           predictors(result,directory),participants(result,directory)]
    print("Drew "+", ".join(paths),flush=True)
    return paths


if __name__=="__main__":
    render()
