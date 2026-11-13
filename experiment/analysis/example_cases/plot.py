"""Draw the example cars from results/cases.npz; edit freely and rerun (no analysis is repeated)."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

import numpy as np

from experiment.analysis.shared import figures
from experiment.analysis.shared.output import read_results

NAME="example_cases"
TITLES=dict(agree="(A)  The social layer barely matters",disagree="(B)  The three ways of driving diverge")
STATE_LABELS=dict(automation_trust="Automation trust",perceived_risk="Perceived risk",workload="Workload")


def runs(on):
    """(start, length) pairs of consecutive automated cycles, on a 1-based cycle axis."""
    padded=np.concatenate([[False],np.asarray(on,dtype=bool),[False]])
    edges=np.flatnonzero(padded[1:]!=padded[:-1])
    return [(start+0.5,end-start) for start,end in zip(edges[::2],edges[1::2])]


def strip(axis,y,on,color,height=0.62):
    axis.broken_barh([(0.5,len(on))],(y-height/2,height),facecolors="#f1f0ec")
    axis.broken_barh(runs(on),(y-height/2,height),facecolors=color)


def draw_case(axes,info,data,title,states):
    cycles=np.arange(1,len(data["solo_on"])+1)
    complexity,*state_axes,opinion,timeline=axes
    complexity.fill_between(cycles,data["complexity"],step="mid",color=figures.COLORS["passenger"],linewidth=0)
    complexity.set(ylim=(0,1.15),yticks=[0,1])
    complexity.set_yticklabels(["low","high"],fontsize=7)
    complexity.set_ylabel("Task\ncomplexity",fontsize=7)
    changed=info["changed_cycles"]
    complexity.set_title(
        f"{title}\n{info['driver']} driving with {', '.join(info['passengers'])}  ·  track {info['track']}\n"
        f"Steps different from solo: decision {changed['decision_vs_solo']} · "
        f"cognition {changed['cognition_vs_solo']}"
        ,
        fontsize=7.5,loc="left")
    index={name:i for i,name in enumerate(("automation_trust","perceived_risk","workload"))}
    for axis,state in zip(state_axes,states):
        if state not in info["modeled_states"]:
            axis.set_visible(False)
            continue
        i=index[state]
        axis.plot(cycles,data["solo_cognition"][:,i],color=figures.COLORS["solo"],linewidth=1.4,label="Alone (= decision-level)")
        axis.plot(cycles,data["cognition_cognition"][:,i],color=figures.COLORS["cognition"],linewidth=1.6,label="Cognition-level")
        for name,threshold in info["tree_splits"]:
            if name==state:
                axis.axhline(threshold,color=figures.COLORS["reference"],linewidth=0.8,linestyle="--",
                             label="Driver's decision-tree split")
        axis.set_ylim(-0.02,1.02)
        axis.set_ylabel(STATE_LABELS[state],fontsize=7)
    opinion.axhline(0,color=figures.COLORS["reference"],linewidth=0.8,linestyle="--")
    opinion.plot(cycles,data["decision_opinion"],color=figures.COLORS["decision"],linewidth=1.4)
    opinion.set(ylim=(-1.08,1.08),yticks=[-1,0,1])
    opinion.set_ylabel("Car's vote\n(driver's view)",fontsize=7)
    opinion.text(1.5,0.82,"automate",fontsize=6.5,color=figures.INK["secondary"],va="center")
    opinion.text(1.5,-0.82,"manual",fontsize=6.5,color=figures.INK["secondary"],va="center")
    rows=[(f"{p} alone",data["passenger_solo_on"][k],figures.COLORS["passenger"]) for k,p in enumerate(info["passengers"])]
    rows+=[("Driver alone",data["solo_on"],figures.COLORS["solo"]),("Decision-level",data["decision_on"],figures.COLORS["decision"]),
           ("Cognition-level",data["cognition_on"],figures.COLORS["cognition"])]
    for y,(label,on,color) in enumerate(reversed(rows)):
        strip(timeline,y,on,color)
    timeline.set_yticks(range(len(rows)),[label for label,_,_ in reversed(rows)],fontsize=7)
    timeline.set(ylim=(-0.6,len(rows)-0.4))
    timeline.grid(False)
    timeline.spines["left"].set_visible(False)
    timeline.tick_params(axis="y",length=0)
    timeline.set_xlabel("Steps (filled = automation on)",fontsize=8)
    for axis in axes:
        axis.set_xlim(0.5,len(cycles)+0.5)
        axis.tick_params(labelsize=7)


# Simple figure: the driver's automation decision in each setting over the task complexity.
# Identical on/off lines would hide each other, so each setting is drawn slightly offset.
SIMPLE_SETTINGS=(("solo_on","Driver alone","solo",0.05),("decision_on","Decision-level","decision",0.0),
                 ("cognition_on","Cognition-level","cognition",-0.05))


def simple_case(axis,info,data,title):
    from matplotlib.patches import Patch
    cycles=np.arange(1,len(data["solo_on"])+1)
    for start,length in runs(data["complexity"]):
        axis.axvspan(start,start+length,color="#e4e3df",linewidth=0)
    for key,label,mode,offset in SIMPLE_SETTINGS:
        axis.step(cycles,data[key].astype(float)+offset,where="mid",color=figures.COLORS[mode],linewidth=1.6,label=label)
    axis.grid(False)
    axis.set(xlim=(0.5,len(cycles)+0.5),ylim=(-0.25,1.25),xlabel="Steps")
    axis.set_yticks([0,1],["Manual","Automation"])
    changed=info["changed_cycles"]
    axis.set_title(
        f"{title}\n"
        #f"{info['driver']} driving with {', '.join(info['passengers'])}\n"
        #f"Steps different from solo: decision {changed['decision_vs_solo']} · cognition {changed['cognition_vs_solo']}"
        ,
        fontsize=8,loc="left")
    return Patch(color="#e4e3df",label="High task complexity")


def render_simple(result,directory,saved):
    cases=result["cases"]
    figure,axes=figures.figure(len(cases),figures.DOUBLE_COLUMN,2.4,sharey=True)
    for axis,(label,info) in zip(axes,cases.items()):
        data={key.split("__",1)[1]:saved[key] for key in saved.files if key.startswith(f"{label}__")}
        complexity=simple_case(axis,info,data,TITLES.get(label,label))
    handles,_=axes[0].get_legend_handles_labels()
    figure.legend([*handles,complexity],[h.get_label() for h in (*handles,complexity)],
                  loc="lower center",ncol=4,frameon=False,fontsize=7)
    figure.tight_layout(rect=(0,0.08,1,1))
    return figures.save(figure,directory,"example_cases_simple.png",tight=False)


def render(output=None):
    result,directory=read_results(NAME,output)
    saved=np.load(directory/"cases.npz")
    simple=render_simple(result,directory,saved)
    cases=result["cases"]
    states=[s for s in ("automation_trust","perceived_risk","workload") if any(s in c["modeled_states"] for c in cases.values())]
    heights=[0.45,*[1.0]*len(states),0.8,0.3*(max(len(c["passengers"]) for c in cases.values())+3)+0.3]
    figure,axes=figures.figure(len(cases),figures.DOUBLE_COLUMN,1.25*sum(heights)+0.4,rows=len(heights),
                               sharex="col",gridspec_kw=dict(height_ratios=heights))
    for column,(label,info) in enumerate(cases.items()):
        data={key.split("__",1)[1]:saved[key] for key in saved.files if key.startswith(f"{label}__")}
        draw_case(axes[:,column],info,data,TITLES.get(label,label),states)
    handles,labels=axes[1,0].get_legend_handles_labels()
    unique=dict(zip(labels,handles))
    figure.legend(unique.values(),unique.keys(),loc="lower center",ncol=3,frameon=False,fontsize=7,bbox_to_anchor=(0.5,0))
    figure.tight_layout(rect=(0,0.03,1,1))
    path=figures.save(figure,directory,"example_cases.png",tight=False)
    print(f"Drew {path}, {simple}",flush=True)
    return [path,simple]


if __name__=="__main__":
    render()
