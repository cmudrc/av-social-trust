# How does each driver behave when driving alone?

Summarizes solo models as always manual, always automated or varying, and counts models whose predicted cognition was clipped.

Open **run.py** in this folder and choose VS Code's **Run Python File**.
Alternatively, from the repository root:

```sh
python experiment/analysis/baseline_quality/run.py
```

Reads experiment/runs/ directly; no preparation needed.

Output: `experiment/analysis/baseline_quality/results/summary.json` and `summary.md`; the latest summary is also inserted into this README.

To reuse this question from another script:

```python
from experiment.analysis.baseline_quality.run import run

# Call explicitly when this question is needed.
result = run()
```

Importing the module does not run the analysis.

The run also saves `results/figures/baseline_regimes.png` and includes it in the results section.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-10 21:22:45 EDT

Completed solo baselines: **5,616**.

| Automation behavior | Models | Share |
| --- | ---: | ---: |
| Always manual | 2,390 | 42.6% |
| Varying | 3,098 | 55.2% |
| Always automated | 128 | 2.3% |

Models with cognitive clipping: **810** (14.4%).

![Solo baseline regimes](results/figures/baseline_regimes.png)

| Driver | Baselines | Always manual | Varying | Always automated | With clipping |
| --- | ---: | ---: | ---: | ---: | ---: |
| P01 | 216 | 80 | 128 | 8 | 0 |
| P02 | 216 | 36 | 166 | 14 | 154 |
| P03 | 216 | 172 | 44 | 0 | 0 |
| P04 | 216 | 148 | 68 | 0 | 0 |
| P05 | 216 | 126 | 90 | 0 | 0 |
| P06 | 216 | 0 | 216 | 0 | 144 |
| P07 | 216 | 146 | 70 | 0 | 168 |
| P08 | 216 | 0 | 216 | 0 | 0 |
| P09 | 216 | 164 | 52 | 0 | 0 |
| P10 | 216 | 198 | 18 | 0 | 0 |
| P11 | 216 | 88 | 72 | 56 | 8 |
| P12 | 216 | 142 | 66 | 8 | 0 |
| P13 | 216 | 58 | 130 | 28 | 0 |
| P14 | 216 | 156 | 60 | 0 | 0 |
| P15 | 216 | 114 | 102 | 0 | 168 |
| P16 | 216 | 0 | 214 | 2 | 0 |
| P17 | 216 | 4 | 212 | 0 | 0 |
| P18 | 216 | 98 | 118 | 0 | 0 |
| P19 | 216 | 92 | 124 | 0 | 0 |
| P20 | 216 | 140 | 76 | 0 | 0 |
| P21 | 216 | 0 | 216 | 0 | 168 |
| P22 | 216 | 32 | 172 | 12 | 0 |
| P23 | 216 | 0 | 216 | 0 | 0 |
| P24 | 216 | 126 | 90 | 0 | 0 |
| P25 | 216 | 162 | 54 | 0 | 0 |
| P26 | 216 | 108 | 108 | 0 | 0 |

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
