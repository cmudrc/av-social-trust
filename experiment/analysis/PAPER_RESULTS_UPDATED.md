# Social influence across track complexity and time

Updated selection and results draft, 11 October 2026. This document accompanies
the revised figures; the earlier `FIGURE_GUIDE.md` has not been rewritten.

The common outcome is the driver's automation decision. The social effect is
the percentage of steps at which that decision differs from the matched solo
run. A difference can be toward automation or toward manual driving. It measures
how much adding the social layer changes modeled behavior, not the accuracy or
safety of the resulting behavior.

## Draft results text

Adding passengers changed driver behavior to different degrees across the
simulated cars. The selected example drives illustrate this variation: in one
case, each social model differed from solo driving at only one of the 100 steps;
in the other, decision-level and cognition-level influence changed 49 and 47
decisions, respectively. These examples illustrate the outcome; the aggregate
comparisons establish its frequency.

The size of the social effect decreased as track complexity increased.
Decision-level influence changed 18.3%, 10.5% and 6.1% of driver decisions at
Low, Medium and High complexity. Cognition-level influence changed 27.5%, 21.9%
and 18.7%, respectively. Cognition-level influence produced larger departures
from solo driving at every complexity level, and remained substantial on the
high-complexity tracks.

The time course of the effect also depended on complexity and on where influence
was applied. On high-complexity tracks, decision-level differences fell from
15.7% in steps 1–20 to 3.9% in steps 21–100. The corresponding cognition-level
differences fell from 22.3% to 19.2%, remaining much larger later in the drive.
On low-complexity tracks, decision-level differences were nearly unchanged
(18.4% to 18.8%), while cognition-level differences increased from 24.7% to 29.7%.
Thus, social influence did not simply fade with time: its persistence depended
on the track and the influence mechanism. Ten-step averages show this pattern
at greater temporal resolution without the fluctuations of individual steps.

Including the social layer also changed the driver's self-trust. Starting from
a shared mean of 0.515, final self-trust averaged 0.798 with decision-level
influence and 0.673 with cognition-level influence. Solo self-trust remained
constant under the model's update rule. Low, Medium and High starting-confidence
groups ended with closely spaced group means in decision mode (approximately
0.796, 0.796 and 0.803). The corresponding cognition-mode means were 0.677, 0.651
and 0.685. Starting confidence therefore provided an incomplete description of
later confidence. These are group averages, not evidence that every individual
driver converged to one value.

Track complexity was also associated with the development of self-trust. Final
confidence was higher on higher-complexity tracks in both social models, even
though those tracks showed smaller decision differences from solo driving.
This connects the track and adaptation results, but the two associations alone
do not establish that increasing confidence caused the smaller social effect.
In the model, self-trust competes with trust in passengers when determining the
weight given to the driver's own judgment. The social layer can therefore alter
both a current decision and the driver's later susceptibility to influence.

An additional controlled experiment tested whether weak initial passenger ties
ensure continued similarity to solo driving. Both social models matched solo
in the first step after interpersonal trust was reduced while self-trust was
retained. With trust learning enabled, differences reached 9.1% of decisions
in steps 81–100 under decision-level influence and 21.9% under cognition-level
influence. Holding trust fixed gave corresponding rates of 0.0% and 7.5%.
Weak initial ties therefore did not guarantee a persistently small social
effect. This experiment isolates the combined contribution of interpersonal
and self-trust learning within the sampled simulations.

## Selected figures and captions

Use the example, complexity, time and confidence figures as the core sequence.
Starting-confidence and confidence-by-complexity panels add detail to the
adaptation result. The controlled weak-ties experiment adds a stronger mechanism
result if space permits. The alternatives below are choices, not additional
figures that all need to appear in the paper.

### 1. What a social effect looks like

[Example drives — PDF](example_cases/results/figures/example_cases_simple.pdf)

![Example drives](example_cases/results/figures/example_cases_simple.png)

**Caption:** Driver automation decisions in three matched model variants for two
selected cars. One case shows nearly identical behavior; the other shows
different automation choices and switching times. Gray shading identifies
high task-complexity steps. Small vertical offsets distinguish coincident lines.

### 2. How much the track changes the social effect

[Complexity effects — PDF](track_social_effects/results/figures/complexity_effects.pdf)

![Complexity effects](track_social_effects/results/figures/complexity_effects.png)

**Caption:** Mean percentage of driver decisions different from the matched
solo baseline at Low, Medium and High track complexity. Comparisons retain the
same cars and initial conditions across tracks, average over persistence
settings, and give equal weight to drivers and passenger counts.

### 3. How the effect develops over steps, with complexity included

**Recommended detailed version:**
[ten-step averages by complexity — PDF](influence_timing/results/figures/step_blocks_by_complexity.pdf).

![Ten-step averages by complexity](influence_timing/results/figures/step_blocks_by_complexity.png)

**Caption:** Mean percentage of driver decisions different from solo driving
within successive, non-overlapping ten-step blocks, shown by track complexity
for each influence mechanism. Points represent steps 1–10, 11–20, …, 91–100 and
are placed at block midpoints. Curves use the fixed sample of 46,800 car–track
cases, with 200 cases per driver and track. Lines connect block averages.

**Simpler alternative:**
[early/later by complexity — PDF](influence_timing/results/figures/timing_by_complexity.pdf).
This uses all comparisons and asks the same question with only two windows.
Early is steps 1–20; later is steps 21–100. Each value is a rate per step, so the
unequal window lengths do not inflate the later rate.

The [overall early/later figure](influence_timing/results/figures/timing.pdf) and
[overall ten-step figure](influence_timing/results/figures/step_blocks.pdf) are
alternatives when complexity panels are unnecessary. Overall early/later rates
are 16.1% → 11.0% for decision-level influence and 22.8% → 24.1% for cognition-level
influence. The complexity split adds information: these overall means conceal
different time patterns on low- and high-complexity tracks.

No “outvoted” or “cognitive pull” curves appear in the revised time plots.
Those were benchmarks: an equal-weight occupant vote opposing the driver,
or applying the driver's decision rule to mean occupant cognitive states.
Neither is needed to interpret the percentage of decisions different from solo.

### 4. Social interaction changes confidence as well as decisions

[Confidence trajectories — PDF](driver_confidence/results/figures/confidence_trajectories.pdf)

![Confidence trajectories](driver_confidence/results/figures/confidence_trajectories.png)

**Caption:** Mean driver self-trust over the drive in the three model variants.
Step 0 is the initial state; subsequent points follow completed simulation
steps. The same 780 sampled base cars are repeated on all nine tracks, with equal
driver and passenger-count weights. Solo confidence is constant by construction.

Self-trust is confidence in one's own judgment. It is updated from passengers'
trust in the driver, not measured driving success or decision correctness.
The [confidence intervention](driver_confidence/results/figures/confidence_intervention.pdf)
is a supporting way to connect self-trust directly to the current decision:
it changes only self-trust in an observed snapshot and recalculates influence.
It does not estimate a complete future drive under altered initial confidence.

### 5. Starting confidence is not the whole story

[Starting confidence, three categories — PDF](driver_confidence/results/figures/starting_confidence.pdf)

![Starting confidence](driver_confidence/results/figures/starting_confidence.png)

**Caption:** Mean self-trust trajectories grouped by Low, Medium and High
starting confidence. Category differences narrow during the drive, especially
under decision-level influence. The groups describe existing matched runs;
other starting conditions are not held fixed between confidence categories.

**Use three categories in the main paper.** Low is below 1/3, Medium is from
1/3 to below 2/3, and High is at least 2/3 on the model scale. Each category
contains two of the experiment's six starting values. These are descriptive
display categories, not validated psychological thresholds. The legend uses
names; the boundaries belong in the methods or caption.

A [five-category alternative](driver_confidence/results/figures/starting_confidence_five.pdf)
uses Very low, Low, Medium, High and Very high, with boundaries at 0.2, 0.4, 0.6
and 0.8. It provides finer detail, but closely overlapping curves make the main
pattern harder to see. Four categories offer no clear advantage for this design.

### 6. Track complexity also accompanies confidence adaptation

[Confidence by complexity — PDF](driver_confidence/results/figures/confidence_by_complexity.pdf)

![Confidence by complexity](driver_confidence/results/figures/confidence_by_complexity.png)

**Caption:** Mean driver self-trust over steps at Low, Medium and High track
complexity. Initial conditions and cars are matched across tracks, and each
complexity category averages over persistence settings. Final confidence is
0.611, 0.851 and 0.933 in decision mode, and 0.562, 0.701 and 0.754 in cognition
mode. This figure concerns confidence adaptation; the earlier complexity figure
concerns decisions, so they answer different questions.

## What else adds substance?

The strongest additional result is
[the controlled weak-ties figure](trust_learning/results/figures/weak_ties.pdf).
It distinguishes an initial condition from a process that unfolds during the
drive. Its 130 base cars on nine tracks form a targeted experiment, not the
entire starting-state sweep. It freezes interpersonal and self-trust learning
together, so it does not separate the two rules. The frozen cognition condition
retains small nonzero social weights, which can still alter later states.

A second, optional network result is
[weighted centrality over time](network_confidence/results/figures/centrality_over_time.pdf)
and [weighted centrality versus confidence](network_confidence/results/figures/centrality_confidence.pdf).
These are more directly related to the proposed network question than the old
four-panel network average.

![Weighted centrality and confidence](network_confidence/results/figures/centrality_confidence.png)

**What centrality means here:** it measures the driver's share of influence
through the current directed trust network, including indirect paths. A value
of 1 means an equal share among occupants, above 1 means more than an equal
share. It uses the trust weights, not merely the number of connections. The
measure holds the current weights fixed for its calculation; it does not claim
the changing simulation reaches consensus.

Greater mean confidence accompanies greater mean centrality only loosely:
rank associations are 0.211 in decision mode and 0.258 in cognition mode.
Centrality includes self-trust through the network weights, so this association
is not an independent causal finding. The useful interpretation is that
**confidence and network influence are related but not interchangeable**.
The centrality-over-time figure also shows variation between cases rather than
only a near-constant mean. The central half of early-to-late drive-window
centrality values narrows from approximately 0.89–1.13 to 0.99–1.05 in decision
mode, versus 0.88–1.14 to 0.97–1.16 in cognition mode. Its shaded ranges describe
case variation, not uncertainty in the mean.

Passengers' “listening” in the older figure meant the influence weight assigned
to the driver's judgment. Passengers can also weight their own or another
passenger's judgment. It did not mean obedience to the driver.

## Keep these outside the main results

- [Solo regimes](baseline_quality/results/figures/baseline_regimes.png): baseline
  description, appendix or supplement.
- [Similarity categories](baseline_similarity/results/figures/categories_by_condition.pdf):
  optional supplement. The right panel groups cases by **solo baseline behavior**;
  it still compares the two social models against that baseline. Blue means only
  decision-level influence resembles solo, orange means only cognition-level
  influence does, green means both, and gray means neither. “Resembles” means
  at most five different decisions out of 100. This threshold outcome is less
  direct than the main changed-decision percentage and can be omitted.
- Pressure ratios, pressure heatmaps and the old network averages: diagnostics
  unless the paper makes a specific claim requiring them.

## Scope and reporting details

The whole-drive complexity result uses all 514,800 matched base car/start cases
and balances drivers and passenger counts. Early/later timing uses the full
4,633,200 comparison grid with pooled case weights; ten-step timing uses its
separate 46,800-case sample. Confidence and centrality use 780 matched base cars
on nine tracks, with equal driver and passenger-count weights. The targeted
trust-learning experiment uses 130 base cars on those tracks. Exact percentages
from these populations should not be combined as though they had identical
sampling and weights.

The nine tracks are fixed generated trajectories spanning three complexity
levels. Repeating cars on them does not create additional independent track
realizations. Results concern the specified model, tracks and sampled starting
states. Temporal associations alone do not identify which learning rule caused
the change; controlled interventions provide the stronger mechanism evidence.
