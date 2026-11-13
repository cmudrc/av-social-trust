# Does the driver's position in the network explain agreement between methods?

Compare the driver's binary automation decisions in solo, decision-level and
cognition-level runs. Use the same sampled driver, passengers and starting state
on every track. Distinguish **being listened to** from **keeping one's own view**:
in the saved row-normalized matrix, `W[i,j]` is how much person i listens to j.
The matrix saved as `influence_matrix` is the one used before social influence
in that cycle. The saved `trust` is updated afterward and would be misaligned.

Three measures:

- **Driver keeps own view:** the driver's effective self-weight for the configured
  discussion rounds. This directly controls exposure to passengers.
- **Passengers listen to driver:** their mean effective weight on the driver's
  opinion. Incoming influence is not the same as the driver's own weight.
- **Relative frozen-network influence:** the driver's share in the stationary
  left distribution of the current matrix, multiplied by occupant count. One
  means an equal share. It measures repeated discussion if weights were fixed;
  it does not assume the evolving model actually reaches that consensus. The
  calculation requires strictly positive weights, as in this experiment's
  fully connected networks. Unsupported networks fail explicitly.

Questions implemented, with raw values and comparisons within driver, track
and passenger count where appropriate:

1. Does a stronger **initial** driver position predict fewer changed cycles?
2. When the driver has more influence **during a drive**, do the modes resemble
   solo driving? Does the relationship remain within comparable drive stages
   and levels of current passenger disagreement?
3. Do decision and cognition methods agree when the driver is influential?
4. Does keeping more than half the weight protect the driver when passengers
   disagree? Decision-level binary voting provides exact protection; cognitive
   mixing need not, because a small change can cross a tree threshold.
5. Does the early network predict late differences? Do network position and
   behavior change together from the first to the last 20 cycles?
6. Is disagreement coming from influential passengers? Compare the total
   driver weight assigned to opposing passengers with changes to the current
   private choice and with changes to solo driving.

The frozen-network measure follows the consensus weights in
[DeGroot (1974), Reaching a Consensus](https://pages.ucsd.edu/~aronatas/project/academic/degroot%20consensus.pdf).
Here it is recalculated for each cycle's matrix, explicitly keeping its
fixed-network interpretation separate from the simulated evolving drive.

This is an association study. Trust learns from private opinions, and cognitive
influence changes later opinions. A changing network can therefore be both a
result and a predictor of changing behavior. Current private disagreement is
not an independent external control. No claim that centrality *causes* agreement
is supported by these correlations; a fixed-network intervention would be a
separate new simulation experiment.

Extraction uses a reproducible balanced sample: two passenger compositions per
driver and passenger count, three starts per composition, repeated on every
track (normally 780 base cars, 7,020 car–track pairs). The sample is explicitly
reported; it is not the full experiment. Equal weight is given to drivers and
passenger counts within each driver. Both correlation variants are descriptive,
with no independent-cycle p-values. Group-adjusted plots show deviations from
the usual rate within comparable groups, not standardized causal estimates.
Sparse bins (<100 sampled cycles or <10 distinct sampled cars) are omitted from
figures and retained in JSON. Points use the observed mean weight within a bin.
A half-sample check reports how overall changed-cycle means and initial/dynamic
correlations vary. This is a stability check, not a significance test.

```sh
python experiment/analysis/network_dynamics/run.py
python experiment/analysis/network_dynamics/plot.py  # redraw only
```

Requires the existing comparison cache and current analysis table. Reads raw
archives without changing them. Extraction checkpoints one file per archive in
`results/sample_archives/`, checks source signatures, extraction code and sampled
model keys on reuse, and validates sampled choices against the comparison cache. Re-running
reuses extraction but recomputes summaries. `cycles.npz` saves selected per-cycle
measures and outcomes; `summary.json` and PNG/PDF figures contain all results.
The primary paper candidate is weighted disagreement, supported by the own-weight
/ disagreement plot. Use the initial-network plot to distinguish starting
conditions from evolving associations; the track-specific early-to-late arrows
are an exploratory supplement.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-11 14:51:39 EDT

**780 sampled cars × 9 tracks = 7,020 car–track comparisons.**

Fixed random passenger compositions and starts within every driver and passenger count; identical cars on every track.

Descriptive associations in a balanced sample. Trust evolves from opinions, so changing centrality and changing behavior can share a cause. No causal claim or independent-cycle significance test.

The three network measures are evaluated on the weights used **before** each cycle’s social influence. Passengers listening to the driver is different from the driver listening to passengers. Relative frozen-network influence equals 1 for an equal-share driver; above 1 means greater influence. It describes repeated discussion with the current weights held fixed, not the actual long-run drive.

### Does a strong starting position predict less change?

![Starting network](results/figures/starting_network.png)

| Mode | Starting measure | Rank association | Within driver / track / passenger count |
| --- | ---: | ---: | ---: |
| decision | How much the driver keeps their own view | -0.140 | -0.146 |
| decision | How much passengers listen to the driver | -0.050 | -0.046 |
| decision | Driver’s relative influence if the network were held fixed | -0.086 | -0.081 |
| cognition | How much the driver keeps their own view | -0.066 | -0.022 |
| cognition | How much passengers listen to the driver | -0.063 | -0.052 |
| cognition | Driver’s relative influence if the network were held fixed | -0.046 | -0.061 |

Negative association means larger starting values accompany fewer changed cycles; positive means more.

### Does greater influence during the drive accompany agreement?

![Network and behavior](results/figures/network_associations.png)

The top row gives raw changed-cycle rates. The bottom row subtracts the usual rate within driver × track × passenger-count × drive-stage × current-disagreement groups. Zero means no difference from that group’s usual rate. These differences are associations, not causal effects. Bins with fewer than 100 sampled cycles or 10 distinct sampled cars are omitted from the figure. Points use observed mean weights within bins.

### When do the two social methods agree with each other?

All three methods agree on **70.7%** of sampled car–cycles (balanced weighting).

![Agreement between social methods](results/figures/methods_agreement.png)

Each line uses the indicated method’s own evolving network. The networks begin identically but can differ later. The outcome here is disagreement between decision-level and cognition-level choices, rather than disagreement with solo driving.

### Does the driver’s own weight matter when passengers disagree?

![Own weight and disagreement](results/figures/own_weight_disagreement.png)

Decision mode: **0 changed cycles** among 39,769 cycles where the driver retains more than half the weight. Binary weighted voting makes the driver impossible to overrule above this point. Cognition mixing has no equivalent protection: a small cognitive change can cross a decision-tree threshold. In cognition mode, agreement among current private votes does not imply agreement with solo driving, because prior influence has already changed cognition.

### Do network influence and behavior move together over time?

![Network over time](results/figures/network_over_time.png)

![Early and late changes](results/figures/early_late.png)

### Is disagreement coming from influential passengers?

![Weighted disagreement](results/figures/weighted_disagreement.png)

The horizontal axis counts how much of the driver’s influence weight belongs to passengers whose current private vote opposes the driver. In decision mode, more than half this weight flips the vote; in cognition mode, mixing states is a different mechanism. The two panels distinguish changing the driver’s current private choice from changing the solo trajectory.

Full outputs include early-network / late-behavior associations, early-to-late changes, cross-method disagreement, and a half-sample stability check. Use these as additional descriptive questions; social trust learns from opinions, so a time trend alone cannot identify what causes what.

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
