# Does high task complexity shrink the social effect because the occupants already agree?

Reports, for Low, Medium and High complexity tracks, how often the car puts
pressure on the driver (from every occupant's solo run) and how often the driver's
decisions actually change:

- **Any passenger disagrees**: at least one passenger would decide differently alone.
- **Outvoted**: an equal-weight vote of the car overrules the driver's solo choice;
  the pressure decision-level influence can act on.
- **Cognitive pull**: the driver's tree, applied to the mean of the occupants' solo
  cognitive states, flips the driver's solo choice; the pressure cognition-level
  influence can act on.

If pressure falls with complexity as much as the change does, the smaller social
effect on hard tracks comes from agreement among occupants rather than from
drivers ignoring their passengers. Cars, weights and persistence averaging match
`track_social_effects`.

Open **run.py** in this folder and choose VS Code's **Run Python File**, or from the
repository root:

```sh
python experiment/analysis/complexity_pressure/run.py
```

Run ../compare_modes/run.py first. Output: `results/summary.json` and `results/summary.md`.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-16 12:43:56 EDT

**514,800 matched cars.** Equal drivers, equal passenger counts within driver; each car averaged over persistence.

Pressure comes from each occupant's solo run and ignores trust weights and feedback. Descriptive.

### Pressure and change by complexity (percent of the drive)

| Complexity | Any passenger disagrees | Outvoted (decision pressure) | Decision-level changed | Cognitive pull (cognition pressure) | Cognition-level changed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Low | 72.6% | 25.6% | 18.3% | 29.9% | 27.5% |
| Medium | 39.9% | 12.9% | 10.5% | 24.6% | 21.9% |
| High | 22.2% | 6.8% | 6.1% | 22.3% | 18.7% |

| Complexity | Cars never outvoted | Cars never pulled | Decision change / pressure | Cognition change / pressure | Spearman ρ pressure vs change, decision | Spearman ρ pressure vs change, cognition |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Low | 17.0% | 15.8% | 0.72 | 0.92 | 0.81 | 0.64 |
| Medium | 26.1% | 21.9% | 0.82 | 0.89 | 0.92 | 0.79 |
| High | 42.5% | 36.7% | 0.89 | 0.84 | 0.91 | 0.84 |

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
