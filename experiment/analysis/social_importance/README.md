# How large and persistent are the changes caused by social influence in the simulation?

Summarizes changed cycles, switching toward or away from automation, early/late agreement and mismatch quartiles, overall and for each driver.

Open **run.py** in this folder and choose VS Code's **Run Python File**.
Alternatively, from the repository root:

```sh
python experiment/analysis/social_importance/run.py
```

Run ../compare_modes/run.py first.

Output: `experiment/analysis/social_importance/results/summary.json` and `summary.md`; the latest summary is also inserted into this README.

Changed-cycle thresholds are exploratory measures, not validated importance cutoffs.

To reuse this question from another script:

```python
from experiment.analysis.social_importance.run import run

# Call explicitly when this question is needed.
result = run()
```

Importing the module does not run the analysis.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-10 22:22:05 EDT

Matched comparisons: **4,633,200**.

Descriptive; changed-cycle thresholds are exploratory, not validated importance cutoffs.

| Comparison | Mean changed cycles | Median changed cycles | Models with any change |
| --- | ---: | ---: | ---: |
| decision_vs_baseline | 12.00 | 4.00 | 66.1% |
| cognition_vs_baseline | 23.86 | 11.00 | 67.8% |
| decision_vs_cognition | 26.63 | 13.00 | 73.7% |

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
