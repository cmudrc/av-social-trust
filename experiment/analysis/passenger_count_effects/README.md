# How do decision changes vary with passenger count?

Groups matched comparisons by passenger count and track difficulty, including their combination.

Open **run.py** in this folder and choose VS Code's **Run Python File**.
Alternatively, from the repository root:

```sh
python experiment/analysis/passenger_count_effects/run.py
```

Run ../compare_modes/run.py first.

Output: `experiment/analysis/passenger_count_effects/results/summary.json` and `summary.md`; the latest summary is also inserted into this README.

These summaries describe associations across the sampled simulations; they do not isolate the causal effect of each parameter.

To reuse this question from another script:

```python
from experiment.analysis.passenger_count_effects.run import run

# Call explicitly when this question is needed.
result = run()
```

Importing the module does not run the analysis.

All grouped results are also saved as `results/groups.jsonl`, one JSON record per group.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-10 22:10:12 EDT

Matched comparisons: **4,633,200**.

Descriptive associations, not isolated causal effects or independent-person significance tests.

Agreement is the percentage of cycles with the same automation decision.

| Feature | Group | Models | Drivers | Decision / solo | Cognition / solo | Decision / cognition |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| passenger_count | 1 | 140,400 | 26 | 90.0% | 82.6% | 77.8% |
| track_difficulty | high | 1,544,400 | 26 | 93.7% | 80.2% | 79.6% |
| passenger_count × track_difficulty | 1 \| high | 46,800 | 26 | 94.9% | 86.4% | 84.6% |
| passenger_count | 2 | 1,123,200 | 26 | 87.0% | 78.0% | 74.0% |
| passenger_count × track_difficulty | 2 \| high | 374,400 | 26 | 93.8% | 81.9% | 80.9% |
| passenger_count | 3 | 1,123,200 | 26 | 89.6% | 76.2% | 74.3% |
| passenger_count × track_difficulty | 3 \| high | 374,400 | 26 | 94.1% | 80.3% | 79.9% |
| passenger_count | 4 | 1,123,200 | 26 | 87.5% | 74.9% | 72.3% |
| passenger_count × track_difficulty | 4 \| high | 374,400 | 26 | 93.3% | 79.0% | 78.4% |
| passenger_count | 5 | 1,123,200 | 26 | 87.6% | 74.6% | 72.4% |
| passenger_count × track_difficulty | 5 \| high | 374,400 | 26 | 93.5% | 78.7% | 78.4% |
| track_difficulty | low | 1,544,400 | 26 | 81.3% | 71.3% | 65.4% |
| passenger_count × track_difficulty | 1 \| low | 46,800 | 26 | 83.6% | 78.2% | 69.2% |
| passenger_count × track_difficulty | 2 \| low | 374,400 | 26 | 78.4% | 73.5% | 64.9% |
| passenger_count × track_difficulty | 3 \| low | 374,400 | 26 | 84.5% | 71.3% | 67.1% |
| passenger_count × track_difficulty | 4 \| low | 374,400 | 26 | 80.9% | 69.9% | 64.5% |
| passenger_count × track_difficulty | 5 \| low | 374,400 | 26 | 81.0% | 69.5% | 64.5% |
| track_difficulty | normal | 1,544,400 | 26 | 89.0% | 77.0% | 75.2% |
| passenger_count × track_difficulty | 1 \| normal | 46,800 | 26 | 91.6% | 83.2% | 79.6% |
| passenger_count × track_difficulty | 2 \| normal | 374,400 | 26 | 88.7% | 78.7% | 76.0% |
| passenger_count × track_difficulty | 3 \| normal | 374,400 | 26 | 90.3% | 77.1% | 75.8% |
| passenger_count × track_difficulty | 4 \| normal | 374,400 | 26 | 88.3% | 75.8% | 74.0% |
| passenger_count × track_difficulty | 5 \| normal | 374,400 | 26 | 88.5% | 75.6% | 74.2% |

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
