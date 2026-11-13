"""Simple weighted-centrality figures from matched saved trajectory summaries."""
from pathlib import Path
import sys
if __package__ in (None,''):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/'src')]
import numpy as np
from experiment.analysis.shared import figures
from experiment.analysis.shared.output import read_results


def render(output=None):
    result,output=read_results('network_confidence',output)
    modes=('decision','cognition')
    fig,axes=figures.figure(2,7.16,3.4,sharey=True)
    for ax,mode in zip(axes,modes):
        p=result['profiles'][mode]
        ax.fill_between(p['steps'],p['lower'],p['upper'],color=figures.COLORS[mode],alpha=.18,label='Central half of cases')
        ax.plot(p['steps'],p['median'],color=figures.COLORS[mode],linewidth=2,label='Median driver centrality')
        ax.axhline(1,color='#777',linestyle='--',linewidth=.8,label='Equal share of influence')
        ax.set(xlabel='Steps',xlim=(0,100),ylim=(.5,1.5),title=f'{mode.capitalize()}-level influence')
        ax.legend(fontsize=6,loc='lower right')
    axes[0].set_ylabel('Driver’s weighted centrality\n(relative to an equal share)')
    figures.save(fig,output,'centrality_over_time')
    with np.load(output/'plots.npz',allow_pickle=False) as z:
        data={k:z[k] for k in z.files}
    fig,axes=figures.figure(2,7.16,3.4,sharey=True)
    ymax=max(2,float(data['centrality'].max())*1.05)
    for m,(ax,mode) in enumerate(zip(axes,modes)):
        ax.scatter(data['confidence'][:,m],data['centrality'][:,m],s=5,alpha=.1,color=figures.COLORS[mode],rasterized=True)
        rows=result['confidence_bins'][mode]
        ax.plot([r['confidence'] for r in rows],[r['centrality'] for r in rows],color=figures.COLORS[mode],marker='o',linewidth=2,label='Mean within confidence groups')
        ax.axhline(1,color='#777',linestyle='--',linewidth=.8)
        ax.set(xlabel='Mean driver confidence over the drive',title=f'{mode.capitalize()}-level influence',xlim=(0,1),ylim=(0,ymax))
        ax.legend(fontsize=6,loc='upper left')
    axes[0].set_ylabel('Mean weighted centrality\n(relative to an equal share)')
    figures.save(fig,output,'centrality_confidence')


if __name__=='__main__':
    render()
