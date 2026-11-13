# How do decision changes vary with social trust and influence weights?

Examines incoming and outgoing trust, the driver's initial self-weight, fixed alpha tradeoffs and passenger count. It describes variation within the configured network topology.

Open **run.py** in this folder and choose VS Code's **Run Python File**.
Alternatively, from the repository root:

```sh
python experiment/analysis/network_effects/run.py
```

Run ../compare_modes/run.py first.

Output: `experiment/analysis/network_effects/results/summary.json` and `summary.md`; the latest summary is also inserted into this README.

These summaries describe associations across the sampled simulations; they do not isolate the causal effect of each parameter.

To reuse this question from another script:

```python
from experiment.analysis.network_effects.run import run

# Call explicitly when this question is needed.
result = run()
```

Importing the module does not run the analysis.

All grouped results are also saved as `results/groups.jsonl`, one JSON record per group.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-10 22:13:54 EDT

Matched comparisons: **4,633,200**.

Descriptive associations, not isolated causal effects or independent-person significance tests.

Agreement is the percentage of cycles with the same automation decision.

| Feature | Group | Models | Drivers | Decision / solo | Cognition / solo | Decision / cognition |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| inbound_trust_mean | [0.6, 0.8) | 1,168,848 | 26 | 88.2% | 76.4% | 73.6% |
| outbound_trust_mean | [0, 0.2) | 217,827 | 26 | 89.4% | 78.2% | 75.4% |
| driver_initial_self_weight | [0.8, 1] | 72,495 | 26 | 90.5% | 81.0% | 77.6% |
| alpha_inbound_mean | [0.6, 0.8) | 1,083,015 | 26 | 87.8% | 76.1% | 73.2% |
| alpha_outbound_mean | [0, 0.2) | 185,841 | 26 | 86.0% | 77.8% | 73.2% |
| passenger_count | 1 | 140,400 | 26 | 90.0% | 82.6% | 77.8% |
| driver_self_plus_inbound_sum | [1, 2) | 1,612,170 | 26 | 87.9% | 76.9% | 73.8% |
| passenger_count × driver_initial_self_weight | 1 \| [0.8, 1] | 27,135 | 26 | 92.7% | 84.2% | 80.5% |
| inbound_trust_mean | [0.4, 0.6) | 1,938,501 | 26 | 87.9% | 75.8% | 73.1% |
| outbound_trust_mean | [0.6, 0.8) | 1,166,319 | 26 | 87.8% | 76.0% | 73.2% |
| driver_initial_self_weight | [0.4, 0.6) | 604,233 | 26 | 88.6% | 77.7% | 74.5% |
| alpha_inbound_mean | [0.8, 1] | 189,135 | 26 | 87.0% | 77.7% | 73.6% |
| passenger_count × driver_initial_self_weight | 1 \| [0.4, 0.6) | 43,038 | 26 | 90.1% | 82.5% | 77.7% |
| inbound_trust_mean | [0.8, 1] | 279,999 | 26 | 88.8% | 78.6% | 75.2% |
| outbound_trust_mean | [0.2, 0.4) | 1,021,734 | 26 | 88.4% | 76.1% | 73.5% |
| driver_initial_self_weight | [0.6, 0.8) | 148,338 | 26 | 89.9% | 79.3% | 76.0% |
| passenger_count × driver_initial_self_weight | 1 \| [0.6, 0.8) | 23,778 | 26 | 92.2% | 83.4% | 79.6% |
| inbound_trust_mean | [0.2, 0.4) | 1,027,836 | 26 | 87.9% | 75.7% | 73.1% |
| outbound_trust_mean | [0.8, 1] | 279,441 | 26 | 87.6% | 77.6% | 74.0% |
| driver_initial_self_weight | [0, 0.2) | 2,022,354 | 26 | 87.5% | 75.2% | 72.7% |
| alpha_inbound_mean | [0, 0.2) | 186,714 | 26 | 88.9% | 78.1% | 75.0% |
| alpha_outbound_mean | [0.4, 0.6) | 2,091,627 | 26 | 87.9% | 75.8% | 73.1% |
| driver_self_plus_inbound_sum | [0, 0.5) | 93,546 | 26 | 86.7% | 77.1% | 73.3% |
| passenger_count × driver_initial_self_weight | 1 \| [0, 0.2) | 23,265 | 26 | 87.4% | 81.0% | 75.4% |
| outbound_trust_mean | [0.4, 0.6) | 1,947,879 | 26 | 87.8% | 75.8% | 73.1% |
| alpha_inbound_mean | [0.4, 0.6) | 2,089,944 | 26 | 88.0% | 75.8% | 73.2% |
| inbound_trust_mean | [0, 0.2) | 218,016 | 26 | 87.4% | 76.4% | 73.1% |
| alpha_outbound_mean | [0.2, 0.4) | 1,085,733 | 26 | 86.8% | 76.1% | 72.9% |
| alpha_inbound_mean | [0.2, 0.4) | 1,084,392 | 26 | 88.2% | 76.3% | 73.6% |
| alpha_outbound_mean | [0.8, 1] | 186,894 | 26 | 91.0% | 78.0% | 75.8% |
| driver_initial_self_weight | [0.2, 0.4) | 1,785,780 | 26 | 88.1% | 76.2% | 73.4% |
| alpha_outbound_mean | [0.6, 0.8) | 1,083,105 | 26 | 89.3% | 76.2% | 73.9% |
| passenger_count × driver_initial_self_weight | 1 \| [0.2, 0.4) | 23,184 | 26 | 87.3% | 81.5% | 75.4% |
| driver_self_plus_inbound_sum | [0.5, 1) | 232,488 | 26 | 87.2% | 77.2% | 73.6% |
| passenger_count | 2 | 1,123,200 | 26 | 87.0% | 78.0% | 74.0% |
| driver_self_plus_inbound_sum | [2, 3) | 1,768,545 | 26 | 88.2% | 75.7% | 73.3% |
| passenger_count × driver_initial_self_weight | 2 \| [0.4, 0.6) | 302,166 | 26 | 87.4% | 78.5% | 74.4% |
| passenger_count × driver_initial_self_weight | 2 \| [0.2, 0.4) | 378,450 | 26 | 86.4% | 78.1% | 73.8% |
| passenger_count × driver_initial_self_weight | 2 \| [0, 0.2) | 317,349 | 26 | 86.5% | 77.1% | 73.2% |
| passenger_count × driver_initial_self_weight | 2 \| [0.6, 0.8) | 88,560 | 26 | 88.8% | 79.1% | 75.2% |

Showing 40 of 62 groups; all groups are in summary.json and groups.jsonl.

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
