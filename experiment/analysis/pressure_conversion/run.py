"""When the car would overrule or pull the driver, what decides whether behavior changes?"""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

import numpy as np

from experiment.config import RUNS_DIR
from experiment.analysis.shared.output import result_directory,write_results
from experiment.analysis.shared.stats import MODES,bins,fmt,grouped,markdown_table,values
from experiment.analysis.shared.table import DIFFICULTIES,load

NAME="pressure_conversion"
UNIT=[0,0.2,0.4,0.6,0.8,1]
FEATURES=dict(
    driver_initial_self_weight=("Driver's initial self-weight",[0,0.2,0.4,0.5,0.6,0.8,1]),
    inbound_trust_mean=("Passengers' trust in the driver",UNIT),
    outbound_trust_mean=("Driver's trust in passengers",UNIT),
    alpha_inbound_mean=("Passengers' homophily when trusting the driver (alpha)",UNIT),
    alpha_outbound_mean=("Driver's homophily when trusting passengers (alpha)",UNIT),
    driver_self_trust=("Driver's initial self-trust",None),
    passenger_count=("Passengers",None),
    track_difficulty=("Track difficulty",None),
    track_persistence=("Track persistence",None),
    solo_regime=("Driver alone",None))


def labelled(table,name,edges):
    if name=="solo_regime":
        fraction=values(table,"baseline_automation_fraction")
        return np.where(fraction==0,0,np.where(fraction==1,2,1)),["always manual","varying","always automated"]
    if name=="track_difficulty":
        return table[name],list(DIFFICULTIES)
    if edges is not None:
        return bins(table[name],edges)
    levels,codes=np.unique(table[name],return_inverse=True)
    return codes.ravel(),[f"{level:g}" for level in levels]


def summarize(table):
    columns={name:values(table,name) for name in (
        "decision_mismatch_cycles","solo_outvoted_cycles","cognition_mismatch_cycles","solo_cognitive_pull_cycles",
        "decision_switched_off","decision_switched_on","solo_outvoted_off_cycles","solo_outvoted_on_cycles",
        "cognition_switched_off","cognition_switched_on")}
    ratios=dict(decision_conversion=("decision_mismatch_cycles","solo_outvoted_cycles"),
                cognition_conversion=("cognition_mismatch_cycles","solo_cognitive_pull_cycles"),
                decision_off_conversion=("decision_switched_off","solo_outvoted_off_cycles"),
                decision_on_conversion=("decision_switched_on","solo_outvoted_on_cycles"))
    everyone=grouped(np.zeros(len(columns["decision_mismatch_cycles"]),dtype=int),["all"],columns,ratios)[0]
    result=dict(comparison_rows=everyone["n"],
        interpretation=("Conversion is pooled simulated changed cycles divided by pooled equal-weight pressure cycles "
                        "(outvoted cycles for decision mode, cognitive-pull cycles for cognition mode). "
                        "This is a ratio of counts, not the fraction of pressure cycles that cause a change: "
                        "the numerator and denominator can include different cycles. Values above 1 mean "
                        "there are more changed cycles than equal-weight pressure cycles. Descriptive; "
                        "neither pressure nor other conditions are held fixed."),
        overall=everyone,features={})
    for name,(label,edges) in FEATURES.items():
        codes,labels=labelled(table,name,edges)
        groups=grouped(codes,labels,columns,ratios)
        spread={}
        for mode in ("decision","cognition"):
            defined=[g[f"{mode}_conversion"] for g in groups if g[f"{mode}_conversion"] is not None]
            spread[mode]=max(defined)-min(defined) if defined else None
        result["features"][name]=dict(label=label,groups=groups,spread=spread)
    return result


def markdown(result,figure):
    o=result["overall"]
    lines=[f"Matched comparisons: **{result['comparison_rows']:,}**.","",result["interpretation"],"",
        f"Overall count ratio: decision **{o['decision_conversion']:.2f}**, cognition **{o['cognition_conversion']:.2f}**. "
        f"The decision-mode off-direction count ratio is **{o['decision_off_conversion']:.2f}** "
        f"and the on-direction count ratio is **{o['decision_on_conversion']:.2f}**; these are not conversion probabilities.","",
        f"![Conversion]({figure})","","### Which conditions change conversion most?","",
        "Spread is the largest minus the smallest group conversion for that condition.","",
        markdown_table(["Condition","Decision spread","Cognition spread"],
            [[f["label"],fmt(f["spread"]["decision"],2),fmt(f["spread"]["cognition"],2)]
             for f in sorted(result["features"].values(),key=lambda f:-max((v for v in f["spread"].values() if v is not None),default=0))]),""]
    for feature in result["features"].values():
        lines+=[f"### {feature['label']}","",markdown_table(
            ["Group","Cars","Outvoted","Decision change","Decision conversion","Off conversion","On conversion",
             "Cognitive pull","Cognition change","Cognition conversion"],
            [[g["group"],f"{g['n']:,}",fmt(g["solo_outvoted_cycles"]),fmt(g["decision_mismatch_cycles"]),
              fmt(g["decision_conversion"],2),fmt(g["decision_off_conversion"],2),fmt(g["decision_on_conversion"],2),
              fmt(g["solo_cognitive_pull_cycles"]),fmt(g["cognition_mismatch_cycles"]),fmt(g["cognition_conversion"],2)]
             for g in feature["groups"]]),""]
    return "\n".join(lines)


def run(directory=None,output=None,runs=RUNS_DIR):
    from experiment.analysis.pressure_conversion.plot import render
    table=load(directory,runs)
    output=Path(output) if output is not None else result_directory(NAME)
    result=summarize(table)
    write_results(NAME,result,markdown(result,"results/figures/conversion.png"),output=output)
    render(output)
    print(f"Saved {output/'summary.json'}; README updated.",flush=True)
    return result


if __name__=="__main__":
    run()
