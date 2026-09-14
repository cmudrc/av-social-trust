# Reusing Sibi's individual model inside the social simulation

Status: architecture recommendation; no supplied implementation or participant
parameter files have been inspected. This revises the replay-first recommendation
in [architecture.md](architecture.md).

## Recommendation

Use Sibi's individual cognitive dynamics and reliance decision rule as the
baseline. Add the social model around that baseline through a small adapter.
Create a new individual model only if a specific limitation requires it, and
compare it against the original baseline. An independently invented decision
rule would change both the personal and social mechanisms at once.

The supplied comparison note is `Sibi_2025_06_17_Opinion_Dynamics-3.pdf`
(its printed header is dated June 17, 2026). Sections 1.1-1.2 recap the IDETC
opinion model; their success/failure increments and -0.2 threshold are not the
identified parameters of the driving model. Section 1.3 introduces the separate
hybrid model, while Section 1.5 proposes changes to social influence weights.

The referenced [hybrid-model paper](https://arxiv.org/html/2512.05845v1),
Sections II-III, describes three continuous states: automation trust, perceived
risk, and workload. It uses task complexity as input, a one-second sampling
interval, and states scaled to [0, 1]. Its simplified affine cognitive dynamics
are independent of the automation mode. A threshold rule selects automation
when trust exceeds its threshold, risk is below its threshold, or workload
exceeds its threshold. It identifies participant-specific models for 16 people;
this is not automatically the 37-participant dataset previously discussed.

## Keep the cognitive update and decision separately callable

The following is a proposed interface, not a claim about Sibi's existing API:

```python
private = individual_model.advance_cognition(
    cognition=current_cognition,
    context=shared_context,
    parameters=participant_parameters,
)

reliance = individual_model.choose_reliance(
    cognition=socially_updated_cognition,
    parameters=participant_parameters,
)
```

`observer.py` can adapt `advance_cognition`; `decision.py` can adapt
`choose_reliance`. Both should delegate to the same versioned individual-model
implementation. If his code returns cognition and reliance together, it must
expose the cognitive result and allow the decision to be recomputed after social
influence. Applying social influence after a finalized decision would leave the
current decision unaffected by passengers.

Do not confuse this predictive state transition with a measurement observer
that estimates cognition using observed reliance. In a forward simulation,
future reliance is an output; it cannot also be supplied as observed input to
infer the state that causes it. A measurement observer belongs in the separate
calibration or replay pathway.

## A minimal coupled update

Let each agent have cognition `z_i = [tau_i, risk_i, workload_i]`. Keep the raw
social trust matrix `T` separate; its diagonal is social self-trust, not tau.
The proposed social intervention affects automation trust only at first.

1. Advance each person's cognition once with their own fitted parameters and
   the common driving context: `z_private_i = F_i(z_i, context)`.
2. Extract private automation trust and convert scales:
   `o_private_i = 2 * tau_private_i - 1`.
3. Derive `W` from the old raw social trust and apply the configured finite
   social update: `o_next = W @ o_private` for one discussion round.
4. Convert back: `tau_next_i = (o_next_i + 1) / 2`. Keep the privately updated
   risk and workload components unchanged by social discussion in this version.
5. Evaluate the driver's original reliance rule using this updated cognition.
   Apply environmental availability constraints outside the voluntary rule.
6. Update raw interpersonal and social self-trust using the private opinions
   and old raw trust, as in the existing `trust_step` convention.
7. Feed the resulting cognition into the next individual update. Do not reset
   it to a separate solo trajectory on every step.

This is a proposed social extension, not an equivalence or a validated passenger
model. Preserve the original model's input units, timestep, and handling of
out-of-range predictions. In particular, an affine model does not automatically
stay inside [0, 1]; verify its code's boundary convention before using the
current consensus validator, and do not silently add clipping during replication.

For a solo driver, social influence must be the identity. Then the combined
model reduces exactly to Sibi's individual model, apart from any explicitly
disabled environmental override outside the original test conditions. This is
the most useful first integration test.

## Three decisions to retain explicitly

**Temporal persistence and social self-weight are different parameters.** Under
row stochasticity, removing all interpersonal influence gives `W_ii = 1`.
Therefore the identification `A = W_ii` in the comparison note describes only a
restricted special case; it does not identify a general fitted temporal
coefficient with a social self-trust weight. Preserve Sibi's fitted `A` inside
the individual dynamics and use `W` only for the additional social mixing.

**Retain the agreed social model while evaluating integration.** The note's
proposal for constant diagonal influence is an alternative to the current
dynamic social self-trust. Its stochasticity argument uses shared learning
rates and tradeoffs; with connection-specific parameters, that proof does not
apply automatically. Keep raw `T` and normalized `W` as implemented. The note's
normative reference `o_r` is not fully defined there; the current group-mean
choice remains an explicit choice made in this project.

**Attention and passenger transfer are extensions.** First reproduce the solo
model without adding attention attenuation. Then investigate distracted
passengers under a separately documented assumption. Avoid multiplying a fitted
state or its full dynamics by attention without specifying what process is
being changed. In a shared car, only the driver chooses actual automation mode;
a passenger's hypothetical preference is not another vehicle mode. Reusing
solo-driver dynamics for a passenger, especially workload, requires validation.

## What to obtain from Sibi

- The current forward-simulation code, with cognitive update and decision rule
  accessible separately, or sufficient equations to port them faithfully.
- Participant-specific fitted coefficients, thresholds, initial conditions,
  parameter ordering, model version, and associated participant/session IDs.
- Input definitions and units, sample interval, state scaling, threshold boundary
  rules, and any clipping, resetting, or estimation steps in the implementation.
- One small input sequence and its expected state/reliance trajectory to verify
  the adapter. Confirm which dataset and driving conditions the parameters cover.

The published model is a sensible reference, but Sibi's current code may have
changed. Requesting these materials does not require raw private participant
streams for initial software integration if he can provide a suitable test case.

Until then, implement the interface with clearly synthetic coefficients using
the published structure. Those runs test architecture and numerical behavior;
they must not be described as predictions for real participants. Once the adapter
reproduces a solo trajectory, add the social layer and compare the same driver
alone and in a group with the individual model held fixed.
