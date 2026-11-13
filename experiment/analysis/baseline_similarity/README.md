# When do decision- and/or cognition-level driving look like driving alone?

For every simulated car, compares the driver's 100 automation decisions under
decision-level and cognition-level influence with the same driver's solo run, and
asks which of the two still *look like driving alone*. A mode looks alike when at
most `ALIKE_MAX_CHANGED` (default 5) of the 100 cycles differ from the solo run.
Each car falls into one of four categories:

| Category | Decision-level | Cognition-level |
| --- | --- | --- |
| both alike | alike | alike |
| only decision alike | alike | changed |
| only cognition alike | changed | alike |
| neither alike | changed | changed |

The results report how often each category occurs, how it shifts with the
scenario (passenger count, track difficulty, the driver's solo behavior,
participant) and with the solo-counterfactual pressure (outvoted and
cognitive-pull cycles; see occupant_disagreement). Two calculations look for
predictors:

- **AUC of each feature alone** for "decision alike", "cognition alike" and
  "both alike". 0.5 means the feature does not separate alike from changed cars;
  values far from 0.5 in either direction mean it does.
- **A depth-3 classification tree** (shared/rules.py, NumPy only) trained on 70%
  of the cars and tested on the other 30%. Its leaves read as rules such as
  "outvoted cycles < 6 and cognitive-pull cycles < 5 → both alike".

The run also writes **the per-car dataset** `results/similarity_dataset.csv.gz`
(one row per car, about 150 MB compressed): driver, track, passengers, scenario
settings, solo behavior, pressure, changed cycles and agreement with driving
alone for decision vs solo, cognition vs solo and decision vs cognition, and the
category. Set `EXPORT_DATASET = False` in run.py to skip it.

Open **run.py** in this folder and choose VS Code's **Run Python File**.
Alternatively, from the repository root:

```sh
python experiment/analysis/baseline_similarity/run.py
```

Run ../compare_modes/run.py first. With the shared analysis table already built,
the run takes about a minute, most of it writing the dataset.

Figures are drawn by **plot.py** from the saved results, never from the runs:
`agreement_map` (every car by decision- and cognition-level agreement, from
`results/agreement_map.npz`), `pressure_plane` (share of alike cars across
outvoted × cognitive-pull cycles), `categories_by_condition`, `predictors` (AUCs)
and `participants`. Each is saved as PNG and PDF in `results/figures/`. Edit
plot.py and run it to restyle in seconds; run.py calls it automatically.

These summaries describe associations across the sampled simulations; they do not isolate the causal effect of each parameter.

To reuse this question from another script:

```python
from experiment.analysis.baseline_similarity.run import run

# Call explicitly when this question is needed.
result = run()
```

Importing the module does not run the analysis.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-11 14:07:38 EDT

Matched comparisons: **4,633,200**.

A mode looks like driving alone when at most 5 of 100 cycles differ from the driver's solo run. Shares and AUCs describe the simulated grid; they are not causal estimates.

| Category | Share of cars |
| --- | ---: |
| both alike | 33.6% |
| only decision alike | 21.1% |
| only cognition alike | 8.3% |
| neither alike | 37.0% |

![Agreement map](results/figures/agreement_map.png)

### Sensitivity to the threshold

| Changed cycles allowed | both alike | only decision alike | only cognition alike | neither alike |
| --- | ---: | ---: | ---: | ---: |
| 0 | 22.1% | 11.8% | 10.1% | 56.0% |
| 5 | 33.6% | 21.1% | 8.3% | 37.0% |
| 10 | 41.0% | 25.2% | 8.2% | 25.6% |
| 20 | 54.7% | 25.2% | 7.5% | 12.7% |

### Where each category lives in the pressure plane

![Pressure plane](results/figures/pressure_plane.png)

### By condition

![Categories by condition](results/figures/categories_by_condition.png)

#### Passengers

| Group | Cars | both alike | only decision alike | only cognition alike | neither alike |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 140,400 | 34.2% | 26.5% | 12.6% | 26.8% |
| 2 | 1,123,200 | 33.0% | 23.0% | 9.9% | 34.0% |
| 3 | 1,123,200 | 34.9% | 22.1% | 7.1% | 35.9% |
| 4 | 1,123,200 | 32.8% | 20.0% | 8.3% | 38.9% |
| 5 | 1,123,200 | 33.4% | 18.4% | 7.6% | 40.6% |

#### Track difficulty

| Group | Cars | both alike | only decision alike | only cognition alike | neither alike |
| --- | ---: | ---: | ---: | ---: | ---: |
| low | 1,544,400 | 17.0% | 23.1% | 13.7% | 46.2% |
| normal | 1,544,400 | 34.8% | 21.1% | 6.6% | 37.5% |
| high | 1,544,400 | 48.9% | 19.0% | 4.8% | 27.4% |

#### Driver alone

| Group | Cars | both alike | only decision alike | only cognition alike | neither alike |
| --- | ---: | ---: | ---: | ---: | ---: |
| always manual | 1,971,750 | 67.8% | 15.7% | 12.4% | 4.1% |
| varying | 2,555,850 | 7.9% | 25.6% | 4.3% | 62.1% |
| always automated | 105,600 | 14.4% | 10.9% | 30.7% | 44.0% |

#### Outvoted cycles

| Group | Cars | both alike | only decision alike | only cognition alike | neither alike |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 1,819,992 | 69.7% | 26.9% | 1.6% | 1.8% |
| 1–4 | 470,296 | 41.2% | 50.5% | 2.0% | 6.3% |
| 5–9 | 401,186 | 11.3% | 26.2% | 12.3% | 50.3% |
| 10–19 | 610,344 | 3.9% | 12.6% | 16.4% | 67.1% |
| 20–39 | 734,122 | 1.5% | 6.1% | 11.8% | 80.6% |
| 40–100 | 597,260 | 2.0% | 3.8% | 18.7% | 75.5% |

#### Cognitive-pull cycles

| Group | Cars | both alike | only decision alike | only cognition alike | neither alike |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 1,674,714 | 73.8% | 8.5% | 14.8% | 2.9% |
| 1–4 | 310,478 | 52.9% | 15.0% | 20.9% | 11.2% |
| 5–9 | 266,758 | 16.7% | 28.1% | 6.7% | 48.5% |
| 10–19 | 491,834 | 5.7% | 32.4% | 3.0% | 58.9% |
| 20–39 | 630,606 | 4.7% | 25.4% | 2.1% | 67.9% |
| 40–100 | 1,258,810 | 4.2% | 31.2% | 2.2% | 62.4% |

### What predicts looking like driving alone?

AUC of each feature alone: 0.5 means no separation; above 0.5, higher values go with looking alike; below 0.5, lower values do.

![Predictors](results/figures/predictors.png)

| Feature | Decision alike | Cognition alike | Both alike |
| --- | ---: | ---: | ---: |
| Outvoted cycles | 0.06 | 0.23 | 0.13 |
| Cognitive-pull cycles | 0.28 | 0.09 | 0.12 |
| Driver's solo decision switches | 0.21 | 0.13 | 0.15 |
| Driver's solo automation fraction | 0.19 | 0.15 | 0.14 |
| Cycles any passenger would decide differently | 0.30 | 0.37 | 0.28 |
| Passengers' solo automation fraction | 0.39 | 0.42 | 0.33 |
| Track difficulty | 0.62 | 0.60 | 0.66 |
| Track persistence | 0.45 | 0.41 | 0.39 |
| Driver's initial automation trust | 0.45 | 0.46 | 0.46 |
| Driver's initial perceived risk | 0.52 | 0.54 | 0.54 |
| Driver's initial self-weight | 0.54 | 0.51 | 0.52 |
| Driver's initial self-trust | 0.53 | 0.51 | 0.51 |
| Passengers' initial automation trust | 0.49 | 0.49 | 0.47 |
| Passenger count | 0.48 | 0.49 | 0.50 |
| Driver's homophily when trusting passengers (alpha) | 0.52 | 0.50 | 0.51 |
| Driver's trust in passengers | 0.48 | 0.50 | 0.49 |
| Passengers' trust in the driver | 0.51 | 0.51 | 0.51 |
| Driver's initial workload | 0.50 | 0.51 | 0.50 |
| Passengers' homophily when trusting the driver (alpha) | 0.49 | 0.50 | 0.50 |
| Passengers' initial self-trust | 0.50 | 0.50 | 0.50 |

### Rules (depth-3 tree)

Held-out accuracy **82.0%** (always guessing the most common category: 37.0%).

| Rule | Cars (training) | Most likely | both alike | only decision alike | only cognition alike | neither alike |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Outvoted cycles < 6 and Cognitive-pull cycles < 5 and Passengers' solo automation fraction < 0.155 | 752,275 | both alike | 89.4% | 9.6% | 0.9% | 0.1% |
| Outvoted cycles < 6 and Cognitive-pull cycles < 5 and Passengers' solo automation fraction ≥ 0.155 | 345,331 | both alike | 79.1% | 14.4% | 5.7% | 0.8% |
| Outvoted cycles < 6 and Cognitive-pull cycles ≥ 5 and Driver's solo automation fraction < 0.06 | 270,902 | only decision alike | 32.5% | 64.4% | 1.1% | 2.0% |
| Outvoted cycles < 6 and Cognitive-pull cycles ≥ 5 and Driver's solo automation fraction ≥ 0.06 | 307,007 | only decision alike | 3.6% | 81.8% | 0.3% | 14.3% |
| Outvoted cycles ≥ 6 and Cognitive-pull cycles < 5 and Driver's solo decision switches < 1 | 220,254 | only cognition alike | 12.1% | 2.7% | 70.5% | 14.7% |
| Outvoted cycles ≥ 6 and Cognitive-pull cycles < 5 and Driver's solo decision switches ≥ 1 | 72,276 | only cognition alike | 10.7% | 5.2% | 53.1% | 31.1% |
| Outvoted cycles ≥ 6 and Cognitive-pull cycles ≥ 5 and Outvoted cycles < 17 | 424,929 | neither alike | 1.2% | 17.5% | 3.6% | 77.7% |
| Outvoted cycles ≥ 6 and Cognitive-pull cycles ≥ 5 and Outvoted cycles ≥ 17 | 850,413 | neither alike | 0.5% | 6.0% | 3.8% | 89.7% |

### By participant

![Participants](results/figures/participants.png)

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
