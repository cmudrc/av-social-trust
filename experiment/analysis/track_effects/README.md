# How do decision changes vary with track difficulty and persistence?

Examines difficulty, persistence, repetitions, realized complexity and complexity switches, including combinations with passenger count.

Open **run.py** in this folder and choose VS Code's **Run Python File**.
Alternatively, from the repository root:

```sh
python experiment/analysis/track_effects/run.py
```

Run ../compare_modes/run.py first.

Output: `experiment/analysis/track_effects/results/summary.json` and `summary.md`; the latest summary is also inserted into this README.

These summaries describe associations across the sampled simulations; they do not isolate the causal effect of each parameter.

To reuse this question from another script:

```python
from experiment.analysis.track_effects.run import run

# Call explicitly when this question is needed.
result = run()
```

Importing the module does not run the analysis.

All grouped results are also saved as `results/groups.jsonl`, one JSON record per group.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-10 22:20:36 EDT

Matched comparisons: **4,633,200**.

Descriptive associations, not isolated causal effects or independent-person significance tests.

Agreement is the percentage of cycles with the same automation decision.

| Feature | Group | Models | Drivers | Decision / solo | Cognition / solo | Decision / cognition |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| track_difficulty | high | 1,544,400 | 26 | 93.7% | 80.2% | 79.6% |
| track_persistence | 0.3 | 1,544,400 | 26 | 87.7% | 77.9% | 74.6% |
| track_replicate | 0 | 4,633,200 | 26 | 88.0% | 76.1% | 73.4% |
| track | high_p0_0 | 514,800 | 26 | 93.5% | 80.0% | 79.7% |
| mean_complexity | 0.74 | 514,800 | 26 | 93.5% | 80.0% | 79.7% |
| complexity_switches | 20 | 514,800 | 26 | 93.5% | 80.0% | 79.7% |
| passenger_count | 1 | 140,400 | 26 | 90.0% | 82.6% | 77.8% |
| track_difficulty × passenger_count | high \| 1 | 46,800 | 26 | 94.9% | 86.4% | 84.6% |
| track_difficulty × track_persistence | high \| 0.3 | 514,800 | 26 | 93.5% | 80.0% | 79.7% |
| passenger_count | 2 | 1,123,200 | 26 | 87.0% | 78.0% | 74.0% |
| track_difficulty × passenger_count | high \| 2 | 374,400 | 26 | 93.8% | 81.9% | 80.9% |
| passenger_count | 3 | 1,123,200 | 26 | 89.6% | 76.2% | 74.3% |
| track_difficulty × passenger_count | high \| 3 | 374,400 | 26 | 94.1% | 80.3% | 79.9% |
| passenger_count | 4 | 1,123,200 | 26 | 87.5% | 74.9% | 72.3% |
| track_difficulty × passenger_count | high \| 4 | 374,400 | 26 | 93.3% | 79.0% | 78.4% |
| passenger_count | 5 | 1,123,200 | 26 | 87.6% | 74.6% | 72.4% |
| track_difficulty × passenger_count | high \| 5 | 374,400 | 26 | 93.5% | 78.7% | 78.4% |
| track_persistence | 0.6 | 1,544,400 | 26 | 88.0% | 76.1% | 73.1% |
| track | high_p1_0 | 514,800 | 26 | 95.2% | 81.0% | 80.9% |
| mean_complexity | 0.84 | 514,800 | 26 | 95.2% | 81.0% | 80.9% |
| complexity_switches | 16 | 514,800 | 26 | 95.2% | 81.0% | 80.9% |
| track_difficulty × track_persistence | high \| 0.6 | 514,800 | 26 | 95.2% | 81.0% | 80.9% |
| track_persistence | 0.9 | 1,544,400 | 26 | 88.3% | 74.4% | 72.4% |
| track | high_p2_0 | 514,800 | 26 | 92.4% | 79.5% | 78.1% |
| mean_complexity | 0.71 | 514,800 | 26 | 92.4% | 79.5% | 78.1% |
| complexity_switches | 4 | 514,800 | 26 | 92.4% | 79.5% | 78.1% |
| track_difficulty × track_persistence | high \| 0.9 | 514,800 | 26 | 92.4% | 79.5% | 78.1% |
| track_difficulty | low | 1,544,400 | 26 | 81.3% | 71.3% | 65.4% |
| track | low_p0_0 | 514,800 | 26 | 80.7% | 75.4% | 68.2% |
| mean_complexity | 0.18 | 514,800 | 26 | 80.7% | 75.4% | 68.2% |
| complexity_switches | 24 | 514,800 | 26 | 80.7% | 75.4% | 68.2% |
| track_difficulty × passenger_count | low \| 1 | 46,800 | 26 | 83.6% | 78.2% | 69.2% |
| track_difficulty × track_persistence | low \| 0.3 | 514,800 | 26 | 80.7% | 75.4% | 68.2% |
| track_difficulty × passenger_count | low \| 2 | 374,400 | 26 | 78.4% | 73.5% | 64.9% |
| track_difficulty × passenger_count | low \| 3 | 374,400 | 26 | 84.5% | 71.3% | 67.1% |
| track_difficulty × passenger_count | low \| 4 | 374,400 | 26 | 80.9% | 69.9% | 64.5% |
| track_difficulty × passenger_count | low \| 5 | 374,400 | 26 | 81.0% | 69.5% | 64.5% |
| track | low_p1_0 | 514,800 | 26 | 80.1% | 69.4% | 62.4% |
| mean_complexity | 0.1 | 514,800 | 26 | 80.1% | 69.4% | 62.4% |
| complexity_switches | 9 | 514,800 | 26 | 80.1% | 69.4% | 62.4% |

Showing 40 of 62 groups; all groups are in summary.json and groups.jsonl.

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
