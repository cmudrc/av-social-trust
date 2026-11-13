# Does the social layer push the driver toward or away from automation?

The other analyses count changed decisions in either direction. This question
adds the direction:

1. **Net change**: the driver's automation share with passengers minus the
   matched solo run, in percentage points of the drive. Changed cycles toward
   automation and toward manual driving are reported separately.
2. **Passengers' lean**: whether the change follows what the passengers would do
   alone. Lean is the passengers' solo automation share minus the driver's solo
   automation share at the same track and start. A positive lean means the
   passengers would use automation more than the driver if each drove alone.
   An initial automation-trust lean is reported as a check.

Cars are matched on all nine tracks, averaged over persistence within each
complexity level, and weighted equally by driver and by passenger count within
driver, as in `track_social_effects`. Associations are descriptive.

Open **run.py** in this folder and choose VS Code's **Run Python File**.
Alternatively, from the repository root:

```sh
python experiment/analysis/social_direction/run.py
```

Run ../compare_modes/run.py first (the shared analysis table must be current).

Output: `results/summary.json`, `results/summary.md` and
`results/figures/net_change_by_lean.png` / `.pdf`. Redraw the figure from saved
results with `plot.py`.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-16 13:53:43 EDT

**514,800 matched cars** on all tracks, 26 drivers.

Equal drivers, equal passenger counts within driver, equal cars within each cell; each car averaged over the three persistence levels of a complexity level.

Net change = the driver's automation share with passengers minus the matched solo run, in percentage points of the drive (positive = more automation). Descriptive.

### Direction of the social effect

| Complexity | Mode | Net change (pp) | Changed toward automation | Changed toward manual | All changed decisions | Cars using more automation | Cars using less automation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Low | Decision-level | -3.8 | 7.2% | 11.1% | 18.3% | 40.1% | 51.8% |
| Low | Cognition-level | -3.3 | 12.1% | 15.4% | 27.5% | 37.3% | 50.1% |
| Medium | Decision-level | -5.6 | 2.4% | 8.1% | 10.5% | 31.1% | 51.2% |
| Medium | Cognition-level | +8.1 | 15.0% | 6.9% | 21.9% | 38.2% | 43.7% |
| High | Decision-level | -3.6 | 1.2% | 4.8% | 6.1% | 23.8% | 42.5% |
| High | Cognition-level | +11.6 | 15.1% | 3.6% | 18.7% | 37.2% | 29.6% |

### Does the change follow the passengers' lean?

Passengers' solo automation share minus the driver's solo automation share (same track and start).

![Net change by passengers' lean](results/figures/net_change_by_lean.png)

| Complexity | Passengers' lean | Cars | Mean lean | Decision net (pp) | Cognition net (pp) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Low | -100 to -50 pp [-1, -0.5) | 16.6% | -0.67 | -43.2 | -18.7 |
| Low | -50 to -30 pp [-0.5, -0.3) | 11.7% | -0.40 | -15.4 | -17.4 |
| Low | -30 to -15 pp [-0.3, -0.15) | 8.2% | -0.23 | -7.4 | -13.3 |
| Low | -15 to -5 pp [-0.15, -0.05) | 5.9% | -0.10 | -5.1 | -7.7 |
| Low | -5 to +5 pp [-0.05, 0.05) | 7.7% | +0.00 | -2.9 | -2.2 |
| Low | +5 to +15 pp [0.05, 0.15) | 8.6% | +0.10 | -0.4 | +0.4 |
| Low | +15 to +30 pp [0.15, 0.3) | 13.5% | +0.22 | +3.2 | +4.4 |
| Low | +30 to +50 pp [0.3, 0.5) | 15.3% | +0.39 | +10.3 | +10.1 |
| Low | +50 to +100 pp [0.5, 1) | 12.5% | +0.66 | +34.2 | +10.9 |
| Medium | -100 to -50 pp [-1, -0.5) | 3.8% | -0.62 | -48.5 | -7.5 |
| Medium | -50 to -30 pp [-0.5, -0.3) | 8.9% | -0.39 | -29.9 | +4.9 |
| Medium | -30 to -15 pp [-0.3, -0.15) | 11.3% | -0.23 | -17.7 | +8.0 |
| Medium | -15 to -5 pp [-0.15, -0.05) | 9.1% | -0.09 | -8.1 | +8.5 |
| Medium | -5 to +5 pp [-0.05, 0.05) | 20.3% | +0.01 | -1.7 | +8.8 |
| Medium | +5 to +15 pp [0.05, 0.15) | 20.2% | +0.10 | +0.3 | +9.8 |
| Medium | +15 to +30 pp [0.15, 0.3) | 19.2% | +0.21 | +3.8 | +10.0 |
| Medium | +30 to +50 pp [0.3, 0.5) | 5.8% | +0.37 | +13.2 | +9.2 |
| Medium | +50 to +100 pp [0.5, 1) | 1.4% | +0.60 | +26.0 | +4.2 |
| High | -100 to -50 pp [-1, -0.5) | 0.8% | -0.82 | -70.5 | -63.9 |
| High | -50 to -30 pp [-0.5, -0.3) | 2.0% | -0.35 | -27.8 | +20.1 |
| High | -30 to -15 pp [-0.3, -0.15) | 10.1% | -0.22 | -17.9 | +18.1 |
| High | -15 to -5 pp [-0.15, -0.05) | 14.3% | -0.10 | -8.8 | +20.2 |
| High | -5 to +5 pp [-0.05, 0.05) | 36.0% | +0.01 | -1.0 | +10.8 |
| High | +5 to +15 pp [0.05, 0.15) | 27.9% | +0.09 | +1.4 | +8.9 |
| High | +15 to +30 pp [0.15, 0.3) | 7.5% | +0.20 | +5.6 | +7.1 |
| High | +30 to +50 pp [0.3, 0.5) | 1.2% | +0.36 | +10.2 | +4.9 |
| High | +50 to +100 pp [0.5, 1) | 0.3% | +0.72 | +24.0 | +3.7 |

| Complexity | Spearman ρ lean vs net, decision | Spearman ρ lean vs net, cognition |
| --- | ---: | ---: |
| Low | 0.87 | 0.20 |
| Medium | 0.88 | 0.11 |
| High | 0.85 | 0.08 |

### Check: initial automation-trust lean

Passengers' mean initial automation trust minus the driver's (model scale 0-1); net change averaged over all tracks.

| Initial trust lean | Cars | Decision net (pp) | Cognition net (pp) |
| --- | ---: | ---: | ---: |
| Much less [-1, -0.3) | 21.5% | -7.3 | +2.1 |
| Less [-0.3, -0.1) | 18.7% | -5.4 | +3.3 |
| Similar [-0.1, 0.1) | 19.7% | -3.8 | +5.5 |
| More [0.1, 0.3) | 18.5% | -3.5 | +7.4 |
| Much more [0.3, 1) | 21.6% | -1.8 | +8.9 |

Spearman ρ, initial trust lean vs net: decision 0.14, cognition 0.09.

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
