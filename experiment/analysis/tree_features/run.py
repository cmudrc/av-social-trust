"""Which cognitive states do the 26 participant models and decision trees use?

Reports, per participant, the states included in the fitted dynamics, the states
the decision tree splits on, the number of splits, and whether the fitted state
matrix is diagonal. Answers how many trees use workload, the state that transfers
least well from drivers to passengers.
"""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(root), str(root/"src")]

import numpy as np

from experiment.model import STATE_NAMES
from experiment.participants import load_participants
from experiment.analysis.shared.output import result_directory, write_results
from experiment.analysis.shared.stats import markdown_table

NAME = "tree_features"
SHORT = dict(automation_trust="trust", perceived_risk="risk", workload="workload")


def splits(node, found):
    if "feature_index" in node:
        found.append(int(node["feature_index"]))
        splits(node["left"], found)
        splits(node["right"], found)
    return found


def summarize(participants):
    rows = []
    for person, record in participants.items():
        split_features = splits(record["tree"], [])
        A = np.asarray(record["A"], dtype=float)
        rows.append(dict(participant=person,
                         model_states=[STATE_NAMES[i] for i in record["state_indices"]],
                         tree_states=sorted({STATE_NAMES[i] for i in split_features}, key=STATE_NAMES.index),
                         tree_splits=len(split_features),
                         diagonal_state_matrix=bool(np.allclose(A, np.diag(np.diag(A))))))
    count = lambda key, state: sum(state in r[key] for r in rows)
    return dict(participants=len(rows),
                models_by_state_count={str(k): sum(len(r["model_states"]) == k for r in rows) for k in (1, 2, 3)},
                models_including={s: count("model_states", s) for s in STATE_NAMES},
                trees_splitting_on={s: count("tree_states", s) for s in STATE_NAMES},
                trees_without_splits=sum(r["tree_splits"] == 0 for r in rows),
                diagonal_state_matrices=sum(r["diagonal_state_matrix"] for r in rows),
                rows=rows)


def markdown(result):
    states = lambda names: ", ".join(SHORT[n] for n in names) or "—"
    return "\n".join([
        f"**{result['participants']} participant models.**", "",
        "| | Trust | Risk | Workload |", "| --- | ---: | ---: | ---: |",
        "| Models including the state | " + " | ".join(str(result["models_including"][s]) for s in STATE_NAMES) + " |",
        "| Trees splitting on the state | " + " | ".join(str(result["trees_splitting_on"][s]) for s in STATE_NAMES) + " |", "",
        f"Models with one / two / three states: {result['models_by_state_count']['1']} / "
        f"{result['models_by_state_count']['2']} / {result['models_by_state_count']['3']}. "
        f"Trees without splits: {result['trees_without_splits']}. "
        f"Diagonal state matrices: {result['diagonal_state_matrices']} of {result['participants']}.", "",
        markdown_table(["Participant", "Model states", "Tree splits on", "Splits", "Diagonal A"],
                       [[r["participant"], states(r["model_states"]), states(r["tree_states"]), str(r["tree_splits"]),
                         "yes" if r["diagonal_state_matrix"] else "no"] for r in result["rows"]])])


def run(output=None):
    result = summarize(load_participants())
    output = Path(output) if output else result_directory(NAME)
    output.mkdir(parents=True, exist_ok=True)
    write_results(NAME, result, markdown(result), output=output)
    print(f"Saved {output}.", flush=True)
    return result


if __name__ == "__main__":
    run()
