# Which cognitive states do the participant models and decision trees use?

Lists, for each of the 26 participant models, the cognitive states included in
the fitted dynamics, the states its decision tree splits on, the number of splits,
and whether the fitted state matrix is diagonal. The headline is how many trees
use workload, the state that transfers least well from drivers to passengers.

Open **run.py** in this folder and choose VS Code's **Run Python File**, or from the
repository root:

```sh
python experiment/analysis/tree_features/run.py
```

Reads the private participant export in `experiment/data/`. Output:
`results/summary.json` and `results/summary.md`.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-16 12:43:35 EDT

**26 participant models.**

| | Trust | Risk | Workload |
| --- | ---: | ---: | ---: |
| Models including the state | 16 | 12 | 13 |
| Trees splitting on the state | 16 | 12 | 13 |

Models with one / two / three states: 11 / 15 / 0. Trees without splits: 0. Diagonal state matrices: 26 of 26.

| Participant | Model states | Tree splits on | Splits | Diagonal A |
| --- | ---: | ---: | ---: | ---: |
| P01 | risk | risk | 1 | yes |
| P02 | trust, risk | trust, risk | 2 | yes |
| P03 | trust, workload | trust, workload | 2 | yes |
| P04 | risk, workload | risk, workload | 2 | yes |
| P05 | trust | trust | 1 | yes |
| P06 | trust | trust | 1 | yes |
| P07 | trust, risk | trust, risk | 2 | yes |
| P08 | workload | workload | 2 | yes |
| P09 | risk, workload | risk, workload | 2 | yes |
| P10 | risk, workload | risk, workload | 2 | yes |
| P11 | trust, workload | trust, workload | 2 | yes |
| P12 | trust, risk | trust, risk | 2 | yes |
| P13 | trust, workload | trust, workload | 2 | yes |
| P14 | risk, workload | risk, workload | 2 | yes |
| P15 | risk, workload | risk, workload | 2 | yes |
| P16 | workload | workload | 1 | yes |
| P17 | risk, workload | risk, workload | 2 | yes |
| P18 | trust | trust | 1 | yes |
| P19 | trust, workload | trust, workload | 2 | yes |
| P20 | trust | trust | 2 | yes |
| P21 | workload | workload | 1 | yes |
| P22 | trust | trust | 1 | yes |
| P23 | trust | trust | 2 | yes |
| P24 | trust | trust | 1 | yes |
| P25 | trust, risk | trust, risk | 2 | yes |
| P26 | trust, risk | trust, risk | 2 | yes |

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
