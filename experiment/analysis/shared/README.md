# Shared helpers

`metrics.py` defines the on/off comparison calculations and their batched form.
`common.py` provides the grouped-report calculations used by several questions.
`output.py` saves per-question artifacts and replaces a generated results section
in the question's README while preserving the authored text. Run the scripts in
the question folders; this folder provides their shared functions.

`table.py` builds and caches the numeric analysis table used by the social-layer
questions: comparison features and metrics, plus each car's solo disagreement,
outvoted and cognitive-pull cycles from the occupants' solo baselines.
`rules.py` grows a shallow classification tree whose leaves read as rules.
`stats.py` provides grouped means and ratios, rank correlations and variance
shares; `figures.py` gives the figures one consistent look (decision mode blue,
cognition mode orange).
