"""When do decision- and/or cognition-level driving look like driving alone, and what predicts it?"""

import gzip
from pathlib import Path
import sys
import time

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

import numpy as np
from scipy.stats import rankdata

from experiment.config import RUNS_DIR
from experiment.analysis.shared import rules
from experiment.analysis.shared.output import result_directory,write_results
from experiment.analysis.shared.stats import DESIGN,LABELS,cycle_bins,fmt,markdown_table,values
from experiment.analysis.shared.table import DIFFICULTIES,load

NAME="baseline_similarity"
# A mode "looks like driving alone" when at most this many of the 100 cycles differ from the solo run.
ALIKE_MAX_CHANGED=5
SENSITIVITY=(0,5,10,20)
CATEGORIES=("both alike","only decision alike","only cognition alike","neither alike")
PRESSURE_EDGES=(0,1,5,10,20,40,101)
EXPORT_DATASET=True  # Write results/similarity_dataset.csv.gz (one row per car; a few minutes).
PREDICTORS=(*DESIGN,"baseline_automation_fraction","driver_solo_switches","passenger_solo_automation",
            "solo_disagreement_cycles","solo_outvoted_cycles","solo_cognitive_pull_cycles")
TREE_DEPTH=3
TREE_SEED=5


def categories(decision_changed,cognition_changed,limit=ALIKE_MAX_CHANGED):
    decision,cognition=decision_changed<=limit,cognition_changed<=limit
    return np.where(decision&cognition,0,np.where(decision,1,np.where(cognition,2,3)))


def shares(codes,groups,labels):
    """Category shares (rows: groups, columns: categories) and group sizes."""
    counts=np.bincount(groups*len(CATEGORIES)+codes,minlength=len(labels)*len(CATEGORIES)).reshape(len(labels),len(CATEGORIES))
    sizes=counts.sum(axis=1)
    return [dict(group=label,n=int(size),**{c:float(v/size) for c,v in zip(CATEGORIES,row)})
            for label,size,row in zip(labels,sizes,counts) if size]


def auc(ranks,positive):
    """Area under the ROC curve of one feature for a binary outcome, from precomputed ranks."""
    n_pos=int(positive.sum())
    n_neg=len(positive)-n_pos
    if not n_pos or not n_neg:
        return None
    return float((ranks[positive].sum()-n_pos*(n_pos+1)/2)/(n_pos*n_neg))


def export(table,path,codes):
    """One row per car with its settings, solo-counterfactual pressure and similarity to driving alone."""
    people,tracks=table["_drivers"],table["_tracks"]
    seats=table["passenger_seats"]
    numeric=dict(composition=table["composition"],start=table["start"],passenger_count=table["passenger_count"],
        **{name:table[name] for name in DESIGN if name not in ("track_difficulty","passenger_count")},
        driver_solo_automation=table["baseline_automation_fraction"],driver_solo_switches=table["driver_solo_switches"],
        passenger_solo_automation=table["passenger_solo_automation"],solo_disagreement_cycles=table["solo_disagreement_cycles"],
        outvoted_cycles=table["solo_outvoted_cycles"],cognitive_pull_cycles=table["solo_cognitive_pull_cycles"],
        decision_changed_cycles=table["decision_mismatch_cycles"],cognition_changed_cycles=table["cognition_mismatch_cycles"],
        decision_cognition_changed_cycles=table["cross_mismatch_cycles"])
    header=["driver","track","track_difficulty","passengers",*numeric,"decision_agreement","cognition_agreement",
            "decision_cognition_agreement","decision_alike","cognition_alike","category"]
    print(f"Writing the per-car dataset to {path} ...",flush=True)
    started=reported=time.monotonic()
    with gzip.open(path,"wt",compresslevel=5,newline="") as stream:
        stream.write(",".join(header)+"\n")
        for begin in range(0,len(codes),250_000):
            part=slice(begin,begin+250_000)
            rows=zip(*([people[i] for i in table["driver"][part]],[tracks[i] for i in table["track"][part]],
                       [DIFFICULTIES[i] for i in table["track_difficulty"][part]],
                       [";".join(people[s] for s in row if s>=0) for row in seats[part]],
                       *[np.round(values[part].astype(np.float64),6).tolist() if values.dtype.kind=="f" else values[part].tolist()
                         for values in numeric.values()],
                       *[np.round(1-table[f"{pair}_mismatch_cycles"][part]/100,2).tolist() for pair in ("decision","cognition","cross")],
                       (table["decision_mismatch_cycles"][part]<=ALIKE_MAX_CHANGED).astype(int).tolist(),
                       (table["cognition_mismatch_cycles"][part]<=ALIKE_MAX_CHANGED).astype(int).tolist(),
                       [CATEGORIES[c] for c in codes[part]]))
            stream.write("".join(",".join(map(str,row))+"\n" for row in rows))
            if time.monotonic()-reported>=5:
                print(f"  Wrote {min(begin+250_000,len(codes)):,}/{len(codes):,} cars",flush=True)
                reported=time.monotonic()
    print(f"Wrote the dataset in {time.monotonic()-started:.0f}s",flush=True)
    return header


def summarize(table):
    decision,cognition=table["decision_mismatch_cycles"].astype(np.int64),table["cognition_mismatch_cycles"].astype(np.int64)
    codes=categories(decision,cognition)
    n=len(codes)
    result=dict(comparison_rows=n,alike_max_changed=ALIKE_MAX_CHANGED,categories=list(CATEGORIES),
        interpretation=(f"A mode looks like driving alone when at most {ALIKE_MAX_CHANGED} of 100 cycles differ from "
                        "the driver's solo run. Shares and AUCs describe the simulated grid; they are not causal estimates."),
        overall=shares(codes,np.zeros(n,dtype=int),["all"])[0],
        sensitivity=[dict(max_changed=limit,**shares(categories(decision,cognition,limit),np.zeros(n,dtype=int),["all"])[0])
                     for limit in SENSITIVITY])
    fraction=values(table,"baseline_automation_fraction")
    groupings=dict(passenger_count=("Passengers",table["passenger_count"]-1,[str(k) for k in range(1,6)]),
        track_difficulty=("Track difficulty",table["track_difficulty"],list(DIFFICULTIES)),
        solo_regime=("Driver alone",np.where(fraction==0,0,np.where(fraction==1,2,1)),["always manual","varying","always automated"]),
        outvoted=("Outvoted cycles",*cycle_bins(table["solo_outvoted_cycles"],PRESSURE_EDGES)),
        cognitive_pull=("Cognitive-pull cycles",*cycle_bins(table["solo_cognitive_pull_cycles"],PRESSURE_EDGES)),
        participant=("Participant (driver)",table["driver"],list(table["_drivers"])))
    result["groups"]={name:dict(label=label,groups=shares(codes,group,labels)) for name,(label,group,labels) in groupings.items()}
    outvoted,ov_labels=cycle_bins(table["solo_outvoted_cycles"],PRESSURE_EDGES)
    pull,pull_labels=cycle_bins(table["solo_cognitive_pull_cycles"],PRESSURE_EDGES)
    plane=np.bincount((outvoted*len(pull_labels)+pull)*len(CATEGORIES)+codes,
                      minlength=len(ov_labels)*len(pull_labels)*len(CATEGORIES)).reshape(len(ov_labels),len(pull_labels),len(CATEGORIES))
    result["pressure_plane"]=dict(outvoted_bins=ov_labels,cognitive_pull_bins=pull_labels,counts=plane.tolist())
    print("Ranking predictors...",flush=True)
    outcomes=dict(decision_alike=decision<=ALIKE_MAX_CHANGED,cognition_alike=cognition<=ALIKE_MAX_CHANGED,both_alike=codes==0)
    result["predictors"]=[]
    for name in PREDICTORS:
        ranks=rankdata(values(table,name))
        result["predictors"].append(dict(feature=name,label=LABELS[name],**{o:auc(ranks,mask) for o,mask in outcomes.items()}))
    result["predictors"].sort(key=lambda p:-max(abs(p[o]-0.5) for o in outcomes))
    print("Growing the rule tree...",flush=True)
    random=np.random.default_rng(TREE_SEED)
    train=random.random(n)<0.7
    features={name:values(table,name) for name in PREDICTORS}
    tree=rules.fit({k:v[train] for k,v in features.items()},codes[train],CATEGORIES,depth=TREE_DEPTH)
    predicted=rules.predict(tree,{k:v[~train] for k,v in features.items()})
    majority=np.bincount(codes[train]).argmax()
    result["tree"]=dict(depth=TREE_DEPTH,held_out_accuracy=float(np.mean(predicted==codes[~train])),
                        majority_accuracy=float(np.mean(codes[~train]==majority)),rules=rules.leaves(tree,LABELS),model=tree)
    return result,codes


def agreement_map(table):
    """Counts of cars by decision and cognition agreement with driving alone (0–100 cycles each)."""
    cells=(100-table["decision_mismatch_cycles"].astype(np.int64))*101+(100-table["cognition_mismatch_cycles"].astype(np.int64))
    return np.bincount(cells,minlength=101*101).reshape(101,101)


def markdown(result):
    o=result["overall"]
    lines=[f"Matched comparisons: **{result['comparison_rows']:,}**.","",result["interpretation"],"",
        markdown_table(["Category","Share of cars"],[[c,fmt(o[c],1,True)] for c in CATEGORIES]),"",
        "![Agreement map](results/figures/agreement_map.png)","","### Sensitivity to the threshold","",
        markdown_table(["Changed cycles allowed",*CATEGORIES],
            [[str(s["max_changed"]),*[fmt(s[c],1,True) for c in CATEGORIES]] for s in result["sensitivity"]]),"",
        "### Where each category lives in the pressure plane","","![Pressure plane](results/figures/pressure_plane.png)","",
        "### By condition","","![Categories by condition](results/figures/categories_by_condition.png)",""]
    for name,group in result["groups"].items():
        if name=="participant":
            continue
        lines+=[f"#### {group['label']}","",markdown_table(["Group","Cars",*CATEGORIES],
            [[g["group"],f"{g['n']:,}",*[fmt(g[c],1,True) for c in CATEGORIES]] for g in group["groups"]]),""]
    lines+=["### What predicts looking like driving alone?","",
        "AUC of each feature alone: 0.5 means no separation; above 0.5, higher values go with looking alike; "
        "below 0.5, lower values do.","","![Predictors](results/figures/predictors.png)","",
        markdown_table(["Feature","Decision alike","Cognition alike","Both alike"],
            [[p["label"],fmt(p["decision_alike"],2),fmt(p["cognition_alike"],2),fmt(p["both_alike"],2)] for p in result["predictors"]]),"",
        f"### Rules (depth-{result['tree']['depth']} tree)","",
        f"Held-out accuracy **{100*result['tree']['held_out_accuracy']:.1f}%** "
        f"(always guessing the most common category: {100*result['tree']['majority_accuracy']:.1f}%).","",
        markdown_table(["Rule","Cars (training)","Most likely",*CATEGORIES],
            [[r["rule"],f"{r['n']:,}",r["majority"],*[fmt(r["shares"][c],1,True) for c in CATEGORIES]] for r in result["tree"]["rules"]]),"",
        "### By participant","","![Participants](results/figures/participants.png)"]
    return "\n".join(lines)


def run(directory=None,output=None,runs=RUNS_DIR):
    from experiment.analysis.baseline_similarity.plot import render
    table=load(directory,runs)
    output=Path(output) if output is not None else result_directory(NAME)
    result,codes=summarize(table)
    output.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(output/"agreement_map.npz",counts=agreement_map(table))
    if EXPORT_DATASET:
        result["dataset"]=dict(path="results/similarity_dataset.csv.gz",columns=export(table,output/"similarity_dataset.csv.gz",codes))
    write_results(NAME,result,markdown(result),output=output)
    render(output)
    print(f"Saved {output/'summary.json'}; README updated.",flush=True)
    return result


if __name__=="__main__":
    run()
