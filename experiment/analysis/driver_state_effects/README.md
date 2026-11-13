# How do decision changes vary with the driver's starting state?

Examines initial self-trust, automation trust, perceived risk and workload, including passenger count and its combination with self-trust.

Open **run.py** in this folder and choose VS Code's **Run Python File**.
Alternatively, from the repository root:

```sh
python experiment/analysis/driver_state_effects/run.py
```

Run ../compare_modes/run.py first.

Output: `experiment/analysis/driver_state_effects/results/summary.json` and `summary.md`; the latest summary is also inserted into this README.

These summaries describe associations across the sampled simulations; they do not isolate the causal effect of each parameter.

To reuse this question from another script:

```python
from experiment.analysis.driver_state_effects.run import run

# Call explicitly when this question is needed.
result = run()
```

Importing the module does not run the analysis.

All grouped results are also saved as `results/groups.jsonl`, one JSON record per group.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-10 22:16:53 EDT

Matched comparisons: **4,633,200**.

Descriptive associations, not isolated causal effects or independent-person significance tests.

Agreement is the percentage of cycles with the same automation decision.

| Feature | Group | Models | Drivers | Decision / solo | Cognition / solo | Decision / cognition |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| driver_self_trust | 0.8 | 772,200 | 26 | 88.5% | 76.6% | 73.7% |
| driver_automation_trust | [0, 0.2) | 905,850 | 26 | 89.2% | 75.1% | 71.9% |
| driver_perceived_risk | [0.2, 0.4) | 980,100 | 26 | 88.6% | 76.8% | 73.4% |
| driver_workload | [0, 0.2) | 876,150 | 26 | 87.3% | 74.3% | 73.0% |
| passenger_count | 1 | 140,400 | 26 | 90.0% | 82.6% | 77.8% |
| passenger_count × driver_self_trust | 1 \| 0.8 | 23,400 | 26 | 91.4% | 83.2% | 78.7% |
| driver_self_trust | 0.6 | 772,200 | 26 | 88.2% | 76.2% | 73.5% |
| passenger_count × driver_self_trust | 1 \| 0.6 | 23,400 | 26 | 90.5% | 83.0% | 78.1% |
| driver_self_trust | 0.4 | 772,200 | 26 | 87.3% | 76.8% | 73.8% |
| driver_automation_trust | [0.4, 0.6) | 876,150 | 26 | 89.3% | 78.2% | 74.5% |
| driver_workload | [0.8, 1] | 950,400 | 26 | 87.4% | 76.2% | 72.9% |
| passenger_count × driver_self_trust | 1 \| 0.4 | 23,400 | 26 | 89.3% | 82.8% | 77.8% |
| driver_self_trust | 0.01 | 772,200 | 26 | 87.8% | 75.0% | 72.6% |
| passenger_count × driver_self_trust | 1 \| 0.01 | 23,400 | 26 | 87.9% | 81.1% | 75.8% |
| driver_self_trust | 0.99 | 772,200 | 26 | 89.0% | 76.5% | 73.9% |
| driver_automation_trust | [0.8, 1] | 891,000 | 26 | 86.1% | 75.4% | 73.0% |
| driver_perceived_risk | [0.8, 1] | 965,250 | 26 | 88.5% | 77.5% | 73.4% |
| driver_workload | [0.4, 0.6) | 980,100 | 26 | 87.7% | 75.4% | 72.2% |
| passenger_count × driver_self_trust | 1 \| 0.99 | 23,400 | 26 | 92.3% | 83.2% | 79.4% |
| driver_self_trust | 0.2 | 772,200 | 26 | 87.2% | 75.9% | 72.9% |
| passenger_count × driver_self_trust | 1 \| 0.2 | 23,400 | 26 | 88.8% | 82.1% | 77.0% |
| driver_automation_trust | [0.6, 0.8) | 1,009,800 | 26 | 87.3% | 75.7% | 72.5% |
| driver_perceived_risk | [0, 0.2) | 861,300 | 26 | 86.5% | 71.9% | 72.2% |
| driver_workload | [0.6, 0.8) | 831,600 | 26 | 89.2% | 78.8% | 74.9% |
| driver_perceived_risk | [0.4, 0.6) | 905,850 | 26 | 87.6% | 76.3% | 73.7% |
| driver_automation_trust | [0.2, 0.4) | 950,400 | 26 | 88.1% | 76.4% | 74.9% |
| driver_workload | [0.2, 0.4) | 994,950 | 26 | 88.5% | 76.2% | 74.0% |
| driver_perceived_risk | [0.6, 0.8) | 920,700 | 26 | 88.8% | 77.8% | 74.1% |
| passenger_count | 2 | 1,123,200 | 26 | 87.0% | 78.0% | 74.0% |
| passenger_count × driver_self_trust | 2 \| 0.8 | 187,200 | 26 | 87.6% | 78.5% | 74.3% |
| passenger_count × driver_self_trust | 2 \| 0.6 | 187,200 | 26 | 87.1% | 78.2% | 74.2% |
| passenger_count × driver_self_trust | 2 \| 0.4 | 187,200 | 26 | 86.2% | 78.5% | 74.2% |
| passenger_count × driver_self_trust | 2 \| 0.01 | 187,200 | 26 | 86.8% | 76.8% | 73.1% |
| passenger_count × driver_self_trust | 2 \| 0.99 | 187,200 | 26 | 88.0% | 78.5% | 74.6% |
| passenger_count × driver_self_trust | 2 \| 0.2 | 187,200 | 26 | 86.2% | 77.6% | 73.4% |
| passenger_count | 3 | 1,123,200 | 26 | 89.6% | 76.2% | 74.3% |
| passenger_count × driver_self_trust | 3 \| 0.8 | 187,200 | 26 | 90.2% | 76.7% | 74.6% |
| passenger_count × driver_self_trust | 3 \| 0.6 | 187,200 | 26 | 89.8% | 76.2% | 74.4% |
| passenger_count × driver_self_trust | 3 \| 0.4 | 187,200 | 26 | 88.9% | 76.7% | 74.7% |
| passenger_count × driver_self_trust | 3 \| 0.01 | 187,200 | 26 | 89.4% | 75.1% | 73.4% |

Showing 40 of 56 groups; all groups are in summary.json and groups.jsonl.

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
