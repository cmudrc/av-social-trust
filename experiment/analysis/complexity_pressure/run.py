"""Does high task complexity shrink the social effect because the occupants already agree?

For each complexity level this reports how often the car puts pressure on the
driver, measured from every occupant's solo run at the same track and start:

- disagreement cycles: at least one passenger would decide differently alone;
- outvoted cycles: an equal-weight vote of the car overrules the driver's solo
  choice (the pressure decision-level influence can act on);
- cognitive-pull cycles: the driver's own tree, applied to the mean of the
  occupants' solo cognitive states, flips the driver's solo choice (the pressure
  cognition-level influence can act on).

These are compared with the simulated changes from solo driving. Cars, weights
and persistence averaging match track_social_effects and social_direction.
Associations are descriptive.
"""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(root), str(root/"src")]

from experiment.config import RUNS_DIR
from experiment.analysis.shared.output import result_directory, write_results
from experiment.analysis.shared.paired import selected_columns, archive_definition, correlation
from experiment.analysis.shared.stats import markdown_table
from experiment.analysis.social_direction.run import COMPLEXITIES, KEYS, VALUES, per_complexity, weighted_mean

NAME = "complexity_pressure"
PRESSURES = dict(decision="solo_outvoted_cycles", cognition="solo_cognitive_pull_cycles")


def summarize(table, steps):
    driver, _, weights, groups = per_complexity(table)
    rows = []
    for key, label in COMPLEXITIES:
        g = groups[key]
        row = dict(complexity=key, label=label,
                   disagreement_percent=weighted_mean(100*g["solo_disagreement_cycles"]/steps, weights))
        for mode, pressure in PRESSURES.items():
            p = 100*g[pressure]/steps
            change = 100*g[f"{mode}_mismatch_cycles"]/steps
            row[f"{mode}_pressure_percent"] = weighted_mean(p, weights)
            row[f"{mode}_changed_percent"] = weighted_mean(change, weights)
            row[f"{mode}_cars_without_pressure"] = weighted_mean((g[pressure] == 0).astype(float), weights)
            row[f"{mode}_change_per_pressure"] = (row[f"{mode}_changed_percent"]/row[f"{mode}_pressure_percent"]
                                                 if row[f"{mode}_pressure_percent"] else None)
            row[f"{mode}_pressure_change_spearman"] = correlation(g[pressure], g[f"{mode}_mismatch_cycles"])
        rows.append(row)
    return dict(comparison_rows=len(table["driver"]), complete_cars=len(driver), steps=steps,
                weighting="Equal drivers, equal passenger counts within driver; each car averaged over persistence.",
                interpretation="Pressure comes from each occupant's solo run and ignores trust weights and feedback. "
                               "Descriptive.",
                complexities=rows)


def markdown(result):
    rows = result["complexities"]
    pct = lambda v: f"{v:.1f}%"
    return "\n".join([
        f"**{result['complete_cars']:,} matched cars.** {result['weighting']}", "", result["interpretation"], "",
        "### Pressure and change by complexity (percent of the drive)", "",
        markdown_table(["Complexity", "Any passenger disagrees", "Outvoted (decision pressure)", "Decision-level changed",
                        "Cognitive pull (cognition pressure)", "Cognition-level changed"],
                       [[r["label"], pct(r["disagreement_percent"]), pct(r["decision_pressure_percent"]),
                         pct(r["decision_changed_percent"]), pct(r["cognition_pressure_percent"]),
                         pct(r["cognition_changed_percent"])] for r in rows]), "",
        markdown_table(["Complexity", "Cars never outvoted", "Cars never pulled", "Decision change / pressure",
                        "Cognition change / pressure", "Spearman ρ pressure vs change, decision",
                        "Spearman ρ pressure vs change, cognition"],
                       [[r["label"], pct(100*r["decision_cars_without_pressure"]), pct(100*r["cognition_cars_without_pressure"]),
                         f"{r['decision_change_per_pressure']:.2f}", f"{r['cognition_change_per_pressure']:.2f}",
                         f"{r['decision_pressure_change_spearman']:.2f}", f"{r['cognition_pressure_change_spearman']:.2f}"]
                        for r in rows])])


def run(directory=None, output=None, runs=RUNS_DIR):
    table = selected_columns(KEYS+VALUES, directory)
    steps = archive_definition(runs, table["_drivers"][0], table["_tracks"][0])["parameters"]["steps"]
    result = summarize(table, steps)
    output = Path(output) if output else result_directory(NAME)
    output.mkdir(parents=True, exist_ok=True)
    write_results(NAME, result, markdown(result), output=output)
    print(f"Saved {output}.", flush=True)
    return result


if __name__ == "__main__":
    run()
