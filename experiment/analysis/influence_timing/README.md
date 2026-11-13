# Does the social effect fade, persist or build up during a drive?

The revised paper figures show only driver decisions different from solo:
`timing` (overall early/later), `timing_by_complexity` (the same split by
Low / Medium / High complexity), `step_blocks` (overall ten-step averages),
and `step_blocks_by_complexity` (ten-step averages for each complexity).
`cycle_dynamics` retains unsmoothed per-step rates as a diagnostic, with the
equal-weight pressure curves removed. All time axes say **Steps**.
Ten-step blocks are 1–10, 11–20, …, 91–100 and their values are saved in
`results/step_blocks.json`. Step 0 is not a simulated decision.

Compares the share of cycles that differ from the solo baseline early in the
drive (cycles 1–20) and later (cycles 21–100), for both influence modes. It also
compares how early and late *pressure* changes, which helps assess two explanations
for a fading effect: the occupants coming to agree with each other, or the trust
dynamics damping the influence. It also reports when the first change happens,
and how often cognition-level influence changes behavior with no equal-weight
cognitive pull at all. Unequal weights and cognitive feedback can both produce
such changes; this observational comparison does not isolate either mechanism.

Two equal-weight measures, computed from every occupant's solo baseline at the
same track and start, describe the pressure the car puts on the driver:

- **Outvoted cycles**: an unweighted vote of all occupants' solo choices goes
  against the driver's solo choice (a tie counts as manual, as in the model).
- **Cognitive-pull cycles**: the driver's own decision tree, applied to the mean
  of all occupants' solo cognitive states, gives a different choice than the
  driver's solo run.

Both ignore trust weights and feedback, so comparing them with the simulated
changes shows what the social dynamics add or remove.

Open **run.py** in this folder and choose VS Code's **Run Python File**.
Alternatively, from the repository root:

```sh
python experiment/analysis/influence_timing/run.py
```

Run ../compare_modes/run.py first. The first question that runs after the
comparison cache changes builds `compare_modes/results/analysis_table.npz`
(about two minutes; it also reads the solo baselines in experiment/runs/).
Later questions load that table in seconds.

Output: `experiment/analysis/influence_timing/results/summary.json`, `summary.md` and
`results/figures/timing.png`; the latest summary is also inserted into this README.

These summaries describe associations across the sampled simulations; they do not isolate the causal effect of each parameter.

Figures are drawn by **plot.py** from the saved results, never from the runs: `timing` (early versus late) and `cycle_dynamics` (share of cars changed and under pressure at every cycle, by track difficulty). The per-cycle curves need each car's decisions, which the comparison cache does not keep, so run.py reads a fixed random sample of cars from the archives (`SAMPLE_PER_ARCHIVE` per driver and track; about two and a half minutes) and saves the curves in `results/cycles.npz`. Each is saved as PNG and as vector PDF for the paper in `results/figures/`. Edit plot.py and run it to restyle a figure in seconds without repeating the analysis; run.py calls it automatically.

To reuse this question from another script:

```python
from experiment.analysis.influence_timing.run import run

# Call explicitly when this question is needed.
result = run()
```

Importing the module does not run the analysis.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-11 15:47:20 EDT

Matched comparisons: **4,633,200**.

Mismatch rate is the share of cycles whose automation decision differs from the solo baseline, in cycles 1–20 (early) and 21–100 (late). Pressure rate is the share of cycles with equal-weight pressure in the same window (outvoted cycles for decision mode, cognitive-pull cycles for cognition mode). A late/early ratio below 1 means the effect fades; above 1 means it builds up. Descriptive.

| Mode | Early mismatch | Late mismatch | Late / early | Early pressure | Late pressure | Pressure late / early |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Decision | 16.1% | 11.0% | 0.68 | 19.0% | 14.6% | 0.77 |
| Cognition | 22.8% | 24.1% | 1.06 | 24.2% | 26.1% | 1.08 |

![Timing](results/figures/timing.png)

Per-cycle curves use a random sample of 46,800 cars (200 per driver and track, seed 11):

![Cycle by cycle](results/figures/cycle_dynamics.png)

### When does the first change happen?

| Mode | Cars with any change | First change: quartiles | By cycle 5 | By cycle 20 |
| --- | ---: | ---: | ---: | ---: |
| Decision | 66.1% | 1 / 4 / 25 | 53.8% | 72.4% |
| Cognition | 67.8% | 1 / 5 / 23 | 50.7% | 73.3% |

### Cognition-level changes the equal-weight snapshot does not predict

In **36.1%** of cars the mean of the occupants' solo cognition never flips the driver's tree. Cognition influence still changes **16.7%** of them (mean **4.90** cycles; early mismatch 2.8%, late 5.4%). Unequal trust weights and feedback can both produce changes absent from this equal-weight snapshot. Mixed cognition becomes the next cycle's state, allowing effects to accumulate; this comparison does not isolate that mechanism.

### Driver's homophily when trusting passengers (alpha)

| Group | Cars | Decision early | Decision late | Decision late / early | Outvoted late / early | Cognition early | Cognition late | Cognition late / early | Pull late / early |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [0, 0.2) | 185,841 | 18.0% | 13.1% | 0.73 | 0.76 | 21.6% | 22.3% | 1.03 | 1.09 |
| [0.2, 0.4) | 1,085,733 | 17.3% | 12.1% | 0.70 | 0.77 | 23.0% | 24.2% | 1.05 | 1.07 |
| [0.4, 0.6) | 2,091,627 | 16.3% | 11.1% | 0.68 | 0.77 | 23.0% | 24.5% | 1.06 | 1.08 |
| [0.6, 0.8) | 1,083,105 | 14.8% | 9.7% | 0.66 | 0.77 | 22.8% | 24.1% | 1.06 | 1.08 |
| [0.8, 1] | 186,894 | 12.9% | 8.1% | 0.62 | 0.77 | 21.5% | 22.1% | 1.03 | 1.10 |

### Driver's trust in passengers

| Group | Cars | Decision early | Decision late | Decision late / early | Outvoted late / early | Cognition early | Cognition late | Cognition late / early | Pull late / early |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [0, 0.2) | 217,827 | 10.1% | 10.8% | 1.07 | 0.76 | 19.3% | 22.4% | 1.16 | 1.09 |
| [0.2, 0.4) | 1,021,734 | 14.5% | 10.8% | 0.75 | 0.77 | 22.6% | 24.2% | 1.07 | 1.07 |
| [0.4, 0.6) | 1,947,879 | 16.7% | 11.1% | 0.66 | 0.77 | 23.1% | 24.5% | 1.06 | 1.08 |
| [0.6, 0.8) | 1,166,319 | 17.3% | 11.0% | 0.63 | 0.77 | 23.3% | 24.2% | 1.04 | 1.08 |
| [0.8, 1] | 279,441 | 18.2% | 10.9% | 0.60 | 0.76 | 22.7% | 22.3% | 0.98 | 1.09 |

### Passengers

| Group | Cars | Decision early | Decision late | Decision late / early | Outvoted late / early | Cognition early | Cognition late | Cognition late / early | Pull late / early |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 140,400 | 14.0% | 8.9% | 0.64 | 0.77 | 18.1% | 17.2% | 0.95 | 1.11 |
| 2 | 1,123,200 | 16.1% | 12.3% | 0.76 | 0.76 | 21.6% | 22.1% | 1.02 | 1.09 |
| 3 | 1,123,200 | 15.2% | 9.2% | 0.60 | 0.76 | 22.8% | 24.0% | 1.05 | 1.08 |
| 4 | 1,123,200 | 16.8% | 11.4% | 0.68 | 0.77 | 23.6% | 25.5% | 1.08 | 1.07 |
| 5 | 1,123,200 | 16.7% | 11.3% | 0.67 | 0.77 | 23.9% | 25.8% | 1.08 | 1.06 |

### Track difficulty

| Group | Cars | Decision early | Decision late | Decision late / early | Outvoted late / early | Cognition early | Cognition late | Cognition late / early | Pull late / early |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low | 1,544,400 | 18.4% | 18.8% | 1.02 | 1.17 | 24.7% | 29.7% | 1.20 | 1.20 |
| normal | 1,544,400 | 14.3% | 10.2% | 0.71 | 0.77 | 21.5% | 23.4% | 1.09 | 1.08 |
| high | 1,544,400 | 15.7% | 3.9% | 0.25 | 0.24 | 22.3% | 19.2% | 0.86 | 0.94 |

### Driver alone

| Group | Cars | Decision early | Decision late | Decision late / early | Outvoted late / early | Cognition early | Cognition late | Cognition late / early | Pull late / early |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| always manual | 1,971,750 | 6.4% | 3.8% | 0.60 | 0.83 | 9.1% | 10.6% | 1.16 | 1.04 |
| varying | 2,555,850 | 22.8% | 15.3% | 0.67 | 0.74 | 32.8% | 34.0% | 1.04 | 1.09 |
| always automated | 105,600 | 37.3% | 38.5% | 1.03 | 1.03 | 39.0% | 36.5% | 0.94 | 1.04 |

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
