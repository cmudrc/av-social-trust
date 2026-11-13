# A clear results story for the paper

The paper's common question is: **when does including passengers change the
driver decisions predicted by the model?** Measure this by comparing the
driver's automation decision at each cycle with their matched solo run. Changed
decisions establish that the social layer matters to simulated behavior. They
do not establish improved safety or predictive accuracy.

The figures can tell a connected story: the effect varies across cars; track
complexity changes its size; the influence mechanism changes its form; and
trust learning can make an initially weak network consequential over time.
Confidence belongs in this story when connected to the driver's influence
weights and decisions.

## The selected figures, in plain language

| Figure | The question it answers | What we can say | Place in the paper |
| --- | --- | --- | --- |
| [Similarity categories](baseline_similarity/results/figures/categories_by_condition.pdf) | When can we approximate social driving with solo driving? | Both social models resemble solo more often at higher complexity. A model can resemble solo while the other differs. “Alike” means at most **5 changed cycles out of 100**, not identical behavior. Bars show shares of **car–track cases**, not shares of changed decisions. | Main overview, if this approximation question is central. |
| [Simple examples](example_cases/results/figures/example_cases_simple.pdf) | What does a social effect look like in a drive? | One selected car shows almost coincident choices; another shows different switching times and automation choices. | An intuitive introduction to the results. The selected examples do not estimate prevalence. |
| [Complexity effects](track_social_effects/results/figures/complexity_effects.pdf) | How much does track complexity change the social effect? | Changed decisions fall from **18.3% to 6.1%** for decision-level influence and **27.5% to 18.7%** for cognition-level influence, from Low to High complexity. Cognition-level influence remains substantial on the high-complexity tracks. | Main quantitative result. |
| [Passenger count and complexity](track_social_effects/results/figures/by_passengers.pdf) | Do complexity and passenger count show the same pattern in both social models? | All count groups decline with complexity. Cognition-level effects generally increase with passenger count, with little separation between four and five passengers. Decision-level effects are not monotonic in count; two passengers produce the largest mean effect at low complexity. | Main companion panel, or combine with complexity effects. |
| [Confidence trajectories](driver_confidence/results/figures/confidence_trajectories.pdf) | Does including the social layer also change the driver's self-trust? | Mean self-trust changes from **0.515 to 0.798** in decision mode and **0.673** in cognition mode. Solo self-trust is constant by the specified model rule. | Mechanism result, paired with a figure showing effects on decisions. |
| [Starting confidence](driver_confidence/results/figures/starting_confidence.pdf) | Does the initial confidence group retain its position throughout the drive? | Group means become much closer as the drive progresses, especially in decision mode. A static initial-confidence description misses later social adaptation. | Supporting result. These are grouped existing runs, not an experiment changing confidence alone. Similar group means do not mean every individual converges. |
| [Confidence by complexity](driver_confidence/results/figures/confidence_by_complexity.pdf) | Does the track also change learned self-trust? | Higher-complexity tracks end with higher mean self-trust in both social modes. | Companion to complexity effects if the paper explains adaptation. The two figures alone do not establish that higher confidence causes the smaller decision effect. |
| [Influence timing](influence_timing/results/figures/timing.pdf) | Does the social effect persist throughout the drive? | Across the full grid, decision-level divergence declines from **16.1% early to 11.0% later**; cognition-level divergence is **22.8% early and 24.1% later**. | Optional temporal result. “Early” is cycles 1–20; “later” is 21–100. |
| [Cycle dynamics](influence_timing/results/figures/cycle_dynamics.pdf) | How do those time patterns vary with complexity? | Solid lines show the percentage of sampled cars differing from solo at each cycle. Decision-level differences drop strongly on the high-complexity tracks; cognition-level differences persist. Dotted lines are equal-weight benchmarks, not observed social influence. | Supporting detail; the simpler timing figure is easier to explain. |
| [Network over time](network_dynamics/results/figures/network_over_time.pdf) | Do average influence weights change during the drive? | The first three panels describe mean network properties. The fourth shows differences from solo. The relative-influence mean stays close to 1, the equal-share benchmark. | Supplement. The small, truncated vertical ranges emphasize small changes; co-moving averages do not prove that centrality causes agreement. |
| [Disagreement curves](occupant_disagreement/results/figures/change_vs_pressure.pdf) | Which kind of passenger disagreement accompanies each kind of social effect? | Decision-level changes rise with the frequency of an opposing equal-weight vote. Cognition-level changes rise with the frequency at which mixed cognitive states would flip the driver's tree. | A useful explanation of why the two mechanisms differ, if the benchmark is defined clearly. |
| [Disagreement heatmaps](occupant_disagreement/results/figures/pressure_heatmaps.pdf) | How variable are cars around those mean relationships? | Color counts cars; the black curve gives the mean changed-cycle count at each benchmark count; the dashed diagonal compares equal counts. Stronger relationships appear in the two panels matching each mechanism to its own benchmark. | Supplement. The simpler curves tell the same main story. |
| [Pressure count ratio](pressure_conversion/results/figures/conversion.pdf) | How many actual changed cycles occur relative to an equal-weight benchmark? | A value of 0.77 means **77 actual changed cycles per 100 benchmark pressure cycles in aggregate**. Those can be different cycles. It does not mean 77% of pressure events change the decision. | Supplement or omit. It is less direct than the changed-decision outcome and does not isolate learning. |
| [Solo regimes](baseline_quality/results/figures/baseline_regimes.png) | Is the baseline varied enough for social comparisons to be informative? | Drivers include manual, mixed and automation-heavy solo behavior. | Baseline description or supplement. |

The complexity/passenger-count figure describes **joint patterns**, not a proof
that adding one passenger independently causes a particular increase. Passenger
groups contain different compositions. Track comparisons are matched within
the same car and initial conditions, and average over persistence settings.
Three complexity categories cover nine fixed generated tracks; they are not
many independent realizations of each complexity level.

Different analyses use different samples and weights. The complexity analysis
balances drivers and passenger counts across all matched cases; confidence and
network figures use a fixed balanced sample; the older timing and disagreement
summaries describe the full grid, and timing curves use another sample. Their
percentages should not be combined as if they came from one identical population.

## Connecting confidence to the paper's question

The useful claim is **social interaction changes the driver as well as the
current decision**. The model lets passenger appraisals update the driver's
self-trust. That self-trust competes with trust in passengers when determining
how much the driver listens to their own view. Thus confidence is part of the
social influence mechanism, rather than an unrelated psychological outcome.

Use the confidence trajectory alongside
[the immediate confidence intervention](driver_confidence/results/figures/confidence_intervention.pdf).
The latter changes only the driver's current self-trust, holds the rest of the
observed snapshot fixed, and recalculates the choice. Raising self-trust from 0
to 1 reduces differences from the current private choice from **18.5% to 5.9%**
in decision mode and **4.9% to 3.1%** in cognition mode. This directly connects
self-trust to the current social effect within the simulation.

For cognition mode, the private state already includes earlier social influence.
Giving the driver more weight now does not restore the earlier solo trajectory.
This explains why the social layer can remain important even when the driver
currently has greater confidence. The snapshot intervention does not estimate
the entire effect of setting confidence at the start of a drive.

Suggested wording:

> Including passengers changed both driver decisions and the evolution of
> self-trust. Self-trust affected the weight given to the driver's own judgment,
> linking social adaptation to subsequent influence. In the cognition-level
> model, increased weight on the current judgment did not remove differences
> already incorporated into the cognitive state.

Confidence here is **self-trust**, not confidence that a decision is correct.
Its update uses passenger trust, not a measure of driving success. The flat solo
curve reflects the update rule, not evidence that real solo drivers never learn.

## A stronger network question: can weak ties become important?

The new [trust-learning experiment](trust_learning/README.md) tests the user's
proposed mechanism by rerunning complete, matched drives. It retains the same
people, cognition, track and trust preferences while changing the starting
network and whether learning is enabled.

Two meanings of “all trust is near zero” must be separated:

1. **Weak interpersonal trust with self-trust retained:** the driver initially
   gives almost all influence weight to their own judgment. Compare learning
   enabled with trust frozen to see whether this protection persists.
2. **Every trust entry reduced, including self-trust:** normalization preserves
   the initial relative weights. With learning frozen, the two networks produce
   the same decisions throughout the drive. Small absolute trust is not by
   itself a small social layer.

Use [weak ties](trust_learning/results/figures/weak_ties.pdf) for the behavioral
result and [weight recovery](trust_learning/results/figures/weight_recovery.pdf)
to explain it. The [uniform-scaling control](trust_learning/results/figures/uniform_scaling.pdf)
is a supporting check. The experiment uses 130 sampled base cars on all nine
tracks and freezes self-trust and interpersonal learning together; it measures
their combined contribution. It is a targeted mechanism experiment, not the
full starting-state sweep.

In this sample, both weak-tie models match solo in the first cycle. With
learning enabled, late-cycle differences reach **9.1%** for decision-level and
**21.9%** for cognition-level influence. With trust frozen, they are **0.0%**
and **7.5%**, respectively. Here late means cycles **81–100**.
The frozen cognition result is useful: small remaining social weights can
still change cognitive states and later decisions. Weak ties are not absent ties.
Under the original network, learning reduces late decision divergence from
13.5% to 9.1%, so learning does not always increase the social effect.

The existing full-network centrality plots are less direct for this question.
A fully connected network can still distribute weight very unequally. Moreover,
being listened to by passengers and giving one's own view high weight are
different properties. Changes in centrality can be a consequence of agreement,
so correlation alone does not show that centrality makes the methods converge.

## A focused sequence for the results section

1. Show the two example drives to make “changed driver decisions” concrete.
2. Establish the size and conditions of the effect with complexity effects;
   use the passenger-count companion if space permits.
3. Show persistence or emergence over time with the controlled weak-ties result.
4. Connect adaptation to behavior with confidence trajectories and the confidence
   intervention. Keep starting-confidence and confidence-by-complexity plots as
   support unless they answer a central paper question.

The similarity-category figure is a useful overview if the paper emphasizes
when solo driving is an adequate approximation. It uses a separate threshold
outcome, so define it separately from the main percentage of changed decisions.
There is no need to include every diagnostic figure in the main paper.

Additional focused network experiments, if needed later, are: separate
self-trust learning from interpersonal learning; compare equal passenger trust
with concentrated trust while retaining the same total trust in passengers;
and vary whether trust rewards agreement with the driver or agreement with the
group. These require matched interventions before making causal model claims.
