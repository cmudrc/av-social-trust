# Clarified organizational threshold figure

`structure_min_accuracy_clarified.pdf` and `.png` replot an existing cached
conference result. They contain no new simulations, surrogate fits, or
organizational counterfactuals.

The original source CSV is:

`/Users/aslan/Projects/idetc-ai-adoption-paper/figures/cached_min_accuracy/min_accuracy_cache_target_0.500_neg_-0.250_pos_0.250_teamsnum_1_5_10_15_20_25_30_teamssize_5_10_15_20.csv`

The adjacent `structure_min_accuracy_cache.csv` is an unchanged copy of that
file, used by `plot_structure_min_accuracy_clarified.py` for portable reproduction.

The left panel uses average initial opinion -0.25; the right panel uses +0.25.
Columns contain 5, 10, 15, and 20 people per team. Rows run from 1 team at
the bottom to 30 teams at the top, with intermediate counts 5, 10, 15, 20,
and 25. Every cell and both panels share the same color scale.

The target is a model steady-state favorable-opinion fraction `Q + L >= 0.5`.
This differs from actual AI-use eligibility: susceptible agents with mildly
negative opinions may also use AI. AI success probability is the probability
of a satisfactory interaction outcome, rather than an externally validated
accuracy measure.

Cached thresholds range from 0.710 to 0.910 for negative initial opinion and
0.673 to 0.714 for positive initial opinion. Changes with team count and size
are not uniformly monotonic. Because all configurations include social
interaction, these results alone do not isolate the social layer's effect.

The original staged `structure_min_accuracy.pdf` remains unchanged. Model
provenance and the inter-team update implementation must be checked before
publication; relabeling this figure does not resolve that audit.
