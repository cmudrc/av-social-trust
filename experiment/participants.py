"""
Rebuild and run a MATLAB fitctree classification tree exported by export_svse.m.
Based on the supplied tree helper, with structural validation.

    from scipy.io import loadmat
    from experiment.participants import MatlabTree

    data = loadmat("experiment/data/combined_models.mat", simplify_cells=True)
    tree = MatlabTree(data["P01"]["d_tree"])

    tree.predict(X)          # class labels, X is (n_samples, n_features)
    tree.predict_proba(X)    # class probabilities, columns ordered as tree.class_names
    tree.to_dict()           # the tree as nested Python dicts

Requires numpy (and scipy to read the .mat file).
"""

from pathlib import Path
import re

import numpy as np
from scipy.io import loadmat

from experiment.config import DATA_DIR

def _strings(x):
    """MATLAB cellstr -> list of str, whatever shape scipy returned."""
    if isinstance(x, str):
        return [x.strip()]
    return [str(np.asarray(e).ravel()[0]).strip() if not isinstance(e, str) else e.strip()
            for e in np.asarray(x, dtype=object).ravel()]


def _vec(x, dtype=float):
    return np.atleast_1d(np.asarray(x, dtype=dtype)).ravel()


class MatlabTree:
    """A MATLAB ClassificationTree, rebuilt from the exported d_tree struct.

    Node arrays use 0-based Python indexing; -1 means "none" (leaf node).
      children[i]          [left, right] child of node i
      cut_feature[i]       column of X that node i splits on
      cut_point[i]         split threshold: x < cut_point goes left (MATLAB rule)
      is_branch[i]         True for split nodes, False for leaves
      node_class[i]        predicted label at node i
      class_probability[i] class probabilities at node i
    """

    def __init__(self, d_tree):
        t = d_tree if isinstance(d_tree, dict) else {f: getattr(d_tree, f) for f in d_tree._fieldnames}

        if bool(_vec(t["has_categorical"])[0]):
            raise NotImplementedError("Tree has categorical splits, which were not exported.")

        self.is_branch = _vec(t["is_branch"]).astype(bool)
        n = self.is_branch.size
        self.children = np.asarray(t["children"], dtype=float).reshape(n, 2).astype(int) - 1
        self.cut_feature = _vec(t["cut_predictor_index"]).astype(int) - 1
        self.cut_point = _vec(t["cut_point"])
        self.class_probability = np.asarray(t["class_probability"], dtype=float).reshape(n, -1)
        self.predictor_names = _strings(t["predictor_names"])

        num = _vec(t["class_names_num"])
        self.class_names = num if num.size else np.array(_strings(t["class_names_str"]))
        class_indices = _vec(t["node_class_index"])
        if not np.all(np.isin(class_indices, np.arange(1, len(self.class_names) + 1))):
            raise ValueError("Invalid tree node class index.")
        self.node_class = self.class_names[class_indices.astype(int) - 1]
        self._validate()

    def _validate(self):
        """Reject inconsistent node arrays and cycles before traversal."""
        n = len(self.is_branch)
        if (n == 0 or len(self.cut_feature) != n or len(self.cut_point) != n
                or len(self.node_class) != n
                or self.class_probability.shape != (n, len(self.class_names))):
            raise ValueError("Inconsistent tree node arrays.")
        probabilities = self.class_probability
        if (not np.all(np.isfinite(probabilities)) or np.any(probabilities < 0)
                or np.any(probabilities > 1) or not np.allclose(probabilities.sum(axis=1), 1)):
            raise ValueError("Invalid tree class probabilities.")
        branches = self.is_branch
        if (np.any(self.children[branches] < 0) or np.any(self.children[branches] >= n)
                or np.any(self.cut_feature[branches] < 0)
                or np.any(self.cut_feature[branches] >= len(self.predictor_names))
                or not np.all(np.isfinite(self.cut_point[branches]))):
            raise ValueError("Invalid tree split or child index.")
        visited = set()
        pending = [0]
        while pending:
            node = pending.pop()
            if node in visited:
                raise ValueError("Tree has a cycle or shared child.")
            visited.add(node)
            if self.is_branch[node]:
                pending.extend(int(child) for child in self.children[node])
        if len(visited) != n:
            raise ValueError("Tree contains unreachable nodes.")

    def _leaf_nodes(self, X):
        X = np.atleast_2d(np.asarray(X, dtype=float))
        if X.ndim != 2:
            raise ValueError("X must be a vector or a 2-D sample matrix.")
        if X.shape[1] != len(self.predictor_names):
            raise ValueError(f"X has {X.shape[1]} columns; the tree expects "
                             f"{len(self.predictor_names)}: {self.predictor_names}")
        nodes = np.empty(X.shape[0], dtype=int)
        for i, x in enumerate(X):
            n = 0
            while self.is_branch[n]:
                v = x[self.cut_feature[n]]
                if np.isnan(v):       # MATLAB (no surrogate splits): stop at this node
                    break
                n = self.children[n, 0] if v < self.cut_point[n] else self.children[n, 1]
            nodes[i] = n
        return nodes

    def predict(self, X):
        """Class labels for each row of X (columns ordered as predictor_names)."""
        return self.node_class[self._leaf_nodes(X)]

    def predict_proba(self, X):
        """Class probabilities for each row of X, columns ordered as class_names."""
        return self.class_probability[self._leaf_nodes(X)]

    def to_dict(self, node=0):
        """The tree as nested dicts, e.g. for inspection or JSON export."""
        label = self.node_class[node]
        out = {
            "node": int(node),
            "class": label.item() if hasattr(label, "item") else label,
            "probability": self.class_probability[node].tolist(),
        }
        if self.is_branch[node]:
            f = int(self.cut_feature[node])
            out.update({
                "feature": self.predictor_names[f],
                "feature_index": f,
                "threshold": float(self.cut_point[node]),
                "left": self.to_dict(self.children[node, 0]),    # feature < threshold
                "right": self.to_dict(self.children[node, 1]),   # feature >= threshold
            })
        return out


def load_participants(path=DATA_DIR / "combined_models.mat"):
    """Read the private export once. No coefficients/trees are copied into runs."""
    raw = loadmat(Path(path), simplify_cells=True)
    people = sorted((key for key in raw if re.fullmatch(r"P\d+",key)),key=lambda key:int(key[1:]))
    if not people:
        raise ValueError(f"No participant records in {path}")
    participants = {}
    for person in people:
        record = raw[person]
        selected = np.atleast_1d(np.asarray(record["state_selector"],dtype=float)).ravel()
        if (not 1<=len(selected)<=3 or not np.all(np.isin(selected,(1,2,3)))
                or len(set(selected))!=len(selected)):
            raise ValueError(f"Invalid state selector for {person}")
        indices = selected.astype(int)-1
        tree = MatlabTree(record["d_tree"])
        if len(tree.predictor_names)!=3 or not set(tree.class_names)=={0,1}:
            raise ValueError(f"{person}: expected three tree inputs and classes 0/1")
        if not set(tree.cut_feature[tree.is_branch]).issubset(set(indices)):
            raise ValueError(f"{person}: tree splits on an unselected state")
        if "check_X" in record["d_tree"]:
            checks = record["d_tree"]
            expected = tree.class_names[np.atleast_1d(np.asarray(checks["check_label_index"],dtype=int))-1]
            if not np.array_equal(tree.predict(checks["check_X"]),expected):
                raise ValueError(f"{person}: tree disagrees with MATLAB verification samples")
        n = len(indices)
        coefficients = {}
        for name, shape in (("A",(n,n)),("B",(n,)),("c",(n,))):
            value = np.asarray(record[name],dtype=float)
            if value.size!=int(np.prod(shape)) or not np.isfinite(value).all():
                raise ValueError(f"Invalid {person}.{name}")
            coefficients[name] = value.reshape(shape)
        participants[person] = dict(**coefficients,state_indices=indices,
                                  class_names=tree.class_names.tolist(),tree=tree.to_dict())
    return participants
