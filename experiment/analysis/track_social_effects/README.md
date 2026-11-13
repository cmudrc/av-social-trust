# How do tracks change the importance of the social layer?

Use the driver's actual automation decision as the common outcome. A social
mode's effect is the fraction of cycles that differ from that driver's solo run.
The cross-mode comparison measures sensitivity to where influence is modeled.

Three complementary approaches are implemented:

1. Compare the nine named tracks using mean changed-cycle fractions. Show raw
   and balanced summaries so the larger quota for 2–5 passengers does not hide
   one-passenger cars.
2. Compare **the same cars** across tracks: hard minus easy at each persistence,
   persistent minus changing at each difficulty, and the change in the hard–easy
   difference with persistence. Driver, passengers, starting cognition and
   initial social settings are fixed. Only complete nine-track matches enter.
3. Remove each car's average effect and quantify how much of the remaining
   variation follows a common track pattern. This distinguishes a common track
   response from cars reacting differently to the same track.

The main paper figures now use **Low, Medium and High track complexity**, with
no internal track identifiers. Persistence is averaged within each matched car.
`complexity_effects` shows the two social models compared with solo driving;
`paired_contrasts` compares complexity levels for the same cars. The main table
contains those two comparisons, with explicit column names and a definition of
the percentages. `method_difference` is an optional separate result comparing
the two social mechanisms. It does not establish which model is more accurate.

`track_grid` remains a supplementary persistence check, using complexity
categories. Averaging over persistence is not evidence that it has no effect;
the saved contrasts show different responses in the two social methods.
Passenger-count and threshold figures also use complexity categories.
The passenger-count figure separates Low, Medium, and High complexity into three
small panels, with passenger count on the horizontal axis. Each panel has two lines:
blue solid for decision-level influence and orange dashed for cognition-level influence.

Driver ranges describe variation across modeled participants, not uncertainty
intervals. There is one realized track per complexity–persistence cell: the
results establish differences among the actual sequences, rather than a general
causal effect of the generating parameters. Complexity and persistence also
change the realized sequence and its ordering.

Run from the repository root:

```sh
python experiment/analysis/track_social_effects/run.py
```

Requires the existing comparison cache and a current shared analysis table.
`run.py` reads those plus archive settings, without scanning full trajectories.
`plot.py` redraws PNG and PDF figures from saved outputs alone. `summary.json`
retains all paired contrasts, weighting checks and threshold checks;
`plots.npz` saves plot data. No simulation model is changed.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-11 15:20:16 EDT

**514,800 matched cars across 9 tracks**, 26 drivers.

Each percentage is the average fraction of cycles with different driver automation decisions: 100 × (number of differing cycles / number of cycles). For example, 18.3% means about 18 of 100 decisions differ from the matched solo run, on average. It is neither a percentage of cars nor a percentage increase in automation use.

Equal drivers, equal passenger counts within driver, equal cars within each cell.

Average each matched car across persistence levels, then balance drivers and passenger counts.

Exact paired comparisons on the realized tracks. Driver ranges show heterogeneity, not confidence intervals. One realization per track cell cannot establish a general difficulty or persistence effect.

### Main result: complexity and differences from solo driving

![Complexity effects](results/figures/complexity_effects.png)

| Track complexity | Decision-level influence compared with solo driving | Cognition-level influence compared with solo driving |
| --- | ---: | ---: |
| Low | 18.3% | 27.5% |
| Medium | 10.5% | 21.9% |
| High | 6.1% | 18.7% |

Persistence is averaged over for this presentation; this is not evidence that persistence has no effect.

### Compare complexity while keeping the car fixed

Positive differences mean more changed decisions at the higher complexity. Dots show balanced averages; bars span the driver averages, not confidence intervals. Persistence is averaged over within each car.

![Paired complexity differences](results/figures/paired_contrasts.png)

| Comparison | Decision-level influence compared with solo driving | Cognition-level influence compared with solo driving |
| --- | ---: | ---: |
| Medium minus Low complexity | -7.80 percentage points | -5.62 percentage points |
| High minus Low complexity | -12.24 percentage points | -8.79 percentage points |
| High minus Medium complexity | -4.45 percentage points | -3.17 percentage points |

### Optional separate question: does the location of influence matter?

![Difference between influence methods](results/figures/method_difference.png)

This compares decision-level with cognition-level influence. It describes sensitivity to where social influence is modeled; it is not required to establish that either social model differs from solo driving. Neither method is validated as more accurate by this comparison.

### Supplementary checks

![Passenger counts](results/figures/by_passengers.png)

![Threshold sensitivity](results/figures/threshold_sensitivity.png)

![Persistence checks](results/figures/track_grid.png)

The persistence grid remains available as a supplementary check. All figures use complexity categories, with no internal track identifiers. Thresholds are exploratory checks, not definitions of importance. summary.json also retains persistence contrasts, raw weighting, signed changes, paired quartiles, driver ranges and the shared track share of within-car variation.

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
