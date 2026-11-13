"""Describe magnitude, direction and persistence without loading all runs in RAM."""

from collections import Counter,defaultdict
import json
from pathlib import Path
import sqlite3
import sys
import time

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

from experiment.analysis.shared.output import comparison_directory,write_results

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


def summarize(directory=None,output=None):
    path=comparison_directory(directory)/"comparisons.sqlite"
    if not path.exists():
        raise FileNotFoundError("Run experiment/analysis/compare_modes/run.py first")
    print("Reading comparisons for social_importance...",flush=True)
    db=sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True)
    groups=defaultdict(lambda:dict(n=0,hist=Counter(),sums=Counter(),defined=Counter()))
    total=0
    reported=time.monotonic()
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
            if total%1000==0 and time.monotonic()-reported>=5:
                print(f"Read {total:,} comparisons",flush=True)
                reported=time.monotonic()
        result=dict(comparison_rows=total,interpretation="Descriptive; changed-cycle thresholds are exploratory, not validated importance cutoffs.",groups={})
        for (label,pair),g in groups.items():
            n=g["n"]
            stats=dict(n=n,means={name:value/g["defined"][name] for name,value in g["sums"].items()},
                mismatch_cycles_quartiles=[quantile(g["hist"],q) for q in (0.25,0.5,0.75)],
                fraction_any_change=1-g["hist"][0]/n,
                **{f"fraction_at_least_{threshold}_changed_cycles":sum(count for value,count in g["hist"].items() if value>=threshold)/n for threshold in (10,25,50)})
            result["groups"].setdefault(label,{})[pair]=stats
        markdown=[f"Matched comparisons: **{total:,}**.","",result["interpretation"],"",
                  "| Comparison | Mean changed cycles | Median changed cycles | Models with any change |",
                  "| --- | ---: | ---: | ---: |"]
        for pair,stats in result["groups"].get("overall",{}).items():
            markdown.append(f"| {pair} | {stats['means']['mismatch_cycles']:.2f} | "
                            f"{stats['mismatch_cycles_quartiles'][1]:.2f} | {100*stats['fraction_any_change']:.1f}% |")
        destination=write_results("social_importance",result,"\n".join(markdown),output=output)
        print(f"Saved {destination/'summary.json'}: {total:,} comparisons; README updated.",flush=True)
        return result
    finally:
        db.close()


def run(directory=None,output=None):
    return summarize(directory,output)


if __name__=="__main__":
    run()
