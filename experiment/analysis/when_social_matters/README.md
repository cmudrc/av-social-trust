# When does the social layer change the driver's behavior compared with driving alone?

The research question, answered by comparing explanations for how many cycles
differ from the solo baseline. Four nested linear models compare:

1. the scenario parameters (track, passenger count, trust, alpha, starting state);
2. the scenario parameters plus the participant driving;
3. the solo-counterfactual pressure alone (outvoted and cognitive-pull cycles);
4. everything together, plus the driver's solo automation fraction.

The unique R² of each input is how much the full model loses without it. The
pressure tables turn the result into a usable rule: how often a car with a given
amount of pressure changes behavior at all, or by at least ten cycles.

Two equal-weight measures, computed from every occupant's solo baseline at the
same track and start, describe the pressure the car puts on the driver:

- **Outvoted cycles**: an unweighted vote of all occupants' solo choices goes
  against the driver's solo choice (a tie counts as manual, as in the model).
- **Cognitive-pull cycles**: the driver's own decision tree, applied to the mean
  of all occupants' solo cognitive states, gives a different choice than the
  driver's solo run.

Both ignore trust weights and feedback, so comparing them with the simulated
changes shows what the social dynamics add or remove.

Run the other social-layer questions (occupant_disagreement, pressure_conversion,
influence_timing, participant_susceptibility) for the mechanisms behind this
summary.

Open **run.py** in this folder and choose VS Code's **Run Python File**.
Alternatively, from the repository root:

```sh
python experiment/analysis/when_social_matters/run.py
```

Run ../compare_modes/run.py first. The first question that runs after the
comparison cache changes builds `compare_modes/results/analysis_table.npz`
(about two minutes; it also reads the solo baselines in experiment/runs/).
Later questions load that table in seconds.

Output: `experiment/analysis/when_social_matters/results/summary.json`, `summary.md` and
`results/figures/explanations.png`; the latest summary is also inserted into this README.

These summaries describe associations across the sampled simulations; they do not isolate the causal effect of each parameter.

Figures are drawn by **plot.py** from the saved results, never from the runs: `explanations` (variance explained by each explanation). Each is saved as PNG and as vector PDF for the paper in `results/figures/`. Edit plot.py and run it to restyle a figure in seconds without repeating the analysis; run.py calls it automatically.

To reuse this question from another script:

```python
from experiment.analysis.when_social_matters.run import run

# Call explicitly when this question is needed.
result = run()
```

Importing the module does not run the analysis.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-11 09:26:23 EDT

Matched comparisons: **4,633,200**.

R² is the variance in changed cycles explained by a linear model with participant indicators and categorical passenger count and track difficulty. Unique R² is the loss when one input is dropped from the full model. Associations across the simulated grid, not causal estimates.

### Which explanation accounts for the change?

| Explanation | Decision-level influence | Cognition-level influence |
| --- | ---: | ---: |
| Scenario parameters | 0.092 | 0.027 |
| Scenario + participant | 0.246 | 0.332 |
| Solo-counterfactual pressure | 0.717 | 0.481 |
| All of the above + solo automation | 0.737 | 0.547 |

![Explanations](results/figures/explanations.png)

### Decision-level influence: unique contribution in the full model

| Input | Unique R² |
| --- | ---: |
| Outvoted cycles | 0.4230 |
| Passenger count | 0.0077 |
| Driver's homophily when trusting passengers (alpha) | 0.0040 |
| Driver's solo automation fraction | 0.0027 |
| Participant (driver identity) | 0.0017 |
| Cognitive-pull cycles | 0.0006 |
| Passengers' homophily when trusting the driver (alpha) | 0.0003 |
| Track difficulty | 0.0002 |

### Decision-level influence: change by its own pressure

Cars with no pressure: **39.3%**.

| Pressure cycles | Cars | Mean changed cycles | Any change | ≥10 changed cycles |
| --- | ---: | ---: | ---: | ---: |
| 0 | 1,819,992 | 0.9 | 19.3% | 1.4% |
| 1–4 | 470,296 | 2.8 | 90.8% | 1.9% |
| 5–9 | 401,186 | 6.2 | 94.5% | 8.0% |
| 10–19 | 610,344 | 11.4 | 96.0% | 70.6% |
| 20–39 | 734,122 | 21.8 | 98.8% | 85.6% |
| 40–100 | 597,260 | 45.7 | 98.9% | 89.5% |

### Cognition-level influence: unique contribution in the full model

| Input | Unique R² |
| --- | ---: |
| Cognitive-pull cycles | 0.2134 |
| Participant (driver identity) | 0.0601 |
| Track difficulty | 0.0057 |
| Driver's solo automation fraction | 0.0020 |
| Passenger count | 0.0010 |
| Track persistence | 0.0008 |
| Driver's initial perceived risk | 0.0006 |
| Passengers' initial automation trust | 0.0006 |

### Cognition-level influence: change by its own pressure

Cars with no pressure: **36.1%**.

| Pressure cycles | Cars | Mean changed cycles | Any change | ≥10 changed cycles |
| --- | ---: | ---: | ---: | ---: |
| 0 | 1,674,714 | 4.9 | 16.7% | 10.0% |
| 1–4 | 310,478 | 10.6 | 91.2% | 20.9% |
| 5–9 | 266,758 | 14.3 | 95.6% | 28.9% |
| 10–19 | 491,834 | 18.7 | 97.0% | 85.3% |
| 20–39 | 630,606 | 29.4 | 97.5% | 89.8% |
| 40–100 | 1,258,810 | 53.6 | 97.8% | 90.1% |

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
