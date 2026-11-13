"""Vectorized summaries over the analysis table: ranks, grouped ratios and variance shares."""

import numpy as np
from scipy.stats import rankdata

CATEGORICAL = ("driver","track_difficulty","passenger_count")
DESIGN = ("track_difficulty","track_persistence","passenger_count","driver_self_trust",
          "driver_automation_trust","driver_perceived_risk","driver_workload","driver_initial_self_weight",
          "inbound_trust_mean","outbound_trust_mean","alpha_inbound_mean","alpha_outbound_mean",
          "passenger_automation_trust_mean","passenger_self_trust_mean")
# Inbound/outbound are from the driver's point of view: runner.run_metadata() uses
# trust[1:,0] (passengers trusting the driver) as inbound and trust[0,1:] as outbound.
LABELS = dict(driver="Participant (driver identity)",track_difficulty="Track difficulty",
              track_persistence="Track persistence",passenger_count="Passenger count",
              driver_self_trust="Driver's initial self-trust",driver_automation_trust="Driver's initial automation trust",
              driver_perceived_risk="Driver's initial perceived risk",driver_workload="Driver's initial workload",
              driver_initial_self_weight="Driver's initial self-weight",inbound_trust_mean="Passengers' trust in the driver",
              outbound_trust_mean="Driver's trust in passengers",
              alpha_inbound_mean="Passengers' homophily when trusting the driver (alpha)",
              alpha_outbound_mean="Driver's homophily when trusting passengers (alpha)",
              passenger_automation_trust_mean="Passengers' initial automation trust",
              passenger_self_trust_mean="Passengers' initial self-trust",
              baseline_automation_fraction="Driver's solo automation fraction",
              solo_outvoted_cycles="Outvoted cycles",solo_cognitive_pull_cycles="Cognitive-pull cycles",
              solo_disagreement_cycles="Cycles any passenger would decide differently",
              driver_solo_switches="Driver's solo decision switches",
              passenger_solo_automation="Passengers' solo automation fraction")
MODES = dict(decision=dict(label="Decision-level influence",change="decision_mismatch_cycles",
                           pressure="solo_outvoted_cycles",pressure_label="outvoted cycles"),
             cognition=dict(label="Cognition-level influence",change="cognition_mismatch_cycles",
                            pressure="solo_cognitive_pull_cycles",pressure_label="cognitive-pull cycles"))


def values(table, name):
    return np.asarray(table[name],dtype=np.float64)


def spearman(x, y):
    return float(np.corrcoef(rankdata(x),rankdata(y))[0,1])


def bins(x, edges):
    """Codes and labels for [lo, hi) bins; the last bin includes its upper edge."""
    x = np.asarray(x,dtype=np.float64)
    codes = np.clip(np.searchsorted(edges,x,side="right")-1,0,len(edges)-2)
    labels = [f"[{lo:g}, {hi:g}{']' if i==len(edges)-2 else ')'}" for i,(lo,hi) in enumerate(zip(edges,edges[1:]))]
    return codes,labels


def cycle_bins(x, edges=(0,1,5,10,20,40,60,101)):
    """Bins for counts of cycles, labelled as inclusive integer ranges."""
    codes,_ = bins(x,edges)
    labels = [f"{lo}" if hi-lo==1 else f"{lo}–{hi-1}" for lo,hi in zip(edges,edges[1:])]
    return codes,labels


def grouped(codes, labels, columns, ratios=()):
    """Group sizes, means and pooled ratios sum(numerator)/sum(denominator) for each code."""
    codes = np.asarray(codes)
    count = np.bincount(codes,minlength=len(labels))
    rows = []
    sums = {name:np.bincount(codes,weights=value,minlength=len(labels)) for name,value in columns.items()}
    for i,label in enumerate(labels):
        if not count[i]:
            continue
        row = dict(group=label,n=int(count[i]))
        row.update({name:float(sums[name][i]/count[i]) for name in columns})
        for name,(numerator,denominator) in dict(ratios).items():
            row[name] = float(sums[numerator][i]/sums[denominator][i]) if sums[denominator][i] else None
        rows.append(row)
    return rows


def eta_squared(codes, y):
    """Share of the variance of y explained by group means alone."""
    codes,y = np.asarray(codes),np.asarray(y,dtype=np.float64)
    means = np.bincount(codes,weights=y)/np.maximum(np.bincount(codes),1)
    return float(np.var(means[codes])/np.var(y))


def blocks(table, names):
    """Design-matrix column blocks: indicators for categorical names, z-scores otherwise."""
    out = []
    for name in names:
        x = np.asarray(table[name])
        if name in CATEGORICAL:
            levels = np.unique(x)[1:]
            out.append((name,lambda rows,x=x,levels=levels:(x[rows,None]==levels[None,:]).astype(np.float64)))
        else:
            x = x.astype(np.float64)
            mean,scale = x.mean(),x.std() or 1.0
            out.append((name,lambda rows,x=x,mean=mean,scale=scale:((x[rows]-mean)/scale)[:,None]))
    return out


def variance_shares(table, outcome, names, chunk=500_000):
    """Linear R² of all names together, and each name's unique R² (loss when it is dropped).

    The cross-products are accumulated in chunks, so every reduced model is solved
    from the same sufficient statistics without refitting on the raw rows.
    """
    y = values(table,outcome)
    parts = blocks(table,names)
    n = len(y)
    xtx = xty = None
    for begin in range(0,n,chunk):
        rows = slice(begin,min(begin+chunk,n))
        x = np.hstack([np.ones((rows.stop-rows.start,1))]+[make(rows) for _,make in parts])
        xtx = x.T@x if xtx is None else xtx+x.T@x
        xty = x.T@y[rows] if xty is None else xty+x.T@y[rows]
    total = float(((y-y.mean())**2).sum())
    yty = float(y@y)
    widths = [make(slice(0,1)).shape[1] for _,make in parts]
    starts = np.cumsum([1]+widths)

    def r2(columns):
        coefficients = np.linalg.lstsq(xtx[np.ix_(columns,columns)],xty[columns],rcond=None)[0]
        return 1-(yty-coefficients@xty[columns])/total

    every = list(range(xtx.shape[0]))
    full = r2(every)
    unique = {}
    for (name,_),start,width in zip(parts,starts,widths):
        kept = [c for c in every if not start<=c<start+width]
        unique[name] = float(full-r2(kept))
    return dict(r2=float(full),unique=unique)


def markdown_table(headers, rows, align=None):
    align = align or ["---"]+["---:"]*(len(headers)-1)
    lines = ["| "+" | ".join(headers)+" |","| "+" | ".join(align)+" |"]
    lines += ["| "+" | ".join(str(cell).replace("|",r"\|") for cell in row)+" |" for row in rows]
    return "\n".join(lines)


def fmt(value, digits=1, percent=False):
    if value is None or (isinstance(value,float) and not np.isfinite(value)):
        return "—"
    return f"{100*value:.{digits}f}%" if percent else f"{value:,.{digits}f}"
