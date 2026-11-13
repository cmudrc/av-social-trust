"""Draw the timing figures from results/summary.json and results/cycles.npz; edit freely and rerun."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

import numpy as np
import json

from experiment.analysis.shared import figures
from experiment.analysis.shared.output import read_results, atomic_text

NAME="influence_timing"
BLOCK_STEPS=10
LEVELS={'low':'Low','normal':'Medium','high':'High'}
LEVEL_COLORS={'low':'#247db7','normal':'#e78926','high':'#309548'}
MODE_LABELS={'decision':'Decision-level influence','cognition':'Cognition-level influence'}


def early_late(result,directory):
    early=result["early_cycles"]
    figure,(left,)=figures.figure(1,4.5,3.2)
    o=result["overall"]
    for mode in ("decision","cognition"):
        left.plot([0,1],[100*o[f"{mode}_early"],100*o[f"{mode}_late"]],color=figures.COLORS[mode],marker='o',label=MODE_LABELS[mode])
    left.set_xticks([0,1],[f"Early\n1–{early}",f"Later\n{early+1}–100"])
    left.set(xlim=(-.15,1.15),ylim=(0,35),ylabel="Driver decisions different\nfrom solo driving (%)",xlabel='Steps')
    left.set_title("Early versus late effect",fontsize=9)
    left.legend(loc='upper right')
    return figures.save(figure,directory,"timing.png")


def timing_by_complexity(result,directory):
    early=result['early_cycles']
    groups=result["groups"]["track_difficulty"]["groups"]
    figure,axes=figures.figure(2,figures.DOUBLE_COLUMN,3.2,sharey=True)
    for axis,mode in zip(axes,('decision','cognition')):
        for group in groups:
            level=group['group']
            axis.plot([0,1],[100*group[f'{mode}_early'],100*group[f'{mode}_late']],
                      marker='o',color=LEVEL_COLORS[level],label=f'{LEVELS[level]} complexity')
        axis.set(xticks=[0,1],xticklabels=[f'Early\n1–{early}',f'Later\n{early+1}–100'],xlabel='Steps',
                 xlim=(-.15,1.15),ylim=(0,35),title=MODE_LABELS[mode])
    axes[0].set_ylabel('Driver decisions different\nfrom solo driving (%)')
    handles,labels=axes[0].get_legend_handles_labels()
    figure.legend(handles,labels,loc='lower center',ncol=3,frameon=False,fontsize=7)
    figure.tight_layout(rect=(0,.13,1,1))
    return figures.save(figure,directory,'timing_by_complexity',tight=False)


def step_blocks(values,width=BLOCK_STEPS):
    """Non-overlapping means: steps 1–10, 11–20, …, with no duplicated boundary."""
    values=np.asarray(values)
    if not isinstance(width,int) or isinstance(width,bool) or width<1 or values.ndim<1 or values.shape[-1]<1:
        raise ValueError('Expected a nonempty step axis and positive integer block width')
    starts=np.arange(0,values.shape[-1],width)
    ends=np.minimum(starts+width,values.shape[-1])
    centers=(starts+1+ends)/2
    means=np.stack([values[...,lo:hi].mean(axis=-1) for lo,hi in zip(starts,ends)],axis=-1)
    return centers,means,[(int(lo+1),int(hi)) for lo,hi in zip(starts,ends)]


def draw_step_blocks(result,directory):
    with np.load(directory/'cycles.npz',allow_pickle=False) as saved:
        levels=saved['difficulties'].astype(str).tolist()
        counts=saved['cars']
        values={mode:saved[f'{mode}_change'] for mode in ('decision','cognition')}
    block_values={mode:step_blocks(value) for mode,value in values.items()}
    x,_,bounds=block_values['decision']
    summary=dict(block_steps=BLOCK_STEPS,blocks=bounds,sampled_cars=int(counts.sum()),
                 weighting='Existing fixed random sample per driver/track, pooled car weights; not the balanced network sample.',
                 definition='Mean percentage of driver decisions different from solo within each non-overlapping block. No step-zero decision is added.',
                 by_complexity={},overall={})
    figure,(axis,)=figures.figure(1,4.5,3.2)
    for mode in ('decision','cognition'):
        block=block_values[mode][1]
        overall=100*np.average(block,axis=0,weights=counts)
        summary['overall'][mode]=overall.tolist()
        summary['by_complexity'][mode]={LEVELS[level]:(100*block[i]).tolist() for i,level in enumerate(levels)}
        axis.plot(x,overall,color=figures.COLORS[mode],marker='o',markersize=3,label=MODE_LABELS[mode])
    axis.set(xlabel='Steps',ylabel='Driver decisions different\nfrom solo driving (%)',xlim=(0,100),ylim=(0,40))
    axis.legend(loc='upper right')
    paths=[figures.save(figure,directory,'step_blocks')]
    from matplotlib.lines import Line2D
    figure, (axis,) = figures.figure(1, figures.DOUBLE_COLUMN, 3.8)
    for mode, linestyle in (('decision', '-'), ('cognition', '--')):
        for i, level in enumerate(levels):
            axis.plot(x, 100*block_values[mode][1][i], color=LEVEL_COLORS[level],
                      linestyle=linestyle, linewidth=1.8, marker='o', markersize=3)
    axis.set(xlabel='Steps', ylabel='Driver decisions different\nfrom solo driving (%)',
             xlim=(0,100), ylim=(0,40))
    complexity_legend = axis.legend(handles=[
        Line2D([], [], color=LEVEL_COLORS[level], linewidth=1.8,
               label=f'{LEVELS[level]} complexity') for level in levels],
        loc='upper left', ncol=3, frameon=False)
    axis.add_artist(complexity_legend)
    axis.legend(handles=[Line2D([], [], color='#333333', linestyle=style,
                               linewidth=1.8, label=MODE_LABELS[mode])
                         for mode, style in (('decision', '-'), ('cognition', '--'))],
                loc='upper right', frameon=False)
    paths.append(figures.save(figure, directory, 'step_blocks_by_complexity'))
    atomic_text(directory/'step_blocks.json',json.dumps(summary,indent=2)+'\n')
    return paths


def cycle_dynamics(result,directory):
    saved=np.load(directory/"cycles.npz")
    difficulties=[str(d) for d in saved["difficulties"]]
    figure,axes=figures.figure(len(difficulties),figures.DOUBLE_COLUMN,2.6,sharey=True)
    cycles=np.arange(1,saved["decision_change"].shape[1]+1)
    for i,(axis,difficulty) in enumerate(zip(axes,difficulties)):
        for mode in ('decision','cognition'):
            axis.plot(cycles,100*saved[f"{mode}_change"][i],color=figures.COLORS[mode],linewidth=1.4)
        axis.set_title(f"{LEVELS[difficulty]} complexity",fontsize=8)
        axis.set(xlim=(1,cycles[-1]),ylim=(0,40),xlabel="Steps")
    axes[0].set_ylabel("Driver decisions different\nfrom solo driving (%)")
    from matplotlib.lines import Line2D
    handles=[Line2D([],[],color=figures.COLORS["decision"],linewidth=1.8,label="Decision-level: changed vs solo"),
             Line2D([],[],color=figures.COLORS["cognition"],linewidth=1.8,label="Cognition-level: changed vs solo")]
    figure.legend(handles=handles,loc="lower center",ncol=2,frameon=False,fontsize=7)
    figure.tight_layout(rect=(0,0.13,1,1))
    return figures.save(figure,directory,"cycle_dynamics.png",tight=False)


def render(output=None):
    result,directory=read_results(NAME,output)
    paths=[early_late(result,directory),timing_by_complexity(result,directory)]
    if (directory/"cycles.npz").exists():
        paths.append(cycle_dynamics(result,directory))
        paths.extend(draw_step_blocks(result,directory))
    print("Drew "+", ".join(paths),flush=True)
    return paths


if __name__=="__main__":
    render()
