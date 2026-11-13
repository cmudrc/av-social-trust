"""Shared on/off metrics and descriptive parameter reports."""

from collections import Counter
import json
from pathlib import Path
import sqlite3
import time

from experiment.design import canonical
from experiment.analysis.shared.metrics import similarity
from experiment.analysis.shared.output import (atomic_text,comparison_directory,
                                               grouped_markdown,result_directory,write_results)




def report(name,specs,interactions=(),directory=None,output=None):
    path = comparison_directory(directory)/"comparisons.sqlite"
    if not path.exists():
        raise FileNotFoundError("Run experiment/analysis/compare_modes/run.py first")
    db = sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True)
    groups,total = {},0
    reported = time.monotonic()
    print(f"Reading matched comparisons for {name}...",flush=True)
    def label(value,edges):
        if edges is None:
            return str(value)
        for lo,hi in zip(edges,edges[1:]):
            if lo<=value<hi or value==hi==edges[-1]:
                return f"[{lo}, {hi}{']' if hi==edges[-1] else ')'}"
        return "outside_bins"
    try:
        for driver,features,metrics in db.execute("SELECT driver,features,metrics FROM comparisons"):
            values,outcomes = json.loads(features),json.loads(metrics)
            labels = {key:label(values[key],edges) for key,edges in specs.items()}
            keys = list(labels.items())+[(" × ".join(names)," | ".join(labels[n] for n in names)) for names in interactions]
            for key in keys:
                group = groups.setdefault(key,dict(n=0,drivers=set(),sums=Counter(),defined=Counter()))
                group["n"]+=1
                group["drivers"].add(driver)
                for pair in ("decision_vs_baseline","cognition_vs_baseline","decision_vs_cognition"):
                    for metric in ("agreement","balanced_agreement","delta_automation_fraction","on_jaccard"):
                        value = outcomes[pair][metric]
                        if value is not None:
                            full = f"{pair}.{metric}"
                            group["sums"][full]+=value
                            group["defined"][full]+=1
            total+=1
            if total%1000==0 and time.monotonic()-reported>=5:
                print(f"Read {total:,} comparisons",flush=True)
                reported = time.monotonic()
        result = dict(comparison_rows=total,interpretation="Descriptive associations, not isolated causal effects or independent-person significance tests.",
            groups=[dict(feature=key[0],bin=key[1],n=g["n"],drivers=len(g["drivers"]),
                means={name:value/g["defined"][name] for name,value in g["sums"].items()},defined_counts=dict(g["defined"])) for key,g in groups.items()])
        destination = Path(output) if output is not None else result_directory(name)
        destination = write_results(name,result,grouped_markdown(result),output=destination)
        atomic_text(destination/"groups.jsonl","".join(canonical(group)+"\n" for group in result["groups"]))
        print(f"Saved {total:,} comparisons: {destination/'summary.json'}; README updated.",flush=True)
        return result
    finally:
        db.close()
