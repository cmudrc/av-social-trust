"""Shared on/off metrics and descriptive parameter reports."""

from collections import Counter
import json
import sqlite3

import numpy as np

from experiment.config import ANALYSIS_DIR
from experiment.design import canonical


def similarity(reference,influenced):
    reference,influenced = np.asarray(reference,dtype=bool),np.asarray(influenced,dtype=bool)
    if reference.shape!=influenced.shape or reference.ndim!=1 or not len(reference):
        raise ValueError("Sequences must have equal nonempty one-dimensional shapes")
    on,off = int(np.count_nonzero(reference&influenced)),int(np.count_nonzero(~reference&~influenced))
    promote,suppress = int(np.count_nonzero(~reference&influenced)),int(np.count_nonzero(reference&~influenced))
    n = len(reference)
    reference_on,reference_off = int(reference.sum()),int((~reference).sum())
    changes = np.flatnonzero(reference!=influenced)
    return dict(agreement=(on+off)/n,mismatch_cycles=len(changes),both_on=on,both_off=off,
        switched_on=promote,switched_off=suppress,on_jaccard=on/(on+promote+suppress) if on+promote+suppress else None,
        agreement_when_reference_on=on/reference_on if reference_on else None,
        agreement_when_reference_off=off/reference_off if reference_off else None,
        balanced_agreement=(on/reference_on+off/reference_off)/2 if reference_on and reference_off else None,
        delta_automation_fraction=float(influenced.mean()-reference.mean()),
        first_divergence_cycle=int(changes[0]+1) if len(changes) else None,
        early_agreement=float(np.mean(reference[:20]==influenced[:20])),
        late_agreement=float(np.mean(reference[20:]==influenced[20:])) if n>20 else None)


def report(name,specs,interactions=(),directory=ANALYSIS_DIR):
    path = directory/"comparisons.sqlite"
    if not path.exists():
        raise FileNotFoundError("Run experiment/analysis/compare_modes.py first")
    db = sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True)
    groups,total = {},0
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
        output = dict(comparison_rows=total,interpretation="Descriptive associations, not isolated causal effects or independent-person significance tests.",
            groups=[dict(feature=key[0],bin=key[1],n=g["n"],drivers=len(g["drivers"]),
                means={name:value/g["defined"][name] for name,value in g["sums"].items()},defined_counts=dict(g["defined"])) for key,g in groups.items()])
        directory.mkdir(parents=True,exist_ok=True)
        (directory/f"{name}.json").write_text(canonical(output)+"\n")
        print(f"Saved {name}.json: {total:,} comparisons")
        return output
    finally:
        db.close()
