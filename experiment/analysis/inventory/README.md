# Which models have finished?

Counts completed models by baseline, decision influence and cognition influence, and reports the number of result archives.

Open **run.py** in this folder and choose VS Code's **Run Python File**.
Alternatively, from the repository root:

```sh
python experiment/analysis/inventory/run.py
```

Reads experiment/runs/ directly; no preparation needed.

Output: `experiment/analysis/inventory/results/summary.json` and `summary.md`; the latest summary is also inserted into this README.

To reuse this question from another script:

```python
from experiment.analysis.inventory.run import run

# Call explicitly when this question is needed.
result = run()
```

Importing the module does not run the analysis.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-10 21:22:44 EDT

Result archives: **234**. Completed models: **9,272,016**.

| Mode | Completed models |
| --- | ---: |
| baseline | 5,616 |
| cognition | 4,633,200 |
| decision | 4,633,200 |

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
