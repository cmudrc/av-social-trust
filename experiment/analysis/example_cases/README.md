# Two example cars: when do solo, decision- and cognition-level driving agree?

Shows, cycle by cycle, how one driver behaves alone, with decision-level influence
and with cognition-level influence, in two cars:

- **agree**: the passengers would sometimes decide differently alone, yet the three
  ways of driving produce (almost) the same automation decisions;
- **disagree**: all three differ from each other by many cycles.

Each column of the figure shows the track's task complexity, the driver's
cognitive state on the dimensions their decision tree uses (alone versus
cognition-level; decision-level influence leaves cognition unchanged, so it
matches the solo line), the car's weighted vote as the driver sees it in
decision-level influence, and the automation timelines of every passenger alone,
the driver alone and the driver under each influence mode.

By default the two cars are chosen automatically: a driver whose solo choices
vary, in a car with four or five passengers (larger preferred), with the same driver,
track and passenger count
for both cases. The selection constants are at the top of run.py. To show
specific cars instead, set `CASES` there, for example

```python
CASES=dict(agree=("P23","low_p2_0",123,15),disagree=("P23","low_p2_0",617,21))
```

with driver, track, composition and start (the table in the latest results lists
the current choice).

Open **run.py** in this folder and choose VS Code's **Run Python File**.
Alternatively, from the repository root:

```sh
python experiment/analysis/example_cases/run.py
```

Run ../compare_modes/run.py first. run.py selects the cars from the shared
analysis table and reads their full trajectories from experiment/runs/ (a few
seconds once the table exists). It saves them in `results/cases.npz` and the case
details in `results/summary.json`.

Figures are drawn by **plot.py** from those saved files, never from the runs:
`results/figures/example_cases_simple` (the driver's decision in each setting over task complexity) and `results/figures/example_cases` (the full breakdown), each as PNG and PDF. Edit plot.py (titles, colors,
panels) and run it to redraw in seconds; run.py calls it automatically.

To reuse this question from another script:

```python
from experiment.analysis.example_cases.run import run

# Call explicitly when this question is needed.
result = run()
```

Importing the module does not run the analysis.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-11 10:59:53 EDT

Two cars with the same driver and track. In the first, the passengers would sometimes decide differently, yet both influence modes leave the driver's choices almost unchanged. In the second, solo, decision-level and cognition-level driving all differ.

The driver's automation decision in each setting, over the track's task complexity:

![Example cases, simple](results/figures/example_cases_simple.png)

The same cars with the driver's cognition, the car's vote and every occupant's timeline:

![Example cases](results/figures/example_cases.png)

| Case | Driver | Passengers | Track | Composition / start | Decision ≠ solo | Cognition ≠ solo | Decision ≠ cognition | Outvoted | Cognitive pull |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| agree | P22 | P04, P13, P16, P21, P25 | low_p2_0 | 47470 / 9 | 1 | 1 | 2 | 4 | 69 |
| disagree | P22 | P02, P04, P20, P24, P25 | low_p2_0 | 28759 / 0 | 49 | 47 | 54 | 58 | 8 |

Trajectories are saved in `results/cases.npz`; redraw with plot.py.

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
