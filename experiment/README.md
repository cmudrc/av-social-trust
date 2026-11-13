# Participant experiment

This folder replaces the layered `paper/experiments` pipeline. Its code is public;
`data/`, `runs/` and each analysis question's `results/` subfolder are gitignored. The private data copy is
untouched. The new code does not import anything from `paper/`, reuse the old
study results, or create `study_<hash>` directories. Old studies remain where they
were; this runner starts fresh in the initially empty `experiment/runs/`.

Install the experiment dependencies in your Python environment:

```sh
python -m pip install -e '.[experiment]'
```

Select that interpreter in VS Code. Every entry script below supports **Run
Python File**, without arguments or a separate preparation command. Paths are
relative to this folder, not your terminal's working directory.

## Files to run

1. Edit **`config.py`**. `STEPS` controls both track length and model duration.
2. Run **`tracks/generate_tracks.py`**. It saves the shared tracks once in
   `tracks/tracks/`, with one shared manifest for their seeds/settings/checksums.
3. Run **`tracks/visualize_tracks.py`**. It shows all tracks in one Matplotlib
   graph. Set `SELECTED_TRACKS` to names such as `['low_p0_0', 'normal_p0_0', 'high_p0_0']`
   for a subset. `SMOOTHING_WINDOW=1` shows raw binary complexity; the default
   trailing average makes the nine sequences easier to compare. For every
   difficulty, `p0`, `p1`, and `p2` use persistence 0.3, 0.6, and 0.9 respectively.
   `TRACK_REPLICATES` controls independent repetitions of each difficulty–persistence
   pair. Total tracks = number of difficulties × number of persistence levels ×
   repetitions. Names use `<difficulty>_p<persistence-index>_<repetition-index>`.
4. Run **`runner.py`**. It loads the existing track CSVs, loads the private
   participant export once, and runs/resumes the models on multiple processes.

The default plan keeps all 26 drivers, all 25 single-passenger combinations,
and 200 sampled compositions for each of 2–5 passengers per driver. Each uses
nine tracks, 12 cognitive starts and two social starts, with both influence modes.
Matching solo baselines run first and are reused. Total: **9,272,016 models**.

## Multicore and sleep

`CPU_CORES_FREE=2` leaves two logical cores free; set it to `1` if preferred.
At least one worker is used. Workers use one BLAS thread each and a bounded
task queue. `TASK_RUNS` changes scheduling overhead, not checkpoint granularity.
The coordinator prepares every driver/track archive in WAL mode before workers
start, so workers do not compete to change journal mode. Temporary locks during
initialization are retried for up to 60 seconds.

`KEEP_AWAKE=True` starts macOS `caffeinate` **from Python**, including when
launched by VS Code. No terminal wrapper is required. Leave the laptop open,
connected to power, and VS Code's Python process running. Preventing idle sleep
does not override closing the lid or explicitly putting the Mac to sleep.

## Completed models only

Results are grouped into SQLite archives named by driver and shared track:

```text
experiment/
    config.py
    data/combined_models.mat             # private, unchanged
    tracks/tracks/low_p0_0.csv            # shared input, one copy
    tracks/tracks/manifest.json          # shared track generation metadata
    runs/P01_low_p0_0.sqlite              # completed models only
    runs/P01_normal_p0_0.sqlite
    ...                                 # up to 26 × 9 = 234 result archives
    analysis/<question>/results/         # ignored, derived analyses
```

Each `results` row represents **one complete model**. Its primary key is
`(composition, start, variant)` within the driver/track archive. Variant is
`baseline`, `decision`, or `cognition`; composition `0` is solo. Metadata also
contains the readable model name
`<track-code>_<driver-number>_<composition-id>_<passenger-count>_<start>_<variant>`.
`start = cognitive_start * SOCIAL_STARTS + social_start`.

The row holds a compressed NumPy trajectory and its essential labels, initial
features and outcome summary. A packed copy of the driver's on/off sequence
supports fast comparisons without decompressing every trajectory. Initial
cognition/trust/alpha and the complete per-step progression are retained at
float64 precision. Shared track columns, participant coefficients, trees,
personal-state banks and source files are **not copied into runs**.

Only one experiment definition per archive is retained for reproducibility and
to detect incompatible inputs/settings. It contains hashes and settings, not
copies of the inputs. There is no separate job manifest, pending/running table,
completion-marker directory, progress JSON, execution timestamps or PID history.
SQLite's transient WAL files provide transaction durability while writing; normal
runner shutdown checkpoints archives. Never manually remove a live SQLite WAL.

### Stop and restart

Ctrl+C or normal termination asks workers to stop at the next step. An unfinished
model stays in memory and is **not saved**. Models already committed remain.
An abrupt process kill also cannot commit a partial trajectory. Workers check
that their parent is alive and stop if VS Code kills the coordinator.

Run `runner.py` again. It recreates the same deterministic plan, skips complete
models and runs all missing models, including interrupted ones, from step 1.
No resampling occurs on restart. When everything is complete, another invocation
does no computation. The final model keys and trajectories are the same regardless
of stop/restart count; SQLite's internal byte/page layout need not be identical.
Stopping between the two influence modes preserves whichever model completed.

For large existing archives, resume can pause after the initial `Models:` line
while checking completed models, before workers start. Run
`repair_resume_index.py` once to add a small completion lookup index to every
existing archive. It avoids reading the large trajectory table during this scan.
The repair preserves model rows, metadata and resume compatibility, and can be
repeated safely. SQLite coordinates it with an active runner. New result
directories can also use this repair after archives have been created.

Changing CPU allocation or `KEEP_AWAKE` does not invalidate results. Changing
scientific settings, fitted data, shared tracks, relevant code or package versions
requires an empty `RUNS_DIR`. The runner raises an error rather than mixing them
or deleting existing results. Choose a new empty path in `config.py`, or explicitly
remove old results yourself if you want to restart. Regenerate tracks after changing
`STEPS` or track-generation settings. Generating the same settings yields the same
CSV contents and can be done without invalidating results.

The reviewed October 10, 2026 SQLite initialization fix is an explicit exception
for two exact runner/storage source revisions listed in `runtime_compatibility.py`.
It changes archive initialization and lookup indexes, not model calculations.
Existing archives retain their original definitions and remain resumable. All
scientific settings, data, tracks, environment versions and other source hashes
must still match; unrecognized runner/storage edits remain incompatible.

## Model conventions

Each participant uses its own fitted affine cognitive coefficients and its own
decision tree. Solo: private update → tree. Cognition influence: private update →
social cognition → tree, with that cognition fed into the next cycle. Decision
influence: private update → tree's binary vote → social vote, with ties selecting
manual. Both modes update trust from the private binary decision votes, before
social influence. The normative source is the unweighted mean of those votes
over every occupant, including the driver. Each directed connection has a fixed,
randomly sampled homophilic–normative tradeoff, saved as `alpha`; it does not
change during the run. The two modes' private votes can diverge in later cycles
because their cognitive states evolve differently.

Private cognitive predictions are clipped to [0,1], with raw predictions and
clipping flags retained. Unselected cognitive dimensions carry through the private
update and participate in social mixing. `NETWORK_TOPOLOGY` in `config.py` selects
`"star"` (driver–passenger links only) or `"fully_connected"` (all occupant pairs).
Both directions have independently sampled trust and fixed `alpha` values.
Learning rates and discussion rounds are configured in `config.py`. Transferring driver fits to
passengers is an assumption, not a validation against actual passenger behavior.

Track generation conditions persistent binary Markov draws on realized complexity:
low 0.1–0.3, normal 0.4–0.6, high 0.7–0.9 by default. This keeps labels consistent;
it is not an unconditional sample from the Markov process. Base/accepted seeds and
generation attempts are kept in the one shared track manifest.

## Read a model

```python
from experiment.results import read_result

metadata, arrays = read_result(
    'experiment/runs/P01_low_0.sqlite',
    composition=1, start=0, variant='cognition',
)
print(metadata['model_name'])
print(arrays['automation_on'])
print(arrays['social_cognition'])       # steps × occupants × [trust, risk, workload]
print(arrays['trust'])                  # steps × occupants × occupants
```

Occupants are driver first, then metadata's passenger list. Progress arrays include
`step`, `raw_private_cognition`, `private_cognition`, `social_cognition`, `clipped`,
`private_decisions`, `final_decisions`, private/final opinions, tree probabilities,
`automation_on`, `influence_matrix` and post-update `trust`, plus initial-state arrays.
Use metadata's track name to join the one shared CSV for the external situation.

## Separate analysis

Each analysis topic has its own folder, `run.py` entry script and README that
states its question. See [the analysis guide](analysis/README.md) for the full list.
To run selected questions in sequence, edit the calls in `analysis/main.py`,
comment out the ones to skip, and run that file.
Run the scripts individually using VS Code:

- `analysis/inventory/run.py`: which models have finished?
- `analysis/baseline_quality/run.py`: how do drivers behave alone?
- `analysis/compare_modes/run.py`: prepare matched comparisons for the questions below.
- `analysis/passenger_count_effects/run.py`: how do changes vary with passenger count?
- `analysis/network_effects/run.py`: how do changes vary with social trust and weights?
- `analysis/driver_state_effects/run.py`: how do changes vary with the driver's starting state?
- `analysis/track_effects/run.py`: how do changes vary with track difficulty and persistence?
- `analysis/social_importance/run.py`: how large and persistent are social-influence changes?

Run `compare_modes/run.py` before the five comparison-based analyses. Shared
calculation helpers live in `analysis/shared/`.

These scripts open model archives read-only, save derived files in each question's
ignored `results/` subfolder, and update the question's README with a latest-results
section. Comparison extraction shows progress and checkpoints batches in
`analysis/compare_modes/results/comparisons.sqlite`. Repeat extraction after more models finish. Neither
missing influence partners nor missing baselines count as a complete comparison.
Parameter reports describe associations; independently sampled starts do not
establish an isolated causal effect for every parameter.

Checks using fabricated trajectories, without running the experiment:

```sh
python -m unittest experiment.tests.test_pipeline experiment.tests.test_sqlite_runtime experiment.tests.test_analysis_outputs -v
```
