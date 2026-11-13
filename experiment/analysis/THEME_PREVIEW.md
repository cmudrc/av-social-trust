# Figure theme preview

The established figures and plotting modules remain unchanged. These previews
read the same saved results and change only presentation. No simulation or
category boundaries are changed. The manuscript still uses established figures.

- Solid lines: decision-level influence. Dashed lines: cognition-level influence.
- Track complexity: Low blue, Medium muted gold, High red.
- Initial trust and confidence: Low teal, Medium purple, High brown.
- Example cases retains the original blue/orange lines and gray solo decisions
  and track-complexity shading; its preview files are exact copies of the original.
- Complexity effects uses blue solid and orange dashed lines because complexity is on its x-axis.
- Passenger count is on the x-axis in the combined preview, with six curves
  (three complexity levels and two influence levels), preserving all five counts.
- Passenger, timing, trust, and confidence figures use a compact 4.80-inch width,
  about 33% narrower than the earlier 7.16-inch previews. Legends sit below the plot.
- Confidence and trust profiles retain observed step 0 through the final state.
  Overlapping category curves are retained at their true values.

Regenerate previews only:

```sh
PYTHONPATH=src MPLCONFIGDIR=/private/tmp/av-social-trust-matplotlib python3 experiment/analysis/theme_preview.py
```

To keep the established appearance, continue using the existing question-specific
plot modules and figure paths. No Git revert is required. Preview exports are
inside the ignored analysis results directory.

## Passenger count

Preview:

![Passenger count preview](results/theme_preview/figures/by_passengers.png)

[Preview PDF](results/theme_preview/figures/by_passengers.pdf) · [Established PDF](track_social_effects/results/figures/by_passengers.pdf)

## Track complexity

Preview:

![Track complexity preview](results/theme_preview/figures/complexity_effects.png)

[Preview PDF](results/theme_preview/figures/complexity_effects.pdf) · [Established PDF](track_social_effects/results/figures/complexity_effects.pdf)

## Example cases

Preview:

![Example cases preview](results/theme_preview/figures/example_cases_simple.png)

[Preview PDF](results/theme_preview/figures/example_cases_simple.pdf) · [Established PDF](example_cases/results/figures/example_cases_simple.pdf)

## Initial trust in driver

Preview:

![Initial trust in driver preview](results/theme_preview/figures/inbound_trust_by_starting_trust.png)

[Preview PDF](results/theme_preview/figures/inbound_trust_by_starting_trust.pdf) · [Established PDF](driver_confidence/results/figures/inbound_trust_by_starting_trust.pdf)

## Initial driver confidence

Preview:

![Initial driver confidence preview](results/theme_preview/figures/starting_confidence.png)

[Preview PDF](results/theme_preview/figures/starting_confidence.pdf) · [Established PDF](driver_confidence/results/figures/starting_confidence.pdf)

## Social influence over time

Preview:

![Social influence over time preview](results/theme_preview/figures/step_blocks_by_complexity.png)

[Preview PDF](results/theme_preview/figures/step_blocks_by_complexity.pdf) · [Established PDF](influence_timing/results/figures/step_blocks_by_complexity.pdf)
