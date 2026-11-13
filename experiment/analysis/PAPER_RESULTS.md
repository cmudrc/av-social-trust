# Results to consider for the paper

Snapshot: 2026-10-11. This guide interprets the current saved results. Running each
analysis updates its own README and outputs; revisit these example sentences if
inputs or sampling change.

The common outcome is the **driver's actual automation decision** at each cycle.
For each social method, the social effect is the percentage of cycles that differ
from the matched solo trajectory. The comparison between social methods answers
how much the result depends on where influence is applied. A net change in total
automation use is a separate outcome: switches toward and away from automation
can cancel even when many individual decisions change.

## 1. Does track complexity change how much the social layer matters?

**Recommended main result:** use Low, Medium and High track complexity without
internal track names. These categories describe the track-generation conditions,
not three levels observed within every individual cycle. Average over the three
persistence settings for the main figure and table.

Use [complexity effects](track_social_effects/results/figures/complexity_effects.pdf)
and [paired complexity differences](track_social_effects/results/figures/paired_contrasts.pdf).
All 514,800 car–start cases are present on every track. Each car is averaged over
persistence within complexity; drivers and passenger counts receive equal weight.

**What the percentages mean:** for each matched pair, count the cycles in which
the driver's on/off automation decisions differ, divide by the 100 cycles, and
multiply by 100. The table reports the balanced average of those percentages.
Thus 18.3% means about 18 of 100 driver decisions differ, on average. It does not
mean that 18.3% of drivers change, or that automation use increases by 18.3%.
Differences include both switching toward automation and switching toward manual
driving. Matching the same driver, initial state and track isolates differences
between the model variants within this simulation.

| Track complexity | Decision-level influence compared with solo driving | Cognition-level influence compared with solo driving |
| --- | ---: | ---: |
| Low | 18.3% | 27.5% |
| Medium | 10.5% | 21.9% |
| High | 6.1% | 18.7% |

Suggested table caption:

> Mean percentage of simulation cycles in which the driver's automation decision
> differs from the matched solo baseline, by track complexity. Results average
> over persistence settings and give equal weight to drivers and passenger counts.

Possible results wording:

> Across the simulated tracks, divergence from solo driving decreased with
> increasing track complexity. Decision-level influence changed 18.3%, 10.5%
> and 6.1% of driver decisions at low, medium and high complexity, respectively.
> Cognition-level influence changed 27.5%, 21.9% and 18.7%. Cognition-level
> influence therefore produced larger differences from solo behavior at every
> complexity level. Social influence remained visible at high complexity,
> particularly when applied to cognition.

These results describe changed behavior. They do not establish which model is
more accurate, whether the change improves driving, or why the effect decreases.
“Importance” here means sensitivity of modeled driver behavior to adding the
social layer; it is not a direct measure of real-world safety or predictive accuracy.

### Optional separate result: does it matter where social influence is applied?

The comparison between social methods is **not needed** in the main table if its
sole purpose is to show how much adding the social layer changes solo driving.
Keep it separately if the paper also compares the modeling mechanisms.

| Track complexity | Decision-level compared with cognition-level influence |
| --- | ---: |
| Low | 33.9% |
| Medium | 24.0% |
| High | 19.6% |

Use [the separate method-comparison figure](track_social_effects/results/figures/method_difference.pdf).
Here 33.9% means that the two social models make different driver decisions on
about 34 of 100 cycles, on average. The result supports this statement:

> The location of social influence also affected the modeled behavior. The
> decision-level and cognition-level models disagreed on 33.9% of cycles at low
> complexity, falling to 19.6% at high complexity. Thus the choice of influence
> mechanism mattered across all three complexity levels, with greater agreement
> at higher complexity.

This does not identify a better model. The 33.9% is not the difference between
18.3% and 27.5%: those two quantities compare each method with solo driving;
the third measures whether the two social methods disagree **with each other**
on the same cycles. Their changed cycles can occur at different times.

### Persistence and other supplementary checks

Persistence is averaged over in the main presentation, rather than assumed to
have no effect. On low-complexity tracks, changing persistence from 0.3 to 0.9
reduced decision-level changed decisions by 3.37 percentage points but increased
cognition-level changed decisions by 6.58 points. Retain the persistence grid
and contrasts as supplementary checks; do not write that persistence is irrelevant.

The analysis also retains raw versus balanced weighting, passenger-count results,
changed-cycle threshold checks and the shared track pattern in within-car variation.
Details: [track analysis](track_social_effects/README.md).

**Scope of claim:** there are nine generated sequences, one per
complexity–persistence cell. They differ in realized complexity and ordering.
Averaging over persistence simplifies the presentation; it does not remove these
sequence differences. The repeated car simulations do not create additional
independent track realizations. Generalizing the effects of complexity beyond
these sequences requires more track realizations.

## 2. Does an influential driver behave more like their solo self?

Separate three meanings of influence: retaining one's own view, being listened
to by passengers, and being influential through the full directed network. The
last measure describes the network at that cycle with weights held fixed; it is
not a prediction that the evolving simulation reaches a final consensus. Its
fixed-network interpretation follows
[DeGroot (1974)](https://pages.ucsd.edu/~aronatas/project/academic/degroot%20consensus.pdf).

**Starting position is a weak predictor.** In the balanced sample of
780 cars on nine tracks, rank associations between initial relative network
influence and changed-cycle fraction were -0.086 for decision-level
and -0.046 for cognition-level influence. The
[starting-network figure](network_dynamics/results/figures/starting_network.pdf)
is useful if the paper needs to distinguish starting conditions from dynamics.

**Changes during the drive are more closely associated.** After comparing within
driver, track and passenger-count groups, the association between early-to-late
increases in relative network influence and early-to-late changes in decision
disagreement was -0.474 in decision mode and
-0.128 in cognition mode. Larger increases in influence
accompany larger reductions in disagreement with solo driving, especially in
decision mode. The corresponding raw associations were
-0.438 and -0.166.

**Use this as a descriptive result.** Trust updates respond to opinions, so the
network's changing position can be a result of agreement as well as a predictor.
The early-network / late-behavior associations are also saved and are weak;
concurrent associations should not be described as strong forecasts. No
independent-cycle significance tests are reported. The sample and half-sample
checks are explicitly included in [the network analysis](network_dynamics/README.md).

## 3. Does the weight carried by disagreement matter more than the number of dissenters?

**Recommended main network figure:**
[weighted disagreement](network_dynamics/results/figures/weighted_disagreement.pdf).
It connects an understandable network property directly to the model mechanism.
A passenger contributes to this measure only if their current private vote
opposes the driver's current private vote; their contribution is the weight the
driver actually assigns to their view.

Possible results wording:

> The two influence mechanisms respond differently to influential disagreement.
> Decision-level influence follows a weighted vote: opposing passengers must
> carry at least half the weight to reverse a positive driver vote, and more
> than half to reverse a negative vote. Cognitive influence mixes states before
> evaluating the driver's decision rule, so the same voting threshold does not
> apply.

Numerical ties select manual driving. Values extremely close to the half-weight
boundary can differ because of floating-point rounding; do not interpret tiny
boundary-bin exceptions as a new behavioral mechanism.

A complementary [own-weight figure](network_dynamics/results/figures/own_weight_disagreement.pdf)
asks whether the driver can resist disagreement. In decision mode, there were
**zero changed decisions** among 39,769 sampled cycles with more than half
of the effective weight retained by the driver (a small numerical margin is used
for this check). This follows from binary weighted voting; it is a model property
confirmed in the runs, not a newly discovered empirical law. Cognition mode has
no such guarantee because even a small state change can cross a tree threshold.

## 4. Do the methods agree now, or has earlier influence already changed the driver?

[The two panels of weighted disagreement](network_dynamics/results/figures/weighted_disagreement.pdf)
compare the final choice with (left) the current private choice and (right) the
solo choice. In decision mode these references coincide. In cognition mode they
can differ because the state carried into later cycles already includes earlier
social influence. This distinction explains why immediate effects of mixing
can be modest while the full trajectory differs substantially from solo driving.
It does not imply that every difference is caused only by accumulated influence;
current mixing contributes as well.

The analysis also asks
[when decision and cognition methods agree](network_dynamics/results/figures/methods_agreement.pdf).
All three methods agree on 70.7% of balanced sampled car–cycles. This is
cycle agreement, not the fraction of completely identical 100-cycle trajectories.

## 5. What affects driver confidence, and what does confidence affect?

Here confidence means **raw self-trust**, the model variable representing trust
in one's own judgment on a 0–1 scale. It is not trust in automation or the
probability that a decision is correct. The new
[driver-confidence analysis](driver_confidence/README.md) uses the same 780 cars
on all nine tracks and distinguishes update rules, observed associations and
immediate interventions.

**How confidence evolves:** mean confidence starts at 0.515. It remains at
0.515 in solo driving and ends at 0.798 with decision-level influence and
0.673 with cognition-level influence. About
73.7% of sampled car–track cases gain confidence in decision mode and
62.1% in cognition mode; the other cases lose confidence.
The mean increase is not a universal increase for every driver.

Use [confidence trajectories](driver_confidence/results/figures/confidence_trajectories.pdf)
as the main descriptive figure. Confidence is constant in solo mode because its
update rule has no incoming social appraisals. The model does not learn self-trust
from real driving performance or success; this flat baseline is an assumption,
not an empirical finding about people driving alone.

**What directly updates confidence:** it moves toward passengers' mean raw trust
in the driver, by 10% of the gap per cycle. Incoming appraisals greater than current
self-trust raise it; smaller appraisals lower it. Private vote agreement and
alignment with the group update those appraisals. Newly updated appraisals then
affect confidence in the following cycle's trust update. Complexity, cognitive
states and social-network settings act through that pathway; they are not direct
inputs to the confidence-update equation. The
[update figure](driver_confidence/results/figures/confidence_update.pdf) verifies this
specified relationship; it is not a discovery from fitting the simulation data.

**Track association:** final confidence is higher on the higher-complexity
sequences, averaging over persistence:

| Track complexity | Final confidence: decision-level influence | Final confidence: cognition-level influence |
| --- | ---: | ---: |
| Low | 0.611 | 0.562 |
| Medium | 0.851 | 0.701 |
| High | 0.933 | 0.754 |

Use [confidence by complexity](driver_confidence/results/figures/confidence_by_complexity.pdf).
These are comparisons on the realized sequences. They do not prove that difficult
driving directly increases real-world confidence. Passenger-count and starting-
confidence plots, plus associations with private agreement, are saved as supporting
analyses. Initial-confidence versus confidence-change correlations are strongly
negative partly because the update moves toward an appraisal target: low starts
have more room to rise. Do not present this as an independent causal discovery.

**What confidence immediately affects:** it changes how much the driver listens
to their own view. With one discussion round, that weight equals self-trust divided
by self-trust plus the total trust the driver places in passengers. Thus self-trust
and retained own weight are different quantities. Confidence is not directly fed
to the driver's decision tree; its immediate effect on decisions goes through
vote mixing in decision mode and cognitive-state mixing in cognition mode.
In decision mode, the final socially influenced choice is not fed back into
private cognition or the votes used to learn trust. Cognition mode carries its
mixed state into the next cycle, allowing confidence to affect later private
opinions and appraisals as well.

Use [the immediate-intervention figure](driver_confidence/results/figures/confidence_intervention.pdf).
For every recorded cycle, only self-trust is replaced by values from 0 to 1.
The private inputs and all other trust entries remain fixed. In decision mode,
the fraction of decisions different from the current private decision drops
from 18.5% at self-trust 0 to
5.9% at self-trust 1. The same quantities in cognition mode drop
from 4.9% to 3.1%.

Even self-trust 1 gives mean retained weights of only 0.363 in
decision snapshots and 0.394 in cognition snapshots: total
trust in several passengers can outweigh it. "Maximal confidence" does not mean
the driver ignores passengers.

In cognition mode, differences from **solo driving** remain
21.5% even at self-trust 1, compared with
22.9% at self-trust 0. Changing confidence in a single snapshot does not
undo earlier social changes already present in the private cognitive state.
These interventions are separate immediate replays; their outputs are not carried
forward. They do not estimate the full effect of setting initial confidence and
rerunning the entire drive, nor a causal effect on real people.

Possible results wording:

> Driver self-trust evolved differently under the two influence mechanisms.
> Starting from a shared mean of 0.515, final confidence averaged 0.798 with
> decision-level influence and 0.673 with cognition-level influence, while solo
> confidence remained constant by construction. Fixed-cycle interventions showed
> that higher self-trust increased the driver's retained influence and reduced
> immediate departures from their private choice. Its effect on differences from
> solo driving was smaller in cognition mode, where the current state already
> incorporated earlier social influence.

## 6. Can weak initial passenger ties become important through trust learning?

The new [trust-learning experiment](trust_learning/README.md) reruns complete
matched drives for **130 base cars on nine tracks (1,170 car–track cases)**.
It reduces interpersonal trust by a factor of 1,024 while retaining initial
self-trust, then compares learning enabled with both self-trust and interpersonal
trust held fixed. Drivers, passengers, initial cognition, alpha and tracks are
the same in every intervention. Each archived reference is reproduced exactly.

Use [weak ties](trust_learning/results/figures/weak_ties.pdf) as the main network
result and [weight recovery](trust_learning/results/figures/weight_recovery.pdf)
to explain the changing weight given to the driver's own judgment.

| Starting network / trust learning | First-cycle difference: decision influence | Late difference: decision influence | First-cycle difference: cognition influence | Late difference: cognition influence |
| --- | ---: | ---: | ---: | ---: |
| Original trust / enabled | 24.0% | 9.1% | 24.4% | 21.7% |
| Original trust / frozen | 24.0% | 13.5% | 24.4% | 21.2% |
| Weak passenger ties / enabled | 0.0% | 9.1% | 0.0% | 21.9% |
| Weak passenger ties / frozen | 0.0% | 0.0% | 0.0% | 7.5% |

“Late” means cycles **81–100**, and percentages count driver decisions different
from matched solo driving. This is a smaller sample than the full complexity
analysis, so do not substitute these percentages into the complexity table.

Possible results wording:

> Weak initial trust in passengers eliminated differences from solo driving in
> the first cycle of the sampled runs. With trust learning enabled, differences
> emerged during the drive, reaching 9.1% of late-cycle decisions under
> decision-level influence and 21.9% under cognition-level influence. Holding
> trust fixed preserved solo behavior throughout in decision mode, but not in
> cognition mode, where late-cycle differences reached 7.5%. Initial weak social
> ties therefore did not guarantee a persistently small social effect.

This estimates the **joint effect of both trust-learning rules within the
simulation**, not a real-world causal effect or the separate effect of either
rule. Under the original starting network, learning reduced late decision-level
divergence by 4.4 percentage points. Under weak ties, learning increased it by
9.1 points. Trust learning therefore does not uniformly amplify social effects;
its contribution depends on the initial network.

The weak frozen cognition condition still has small nonzero social weights.
Mixing cognitive states can cross decision boundaries and affect states carried
into later cycles even when the driver keeps most of the influence weight.
It is not the same intervention as removing the social layer completely.

**Uniformly small trust is a different question.** A control reduces every
trust value, including self-trust, by the same factor. Initial normalized
influence weights are unchanged; frozen runs produce identical driver decisions
to the unscaled frozen runs throughout. With learning enabled, their early
behavior can differ because learning updates raw trust toward absolute targets.
Use [uniform scaling](trust_learning/results/figures/uniform_scaling.pdf) as a
supporting control. The experiment uses a power-of-two scaling factor to avoid
introducing numerical changes at exact voting ties through decimal roundoff.

The sample covers all drivers and passenger counts but selects only one base
car/start per driver and count from the existing network sample. It reuses the
nine available tracks. This is a focused mechanism experiment; broader
starting-state and independently generated track replication would be needed
to establish robustness beyond these conditions.

## Which figures I would choose

Start with the **simple examples** and **complexity effects**, adding the
directly labelled **passenger-count** panels if space permits. Use **weak ties**
for a controlled network result and pair **confidence trajectories** with the
**confidence intervention** to connect social adaptation to decisions. The
**similarity categories** are an optional overview of when a solo approximation
is adequate, using an explicitly defined five-cycle threshold.

Keep network averages, pressure ratios, heatmaps and detailed correlation curves
as supporting analyses unless they answer a specific claim. Read
[FIGURE_GUIDE.md](FIGURE_GUIDE.md) for a plain-language explanation of every
selected figure and draft wording. Every figure is saved as PNG and vector PDF;
`plot.py` redraws from saved summaries without rereading trajectories.

Reproduce the analyses:

```sh
python experiment/analysis/track_social_effects/run.py
python experiment/analysis/network_dynamics/run.py
python experiment/analysis/driver_confidence/run.py
python experiment/analysis/trust_learning/run.py
```

The track analysis uses all matched cases; network and confidence analyses use
saved trajectory samples. The trust-learning analysis reruns full drives for a
smaller matched sample with controlled changes. Existing model code and source
archives remain unchanged.
