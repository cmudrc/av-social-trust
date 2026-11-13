# Which participants are affected most by the social layer, and which model properties explain it?

Summarizes each participant as a driver (pressure faced, changed cycles,
conversion) and as a passenger (mean change in the cars they ride in). It
relates these to properties of the fitted participant models: cognitive memory
(the largest absolute eigenvalue of A), track-input sensitivity (the largest
absolute B), the number of modeled cognitive states and the decision-tree size.

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
python experiment/analysis/participant_susceptibility/run.py
```

Run ../compare_modes/run.py first. The first question that runs after the
comparison cache changes builds `compare_modes/results/analysis_table.npz`
(about two minutes; it also reads the solo baselines in experiment/runs/).
Later questions load that table in seconds.

Output: `experiment/analysis/participant_susceptibility/results/summary.json`, `summary.md` and
`results/figures/participants.png`; the latest summary is also inserted into this README.

With 26 participants the correlations are exploratory; they describe these fitted models, not people in general.

Figures are drawn by **plot.py** from the saved results, never from the runs: `participants` (change versus pressure, one point per participant). Each is saved as PNG and as vector PDF for the paper in `results/figures/`. Edit plot.py and run it to restyle a figure in seconds without repeating the analysis; run.py calls it automatically.

To reuse this question from another script:

```python
from experiment.analysis.participant_susceptibility.run import run

# Call explicitly when this question is needed.
result = run()
```

Importing the module does not run the analysis.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-10 23:19:00 EDT

Participants: **26**; matched comparisons: **4,633,200**.

Each participant is summarized as a driver and as a passenger. Spearman correlations use 26 participants, so they are exploratory. Model properties come from the fitted A, B and tree.

![Participants](results/figures/participants.png)

### What goes with susceptibility? (Spearman ρ across participants)

| Measure | Outvoted | Cognitive pull | Cognitive memory (largest absolute eigenvalue of A) | Track-input sensitivity (largest absolute B) | Modeled cognitive states | Decision-tree leaves |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Decision change | 0.99 | 0.75 | 0.36 | -0.44 | -0.14 | -0.07 |
| Cognition change | 0.77 | 0.94 | 0.26 | -0.34 | -0.11 | -0.12 |
| Decision conversion | -0.77 | -0.84 | -0.16 | 0.16 | 0.30 | 0.23 |
| Cognition conversion | 0.05 | -0.23 | 0.57 | -0.57 | 0.50 | 0.32 |
| Solo automation | 0.80 | 0.85 | 0.02 | -0.04 | -0.41 | -0.22 |
| Solo switches | 0.63 | 0.78 | -0.20 | 0.20 | -0.52 | -0.33 |
| Decision change caused as passenger | -0.84 | -0.63 | -0.18 | 0.16 | 0.34 | 0.27 |
| Cognition change caused as passenger | -0.27 | -0.30 | -0.40 | 0.31 | 0.04 | -0.08 |

### Participants

| Participant | Solo automation | Solo switches | Outvoted | Decision change | Decision conversion | Cognitive pull | Cognition change | Cognition conversion | As passenger: decision | As passenger: cognition | Memory | Input sensitivity | States |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P01 | 26.8% | 1.5 | 16.5 | 12.0 | 0.73 | 30.5 | 27.1 | 0.89 | 12.2 | 23.7 | 0.947 | 0.007 | perceived_risk |
| P02 | 19.2% | 1.4 | 13.0 | 9.7 | 0.75 | 73.4 | 68.2 | 0.93 | 12.4 | 21.9 | 1.000 | 0.024 | automation_trust, perceived_risk |
| P03 | 2.1% | 0.3 | 7.6 | 6.7 | 0.89 | 16.0 | 12.7 | 0.80 | 12.6 | 24.3 | 0.538 | 0.023 | automation_trust, workload |
| P04 | 2.6% | 0.4 | 8.5 | 7.5 | 0.89 | 9.2 | 11.9 | 1.29 | 12.3 | 25.2 | 0.883 | 0.078 | perceived_risk, workload |
| P05 | 5.7% | 0.9 | 5.9 | 5.4 | 0.92 | 6.7 | 5.8 | 0.86 | 12.5 | 24.9 | 0.351 | 0.308 | automation_trust |
| P06 | 42.5% | 7.1 | 24.2 | 17.3 | 0.71 | 55.6 | 48.9 | 0.88 | 11.3 | 27.4 | 0.765 | 0.093 | automation_trust |
| P07 | 1.3% | 0.3 | 7.9 | 7.1 | 0.90 | 7.5 | 9.1 | 1.21 | 12.1 | 22.0 | 0.943 | 0.108 | automation_trust, perceived_risk |
| P08 | 42.9% | 11.6 | 25.8 | 19.6 | 0.76 | 39.4 | 29.6 | 0.75 | 11.3 | 24.2 | 0.537 | 0.150 | workload |
| P09 | 8.6% | 0.5 | 9.8 | 8.4 | 0.85 | 12.8 | 15.2 | 1.18 | 12.6 | 23.9 | 0.990 | 0.004 | perceived_risk, workload |
| P10 | 1.7% | 0.1 | 8.2 | 7.3 | 0.89 | 2.3 | 2.3 | 1.00 | 12.5 | 25.1 | 0.982 | 0.004 | perceived_risk, workload |
| P11 | 40.6% | 0.4 | 32.3 | 25.9 | 0.80 | 34.5 | 41.9 | 1.22 | 11.6 | 23.1 | 1.000 | 0.007 | automation_trust, workload |
| P12 | 16.7% | 1.2 | 15.8 | 12.5 | 0.80 | 16.7 | 17.7 | 1.06 | 11.9 | 26.6 | 0.991 | 0.002 | automation_trust, perceived_risk |
| P13 | 40.2% | 3.1 | 27.6 | 20.6 | 0.75 | 49.7 | 49.7 | 1.00 | 11.3 | 22.6 | 0.981 | 0.020 | automation_trust, workload |
| P14 | 3.8% | 0.4 | 6.4 | 5.8 | 0.91 | 4.2 | 3.9 | 0.92 | 12.5 | 25.1 | 0.970 | 0.123 | perceived_risk, workload |
| P15 | 14.6% | 1.3 | 7.4 | 6.1 | 0.82 | 16.0 | 11.6 | 0.73 | 12.5 | 24.7 | 0.294 | 0.461 | perceived_risk, workload |
| P16 | 58.6% | 6.6 | 38.9 | 28.6 | 0.73 | 43.8 | 44.2 | 1.01 | 10.6 | 22.8 | 0.786 | 0.006 | workload |
| P17 | 42.0% | 5.4 | 24.1 | 16.5 | 0.69 | 43.5 | 45.1 | 1.04 | 11.2 | 23.7 | 0.916 | 0.036 | perceived_risk, workload |
| P18 | 5.2% | 0.8 | 7.8 | 6.9 | 0.89 | 23.7 | 23.8 | 1.00 | 12.2 | 23.7 | 0.771 | 0.033 | automation_trust |
| P19 | 14.5% | 1.5 | 8.2 | 6.9 | 0.85 | 29.3 | 30.4 | 1.04 | 12.7 | 23.7 | 0.884 | 0.022 | automation_trust, workload |
| P20 | 11.0% | 0.9 | 6.0 | 5.2 | 0.86 | 11.0 | 11.0 | 1.00 | 12.8 | 22.2 | 0.638 | 0.113 | automation_trust |
| P21 | 38.7% | 9.4 | 21.5 | 16.3 | 0.76 | 49.6 | 23.9 | 0.48 | 11.7 | 25.8 | 0.526 | 0.167 | workload |
| P22 | 37.4% | 2.7 | 20.4 | 13.5 | 0.66 | 25.0 | 23.3 | 0.93 | 11.4 | 23.0 | 0.916 | 0.064 | automation_trust |
| P23 | 57.6% | 7.9 | 38.0 | 27.8 | 0.73 | 31.7 | 23.5 | 0.74 | 10.6 | 24.2 | 0.715 | 0.083 | automation_trust |
| P24 | 10.4% | 1.1 | 6.5 | 5.6 | 0.86 | 11.2 | 10.2 | 0.91 | 12.6 | 26.6 | 0.449 | 0.151 | automation_trust |
| P25 | 1.6% | 0.3 | 7.4 | 6.7 | 0.90 | 10.9 | 15.9 | 1.45 | 12.8 | 26.5 | 0.598 | 0.028 | automation_trust, perceived_risk |
| P26 | 14.6% | 1.3 | 7.7 | 6.1 | 0.80 | 14.6 | 13.5 | 0.93 | 12.9 | 27.7 | 0.767 | 0.270 | automation_trust, perceived_risk |

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
