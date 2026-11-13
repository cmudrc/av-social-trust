"""Decision-comparison calculations; kept separate from output presentation."""

import json

import numpy as np


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


def similarities(reference, influenced):
    """Calculate the same metrics as similarity(), one row per model pair."""
    reference, influenced = np.asarray(reference,dtype=bool), np.asarray(influenced,dtype=bool)
    if reference.shape != influenced.shape or reference.ndim != 2 or reference.shape[1] == 0:
        raise ValueError("Batches must have equal nonempty two-dimensional shapes")
    n = reference.shape[1]
    changed = reference != influenced
    on = np.count_nonzero(reference & influenced,axis=1)
    off = np.count_nonzero(~reference & ~influenced,axis=1)
    promote = np.count_nonzero(~reference & influenced,axis=1)
    suppress = np.count_nonzero(reference & ~influenced,axis=1)
    mismatch = np.count_nonzero(changed,axis=1)
    reference_on = np.count_nonzero(reference,axis=1)
    first = np.argmax(changed,axis=1)+1
    early = np.mean(~changed[:,:20],axis=1)
    late = np.mean(~changed[:,20:],axis=1) if n>20 else [None]*len(reference)
    delta = np.mean(influenced,axis=1)-np.mean(reference,axis=1)
    rows = []
    for values in zip(on,off,promote,suppress,mismatch,reference_on,first,early,late,delta):
        both_on,both_off,up,down,different,ref_on,first_cycle = map(int,values[:7])
        ref_off = n-ref_on
        on_agreement = both_on/ref_on if ref_on else None
        off_agreement = both_off/ref_off if ref_off else None
        rows.append(dict(agreement=(both_on+both_off)/n,mismatch_cycles=different,
            both_on=both_on,both_off=both_off,switched_on=up,switched_off=down,
            on_jaccard=both_on/(both_on+up+down) if both_on+up+down else None,
            agreement_when_reference_on=on_agreement,agreement_when_reference_off=off_agreement,
            balanced_agreement=(on_agreement+off_agreement)/2 if ref_on and ref_off else None,
            delta_automation_fraction=float(values[9]),
            first_divergence_cycle=first_cycle if different else None,
            early_agreement=float(values[7]),late_agreement=float(values[8]) if n>20 else None))
    return rows


def comparison_batch(rows, baseline, steps, driver, track):
    """Decode and compare a bounded batch without loading trajectory arrays."""
    if not rows:
        return []
    width = (steps+7)//8
    cognition = np.unpackbits(np.frombuffer(b"".join(row[3] for row in rows),dtype=np.uint8)
                             .reshape(len(rows),width),axis=1)[:,:steps].astype(bool)
    decision = np.unpackbits(np.frombuffer(b"".join(row[5] for row in rows),dtype=np.uint8)
                            .reshape(len(rows),width),axis=1)[:,:steps].astype(bool)
    base = np.stack([baseline[row[1]][1] for row in rows])
    # Preserve the original convention: the cross-mode reference is cognition.
    pairs = (similarities(base,decision),similarities(base,cognition),similarities(cognition,decision))
    triple = np.mean((base==decision)&(decision==cognition),axis=1)
    base_fraction = np.mean(base,axis=1)
    output = []
    for i,(composition,start,c_meta,_,d_meta,_) in enumerate(rows):
        cognition_meta,decision_meta = json.loads(c_meta),json.loads(d_meta)
        base_meta = baseline[start][0]
        if cognition_meta["features"] != decision_meta["features"]:
            raise ValueError("Influence variants have different initial conditions")
        for key in ("driver_self_trust","driver_automation_trust","driver_perceived_risk","driver_workload"):
            if base_meta["features"][key] != cognition_meta["features"][key]:
                raise ValueError("Driver initialization differs from baseline")
        metrics = dict(decision_vs_baseline=pairs[0][i],cognition_vs_baseline=pairs[1][i],
                       decision_vs_cognition=pairs[2][i],all_three_agreement=float(triple[i]),
                       baseline_automation_fraction=float(base_fraction[i]))
        for name,meta in (("baseline",base_meta),("decision",decision_meta),("cognition",cognition_meta)):
            metrics[f"{name}_driver_clipping_fraction"] = meta["summary"]["driver_clipping_fraction"]
        features = dict(cognition_meta["features"],passenger_count=len(cognition_meta["passengers"]),
                        track=track,track_difficulty=cognition_meta["track_difficulty"],
                        track_replicate=cognition_meta["track_replicate"],
                        cognitive_start=cognition_meta["cognitive_start"],social_start=cognition_meta["social_start"])
        output.append((driver,track,composition,start,features,metrics))
    return output
