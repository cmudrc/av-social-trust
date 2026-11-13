# Can trust learning make an initially isolated driver socially influenced?

In the current sample, weak passenger ties match solo in the first cycle.
With learning, differences reach 9.1% of late decisions in decision mode and
21.9% in cognition mode. With trust frozen, the corresponding rates are 0.0%
and 7.5%. Weak ties therefore do not ensure lasting similarity to solo driving,
especially when influence changes cognition. Late means cycles 81–100.

This controlled experiment reruns complete drives with the same occupants,
initial cognition, trust preferences and track. It changes initial trust and
whether trust learning operates. It never modifies the source archives.

Six conditions compare original trust, weak interpersonal ties with retained
self-trust, and uniformly reduced trust, each with learning enabled or frozen.
“Weak” means dividing interpersonal trust by 1,024. Uniform reduction divides
self-trust by 1,024 as well. These are distinct model interventions.

One fixed random car/start per driver and passenger count is selected from the
existing network sample, and reused on all nine tracks. This covers all 26
drivers and all five passenger counts, but only a small set of starting states.
The comparison estimates the combined effect of interpersonal and self-trust
learning; it does not separate those two rules.

Run from the repository root:

```sh
python3 experiment/analysis/trust_learning/run.py
```

Requires the saved `network_dynamics/results/cycles.npz`. Resumable checkpoints
include source-archive signatures, sampled keys and implementation fingerprints.
Current model, participant export and track hashes must match the archived
experiment. Reference replays must reproduce archived decisions, cognition and
trust exactly. Frozen-trust and uniform-scaling invariants are checked on every
sampled drive. Redraw figures independently with `plot.py`.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-11 15:49:23 EDT

**130 matched base cars × 9 tracks = 1,170 car–track cases.**

Paired full-drive interventions within the simulation. Weak ties reduce every interpersonal edge by 1,024 while retaining self-trust. All-small reduces self-trust too. Fixed conditions freeze both self-trust and interpersonal trust. Results are conditional on this small sampled set of initial states and the nine available tracks.

Early = cycles 1–20; late = cycles 81–100. Percentages count driver decisions different from the matched solo run.

| Starting network / learning | Influence method | First cycle | Early | Late | Whole drive |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original trust, learning | Decision | 24.0% | 14.9% | 9.1% | 10.8% |
| Original trust, learning | Cognition | 24.4% | 22.4% | 21.7% | 22.4% |
| Original trust, fixed | Decision | 24.0% | 18.7% | 13.5% | 15.4% |
| Original trust, fixed | Cognition | 24.4% | 22.7% | 21.2% | 21.8% |
| Weak passenger ties, learning | Decision | 0.0% | 11.5% | 9.1% | 10.3% |
| Weak passenger ties, learning | Cognition | 0.0% | 19.9% | 21.9% | 21.9% |
| Weak passenger ties, fixed | Decision | 0.0% | 0.0% | 0.0% | 0.0% |
| Weak passenger ties, fixed | Cognition | 0.0% | 6.7% | 7.5% | 7.7% |
| All trust reduced, learning | Decision | 24.0% | 19.3% | 9.1% | 12.0% |
| All trust reduced, learning | Cognition | 24.4% | 22.5% | 21.7% | 22.5% |
| All trust reduced, fixed | Decision | 24.0% | 18.7% | 13.5% | 15.4% |
| All trust reduced, fixed | Cognition | 24.4% | 22.7% | 21.2% | 21.8% |

![Weak ties](results/figures/weak_ties.png)

![Network weight](results/figures/weight_recovery.png)

![Uniform scaling](results/figures/uniform_scaling.png)

Uniformly reducing every trust value preserves initial influence weights. With learning frozen, it preserves decisions throughout the drive. Low absolute trust alone therefore does not imply solo-like behavior.

Weak ties retains initial self-trust and reduces interpersonal trust, making the driver initially listen almost entirely to their own view. Learning can build interpersonal trust and also alter self-trust; this comparison estimates their joint effect, not either learning rule separately.

The nine tracks are reused matched trajectories, not independent track realizations for every car. The sample uses one initial car per driver/count; it is a targeted mechanism experiment rather than the full parameter sweep.

Checks: Exact decisions, private cognition and trust match all archived references. Unchanged at every cycle. Frozen decisions unchanged in both modes; initial learned weights unchanged.

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
