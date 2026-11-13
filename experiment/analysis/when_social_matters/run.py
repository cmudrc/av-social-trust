"""When does the social layer change the driver's behavior compared with driving alone?"""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

import numpy as np

from experiment.config import RUNS_DIR
from experiment.analysis.shared.output import result_directory,write_results
from experiment.analysis.shared.stats import DESIGN,LABELS,MODES,cycle_bins,fmt,grouped,markdown_table,values,variance_shares
from experiment.analysis.shared.table import load

NAME="when_social_matters"
PRESSURE=("solo_outvoted_cycles","solo_cognitive_pull_cycles")
EXPLANATIONS=dict(
    scenario=("Scenario parameters",DESIGN),
    scenario_participant=("Scenario + participant",(*DESIGN,"driver")),
    pressure=("Solo-counterfactual pressure",PRESSURE),
    everything=("All of the above + solo automation",(*DESIGN,"driver",*PRESSURE,"baseline_automation_fraction")))
NOTABLE=10


def summarize(table):
    result=dict(comparison_rows=len(table["driver"]),notable_cycles=NOTABLE,
        interpretation=("R² is the variance in changed cycles explained by a linear model with participant indicators "
                        "and categorical passenger count and track difficulty. Unique R² is the loss when one input is "
                        "dropped from the full model. Associations across the simulated grid, not causal estimates."),
        modes={})
    for mode,spec in MODES.items():
        print(f"Fitting explanations for {mode}-level influence...",flush=True)
        change=values(table,spec["change"])
        fits={key:variance_shares(table,spec["change"],names) for key,(_,names) in EXPLANATIONS.items()}
        pressure=values(table,spec["pressure"])
        codes,labels=cycle_bins(pressure,(0,1,5,10,20,40,101))
        rule=grouped(codes,labels,dict(changed=change,notable=(change>=NOTABLE).astype(float),
                                       any_change=(change>0).astype(float)))
        result["modes"][mode]=dict(label=spec["label"],pressure=spec["pressure"],
            r2={key:fit["r2"] for key,fit in fits.items()},
            unique=dict(sorted(fits["everything"]["unique"].items(),key=lambda item:-item[1])),
            by_pressure=rule,share_without_pressure=float(np.mean(pressure==0)))
    return result


def markdown(result,figure):
    lines=[f"Matched comparisons: **{result['comparison_rows']:,}**.","",result["interpretation"],"",
        "### Which explanation accounts for the change?","",
        markdown_table(["Explanation",*(m["label"] for m in result["modes"].values())],
            [[label,*(fmt(m["r2"][key],3) for m in result["modes"].values())] for key,(label,_) in EXPLANATIONS.items()]),"",
        f"![Explanations]({figure})",""]
    for mode in result["modes"].values():
        top=list(mode["unique"].items())[:8]
        lines+=[f"### {mode['label']}: unique contribution in the full model","",
            markdown_table(["Input","Unique R²"],[[LABELS[name],fmt(value,4)] for name,value in top]),"",
            f"### {mode['label']}: change by its own pressure","",
            f"Cars with no pressure: **{100*mode['share_without_pressure']:.1f}%**.","",
            markdown_table(["Pressure cycles","Cars","Mean changed cycles","Any change",f"≥{result['notable_cycles']} changed cycles"],
                [[g["group"],f"{g['n']:,}",fmt(g["changed"]),fmt(g["any_change"],1,True),fmt(g["notable"],1,True)] for g in mode["by_pressure"]]),""]
    return "\n".join(lines)


def run(directory=None,output=None,runs=RUNS_DIR):
    from experiment.analysis.when_social_matters.plot import render
    table=load(directory,runs)
    output=Path(output) if output is not None else result_directory(NAME)
    result=summarize(table)
    write_results(NAME,result,markdown(result,"results/figures/explanations.png"),output=output)
    render(output)
    print(f"Saved {output/'summary.json'}; README updated.",flush=True)
    return result


if __name__=="__main__":
    run()
