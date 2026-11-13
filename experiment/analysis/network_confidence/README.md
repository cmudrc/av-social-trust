# Does greater driver confidence accompany greater weighted network influence?

This analysis joins the existing network and confidence samples by exact
driver, passenger composition, start and track. It checks their ordering and
step alignment before calculating anything. It uses saved arrays, with no
additional simulations or source-archive writes.

The centrality measure follows influence through the full directed weighted
network. Rows describe whose judgments an occupant weights. The driver's
centrality is their share in the left stationary distribution, multiplied by
the number of occupants so different car sizes share a benchmark of 1.
Above 1 means more than an equal share of influence if the current network were
held fixed. This is not the driver's raw self-trust or retained own weight,
and it does not assume the changing simulation actually reaches consensus.

Passengers can weight their own judgment, the driver's and other passengers'
judgments. “Listening” in the older figure referred to these model weights,
not a passenger action or an instruction to obey the driver.

Both confidence and network influence evolve from related trust rules, and
self-trust itself enters the influence matrix. Their association cannot be
interpreted as an independently identified causal effect.

Run `python3 experiment/analysis/network_confidence/run.py`; redraw with
`python3 experiment/analysis/network_confidence/plot.py`.

<!-- analysis-results:start -->
## Latest results

Updated: 2026-10-11 18:05:48 EDT

**780 base cars on 9 tracks (7,020 car–track cases).**

Weighted centrality uses the left stationary distribution of the current row-normalized trust network, multiplied by occupant count. 1 is an equal share of influence. The network is held fixed only for calculating this measure, not in the simulation.

Matched descriptive associations. Centrality includes self-trust through network weights and both evolve under the same trust rules, so their association is not an independent causal effect or a forecast of actual consensus.

![Centrality over time](results/figures/centrality_over_time.png)

Lines show the median and shading the central half of sampled car–track values, after averaging within ten-step blocks. The shaded range describes variation between cases; it is not a confidence interval.

![Centrality and confidence](results/figures/centrality_confidence.png)

Each faint point is one car–track drive average; large points show means in five confidence bins. The horizontal reference is an equal share of network influence.

| Method | Association of drive averages | Within driver / track / passenger count | Association of early-to-late changes |
| --- | ---: | ---: | ---: |
| Decision | 0.211 | 0.358 | 0.355 |
| Cognition | 0.258 | 0.295 | 0.412 |

Early = steps 1–20; late = steps 81–100. Rank associations are descriptive. Repeated tracks and steps are not treated as independent replicates for significance tests.

Full output: [summary.json](results/summary.json), [summary.md](results/summary.md).
<!-- analysis-results:end -->
