"""Does the social layer change behavior only when the occupants would decide differently alone?"""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

import numpy as np

from experiment.config import RUNS_DIR
from experiment.analysis.shared.output import result_directory,write_results
from experiment.analysis.shared.stats import MODES,cycle_bins,fmt,grouped,markdown_table,spearman,values
from experiment.analysis.shared.table import load

NAME="occupant_disagreement"
CANDIDATES=dict(
    solo_disagreement_cycles="Cycles with at least one passenger deciding differently alone",
    solo_unanimous_disagreement_cycles="Cycles with every passenger deciding differently alone",
    solo_opposition_share="Mean share of passengers deciding differently alone",
    solo_outvoted_cycles="Cycles an equal-weight vote of the car overrules the driver",
    solo_cognitive_pull_cycles="Cycles the driver's tree flips on the car's mean cognition",
    passenger_solo_automation="Passengers' solo automation fraction",
    baseline_automation_fraction="Driver's solo automation fraction",
    driver_solo_switches="Driver's solo decision switches")


def summarize(table):
    decision,cognition=values(table,MODES["decision"]["change"]),values(table,MODES["cognition"]["change"])
    disagreement=values(table,"solo_disagreement_cycles")
    outvoted,pull=values(table,"solo_outvoted_cycles"),values(table,"solo_cognitive_pull_cycles")
    result=dict(comparison_rows=len(decision),
        interpretation=("Solo choices come from each occupant's own baseline at the same track and start. "
                        "Decision-mode votes equal these solo choices exactly. Associations are descriptive."),
        means=dict(decision_changed_cycles=decision.mean(),cognition_changed_cycles=cognition.mean(),
                   solo_disagreement_cycles=disagreement.mean(),solo_outvoted_cycles=outvoted.mean(),
                   solo_cognitive_pull_cycles=pull.mean()),
        decision_changes_beyond_disagreement=int(np.count_nonzero(decision>disagreement)),
        correlations={name:dict(label=label,decision=spearman(values(table,name),decision),
                                cognition=spearman(values(table,name),cognition)) for name,label in CANDIDATES.items()})
    conditions=dict(no_disagreement=disagreement==0,not_outvoted=outvoted==0,no_cognitive_pull=pull==0,
                    neither_outvoted_nor_pulled=(outvoted==0)&(pull==0))
    result["without_pressure"]={name:dict(share=float(mask.mean()),
        **{f"{mode}_{stat}":float(fn(change[mask])) if mask.any() else None
           for mode,change in (("decision",decision),("cognition",cognition))
           for stat,fn in (("mean",np.mean),("any_change",lambda v:np.mean(v>0)))})
        for name,mask in conditions.items()}
    columns=dict(decision=decision,cognition=cognition,decision_10=(decision>=10).astype(float),cognition_10=(cognition>=10).astype(float))
    result["by_outvoted"]=grouped(*cycle_bins(outvoted),dict(columns,pressure=outvoted))
    result["by_cognitive_pull"]=grouped(*cycle_bins(pull),dict(columns,pressure=pull))
    count=table["passenger_count"]
    result["by_passenger_count"]=grouped(count-1,[str(k) for k in range(1,6)],
        dict(disagreement=disagreement,unanimous=values(table,"solo_unanimous_disagreement_cycles"),
             outvoted=outvoted,pull=pull,decision=decision,cognition=cognition),
        ratios=dict(decision_per_outvoted=("decision","outvoted"),cognition_per_pull=("cognition","pull")))
    return result


def markdown(result,figure):
    m=result["means"]
    lines=[f"Matched comparisons: **{result['comparison_rows']:,}**.","",result["interpretation"],"",
        f"Decision-mode changes outside cycles of solo disagreement: **{result['decision_changes_beyond_disagreement']:,}** comparisons "
        "(the model guarantees zero: a driver can only be overruled when someone in the car would decide differently).","",
        f"On average the car contains **{m['solo_disagreement_cycles']:.1f}** cycles of solo disagreement, "
        f"**{m['solo_outvoted_cycles']:.1f}** cycles where an equal-weight vote would overrule the driver and "
        f"**{m['solo_cognitive_pull_cycles']:.1f}** cycles where the car's mean cognition would flip the driver's tree. "
        f"Simulated changes average **{m['decision_changed_cycles']:.1f}** (decision) and **{m['cognition_changed_cycles']:.1f}** (cognition) cycles.","",
        "### Which measure tracks the change? (Spearman ρ)","",
        markdown_table(["Measure","Decision / solo","Cognition / solo"],
            [[c["label"],fmt(c["decision"],2),fmt(c["cognition"],2)] for c in result["correlations"].values()]),"",
        "### What happens without social pressure?","",
        markdown_table(["Condition","Share of cars","Decision mean","Decision any change","Cognition mean","Cognition any change"],
            [[name.replace("_"," "),fmt(r["share"],1,True),fmt(r["decision_mean"],2),fmt(r["decision_any_change"],1,True),
              fmt(r["cognition_mean"],2),fmt(r["cognition_any_change"],1,True)] for name,r in result["without_pressure"].items()]),"",
        f"![Change versus pressure]({figure})","",
        "Every car, by its pressure and its change. Each mode lines up with its own pressure (diagonal panels), "
        "not with the other mode's:","","![Pressure heatmaps](results/figures/pressure_heatmaps.png)",""]
    for key,title in (("by_outvoted","Changed cycles by equal-weight outvoted cycles"),("by_cognitive_pull","Changed cycles by cognitive-pull cycles")):
        lines+=[f"### {title}","",markdown_table(["Cycles","Cars","Decision mean","Decision ≥10","Cognition mean","Cognition ≥10"],
            [[g["group"],f"{g['n']:,}",fmt(g["decision"]),fmt(g["decision_10"],1,True),fmt(g["cognition"]),fmt(g["cognition_10"],1,True)]
             for g in result[key]]),""]
    lines+=["### Passenger count works through pressure","",markdown_table(
        ["Passengers","Any disagreement","All disagree","Outvoted","Decision change","Change / outvoted","Cognitive pull","Cognition change","Change / pull"],
        [[g["group"],fmt(g["disagreement"]),fmt(g["unanimous"]),fmt(g["outvoted"]),fmt(g["decision"]),fmt(g["decision_per_outvoted"],2),
          fmt(g["pull"]),fmt(g["cognition"]),fmt(g["cognition_per_pull"],2)] for g in result["by_passenger_count"]])]
    return "\n".join(lines)


def histograms(table):
    """Counts of cars by (pressure cycles, changed cycles) for every mode and pressure pairing."""
    counts={}
    for mode,spec in MODES.items():
        change=table[spec["change"]].astype(np.int64)
        for pressure in ("solo_outvoted_cycles","solo_cognitive_pull_cycles"):
            cells=table[pressure].astype(np.int64)*101+change
            counts[f"{mode}__{pressure}"]=np.bincount(cells,minlength=101*101).reshape(101,101)
    return counts


def run(directory=None,output=None,runs=RUNS_DIR):
    from experiment.analysis.occupant_disagreement.plot import render
    table=load(directory,runs)
    output=Path(output) if output is not None else result_directory(NAME)
    result=summarize(table)
    output.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(output/"pressure_change.npz",**histograms(table))
    write_results(NAME,result,markdown(result,"results/figures/change_vs_pressure.png"),output=output)
    render(output)
    print(f"Saved {output/'summary.json'} and {output/'pressure_change.npz'}; README updated.",flush=True)
    return result


if __name__=="__main__":
    run()
