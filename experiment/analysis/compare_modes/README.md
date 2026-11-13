# Prepare matched comparisons for the analysis questions

Matches each decision-influence model to its cognition-influence partner and solo baseline, then calculates shared decision-comparison metrics. This is a preparation step for the other analyses.

Open **run.py** in this folder and choose VS Code's **Run Python File**.
Alternatively, from the repository root:

```sh
python experiment/analysis/compare_modes/run.py
```

Reads experiment/runs/ directly. Repeat this step to include newly completed models; incomplete matches are skipped.

Output: `experiment/analysis/compare_modes/results/comparisons.sqlite`, `summary.json` and `summary.md`. The running status and final summary are inserted into this README.

To reuse this question from another script:

```python
from experiment.analysis.compare_modes.run import run

# Call explicitly when this question is needed.
result = run()
```

Importing the module does not run the analysis.

Progress appears immediately and updates about every five seconds while extracting. Each completed batch is saved; Ctrl+C stops safely and a later run skips cached pairs. The README status is updated during extraction.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-10 22:08:06 EDT

Status: **complete**.

- Cached matched comparisons: **4,633,200**
- Added in this run: **3,637,200**
- Archives checked: **234/234**
- Current archive: `P26_normal_p2_0.sqlite`

Each comparison matches decision influence, cognition influence and a solo baseline. Missing partners or baselines are skipped. Completed batches remain saved if interrupted.

Data: [comparisons.sqlite](results/comparisons.sqlite).

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
