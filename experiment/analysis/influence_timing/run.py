"""Does the social effect fade, persist or build up during a drive?"""

from pathlib import Path
import sqlite3
import sys
import time

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

import numpy as np

from experiment.config import RUNS_DIR
from experiment.participants import load_participants
from experiment.analysis.shared.output import result_directory,write_results
from experiment.analysis.shared.stats import bins,fmt,grouped,markdown_table,values
from experiment.analysis.shared.table import DIFFICULTIES,EARLY_CYCLES as EARLY,cognitive_pull,load,opposition,solo_runs

NAME="influence_timing"
PRESSURE=dict(decision="solo_outvoted",cognition="solo_cognitive_pull")
UNIT=[0,0.2,0.4,0.6,0.8,1]
# Per-cycle curves need each car's decisions, which the comparison cache does not keep.
# A fixed random sample per driver and track is read from the result archives.
SAMPLE_PER_ARCHIVE=200
SAMPLE_SEED=11
STEPS=100


def timing_columns(table):
    columns={}
    for mode in ("decision","cognition"):
        columns[f"{mode}_early"]=1-values(table,f"{mode}_early_agreement")
        columns[f"{mode}_late"]=1-values(table,f"{mode}_late_agreement")
        early,total=values(table,f"{PRESSURE[mode]}_early_cycles"),values(table,f"{PRESSURE[mode]}_cycles")
        columns[f"{mode}_pressure_early"]=early/EARLY
        columns[f"{mode}_pressure_late"]=(total-early)/(100-EARLY)
    return columns


def with_fade(rows):
    for row in rows:
        for key in ("decision","cognition","decision_pressure","cognition_pressure"):
            row[f"{key}_late_to_early"]=row[f"{key}_late"]/row[f"{key}_early"] if row[f"{key}_early"] else None
    return rows


def summarize(table):
    columns=timing_columns(table)
    n=len(columns["decision_early"])
    result=dict(comparison_rows=n,early_cycles=EARLY,
        interpretation=(f"Mismatch rate is the share of cycles whose automation decision differs from the solo baseline, "
                        f"in cycles 1–{EARLY} (early) and {EARLY+1}–100 (late). Pressure rate is the share of cycles with "
                        "equal-weight pressure in the same window (outvoted cycles for decision mode, cognitive-pull "
                        "cycles for cognition mode). A late/early ratio below 1 means the effect fades; above 1 means "
                        "it builds up. Descriptive."),
        overall=with_fade(grouped(np.zeros(n,dtype=int),["all"],columns))[0],first_divergence={},groups={})
    for mode in ("decision","cognition"):
        first=values(table,f"{mode}_first_divergence_cycle")
        changed=first[np.isfinite(first)]
        result["first_divergence"][mode]=dict(changed_share=float(len(changed)/n),
            quartiles=[float(q) for q in np.quantile(changed,[0.25,0.5,0.75])],
            by_cycle_5=float(np.mean(changed<=5)),by_cycle_20=float(np.mean(changed<=EARLY)))
    pull=values(table,"solo_cognitive_pull_cycles")
    unpressured=pull==0
    cognition=values(table,"cognition_mismatch_cycles")
    result["cognition_without_pull"]=dict(share=float(unpressured.mean()),any_change=float(np.mean(cognition[unpressured]>0)),
        mean_changed_cycles=float(cognition[unpressured].mean()),
        early=float(columns["cognition_early"][unpressured].mean()),late=float(columns["cognition_late"][unpressured].mean()))
    fraction=values(table,"baseline_automation_fraction")
    groupings=dict(
        alpha_outbound_mean=("Driver's homophily when trusting passengers (alpha)",*bins(table["alpha_outbound_mean"],UNIT)),
        outbound_trust_mean=("Driver's trust in passengers",*bins(table["outbound_trust_mean"],UNIT)),
        passenger_count=("Passengers",table["passenger_count"]-1,[str(k) for k in range(1,6)]),
        track_difficulty=("Track difficulty",table["track_difficulty"],list(DIFFICULTIES)),
        solo_regime=("Driver alone",np.where(fraction==0,0,np.where(fraction==1,2,1)),["always manual","varying","always automated"]))
    for name,(label,codes,labels) in groupings.items():
        result["groups"][name]=dict(label=label,groups=with_fade(grouped(codes,labels,columns)))
    return result


def decisions(blob,steps=STEPS):
    return np.unpackbits(np.frombuffer(blob,dtype=np.uint8))[:steps].astype(bool)


def cycle_profiles(table,runs):
    """Per-cycle share of sampled cars that differ from solo, and that face equal-weight pressure, by difficulty."""
    people,tracks=table["_drivers"],table["_tracks"]
    random=np.random.default_rng(SAMPLE_SEED)
    archive=table["driver"].astype(np.int64)*len(tracks)+table["track"]
    order=np.argsort(archive,kind="stable")
    keys,starts=np.unique(archive[order],return_index=True)
    sample=np.concatenate([random.choice(part,min(SAMPLE_PER_ARCHIVE,len(part)),replace=False)
                           for part in np.split(order,starts[1:])])
    sample.sort()
    print(f"Reading per-cycle decisions for {len(sample):,} sampled cars...",flush=True)
    changed={mode:np.zeros((len(sample),STEPS),dtype=bool) for mode in ("decision","cognition")}
    position={int(row):i for i,row in enumerate(sample)}
    reported=time.monotonic()
    for done,key in enumerate(np.unique(archive[sample]),1):
        rows=sample[archive[sample]==key]
        driver,track=people[key//len(tracks)],tracks[key%len(tracks)]
        db=sqlite3.connect((Path(runs)/f"{driver}_{track}.sqlite").resolve().as_uri()+"?mode=ro",uri=True)
        try:
            solo={start:decisions(blob) for start,blob in db.execute(
                "SELECT start,automation_on FROM results WHERE composition=0 AND variant='baseline'")}
            for row in rows:
                composition,start=int(table["composition"][row]),int(table["start"][row])
                for variant,blob in db.execute("SELECT variant,automation_on FROM results WHERE composition=? AND start=? "
                                               "AND variant IN ('decision','cognition')",(composition,start)):
                    changed[variant][position[int(row)]]=decisions(blob)!=solo[start]
        finally:
            db.close()
        if time.monotonic()-reported>=5:
            print(f"  Read {done:,} of {len(keys):,} archives",flush=True)
            reported=time.monotonic()
    print("Measuring per-cycle pressure from the solo baselines...",flush=True)
    participants=load_participants()
    solo,cognition,_=solo_runs(runs,people,tracks,int(table["start"].max())+1,STEPS)
    driver,track,start=table["driver"][sample],table["track"][sample],table["start"][sample]
    seats=table["passenger_seats"][sample].astype(np.int64)
    valid=seats>=0
    safe=np.where(valid,seats,0)
    own=solo[driver,track,start]
    _,outvoted=opposition(own,solo[safe,track[:,None],start[:,None]],valid)
    pulled=cognitive_pull([participants[p]["tree"] for p in people],driver,own,cognition[driver,track,start],
                          cognition[safe,track[:,None],start[:,None]],valid)
    difficulty=table["track_difficulty"][sample]
    profiles=dict(cars=np.bincount(difficulty,minlength=len(DIFFICULTIES)))
    for name,value in dict(decision_change=changed["decision"],cognition_change=changed["cognition"],
                           outvoted=outvoted,cognitive_pull=pulled).items():
        profiles[name]=np.stack([value[difficulty==level].mean(axis=0) for level in range(len(DIFFICULTIES))])
    return profiles,dict(per_archive=SAMPLE_PER_ARCHIVE,seed=SAMPLE_SEED,cars=int(len(sample)))


def markdown(result,figure):
    o=result["overall"]
    lines=[f"Matched comparisons: **{result['comparison_rows']:,}**.","",result["interpretation"],"",
        markdown_table(["Mode","Early mismatch","Late mismatch","Late / early","Early pressure","Late pressure","Pressure late / early"],
            [[mode.title(),fmt(o[f"{mode}_early"],1,True),fmt(o[f"{mode}_late"],1,True),fmt(o[f"{mode}_late_to_early"],2),
              fmt(o[f"{mode}_pressure_early"],1,True),fmt(o[f"{mode}_pressure_late"],1,True),fmt(o[f"{mode}_pressure_late_to_early"],2)]
             for mode in ("decision","cognition")]),"",
        f"![Timing]({figure})","",
        f"Per-cycle curves use a random sample of {result['cycle_sample']['cars']:,} cars "
        f"({result['cycle_sample']['per_archive']} per driver and track, seed {result['cycle_sample']['seed']}):","",
        "![Cycle by cycle](results/figures/cycle_dynamics.png)","","### When does the first change happen?","",
        markdown_table(["Mode","Cars with any change","First change: quartiles","By cycle 5","By cycle 20"],
            [[mode.title(),fmt(f["changed_share"],1,True)," / ".join(f"{q:g}" for q in f["quartiles"]),
              fmt(f["by_cycle_5"],1,True),fmt(f["by_cycle_20"],1,True)] for mode,f in result["first_divergence"].items()]),""]
    c=result["cognition_without_pull"]
    lines+=["### Cognition-level changes the equal-weight snapshot does not predict","",
        f"In **{100*c['share']:.1f}%** of cars the mean of the occupants' solo cognition never flips the driver's tree. "
        f"Cognition influence still changes **{100*c['any_change']:.1f}%** of them (mean **{c['mean_changed_cycles']:.2f}** cycles; "
        f"early mismatch {100*c['early']:.1f}%, late {100*c['late']:.1f}%). Unequal trust weights and feedback "
        "can both produce changes absent from this equal-weight snapshot. Mixed cognition becomes the next "
        "cycle's state, allowing effects to accumulate; this comparison does not isolate that mechanism.",""]
    for group in result["groups"].values():
        lines+=[f"### {group['label']}","",markdown_table(
            ["Group","Cars","Decision early","Decision late","Decision late / early","Outvoted late / early",
             "Cognition early","Cognition late","Cognition late / early","Pull late / early"],
            [[g["group"],f"{g['n']:,}",fmt(g["decision_early"],1,True),fmt(g["decision_late"],1,True),fmt(g["decision_late_to_early"],2),
              fmt(g["decision_pressure_late_to_early"],2),fmt(g["cognition_early"],1,True),fmt(g["cognition_late"],1,True),
              fmt(g["cognition_late_to_early"],2),fmt(g["cognition_pressure_late_to_early"],2)]
             for g in group["groups"]]),""]
    return "\n".join(lines)


def run(directory=None,output=None,runs=RUNS_DIR):
    from experiment.analysis.influence_timing.plot import render
    table=load(directory,runs)
    output=Path(output) if output is not None else result_directory(NAME)
    result=summarize(table)
    profiles,result["cycle_sample"]=cycle_profiles(table,runs)
    output.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(output/"cycles.npz",difficulties=np.array(DIFFICULTIES),**profiles)
    write_results(NAME,result,markdown(result,"results/figures/timing.png"),output=output)
    render(output)
    print(f"Saved {output/'summary.json'} and {output/'cycles.npz'}; README updated.",flush=True)
    return result


if __name__=="__main__":
    run()
