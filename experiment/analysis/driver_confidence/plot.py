"""Driver-confidence figures from saved summaries, with no internal track names."""
from pathlib import Path
import sys
if __package__ in (None, ''):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/'src')]
import numpy as np
from experiment.analysis.shared import figures
from experiment.analysis.shared.output import read_results
from experiment.analysis.shared.paired import balanced_weights

NAMES=dict(baseline='Solo driving',decision='Decision-level influence',cognition='Cognition-level influence')
COLORS=dict(baseline=figures.COLORS['solo'],decision=figures.COLORS['decision'],cognition=figures.COLORS['cognition'])
COMPLEXITY=dict(low='Low',normal='Medium',high='High')


def starting_categories(data, count=3, *, value_field='confidence', group_field='confidence'):
    """Group step-0 through final-state profiles by a named starting quantity."""
    if count not in (3,5):
        raise ValueError('Use three or five confidence categories')
    edges = np.array([0,.2,.4,.6,.8,1]) if count==5 else np.array([0,1/3,2/3,1])
    names = ('Low','Medium','High') if count==3 else ('Very low','Low','Medium','High','Very high')
    weights = balanced_weights(data['driver'],data['passenger_count'])
    profiles = {}
    for m,mode in enumerate(('decision','cognition'),1):
        values = np.concatenate([data[f'{value_field}_before'][:,m],
                                 data[f'{value_field}_after'][:,m,-1:]],axis=1)
        initial = data[f'{group_field}_before'][:,m,0]
        if not np.isfinite(values).all() or not np.isfinite(initial).all():
            raise ValueError('Starting-category profiles require observed finite values')
        codes = np.clip(np.searchsorted(edges,initial,side='right')-1,0,count-1)
        profiles[mode] = [dict(label=names[b],lo=float(edges[b]),hi=float(edges[b+1]),cars=int(keep.sum()),
                               profile=np.average(values[keep],axis=0,weights=weights[keep]).tolist())
                          for b in range(count) for keep in [codes==b] if keep.any()]
    return profiles


def draw_starting_categories(output, profiles, name, *, ylabel='Driver confidence', legend_title='Initial driver confidence'):
    fig,axes=figures.figure(columns=2,width=7.16,height=3.6)
    for m,mode in enumerate(('decision','cognition')):
        for row in profiles[mode]:
            axes[m].plot(range(len(row['profile'])),row['profile'],label=row['label'])
        axes[m].set(xlabel='Steps',ylabel=ylabel if m==0 else '',title=NAMES[mode],ylim=(0,1))
    axes[-1].legend(title=legend_title,fontsize=7,title_fontsize=7)
    figures.save(fig,output,name)


def render_inbound_trust(data, output):
    """Passenger-to-driver raw trust; no self-link or undefined solo curve."""
    from experiment.analysis.shared.output import atomic_text
    import json
    groupings = {}
    for group_field,name,legend in (
        ('confidence','inbound_trust_by_starting_confidence','Initial driver confidence'),
        ('incoming','inbound_trust_by_starting_trust','Initial trust in driver'),
    ):
        profiles = starting_categories(data,value_field='incoming',group_field=group_field)
        draw_starting_categories(output,profiles,name,
                                ylabel='Mean passenger trust in driver',legend_title=legend)
        groupings[group_field] = profiles
    result = dict(
        definition='Mean raw trust passengers place in the driver; passenger-to-driver edges only, excluding self-trust.',
        scale='0–1 raw trust, not normalized influence weights, summed trust or network centrality.',
        steps='Step 0 is initial trust; steps 1–100 are the post-update states, including the final state.',
        weighting='Mean over passengers within each car, then the same driver/passenger-count weights as the starting-confidence figure, normalized within each category.',
        category_boundaries=[0,1/3,2/3,1],
        interpretation='Descriptive groups of existing runs; other initial conditions are not held fixed between categories. Solo has no passengers and no defined inbound passenger trust.',
        source='cycles.npz: incoming_before, incoming_after, confidence_before, driver and passenger_count.',
        sampled_car_tracks=len(data['driver']),
        groupings=groupings,
    )
    atomic_text(output/'inbound_trust_categories.json',json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


def render(output=None):
    result,output=read_results('driver_confidence',output)
    fig,axes=figures.figure(width=7.16,height=3.6)
    for mode,row in result['profiles'].items():
        values=[*row['confidence'],row['confidence_after'][-1]]
        axes[0].plot(range(len(values)),values,color=COLORS[mode],label=NAMES[mode],linewidth=2)
    axes[0].set(xlabel='Steps',ylabel='Driver confidence (self-trust)',ylim=(0,1))
    axes[0].legend(loc='lower right')
    figures.save(fig,output,'confidence_trajectories')
    with np.load(output/'cycles.npz',allow_pickle=False) as saved:
        data={k:saved[k] for k in ('driver','passenger_count','confidence_before','confidence_after',
                                  'incoming_before','incoming_after')}
    categories={}
    for count,name in ((3,'starting_confidence'),(5,'starting_confidence_five')):
        profiles=starting_categories(data,count)
        draw_starting_categories(output,profiles,name)
        categories[str(count)]=profiles
    from experiment.analysis.shared.output import atomic_text
    import json
    atomic_text(output/'starting_categories.json',json.dumps(categories,indent=2)+'\n')
    render_inbound_trust(data,output)
    fig,axes=figures.figure(columns=2,width=7.16,height=3.6)
    for m,mode in enumerate(('decision','cognition')):
        for d,row in result['complexity_profiles'][mode].items():
            values=[*row['confidence'],row['final']]
            axes[m].plot(range(len(values)),values,label=f'{COMPLEXITY[d]} complexity')
        axes[m].set(xlabel='Steps',ylabel='Driver confidence' if m==0 else '',title=NAMES[mode],ylim=(0,1))
    axes[-1].legend(fontsize=6)
    figures.save(fig,output,'confidence_by_complexity')
    fig,axes=figures.figure(width=7.16,height=3.6)
    for mode in ('decision','cognition'):
        rows=result['by_passengers'][mode]
        axes[0].plot([r['passengers'] for r in rows],[r['final'] for r in rows],color=COLORS[mode],marker='o',label=NAMES[mode])
    axes[0].set(xlabel='Passengers',ylabel='Final driver confidence',ylim=(0,1),xticks=range(1,6))
    axes[0].legend()
    figures.save(fig,output,'confidence_by_passengers')
    fig,axes=figures.figure(width=7.16,height=3.6)
    eta=result['self_learning_rate']
    xx=np.linspace(-1,1,50)
    axes[0].plot(xx,eta*xx,color='#777',linestyle='--',label='Model update rule')
    for mode in ('decision','cognition'):
        rows=result['update_curve'][mode]
        axes[0].scatter([r['mean_x'] for r in rows],[r['raw_changed_percent']/100 for r in rows],
                        color=COLORS[mode],label=NAMES[mode],s=25)
    axes[0].axhline(0,color='#aaa',linewidth=.8)
    axes[0].axvline(0,color='#aaa',linewidth=.8)
    axes[0].set(xlabel='Passengers’ trust in driver minus driver confidence',ylabel='Confidence change in this cycle')
    axes[0].legend(fontsize=6)
    figures.save(fig,output,'confidence_update')
    fig,axes=figures.figure(columns=2,width=7.16,height=3.6)
    for j,(field,title) in enumerate((('different_from_solo','Different from solo driving'),('different_from_private','Different from current private decision'))):
        for mode in ('decision','cognition'):
            rows=[r for r in result['confidence_curves'][mode][field] if r['cycles']>=100 and (r['sampled_base_cars'] or 0)>=10]
            axes[j].plot([r['mean_x'] for r in rows],[r['raw_changed_percent'] for r in rows],
                         color=COLORS[mode],marker='o',label=NAMES[mode])
        axes[j].set(xlabel='Observed driver confidence',title=title,ylim=(0,100),xlim=(0,1))
    axes[0].set_ylabel('Cycles with different decisions (%)')
    axes[-1].legend(fontsize=6)
    figures.save(fig,output,'observed_confidence')
    fig,axes=figures.figure(columns=3,width=9,height=3.8)
    for j,(field,title) in enumerate((('own_weight','Weight retained by driver'),
                                    ('different_from_private_percent','Different from current private decision'),
                                    ('different_from_solo_percent','Different from solo driving'))):
        for mode,row in result['interventions'].items():
            axes[j].plot(row['levels'],row[field],marker='o',color=COLORS[mode],label=NAMES[mode])
        axes[j].set(xlabel='Driver confidence set for this cycle',title=title,xticks=[0,.25,.5,.75,1])
        axes[j].set_ylim(0,1 if j==0 else 100)
    axes[0].set_ylabel('Mean own weight')
    axes[1].set_ylabel('Cycles with different decisions (%)')
    axes[-1].legend(fontsize=6)
    figures.save(fig,output,'confidence_intervention')

if __name__=='__main__':
    render()
