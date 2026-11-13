# What affects the driver's confidence, and what does it affect?

The current plots use **Steps** on time axes. `starting_confidence` now uses
three named groups, Low / Medium / High, with boundaries at 1/3 and 2/3.
`starting_confidence_five` saves a Very low / Low / Medium / High / Very high
alternative using boundaries at 0.2, 0.4, 0.6 and 0.8. Numerical definitions
and group profiles are saved in `results/starting_categories.json`. Both
versions include the initial state at step 0 and the final state after step 100.
These are display categories on the model scale, not empirical confidence grades.

Here **confidence means raw self-trust** (`T[0,0]`), on the model's 0–1 scale.
It represents confidence in one's own judgment. It is distinct from trust in
automation, tree probabilities, and the normalized weight assigned to one's own
view. It is a modeling proxy, not a measured probability of being correct.

The analysis reuses the fixed balanced sample from `network_dynamics`: the same
780 cars on all nine tracks. Driver and passenger-count groups receive equal
weight. Comparisons match initial driver cognition and self-trust. No simulation
archive or model is modified.

Questions answered:

1. How does self-trust evolve in solo, decision-level and cognition-level runs?
2. Do low and high starting self-trust approach similar later values?
3. How does confidence differ by Low, Medium and High track complexity, averaging
   across persistence? How does it differ by passenger count?
4. Do passengers' appraisals, private agreement and alignment with the group
   accompany confidence gains or losses?
5. Does higher confidence accompany fewer changed decisions or decision switches?
6. What changes **immediately** if only driver confidence changes, with all other
   inputs to that cycle held fixed?
7. How does passengers' trust in the driver evolve, grouped by starting driver
   confidence or by starting passenger trust?

## Passengers' trust in the driver over steps

[Grouped by the driver's starting confidence — PDF](results/figures/inbound_trust_by_starting_confidence.pdf)
uses the **same Low / Medium / High groups as the starting-confidence figure**.
It tracks a different quantity: the mean raw trust passengers place in the
driver (`T[passenger, driver]`), excluding the driver's self-trust. Trust is
averaged across passengers within each car before averaging across cars with
the existing driver and passenger-count weights. Using a mean avoids treating
more passengers as automatically meaning greater trust.

![Passenger trust by starting driver confidence](results/figures/inbound_trust_by_starting_confidence.png)

Mean final passenger trust is 0.778–0.790 across the three driver-confidence
groups in decision mode and 0.640–0.672 in cognition mode. The groups have
similar initial mean passenger trust, around 0.5. Group differences are
descriptive: the analysis does not change only starting driver confidence.

[Alternative: grouped by starting trust in the driver — PDF](results/figures/inbound_trust_by_starting_trust.pdf)
groups cars by their **initial mean passenger trust**, rather than by driver
self-confidence. Low, Medium and High use the same boundaries at 1/3 and 2/3.
This counterpart to the starting-confidence plot shows whether initially low
and high passenger appraisals remain different over the drive.

![Passenger trust by its own starting level](results/figures/inbound_trust_by_starting_trust.png)

Both figures include step 0 and the final state after step 100. There is no
solo line: with no passengers, passenger-to-driver trust is undefined. Raw
incoming trust is distinct from a normalized influence weight and from network
centrality. Numerical profiles, category counts, definitions and weighting are
saved in `results/inbound_trust_categories.json`. The plots reuse saved trust
histories; they do not run new simulations. The paper draft uses the
initial-confidence plot in the main results and the alternative grouped by
initial passenger trust in the appendix.

## Relationships built into the model

Self-trust moves toward the mean **raw** trust passengers place in the driver:

```text
next self-trust = current self-trust
                 + learning rate × (passengers' mean trust − current self-trust)
```

Solo self-trust stays constant because no passengers supply appraisals. Passengers'
trust in the driver changes with their agreement with the driver's private vote
and the driver's alignment with the group, according to the fixed alpha weights.
These new appraisals affect confidence in the **next** trust update. The analysis
reconstructs pre-cycle trust from initial trust plus the previous cycle's saved
post-update matrix, and verifies both update equations numerically.

The current model learns confidence from social appraisals. It does not update
self-trust from actual driving success, mistakes or independently measured
performance. A constant solo trajectory is therefore a modeling assumption,
not evidence that real drivers' confidence cannot change during solo driving.

Self-trust affects normalized influence weights. With one discussion round:

```text
driver's own weight = self-trust / (self-trust + total driver trust in passengers)
```

The amount of passenger trust matters too: high self-trust is not the same as
having most of the voting weight. Driver confidence changes the driver's row of
the influence matrix. With one discussion round it affects the driver's mixing
immediately, not other agents' mixing in that same round. Decision mode mixes
private votes; cognition mode mixes states and carries the resulting state
forward. Raw self-trust is not a direct input to the driver's decision tree.
In decision mode, final social choices are not fed back into the private cognitive
update or trust-learning votes. In cognition mode, confidence can change mixed
states and therefore later private opinions, social appraisals and confidence.

## Immediate intervention versus observed association

For each saved cycle, replace only self-trust by 0, 0.25, 0.5, 0.75 or 1. Keep the
private states and opinions, all other raw trust entries and automation
availability fixed; then rerun discussion and the driver's decision. This is a
controlled immediate intervention **within the model**. Replayed outputs are
not carried forward. It does not estimate the full effect of changing the initial
confidence for an entire drive or a real-world causal effect.

Observed correlation and bin plots remain descriptive. Opinions and social trust
can cause both changing confidence and changing decisions. Starting confidence
versus later confidence change also contains ordinary regression toward the
model's appraisal target; it should not be claimed as an independent discovery.
No independent-cycle p-values or causal claims from correlations are reported.

```sh
python experiment/analysis/driver_confidence/run.py
python experiment/analysis/driver_confidence/plot.py  # redraw saved figures
```

Run `network_dynamics/run.py` first if its sample is missing or stale. Confidence
extraction checkpoints by archive and checks source and calculation signatures,
participant and track hashes, pre-cycle weights and sampled choices. `cycles.npz`
retains per-cycle confidence, appraisals, choices, gains and intervention outputs.
`summary.json` saves numerical results. Figures are PNG and vector PDF. Main
paper candidates are the confidence trajectories and immediate-intervention
figure; complexity, passenger count, starting confidence and observed association
plots provide supporting results.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-11 15:30:27 EDT

Driver confidence = raw self-trust, on the 0–1 model scale; it is not a calibrated probability of being correct.

**780 sampled cars on nine tracks**, 7,020 car–track comparisons.

Equal drivers and passenger counts; same sampled cars on every track; persistence averaged for complexity figures.

Update relationships are verified model rules. Observed associations are descriptive. Interventions change only confidence in fixed cycle snapshots; they are not new full-drive trajectories or real-world causal estimates.

### Track confidence through the drive

![Confidence trajectories](results/figures/confidence_trajectories.png)

| Method | Initial confidence | Final confidence | Mean change |
| --- | ---: | ---: | ---: |
| baseline | 0.515 | 0.515 | +0.000 |
| decision | 0.515 | 0.798 | +0.284 |
| cognition | 0.515 | 0.673 | +0.158 |

![Different starting confidence](results/figures/starting_confidence.png)

### What affects confidence?

The exact update is: next confidence = current confidence + 0.1 × (passengers’ mean raw trust in the driver − current confidence). Confidence rises when passengers’ trust exceeds it, falls when it is lower, and remains constant when driving alone. This relationship is built into the model, not an empirical discovery.

![Confidence update](results/figures/confidence_update.png)

![Confidence by complexity](results/figures/confidence_by_complexity.png)

![Confidence by passengers](results/figures/confidence_by_passengers.png)

Opinions update passengers’ trust after the cycle. That updated appraisal changes confidence in the following cycle’s trust update. Track complexity and occupant disagreement therefore act indirectly through opinions and trust.

### What does confidence affect?

With one discussion round, the driver’s own weight is raw self-trust divided by (raw self-trust + total driver trust in passengers). High confidence alone does not ensure high own weight.

![Confidence and observed decisions](results/figures/observed_confidence.png)

Observed binned rates are descriptive and can reflect other changing conditions.

![Changing only confidence](results/figures/confidence_intervention.png)

For each recorded cycle, the intervention sets only driver self-trust to 0, 0.25, 0.5, 0.75 or 1. All other trust entries, private opinions, cognitive states and automation availability stay fixed. Discussion and the driver’s decision are recomputed. Outputs are not carried forward to later cycles. This isolates the immediate effect of confidence within the model, not the full effect on a future drive.

Cognition-mode comparisons with the current private decision distinguish immediate influence from changes already carried in cognition. The solo decision is an additional reference, not a new starting state for these interventions.

### Numerical checks and associations

Maximum confidence-update error: 1.35e-16; maximum passenger-trust-update error: 4.44e-16. Replaying the observed snapshots disagreed on [0, 0] decisions (decision, cognition; near-boundary rounding is reported rather than hidden).

| Method | Predictor | Outcome | Rank association | Within comparable groups |
| --- | ---: | ---: | ---: | ---: |
| decision | Initial confidence | Confidence change over drive | -0.869 | -0.945 |
| decision | Initial passengers’ trust in driver | Confidence change over drive | +0.046 | +0.071 |
| decision | Initial driver trust in passengers | Confidence change over drive | +0.027 | +0.046 |
| decision | Passengers agreeing with driver (drive average) | Confidence change over drive | +0.397 | +0.229 |
| decision | Driver agrees with group (drive average) | Confidence change over drive | +0.394 | +0.230 |
| decision | Initial confidence | Different decisions from solo (whole drive) | -0.108 | -0.092 |
| decision | Early confidence | Different decisions from solo (late drive) | -0.074 | -0.032 |
| cognition | Initial confidence | Confidence change over drive | -0.806 | -0.885 |
| cognition | Initial passengers’ trust in driver | Confidence change over drive | +0.042 | +0.083 |
| cognition | Initial driver trust in passengers | Confidence change over drive | +0.027 | +0.068 |
| cognition | Passengers agreeing with driver (drive average) | Confidence change over drive | +0.527 | +0.382 |
| cognition | Driver agrees with group (drive average) | Confidence change over drive | +0.521 | +0.381 |
| cognition | Initial confidence | Different decisions from solo (whole drive) | -0.003 | -0.012 |
| cognition | Early confidence | Different decisions from solo (late drive) | -0.076 | -0.022 |

Within comparable groups means subtracting averages within driver × track × passenger count before calculating the rank association. No independent-cycle significance tests are used. Full measurements and identifiers are saved in cycles.npz.

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
