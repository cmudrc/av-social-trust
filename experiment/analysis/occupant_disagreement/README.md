# Does the social layer change behavior only when the occupants would decide differently alone?

Compares each car's simulated change from the solo baseline with how differently
its occupants would decide if each drove alone. It checks the structural rule of
decision-level influence: a driver can only be overruled in a cycle where someone
in the car would decide differently.

Two equal-weight measures, computed from every occupant's solo baseline at the
same track and start, describe the pressure the car puts on the driver:

- **Outvoted cycles**: an unweighted vote of all occupants' solo choices goes
  against the driver's solo choice (a tie counts as manual, as in the model).
- **Cognitive-pull cycles**: the driver's own decision tree, applied to the mean
  of all occupants' solo cognitive states, gives a different choice than the
  driver's solo run.

Both ignore trust weights and feedback, so comparing them with the simulated
changes shows what the social dynamics add or remove.

Read the correlation table first: it shows which kind of disagreement tracks each
mode. The *without pressure* table shows how often the social layer changes
behavior when the car offers no equal-weight pressure. The passenger-count table
shows whether passenger count matters by itself or only through the pressure it
creates.

Open **run.py** in this folder and choose VS Code's **Run Python File**.
Alternatively, from the repository root:

```sh
python experiment/analysis/occupant_disagreement/run.py
```

Run ../compare_modes/run.py first. The first question that runs after the
comparison cache changes builds `compare_modes/results/analysis_table.npz`
(about two minutes; it also reads the solo baselines in experiment/runs/).
Later questions load that table in seconds.

Output: `experiment/analysis/occupant_disagreement/results/summary.json`, `summary.md` and
`results/figures/change_vs_pressure.png`; the latest summary is also inserted into this README.

These summaries describe associations across the sampled simulations; they do not isolate the causal effect of each parameter.

Figures are drawn by **plot.py** from the saved results, never from the runs: `change_vs_pressure` (binned means) and `pressure_heatmaps` (every car by pressure and change; run.py saves the counts in `results/pressure_change.npz`). Each is saved as PNG and as vector PDF for the paper in `results/figures/`. Edit plot.py and run it to restyle a figure in seconds without repeating the analysis; run.py calls it automatically.

To reuse this question from another script:

```python
from experiment.analysis.occupant_disagreement.run import run

# Call explicitly when this question is needed.
result = run()
```

Importing the module does not run the analysis.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-11 09:33:43 EDT

Matched comparisons: **4,633,200**.

Solo choices come from each occupant's own baseline at the same track and start. Decision-mode votes equal these solo choices exactly. Associations are descriptive.

Decision-mode changes outside cycles of solo disagreement: **0** comparisons (the model guarantees zero: a driver can only be overruled when someone in the car would decide differently).

On average the car contains **48.8** cycles of solo disagreement, **15.5** cycles where an equal-weight vote would overrule the driver and **25.7** cycles where the car's mean cognition would flip the driver's tree. Simulated changes average **12.0** (decision) and **23.9** (cognition) cycles.

### Which measure tracks the change? (Spearman ρ)

| Measure | Decision / solo | Cognition / solo |
| --- | ---: | ---: |
| Cycles with at least one passenger deciding differently alone | 0.42 | 0.23 |
| Cycles with every passenger deciding differently alone | 0.75 | 0.33 |
| Mean share of passengers deciding differently alone | 0.68 | 0.34 |
| Cycles an equal-weight vote of the car overrules the driver | 0.89 | 0.46 |
| Cycles the driver's tree flips on the car's mean cognition | 0.46 | 0.79 |
| Passengers' solo automation fraction | 0.22 | 0.13 |
| Driver's solo automation fraction | 0.65 | 0.59 |
| Driver's solo decision switches | 0.59 | 0.60 |

### What happens without social pressure?

| Condition | Share of cars | Decision mean | Decision any change | Cognition mean | Cognition any change |
| --- | ---: | ---: | ---: | ---: | ---: |
| no disagreement | 5.1% | 0.00 | 0.0% | 8.18 | 23.8% |
| not outvoted | 39.3% | 0.85 | 19.3% | 12.38 | 37.3% |
| no cognitive pull | 36.1% | 4.97 | 32.1% | 4.90 | 16.7% |
| neither outvoted nor pulled | 27.3% | 0.56 | 12.7% | 4.17 | 15.3% |

![Change versus pressure](results/figures/change_vs_pressure.png)

Every car, by its pressure and its change. Each mode lines up with its own pressure (diagonal panels), not with the other mode's:

![Pressure heatmaps](results/figures/pressure_heatmaps.png)

### Changed cycles by equal-weight outvoted cycles

| Cycles | Cars | Decision mean | Decision ≥10 | Cognition mean | Cognition ≥10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 1,819,992 | 0.9 | 1.4% | 12.4 | 25.4% |
| 1–4 | 470,296 | 2.8 | 1.9% | 24.3 | 50.0% |
| 5–9 | 401,186 | 6.2 | 8.0% | 29.2 | 58.3% |
| 10–19 | 610,344 | 11.4 | 70.6% | 29.6 | 74.6% |
| 20–39 | 734,122 | 21.8 | 85.6% | 35.7 | 82.7% |
| 40–59 | 268,286 | 35.2 | 89.5% | 35.1 | 79.0% |
| 60–100 | 328,974 | 54.2 | 89.5% | 34.0 | 68.0% |

### Changed cycles by cognitive-pull cycles

| Cycles | Cars | Decision mean | Decision ≥10 | Cognition mean | Cognition ≥10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 1,674,714 | 5.0 | 13.7% | 4.9 | 10.0% |
| 1–4 | 310,478 | 10.7 | 25.2% | 10.6 | 20.9% |
| 5–9 | 266,758 | 12.2 | 29.9% | 14.3 | 28.9% |
| 10–19 | 491,834 | 14.7 | 48.9% | 18.7 | 85.3% |
| 20–39 | 630,606 | 17.9 | 58.2% | 29.4 | 89.8% |
| 40–59 | 366,796 | 19.6 | 61.5% | 41.1 | 90.7% |
| 60–100 | 892,014 | 16.8 | 49.3% | 58.7 | 89.9% |

### Passenger count works through pressure

| Passengers | Any disagreement | All disagree | Outvoted | Decision change | Change / outvoted | Cognitive pull | Cognition change | Change / pull |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 26.6 | 26.6 | 13.3 | 10.0 | 0.75 | 24.9 | 17.4 | 0.70 |
| 2 | 39.8 | 13.2 | 13.2 | 13.0 | 0.99 | 25.6 | 22.0 | 0.86 |
| 3 | 47.6 | 8.0 | 15.9 | 10.4 | 0.65 | 25.8 | 23.8 | 0.92 |
| 4 | 53.4 | 5.4 | 16.1 | 12.5 | 0.78 | 25.8 | 25.1 | 0.97 |
| 5 | 57.0 | 3.8 | 17.1 | 12.4 | 0.72 | 25.8 | 25.4 | 0.98 |

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
