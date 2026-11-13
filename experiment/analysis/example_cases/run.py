"""Two example cars: one where solo, decision- and cognition-level driving agree, one where they do not."""

import json
from pathlib import Path
import sqlite3
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

import numpy as np

from experiment.config import RUNS_DIR,Settings
from experiment.participants import load_participants
from experiment.results import unpack_trajectory
from experiment.tracks.generate_tracks import load_tracks
from experiment.model import STATE_NAMES
from experiment.analysis.shared.output import result_directory,write_results
from experiment.analysis.shared.stats import values
from experiment.analysis.shared.table import load,passengers

NAME="example_cases"
# Set to explicit cars to override the automatic choice, for example
# CASES=dict(agree=("P23","normal_p2_0",1234,5),disagree=("P23","normal_p2_0",987,3))  # driver, track, composition, start
CASES=None
# Automatic choice: a driver whose solo choices vary, in a large car.
SOLO_AUTOMATION=(0.2,0.8)
MIN_SOLO_SWITCHES=4
PASSENGERS=(4,5)               # Larger cars are preferred when both kinds of example exist.
AGREE_MIN_SOLO_DISAGREEMENT=10  # The passengers would decide differently, yet nothing changes.
DISAGREE_MAX_CHANGE=70          # Avoid trivial near-complete inversions.
SAME_PASSENGER_COUNT=True       # Both cars carry the same number of passengers (not necessarily the same people).


def choose(table):
    """Pick an agreeing and a disagreeing car with the same driver and track (and passenger count, if set)."""
    d,c,x=(values(table,f"{m}_mismatch_cycles") for m in ("decision","cognition","cross"))
    fraction=values(table,"baseline_automation_fraction")
    readable=((fraction>=SOLO_AUTOMATION[0])&(fraction<=SOLO_AUTOMATION[1])
              &(values(table,"driver_solo_switches")>=MIN_SOLO_SWITCHES)&np.isin(table["passenger_count"],PASSENGERS))
    agree_score=d+c+x
    agree=readable&(values(table,"solo_disagreement_cycles")>=AGREE_MIN_SOLO_DISAGREEMENT)
    disagree_score=np.minimum(np.minimum(d,c),x)
    disagree=readable&(np.maximum(np.maximum(d,c),x)<=DISAGREE_MAX_CHANGE)
    key=table["driver"].astype(np.int64)*1000+table["track"]
    if SAME_PASSENGER_COUNT:
        key=key*10+table["passenger_count"]
    best=None
    for pair in np.intersect1d(np.unique(key[agree]),np.unique(key[disagree])):
        a=np.flatnonzero(agree&(key==pair))
        b=np.flatnonzero(disagree&(key==pair))
        i,j=a[np.argmin(agree_score[a])],b[np.argmax(disagree_score[b])]
        rank=(int(table["passenger_count"][j]),disagree_score[j]-agree_score[i],-pair)
        if best is None or rank>best[0]:
            best=(rank,i,j)
    if best is None:
        raise ValueError("No driver and track has both kinds of example; relax the selection constants "
                         "(for example SAME_PASSENGER_COUNT=False)")
    return dict(agree=best[1],disagree=best[2])


def row_index(table,driver,track,composition,start):
    people,tracks=table["_drivers"],table["_tracks"]
    match=np.flatnonzero((table["driver"]==people.index(driver))&(table["track"]==tracks.index(track))
                         &(table["composition"]==composition)&(table["start"]==start))
    if not len(match):
        raise KeyError(f"No matched comparison for {driver} {track} composition {composition} start {start}")
    return match[0]


def trajectory(runs,person,track,composition,start,variant):
    db=sqlite3.connect((Path(runs)/f"{person}_{track}.sqlite").resolve().as_uri()+"?mode=ro",uri=True)
    try:
        row=db.execute("SELECT metadata,trajectory FROM results WHERE composition=? AND start=? AND variant=?",
                       (composition,start,variant)).fetchone()
    finally:
        db.close()
    if row is None:
        raise KeyError((person,track,composition,start,variant))
    return json.loads(row[0]),unpack_trajectory(row[1])


def splits(node):
    if "feature_index" not in node:
        return []
    return [(STATE_NAMES[node["feature_index"]],float(node["threshold"]))]+splits(node["left"])+splits(node["right"])


def extract(table,index,runs,participants,complexity):
    people,tracks=table["_drivers"],table["_tracks"]
    driver,track=people[table["driver"][index]],tracks[table["track"][index]]
    composition,start=int(table["composition"][index]),int(table["start"][index])
    riders=passengers(people,driver,composition)
    _,solo=trajectory(runs,driver,track,0,start,"baseline")
    _,decision=trajectory(runs,driver,track,composition,start,"decision")
    meta,cognition=trajectory(runs,driver,track,composition,start,"cognition")
    if tuple(meta["passengers"])!=riders:
        raise ValueError("Decoded passengers disagree with the archive")
    # Decision influence never changes cognition, so its driver state equals the solo run.
    if not np.allclose(decision["social_cognition"][:,0],solo["private_cognition"][:,0]):
        raise ValueError("Decision-mode driver cognition differs from the solo run")
    rider_solo=[trajectory(runs,p,track,0,start,"baseline")[1]["automation_on"] for p in riders]
    arrays=dict(complexity=np.array([s.task_complexity for s in complexity[track]]),
        solo_on=solo["automation_on"],decision_on=decision["automation_on"],cognition_on=cognition["automation_on"],
        solo_cognition=solo["private_cognition"][:,0],cognition_cognition=cognition["social_cognition"][:,0],
        decision_opinion=decision["final_opinions"][:,0],
        decision_self_weight=decision["influence_matrix"][:,0,0],cognition_self_weight=cognition["influence_matrix"][:,0,0],
        passenger_solo_on=np.array(rider_solo,dtype=bool),
        passenger_cognition_on=cognition["final_decisions"][:,1:].T.astype(bool))
    tree=participants[driver]
    info=dict(driver=driver,passengers=list(riders),track=track,composition=composition,start=start,
        modeled_states=[STATE_NAMES[i] for i in tree["state_indices"]],tree_splits=splits(tree["tree"]),
        changed_cycles=dict(decision_vs_solo=int(table["decision_mismatch_cycles"][index]),
                            cognition_vs_solo=int(table["cognition_mismatch_cycles"][index]),
                            decision_vs_cognition=int(table["cross_mismatch_cycles"][index])),
        outvoted_cycles=int(table["solo_outvoted_cycles"][index]),cognitive_pull_cycles=int(table["solo_cognitive_pull_cycles"][index]),
        solo_disagreement_cycles=int(table["solo_disagreement_cycles"][index]))
    return info,arrays


def markdown(result,figure):
    lines=["Two cars with the same driver and track. In the first, the passengers would sometimes decide "
           "differently, yet both influence modes leave the driver's choices almost unchanged. In the second, "
           "solo, decision-level and cognition-level driving all differ.","",
           "The driver's automation decision in each setting, over the track's task complexity:","",
           "![Example cases, simple](results/figures/example_cases_simple.png)","",
           "The same cars with the driver's cognition, the car's vote and every occupant's timeline:","",
           f"![Example cases]({figure})","",
           "| Case | Driver | Passengers | Track | Composition / start | Decision ≠ solo | Cognition ≠ solo | Decision ≠ cognition | Outvoted | Cognitive pull |",
           "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for label,case in result["cases"].items():
        changed=case["changed_cycles"]
        lines.append(f"| {label} | {case['driver']} | {', '.join(case['passengers'])} | {case['track']} | "
                     f"{case['composition']} / {case['start']} | {changed['decision_vs_solo']} | {changed['cognition_vs_solo']} | "
                     f"{changed['decision_vs_cognition']} | {case['outvoted_cycles']} | {case['cognitive_pull_cycles']} |")
    lines+=["","Trajectories are saved in `results/cases.npz`; redraw with plot.py."]
    return "\n".join(lines)


def run(directory=None,output=None,runs=RUNS_DIR):
    from experiment.analysis.example_cases.plot import render
    table=load(directory,runs)
    output=Path(output) if output is not None else result_directory(NAME)
    chosen=({label:row_index(table,*car) for label,car in CASES.items()} if CASES else choose(table))
    participants=load_participants()
    _,complexity=load_tracks(Settings())
    result=dict(selection=("manual" if CASES else "automatic"),cases={})
    arrays={}
    for label,index in chosen.items():
        info,data=extract(table,index,runs,participants,complexity)
        result["cases"][label]=info
        arrays.update({f"{label}__{name}":value for name,value in data.items()})
        print(f"{label}: {info['driver']} with {', '.join(info['passengers'])} on {info['track']} "
              f"(composition {info['composition']}, start {info['start']}): {info['changed_cycles']}",flush=True)
    output.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(output/"cases.npz",**arrays)
    write_results(NAME,result,markdown(result,"results/figures/example_cases.png"),output=output)
    render(output)
    print(f"Saved {output/'cases.npz'} and figures; README updated.",flush=True)
    return result


if __name__=="__main__":
    run()
