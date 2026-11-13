"""Which participants are affected most by the social layer, and which model properties explain it?"""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

import numpy as np

from experiment.config import RUNS_DIR
from experiment.participants import load_participants
from experiment.analysis.shared.output import result_directory,write_results
from experiment.analysis.shared.stats import fmt,markdown_table,spearman,values
from experiment.analysis.shared.table import load
from experiment.model import STATE_NAMES

NAME="participant_susceptibility"
PROPERTIES=dict(memory="Cognitive memory (largest absolute eigenvalue of A)",input_sensitivity="Track-input sensitivity (largest absolute B)",
                modeled_states="Modeled cognitive states",tree_leaves="Decision-tree leaves")
MEASURES=dict(decision_change="Decision change",cognition_change="Cognition change",
              decision_conversion="Decision conversion",cognition_conversion="Cognition conversion",
              solo_automation="Solo automation",solo_switches="Solo switches",
              passenger_decision_effect="Decision change caused as passenger",
              passenger_cognition_effect="Cognition change caused as passenger")


def leaves(node):
    return 1 if "feature_index" not in node else leaves(node["left"])+leaves(node["right"])


def model_properties(person):
    return dict(memory=float(np.max(np.abs(np.linalg.eigvals(person["A"])))),
                input_sensitivity=float(np.max(np.abs(person["B"]))),
                modeled_states=int(len(person["state_indices"])),tree_leaves=leaves(person["tree"]),
                states=[STATE_NAMES[i] for i in person["state_indices"]])


def summarize(table,participants):
    people=table["_drivers"]
    driver=table["driver"]
    decision,cognition=values(table,"decision_mismatch_cycles"),values(table,"cognition_mismatch_cycles")
    outvoted,pull=values(table,"solo_outvoted_cycles"),values(table,"solo_cognitive_pull_cycles")
    seats=table["passenger_seats"]
    count=np.bincount(driver,minlength=len(people))
    sums=lambda x:np.bincount(driver,weights=x,minlength=len(people))
    totals={name:sums(x) for name,x in dict(decision=decision,cognition=cognition,outvoted=outvoted,pull=pull,
            solo_automation=values(table,"baseline_automation_fraction"),solo_switches=values(table,"driver_solo_switches")).items()}
    rows=[]
    for i,person in enumerate(people):
        riding=(seats==i).any(axis=1)
        row=dict(participant=person,cars_as_driver=int(count[i]),cars_as_passenger=int(riding.sum()),
            solo_automation=totals["solo_automation"][i]/count[i],solo_switches=totals["solo_switches"][i]/count[i],
            outvoted=totals["outvoted"][i]/count[i],cognitive_pull=totals["pull"][i]/count[i],
            decision_change=totals["decision"][i]/count[i],cognition_change=totals["cognition"][i]/count[i],
            decision_conversion=totals["decision"][i]/totals["outvoted"][i] if totals["outvoted"][i] else None,
            cognition_conversion=totals["cognition"][i]/totals["pull"][i] if totals["pull"][i] else None,
            passenger_decision_effect=float(decision[riding].mean()),passenger_cognition_effect=float(cognition[riding].mean()),
            **model_properties(participants[person]))
        rows.append(row)
    correlations={}
    for measure in MEASURES:
        y=np.array([np.nan if r[measure] is None else r[measure] for r in rows],dtype=float)
        correlations[measure]={prop:spearman(np.array([r[prop] for r in rows],dtype=float),y) for prop in PROPERTIES}
        correlations[measure]["outvoted"]=spearman(np.array([r["outvoted"] for r in rows]),y)
        correlations[measure]["cognitive_pull"]=spearman(np.array([r["cognitive_pull"] for r in rows]),y)
    return dict(participants=len(rows),comparison_rows=int(count.sum()),
        interpretation=(f"Each participant is summarized as a driver and as a passenger. Spearman correlations use "
                        f"{len(rows)} participants, so they are exploratory. Model properties come from the fitted A, B and tree."),
        rows=rows,correlations=correlations)


def markdown(result,figure):
    lines=[f"Participants: **{result['participants']}**; matched comparisons: **{result['comparison_rows']:,}**.","",
        result["interpretation"],"",f"![Participants]({figure})","",
        "### What goes with susceptibility? (Spearman ρ across participants)","",
        markdown_table(["Measure","Outvoted","Cognitive pull",*PROPERTIES.values()],
            [[MEASURES[m],*[fmt(c[p],2) for p in ("outvoted","cognitive_pull",*PROPERTIES)]] for m,c in result["correlations"].items()]),"",
        "### Participants","",
        markdown_table(["Participant","Solo automation","Solo switches","Outvoted","Decision change","Decision conversion",
                        "Cognitive pull","Cognition change","Cognition conversion","As passenger: decision","As passenger: cognition",
                        "Memory","Input sensitivity","States"],
            [[r["participant"],fmt(r["solo_automation"],1,True),fmt(r["solo_switches"]),fmt(r["outvoted"]),fmt(r["decision_change"]),
              fmt(r["decision_conversion"],2),fmt(r["cognitive_pull"]),fmt(r["cognition_change"]),fmt(r["cognition_conversion"],2),
              fmt(r["passenger_decision_effect"]),fmt(r["passenger_cognition_effect"]),fmt(r["memory"],3),fmt(r["input_sensitivity"],3),
              ", ".join(r["states"])] for r in result["rows"]])]
    return "\n".join(lines)


def run(directory=None,output=None,runs=RUNS_DIR):
    from experiment.analysis.participant_susceptibility.plot import render
    table=load(directory,runs)
    output=Path(output) if output is not None else result_directory(NAME)
    result=summarize(table,load_participants())
    write_results(NAME,result,markdown(result,"results/figures/participants.png"),output=output)
    render(output)
    print(f"Saved {output/'summary.json'}; README updated.",flush=True)
    return result


if __name__=="__main__":
    run()
