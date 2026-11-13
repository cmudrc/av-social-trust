# When the car would overrule or pull the driver, what decides whether behavior changes?

Compares the number of changed cycles with an equal-weight benchmark.
The count ratio is pooled changed cycles divided by pooled equal-weight pressure
cycles (outvoted cycles for decision mode, cognitive-pull cycles for cognition
mode). It is grouped by trust weights, homophily (alpha), passenger count, track
and the driver's solo regime, and split by direction (switching automation off
or on). Values below 1 mean fewer actual changed cycles than benchmark pressure
cycles; values above 1 mean more. The counts can include different cycles, so
this is not a probability that pressure produces change. The analysis does not
hold pressure fixed or isolate trust learning. Use `trust_learning` for a matched
experiment that enables or freezes learning.

Inbound and outbound are from the driver's point of view: inbound trust is the
passengers' trust in the driver and outbound trust is the driver's trust in
passengers, as recorded by `runner.run_metadata()`.

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
python experiment/analysis/pressure_conversion/run.py
```

Run ../compare_modes/run.py first. The first question that runs after the
comparison cache changes builds `compare_modes/results/analysis_table.npz`
(about two minutes; it also reads the solo baselines in experiment/runs/).
Later questions load that table in seconds.

Output: `experiment/analysis/pressure_conversion/results/summary.json`, `summary.md` and
`results/figures/conversion.png`; the latest summary is also inserted into this README.

These summaries describe associations across the sampled simulations; they do not isolate the causal effect of each parameter.

Figures are drawn by **plot.py** from the saved results, never from the runs: `conversion` (by passenger count and by the driver's homophily). Each is saved as PNG and as vector PDF for the paper in `results/figures/`. Edit plot.py and run it to restyle a figure in seconds without repeating the analysis; run.py calls it automatically.

To reuse this question from another script:

```python
from experiment.analysis.pressure_conversion.run import run

# Call explicitly when this question is needed.
result = run()
```

Importing the module does not run the analysis.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-11 15:47:20 EDT

Matched comparisons: **4,633,200**.

The count ratio is pooled simulated changed cycles divided by pooled equal-weight pressure cycles (outvoted cycles for decision mode, cognitive-pull cycles for cognition mode). The numerator and denominator can include different cycles, so this is not a probability that pressure changes a decision. Values above 1 mean more changed cycles than benchmark pressure cycles. Descriptive; pressure and other conditions are not held fixed.

Overall count ratio: decision **0.77**, cognition **0.93**. The decision-mode off-direction count ratio is **0.71** and the on-direction count ratio is **1.00**; these are not conversion probabilities.

![Conversion](results/figures/conversion.png)

### Which conditions change conversion most?

Spread is the largest minus the smallest group conversion for that condition.

| Condition | Decision spread | Cognition spread |
| --- | ---: | ---: |
| Driver's homophily when trusting passengers (alpha) | 0.35 | 0.08 |
| Passengers | 0.33 | 0.28 |
| Driver alone | 0.28 | 0.29 |
| Driver's initial self-weight | 0.11 | 0.22 |
| Track difficulty | 0.19 | 0.08 |
| Passengers' homophily when trusting the driver (alpha) | 0.14 | 0.08 |
| Driver's trust in passengers | 0.13 | 0.09 |
| Passengers' trust in the driver | 0.10 | 0.10 |
| Driver's initial self-trust | 0.10 | 0.05 |
| Track persistence | 0.03 | 0.02 |

### Driver's initial self-weight

| Group | Cars | Outvoted | Decision change | Decision conversion | Off conversion | On conversion | Cognitive pull | Cognition change | Cognition conversion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [0, 0.2) | 2,022,354 | 15.9 | 12.5 | 0.79 | 0.73 | 1.02 | 25.7 | 24.8 | 0.96 |
| [0.2, 0.4) | 1,785,780 | 15.7 | 11.9 | 0.76 | 0.70 | 0.94 | 25.7 | 23.8 | 0.93 |
| [0.4, 0.5) | 446,283 | 14.5 | 11.5 | 0.80 | 0.73 | 0.99 | 25.8 | 22.7 | 0.88 |
| [0.5, 0.6) | 157,950 | 14.1 | 10.8 | 0.77 | 0.65 | 1.19 | 25.7 | 21.2 | 0.82 |
| [0.6, 0.8) | 148,338 | 13.6 | 10.1 | 0.74 | 0.64 | 1.06 | 25.6 | 20.7 | 0.81 |
| [0.8, 1] | 72,495 | 13.8 | 9.5 | 0.69 | 0.52 | 1.42 | 25.6 | 19.0 | 0.74 |

### Passengers' trust in the driver

| Group | Cars | Outvoted | Decision change | Decision conversion | Off conversion | On conversion | Cognitive pull | Cognition change | Cognition conversion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [0, 0.2) | 218,016 | 14.6 | 12.6 | 0.86 | 0.75 | 1.24 | 25.5 | 23.6 | 0.92 |
| [0.2, 0.4) | 1,027,836 | 15.6 | 12.1 | 0.78 | 0.71 | 1.02 | 25.8 | 24.3 | 0.94 |
| [0.4, 0.6) | 1,938,501 | 15.7 | 12.1 | 0.77 | 0.72 | 0.96 | 25.8 | 24.2 | 0.94 |
| [0.6, 0.8) | 1,168,848 | 15.5 | 11.8 | 0.76 | 0.70 | 0.97 | 25.7 | 23.6 | 0.92 |
| [0.8, 1] | 279,999 | 14.3 | 11.2 | 0.78 | 0.67 | 1.18 | 25.5 | 21.4 | 0.84 |

### Driver's trust in passengers

| Group | Cars | Outvoted | Decision change | Decision conversion | Off conversion | On conversion | Cognitive pull | Cognition change | Cognition conversion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [0, 0.2) | 217,827 | 14.6 | 10.6 | 0.73 | 0.65 | 1.01 | 25.7 | 21.8 | 0.85 |
| [0.2, 0.4) | 1,021,734 | 15.6 | 11.6 | 0.74 | 0.68 | 0.96 | 25.8 | 23.9 | 0.92 |
| [0.4, 0.6) | 1,947,879 | 15.7 | 12.2 | 0.77 | 0.72 | 0.97 | 25.7 | 24.2 | 0.94 |
| [0.6, 0.8) | 1,166,319 | 15.5 | 12.2 | 0.79 | 0.73 | 1.01 | 25.8 | 24.0 | 0.93 |
| [0.8, 1] | 279,441 | 14.3 | 12.4 | 0.87 | 0.73 | 1.34 | 25.5 | 22.4 | 0.88 |

### Passengers' homophily when trusting the driver (alpha)

| Group | Cars | Outvoted | Decision change | Decision conversion | Off conversion | On conversion | Cognitive pull | Cognition change | Cognition conversion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [0, 0.2) | 186,714 | 14.5 | 11.1 | 0.77 | 0.67 | 1.09 | 25.6 | 21.9 | 0.86 |
| [0.2, 0.4) | 1,084,392 | 15.4 | 11.8 | 0.76 | 0.70 | 0.97 | 25.8 | 23.7 | 0.92 |
| [0.4, 0.6) | 2,089,944 | 15.8 | 12.0 | 0.76 | 0.71 | 0.96 | 25.8 | 24.2 | 0.94 |
| [0.6, 0.8) | 1,083,015 | 15.5 | 12.2 | 0.79 | 0.72 | 1.02 | 25.7 | 23.9 | 0.93 |
| [0.8, 1] | 189,135 | 14.4 | 13.0 | 0.90 | 0.76 | 1.37 | 25.4 | 22.3 | 0.88 |

### Driver's homophily when trusting passengers (alpha)

| Group | Cars | Outvoted | Decision change | Decision conversion | Off conversion | On conversion | Cognitive pull | Cognition change | Cognition conversion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [0, 0.2) | 185,841 | 14.3 | 14.0 | 0.98 | 0.82 | 1.55 | 25.5 | 22.2 | 0.87 |
| [0.2, 0.4) | 1,085,733 | 15.4 | 13.2 | 0.85 | 0.77 | 1.16 | 25.7 | 23.9 | 0.93 |
| [0.4, 0.6) | 2,091,627 | 15.8 | 12.1 | 0.77 | 0.71 | 0.96 | 25.8 | 24.2 | 0.94 |
| [0.6, 0.8) | 1,083,105 | 15.4 | 10.7 | 0.70 | 0.65 | 0.85 | 25.8 | 23.8 | 0.92 |
| [0.8, 1] | 186,894 | 14.3 | 9.0 | 0.63 | 0.56 | 0.87 | 25.6 | 22.0 | 0.86 |

### Driver's initial self-trust

| Group | Cars | Outvoted | Decision change | Decision conversion | Off conversion | On conversion | Cognitive pull | Cognition change | Cognition conversion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.01 | 772,200 | 14.7 | 12.2 | 0.83 | 0.74 | 1.12 | 26.2 | 25.0 | 0.95 |
| 0.2 | 772,200 | 15.9 | 12.8 | 0.80 | 0.74 | 1.06 | 25.3 | 24.1 | 0.95 |
| 0.4 | 772,200 | 16.3 | 12.7 | 0.78 | 0.72 | 1.01 | 25.3 | 23.2 | 0.92 |
| 0.6 | 772,200 | 15.5 | 11.8 | 0.76 | 0.70 | 0.97 | 25.8 | 23.8 | 0.92 |
| 0.8 | 772,200 | 15.5 | 11.5 | 0.74 | 0.69 | 0.94 | 25.9 | 23.4 | 0.91 |
| 0.99 | 772,200 | 15.2 | 11.0 | 0.73 | 0.67 | 0.90 | 25.9 | 23.5 | 0.91 |

### Passengers

| Group | Cars | Outvoted | Decision change | Decision conversion | Off conversion | On conversion | Cognitive pull | Cognition change | Cognition conversion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 140,400 | 13.3 | 10.0 | 0.75 | 0.38 | — | 24.9 | 17.4 | 0.70 |
| 2 | 1,123,200 | 13.2 | 13.0 | 0.99 | 0.97 | 1.01 | 25.6 | 22.0 | 0.86 |
| 3 | 1,123,200 | 15.9 | 10.4 | 0.65 | 0.54 | 1.47 | 25.8 | 23.8 | 0.92 |
| 4 | 1,123,200 | 16.1 | 12.5 | 0.78 | 0.84 | 0.64 | 25.8 | 25.1 | 0.97 |
| 5 | 1,123,200 | 17.1 | 12.4 | 0.72 | 0.65 | 1.11 | 25.8 | 25.4 | 0.98 |

### Track difficulty

| Group | Cars | Outvoted | Decision change | Decision conversion | Off conversion | On conversion | Cognitive pull | Cognition change | Cognition conversion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low | 1,544,400 | 26.4 | 18.7 | 0.71 | 0.62 | 0.94 | 30.0 | 28.7 | 0.96 |
| normal | 1,544,400 | 13.2 | 11.0 | 0.83 | 0.79 | 1.07 | 24.7 | 23.0 | 0.93 |
| high | 1,544,400 | 7.0 | 6.3 | 0.90 | 0.85 | 1.41 | 22.5 | 19.8 | 0.88 |

### Track persistence

| Group | Cars | Outvoted | Decision change | Decision conversion | Off conversion | On conversion | Cognitive pull | Cognition change | Cognition conversion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.3 | 1,544,400 | 15.7 | 12.3 | 0.78 | 0.73 | 1.10 | 24.0 | 22.1 | 0.92 |
| 0.6 | 1,544,400 | 15.3 | 12.0 | 0.78 | 0.71 | 1.01 | 25.9 | 23.9 | 0.92 |
| 0.9 | 1,544,400 | 15.5 | 11.7 | 0.75 | 0.70 | 0.93 | 27.3 | 25.6 | 0.94 |

### Driver alone

| Group | Cars | Outvoted | Decision change | Decision conversion | Off conversion | On conversion | Cognitive pull | Cognition change | Cognition conversion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| always manual | 1,971,750 | 4.6 | 4.3 | 0.94 | — | 0.94 | 8.9 | 10.3 | 1.15 |
| varying | 2,555,850 | 22.2 | 16.8 | 0.76 | 0.72 | 1.08 | 38.0 | 33.8 | 0.89 |
| always automated | 105,600 | 57.2 | 38.3 | 0.67 | 0.67 | — | 42.8 | 37.0 | 0.86 |

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
