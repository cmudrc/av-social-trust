# Experiment analysis questions

Each folder contains one analysis topic, its `run.py` script and a README explaining its question, inputs and output.

To run several questions in sequence, open **main.py** and comment out the
`run_question(...)` calls you want to skip. Then use **Run Python File**:

```sh
python experiment/analysis/main.py
```

All questions are enabled initially. Their calls run one at a time, in the order
shown in `main()`. Keep `compare_modes` enabled when the comparison cache needs
to be created or refreshed; comment it out to reuse an up-to-date cache. An error
stops the sequence so dependent questions do not run with missing inputs.
Ctrl+C stops the sequence as well; completed artifacts and comparison batches
remain saved.

| Folder | Question or purpose |
| --- | --- |
| [inventory](inventory/README.md) | Which models have finished? |
| [baseline_quality](baseline_quality/README.md) | How does each driver behave when driving alone? |
| [compare_modes](compare_modes/README.md) | Prepare matched comparisons for the analysis questions |
| [passenger_count_effects](passenger_count_effects/README.md) | How do decision changes vary with passenger count? |
| [network_effects](network_effects/README.md) | How do decision changes vary with social trust and influence weights? |
| [driver_state_effects](driver_state_effects/README.md) | How do decision changes vary with the driver's starting state? |
| [track_effects](track_effects/README.md) | How do decision changes vary with track difficulty and persistence? |
| [social_importance](social_importance/README.md) | How large and persistent are the changes caused by social influence in the simulation? |
| [occupant_disagreement](occupant_disagreement/README.md) | Does the social layer change behavior only when the occupants would decide differently alone? |
| [pressure_conversion](pressure_conversion/README.md) | When the car would overrule or pull the driver, what decides whether behavior changes? |
| [influence_timing](influence_timing/README.md) | Does the social effect fade, persist or build up during a drive? |
| [participant_susceptibility](participant_susceptibility/README.md) | Which participants are affected most, and which model properties explain it? |
| [when_social_matters](when_social_matters/README.md) | When does the social layer change the driver's behavior compared with driving alone? |
| [example_cases](example_cases/README.md) | Two example cars: when do solo, decision- and cognition-level driving agree? |
| [baseline_similarity](baseline_similarity/README.md) | When do decision- and/or cognition-level driving look like driving alone, and what predicts it? (also writes the per-car similarity dataset) |
| [track_social_effects](track_social_effects/README.md) | For the same cars on every track, how do difficulty and persistence change the social effect? Three approaches, with figures and weighting checks. |
| [network_dynamics](network_dynamics/README.md) | Does the driver's initial or changing influence in the directed trust network accompany agreement between the three methods? |
| [driver_confidence](driver_confidence/README.md) | What updates driver self-trust, and what does changing it immediately affect? Trajectories, descriptive associations and fixed-cycle interventions. |
| [trust_learning](trust_learning/README.md) | Can trust learning make weak initial passenger ties matter later? Matched full-drive interventions with learning enabled or frozen. |
| [network_confidence](network_confidence/README.md) | How does weighted driver centrality vary over time and accompany self-trust in exactly matched trajectories? |
| [social_direction](social_direction/README.md) | Does the social layer push the driver toward or away from automation, and does it follow the passengers' lean? |
| [complexity_pressure](complexity_pressure/README.md) | Does high task complexity shrink the social effect because the occupants already agree? |
| [tree_features](tree_features/README.md) | Which cognitive states do the 26 participant models and decision trees use? |

## Direct comparisons for the paper

Use the driver's binary automation decision as the common comparison point.
`track_social_effects` compares all complete car–track matches using direct track
summaries, paired track differences and the common track share of variation.
`network_dynamics` reads a fixed balanced sample of full trajectories to compare
the driver's retained own weight, passengers' attention to the driver, and
relative influence in the current network. It distinguishes starting positions,
concurrent associations, early-to-late changes and disagreement carried by
influential passengers. Both produce PNG and vector PDF figures and save plot
data for fast redraws. Read [PAPER_RESULTS.md](PAPER_RESULTS.md) for the recommended
questions, current findings and figures to consider for the paper. Read
[FIGURE_GUIDE.md](FIGURE_GUIDE.md) for plain-language explanations of the selected
figures and a proposed results story. `trust_learning` reruns a small matched
sample with altered initial networks and learning controls; source archives
remain read-only.

## When does the social layer matter?

The last five questions address the research question: when does adding
passengers (the social layer) change the driver's automation decisions compared
with the solo baseline? They share one idea. Every occupant's solo baseline at
the same track and start shows how that person would decide alone. In
decision-level influence these solo choices are exactly the votes the driver
hears, because voting does not change anyone's cognition. From them the shared
table derives two equal-weight pressure measures:

- **outvoted cycles**: an unweighted vote of the car overrules the driver's solo choice;
- **cognitive-pull cycles**: the driver's own tree, applied to the car's mean
  solo cognition, flips the driver's solo choice.

`when_social_matters` compares these pressures with the scenario parameters and
participant identity as explanations. The other four questions show the
mechanism: whether pressure is necessary (`occupant_disagreement`), what turns
pressure into change (`pressure_conversion`), how the effect develops over a drive
(`influence_timing`) and which participant models are susceptible
(`participant_susceptibility`).

These questions read `compare_modes/results/analysis_table.npz`, a numeric copy
of the comparison cache extended with the pressure columns. The first of them to
run after `compare_modes` changes the cache rebuilds it (about two minutes).

## Figures for the paper

The latest selected figures and a draft results narrative are in
[PAPER_RESULTS_UPDATED.md](PAPER_RESULTS_UPDATED.md). The earlier figure guide
remains a separate snapshot. Timing now includes early/later comparisons and
non-overlapping ten-step averages, with optional complexity panels and no
equal-weight pressure curves. Starting confidence uses three named categories;
a five-category alternative is also saved. Time axes are labelled **Steps**.

Analyses can take minutes; figures should not. The social-layer questions
therefore separate the two: **run.py** computes and saves everything a figure
needs in the question's `results/` folder (summary.json, plus .npz files for
larger data), and **plot.py** draws the figures from those files only. Edit a
plot.py and run it to restyle in seconds. To redraw every figure without running
any analysis, set `REDRAW_ONLY = True` in main.py and run it (about two seconds).
Figures are saved as PNG for the READMEs and as vector PDF for the paper, sized
for a two-column layout (`shared/figures.py` holds the widths, fonts and colors:
decision-level blue, cognition-level orange).

| Figure | What it shows |
| --- | --- |
| `example_cases/results/figures/example_cases` | Two cars, cycle by cycle: one where solo, decision- and cognition-level driving agree, one where they diverge |
| `occupant_disagreement/results/figures/pressure_heatmaps` | Every car by pressure and change: each mode follows its own pressure, not the other mode's |
| `influence_timing/results/figures/cycle_dynamics` | The share of cars changed tracks the share under pressure at every cycle |
| `when_social_matters/results/figures/explanations` | Pressure explains far more of the change than scenario parameters or participant identity |
| `pressure_conversion/results/figures/conversion` | How passenger count and the driver's homophily change how much pressure becomes change |
| `participant_susceptibility/results/figures/participants` | Participants change about as much as the pressure they face |
| `baseline_similarity/results/figures/pressure_plane` | Which modes still look like driving alone, across outvoted × cognitive-pull cycles |
| `baseline_similarity/results/figures/agreement_map` | Every car by decision- and cognition-level agreement with driving alone |
| `influence_timing/results/figures/timing` | Decision-level influence fades on hard tracks because pressure fades |

Start with `inventory/run.py` or `baseline_quality/run.py` to inspect completed models directly. Run `compare_modes/run.py` once before running any of the five comparison-based analyses; repeat it when more models have finished. Each question script can then be run independently in VS Code using **Run Python File**, without arguments.

`shared/` contains the common calculation and output helpers. Each question saves
its artifacts in its own gitignored `results/` subfolder:

```text
baseline_quality/
    run.py
    README.md                    # question + latest results
    results/
        summary.json
        summary.md
        figures/baseline_regimes.png
```

Running a question replaces the generated **Latest results** section in its
README and preserves the human-written explanation. It saves `summary.json` and
`summary.md`; grouped reports also save `groups.jsonl`. Future questions can add
figures or other artifacts to the same `results/` folder. To use the same output
convention, call `shared.output.write_results()` with a result dictionary and a
Markdown summary.

The shared comparison cache lives in `compare_modes/results/comparisons.sqlite`.
The other questions read it without copying the cache. The scripts read
experiment model archives without modifying model rows.

`compare_modes` prints its cache path immediately, then archive progress and
new-comparison counts about every five seconds. It checkpoints each batch and
updates its README with the running status. Ctrl+C preserves completed batches;
running it again filters cached pairs in SQL before loading model metadata.
The first extraction still processes millions of pairs. Calculations are batched,
and the cache fingerprints the metric implementation separately from report
formatting.

Every question script exposes a `run()` function and executes it only in an
`if __name__ == "__main__":` block. Future questions can reuse a previous question
without running it during import:

```python
from experiment.analysis.passenger_count_effects.run import run as analyze_passengers
from experiment.analysis.compare_modes.run import extract
from experiment.analysis.shared.common import similarity

if __name__ == "__main__":
    summary = analyze_passengers()
```

`run()` returns the analysis result. The existing `inventory()`, `summarize()`
and `extract()` functions also remain available for more specific reuse. To add
a question, create a new folder with `__init__.py`, `run.py` and a README, put
its calculations in callable functions, and keep execution in the main block.
