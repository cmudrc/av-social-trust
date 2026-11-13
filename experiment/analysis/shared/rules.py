"""A shallow, histogram-based classification tree whose leaves read as rules.

Only NumPy is available, so this replaces scikit-learn for interpretable splits on
millions of rows: each feature is binned once at quantiles, and every node is grown
from per-bin class counts. Splits minimize weighted Gini impurity.
"""

import numpy as np


def gini(counts):
    counts = np.asarray(counts,dtype=np.float64)
    total = counts.sum(axis=-1,keepdims=True)
    shares = np.divide(counts,total,out=np.zeros_like(counts),where=total>0)
    return 1-(shares**2).sum(axis=-1)


def fit(features, y, classes, depth=3, min_leaf=0.01, bins=32, sample_step=50):
    """features: {name: values}; y: integer class codes; min_leaf is a share of the rows."""
    names = list(features)
    edges = [np.unique(np.quantile(np.asarray(features[n],dtype=np.float64)[::sample_step],
                                   np.linspace(0,1,bins+1)[1:-1])) for n in names]
    binned = [np.searchsorted(e,np.asarray(features[n],dtype=np.float64),side="right") for n,e in zip(names,edges)]
    k = len(classes)
    smallest = max(1,int(min_leaf*len(y)))

    def grow(rows, level):
        counts = np.bincount(y[rows],minlength=k)
        node = dict(n=int(len(rows)),counts=counts.tolist())
        if level==depth or len(rows)<2*smallest:
            return node
        best = None
        for j,(name,edge) in enumerate(zip(names,edges)):
            width = len(edge)+1
            hist = np.bincount(binned[j][rows]*k+y[rows],minlength=width*k).reshape(width,k)
            left = np.cumsum(hist,axis=0)[:-1]
            right = counts-left
            nl,nr = left.sum(axis=1),right.sum(axis=1)
            impurity = (nl*gini(left)+nr*gini(right))/len(rows)
            impurity[(nl<smallest)|(nr<smallest)] = np.inf
            b = int(np.argmin(impurity))
            if np.isfinite(impurity[b]) and (best is None or impurity[b]<best[0]):
                best = (impurity[b],j,b)
        if best is None or best[0]>=gini(counts)-1e-9:
            return node
        _,j,b = best
        goes_left = binned[j][rows]<=b
        node.update(feature=names[j],threshold=float(edges[j][b]),
                    left=grow(rows[goes_left],level+1),right=grow(rows[~goes_left],level+1))
        return node

    return dict(classes=list(classes),root=grow(np.arange(len(y)),0))


def predict(tree, features):
    n = len(next(iter(features.values())))
    out = np.zeros(n,dtype=np.int64)

    def walk(node, rows):
        if "feature" not in node:
            out[rows] = int(np.argmax(node["counts"]))
            return
        left = np.asarray(features[node["feature"]],dtype=np.float64)[rows]<node["threshold"]
        walk(node["left"],rows[left])
        walk(node["right"],rows[~left])

    walk(tree["root"],np.arange(n))
    return out


def leaves(tree, labels=None):
    """Each leaf as a rule: conditions, rows, and class shares."""
    labels = labels or {}
    out = []

    def walk(node, conditions):
        if "feature" not in node:
            total = max(node["n"],1)
            out.append(dict(rule=" and ".join(conditions) or "all cars",n=node["n"],
                            shares={c:count/total for c,count in zip(tree["classes"],node["counts"])},
                            majority=tree["classes"][int(np.argmax(node["counts"]))]))
            return
        name = labels.get(node["feature"],node["feature"].replace("_"," "))
        walk(node["left"],conditions+[f"{name} < {node['threshold']:.3g}"])
        walk(node["right"],conditions+[f"{name} ≥ {node['threshold']:.3g}"])

    walk(tree["root"],[])
    return out
