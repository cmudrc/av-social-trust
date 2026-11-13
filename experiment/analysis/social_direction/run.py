"""Does the social layer push the driver toward or away from automation, and does it follow the passengers?

Net change: the driver's automation share with passengers minus the matched solo
run, in percentage points of the drive (positive = more automation). Changed
cycles toward automation and toward manual driving are also reported; their sum
is the share of changed decisions used in track_social_effects.

Passengers' lean: the passengers' own solo automation share minus the driver's
solo automation share, at the same track and start. It says how much more (or
less) the passengers would use automation than the driver if each drove alone.
In decision mode the passengers' votes are exactly these solo choices.

Cars are matched on all nine tracks, averaged over the three persistence levels
within each complexity level, and weighted equally by driver and by passenger
count within driver, as in track_social_effects. Associations are descriptive.
"""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(root), str(root/"src")]

import numpy as np

from experiment.config import RUNS_DIR
from experiment.analysis.shared.output import result_directory, write_results
from experiment.analysis.shared.paired import (selected_columns, matched_tracks, balanced_weights,
                                               archive_definition, correlation)
from experiment.analysis.shared.stats import bins, markdown_table

NAME = "social_direction"
MODES = ("decision", "cognition")
MODE_LABELS = dict(decision="Decision-level", cognition="Cognition-level")
COMPLEXITIES = (("low", "Low"), ("normal", "Medium"), ("high", "High"))  # table codes 0, 1, 2
# Passengers' lean in percentage points of the drive; narrow bins near zero.
LEAN_EDGES = (-1.0, -0.5, -0.3, -0.15, -0.05, 0.05, 0.15, 0.3, 0.5, 1.0)
LEAN_LABELS = tuple(f"{100*lo:+.0f} to {100*hi:+.0f} pp" for lo, hi in zip(LEAN_EDGES, LEAN_EDGES[1:]))
TRUST_EDGES = (-1.0, -0.3, -0.1, 0.1, 0.3, 1.0)
VALUES = ["baseline_automation_fraction", "passenger_solo_automation",
          "driver_automation_trust", "passenger_automation_trust_mean",
          "solo_outvoted_cycles", "solo_cognitive_pull_cycles", "solo_disagreement_cycles",
          *[f"{m}_{k}" for m in MODES
            for k in ("mismatch_cycles", "switched_on", "switched_off", "delta_automation_fraction")]]
KEYS = ["driver", "track", "composition", "start", "passenger_count", "track_difficulty"]


def weighted_mean(x, w):
    return float(np.sum(w*x)/np.sum(w))


def per_complexity(table):
    """Matched cars, their balanced weights, and every value averaged over each complexity's tracks."""
    matched = matched_tracks(table)
    driver = table["driver"][matched[:, 0]]
    count = table["passenger_count"][matched[:, 0]]
    weights = balanced_weights(driver, count)
    codes = table["track_difficulty"][matched[0]]
    groups = {}
    for code, (key, _) in enumerate(COMPLEXITIES):
        columns = np.flatnonzero(codes == code)
        if not len(columns):
            raise ValueError(f"No {key} tracks in the comparison table")
        index = matched[:, columns]
        groups[key] = {name: table[name][index].astype(np.float64).mean(axis=1) for name in VALUES}
    return driver, count, weights, groups


def direction(group, weights, steps):
    """Net change and changes toward automation / manual, in percent of the drive."""
    out = {}
    for mode in MODES:
        net = 100*group[f"{mode}_delta_automation_fraction"]
        out[mode] = dict(
            net_pp=weighted_mean(net, weights),
            toward_automation_percent=weighted_mean(100*group[f"{mode}_switched_on"]/steps, weights),
            toward_manual_percent=weighted_mean(100*group[f"{mode}_switched_off"]/steps, weights),
            changed_percent=weighted_mean(100*group[f"{mode}_mismatch_cycles"]/steps, weights),
            share_cars_more_automation=weighted_mean((net > 0).astype(float), weights),
            share_cars_less_automation=weighted_mean((net < 0).astype(float), weights))
    return out


def by_bins(x, edges, labels, group, weights):
    codes, _ = bins(x, np.asarray(edges))
    rows = []
    for i, label in enumerate(labels):
        mask = codes == i
        row = dict(group=label, low=edges[i], high=edges[i+1],
                   share_of_cars=float(weights[mask].sum()/weights.sum()), cars=int(mask.sum()))
        if mask.any():
            row["mean_lean"] = weighted_mean(x[mask], weights[mask])
            for mode in MODES:
                row[f"{mode}_net_pp"] = weighted_mean(100*group[f"{mode}_delta_automation_fraction"][mask], weights[mask])
        rows.append(row)
    return rows


def summarize(table, steps):
    driver, count, weights, groups = per_complexity(table)
    result = dict(comparison_rows=len(table["driver"]), complete_cars=len(driver), steps=steps,
                  drivers=len(np.unique(driver)),
                  weighting="Equal drivers, equal passenger counts within driver, equal cars within each cell; "
                            "each car averaged over the three persistence levels of a complexity level.",
                  lean_definition="Passengers' solo automation share minus the driver's solo automation share "
                                  "(same track and start).",
                  lean_bins=dict(edges=list(LEAN_EDGES), labels=list(LEAN_LABELS)),
                  complexities=[])
    pooled_lean, pooled_trust_lean, pooled_net = [], None, {m: [] for m in MODES}
    for key, label in COMPLEXITIES:
        group = groups[key]
        lean = group["passenger_solo_automation"]-group["baseline_automation_fraction"]
        pooled_lean.append(lean)
        for mode in MODES:
            pooled_net[mode].append(100*group[f"{mode}_delta_automation_fraction"])
        result["complexities"].append(dict(
            complexity=key, label=label, direction=direction(group, weights, steps),
            mean_lean=weighted_mean(lean, weights),
            lean_net_spearman={mode: correlation(lean, group[f"{mode}_delta_automation_fraction"]) for mode in MODES},
            by_lean=by_bins(lean, LEAN_EDGES, LEAN_LABELS, group, weights)))
        if pooled_trust_lean is None:
            pooled_trust_lean = group["passenger_automation_trust_mean"]-group["driver_automation_trust"]
    # Initial automation-trust lean, with each car averaged over all three complexity levels.
    all_levels = {f"{m}_delta_automation_fraction": np.mean([groups[k][f"{m}_delta_automation_fraction"]
                                                             for k, _ in COMPLEXITIES], axis=0) for m in MODES}
    result["initial_trust_lean"] = dict(
        definition="Passengers' mean initial automation trust minus the driver's (model scale 0-1); "
                   "net change averaged over all tracks.",
        spearman={mode: correlation(pooled_trust_lean, all_levels[f"{mode}_delta_automation_fraction"]) for mode in MODES},
        by_lean=by_bins(pooled_trust_lean, TRUST_EDGES,
                        ("Much less", "Less", "Similar", "More", "Much more"), all_levels, weights))
    result["behavioral_lean_spearman_all_tracks"] = {
        mode: correlation(np.concatenate(pooled_lean), np.concatenate(pooled_net[mode])) for mode in MODES}
    return result


def fmt(value, digits=1, signed=False):
    if value is None:
        return "—"
    return f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"


def markdown(result, figure):
    lines = [f"**{result['complete_cars']:,} matched cars** on all tracks, {result['drivers']} drivers.", "",
             result["weighting"], "",
             "Net change = the driver's automation share with passengers minus the matched solo run, "
             "in percentage points of the drive (positive = more automation). Descriptive.", "",
             "### Direction of the social effect", "",
             markdown_table(["Complexity", "Mode", "Net change (pp)", "Changed toward automation", "Changed toward manual",
                             "All changed decisions", "Cars using more automation", "Cars using less automation"],
                            [[c["label"], MODE_LABELS[m], fmt(c["direction"][m]["net_pp"], 1, True),
                              f"{c['direction'][m]['toward_automation_percent']:.1f}%",
                              f"{c['direction'][m]['toward_manual_percent']:.1f}%",
                              f"{c['direction'][m]['changed_percent']:.1f}%",
                              f"{100*c['direction'][m]['share_cars_more_automation']:.1f}%",
                              f"{100*c['direction'][m]['share_cars_less_automation']:.1f}%"]
                             for c in result["complexities"] for m in MODES]), "",
             "### Does the change follow the passengers' lean?", "",
             result["lean_definition"], "", f"![Net change by passengers' lean]({figure})", ""]
    rows = []
    for c in result["complexities"]:
        for row in c["by_lean"]:
            rows.append([c["label"], row["group"], f"{100*row['share_of_cars']:.1f}%",
                         fmt(row.get("mean_lean"), 2, True), fmt(row.get("decision_net_pp"), 1, True),
                         fmt(row.get("cognition_net_pp"), 1, True)])
    lines += [markdown_table(["Complexity", "Passengers' lean", "Cars", "Mean lean", "Decision net (pp)", "Cognition net (pp)"], rows), "",
              markdown_table(["Complexity", "Spearman ρ lean vs net, decision", "Spearman ρ lean vs net, cognition"],
                             [[c["label"], fmt(c["lean_net_spearman"]["decision"], 2), fmt(c["lean_net_spearman"]["cognition"], 2)]
                              for c in result["complexities"]]), "",
              "### Check: initial automation-trust lean", "", result["initial_trust_lean"]["definition"], "",
              markdown_table(["Initial trust lean", "Cars", "Decision net (pp)", "Cognition net (pp)"],
                             [[f"{r['group']} [{r['low']:g}, {r['high']:g})", f"{100*r['share_of_cars']:.1f}%",
                               fmt(r.get("decision_net_pp"), 1, True), fmt(r.get("cognition_net_pp"), 1, True)]
                              for r in result["initial_trust_lean"]["by_lean"]]), "",
              f"Spearman ρ, initial trust lean vs net: decision {fmt(result['initial_trust_lean']['spearman']['decision'], 2)}, "
              f"cognition {fmt(result['initial_trust_lean']['spearman']['cognition'], 2)}."]
    return "\n".join(lines)


def run(directory=None, output=None, runs=RUNS_DIR):
    table = selected_columns(KEYS+VALUES, directory)
    steps = archive_definition(runs, table["_drivers"][0], table["_tracks"][0])["parameters"]["steps"]
    result = summarize(table, steps)
    output = Path(output) if output else result_directory(NAME)
    output.mkdir(parents=True, exist_ok=True)
    write_results(NAME, result, markdown(result, "results/figures/net_change_by_lean.png"), output=output)
    from experiment.analysis.social_direction.plot import render
    render(output)
    print(f"Saved {output}: {result['complete_cars']:,} matched cars.", flush=True)
    return result


if __name__ == "__main__":
    run()
