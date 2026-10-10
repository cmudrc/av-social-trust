"""Describe magnitude, direction and persistence without loading all runs in RAM."""

from collections import Counter,defaultdict
import json
from pathlib import Path
import sqlite3
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[2]
    sys.path[:0]=[str(root),str(root/"src")]

from experiment.config import ANALYSIS_DIR
from experiment.design import canonical

PAIRS=("decision_vs_baseline","cognition_vs_baseline","decision_vs_cognition")


def quantile(histogram,q):
    n=sum(histogram.values())
    rank=q*(n-1)
    low,high=int(rank),min(int(rank)+1,n-1)
    values=[]
    for target in (low,high):
        seen=0
        for value,count in sorted(histogram.items()):
            seen+=count
            if seen>target:
                values.append(value)
                break
    return values[0]+(values[1]-values[0])*(rank-low)


def summarize(directory=ANALYSIS_DIR):
    db=sqlite3.connect((directory/"comparisons.sqlite").resolve().as_uri()+"?mode=ro",uri=True)
    groups=defaultdict(lambda:dict(n=0,hist=Counter(),sums=Counter(),defined=Counter()))
    total=0
    try:
        for driver,raw in db.execute("SELECT driver,metrics FROM comparisons"):
            metrics=json.loads(raw)
            for pair in PAIRS:
                value=metrics[pair]
                for group in ("overall",driver):
                    g=groups[group,pair]
                    g["n"]+=1
                    g["hist"][value["mismatch_cycles"]]+=1
                    for name in ("mismatch_cycles","switched_on","switched_off","delta_automation_fraction","early_agreement","late_agreement"):
                        if value[name] is not None:
                            g["sums"][name]+=value[name]
                            g["defined"][name]+=1
            total+=1
        output=dict(comparison_rows=total,interpretation="Descriptive; changed-cycle thresholds are exploratory, not validated importance cutoffs.",groups={})
        for (label,pair),g in groups.items():
            n=g["n"]
            stats=dict(n=n,means={name:value/g["defined"][name] for name,value in g["sums"].items()},
                mismatch_cycles_quartiles=[quantile(g["hist"],q) for q in (0.25,0.5,0.75)],
                fraction_any_change=1-g["hist"][0]/n,
                **{f"fraction_at_least_{threshold}_changed_cycles":sum(count for value,count in g["hist"].items() if value>=threshold)/n for threshold in (10,25,50)})
            output["groups"].setdefault(label,{})[pair]=stats
        (directory/"social_importance.json").write_text(canonical(output)+"\n")
        print(f"Saved social_importance.json: {total:,} comparisons")
        return output
    finally:
        db.close()


if __name__=="__main__":
    summarize()
