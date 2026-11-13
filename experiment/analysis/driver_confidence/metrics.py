"""Raw driver self-trust, its exact update, and immediate confidence interventions."""
import numpy as np
from experiment.analysis.shared.table import tree_predict


def normalize_batch(trust):
    values = np.array(trust, dtype=float, copy=True)
    maxima = values.max(axis=-1)
    active = maxima > 0
    values[active] /= maxima[active, None]
    values[active] /= values[active].sum(axis=-1, keepdims=True)
    for t, row in np.argwhere(~active):
        values[t, row, row] = 1
    return values


def confidence_measures(initial_trust, after_trust, connection_mask, alpha, private_opinions,
                        self_learning_rate, interpersonal_learning_rate):
    """Reconstruct the trust used BEFORE each cycle from its saved AFTER values.

    Current opinions update passengers' trust now. That updated trust affects
    confidence in the next cycle's trust update, not this cycle's update.
    """
    after = np.asarray(after_trust, dtype=float)
    before = np.concatenate([np.asarray(initial_trust, dtype=float)[None], after[:-1]])
    confidence = before[:, 0, 0]
    confidence_after = after[:, 0, 0]
    incoming = np.array(connection_mask[:, 0], dtype=bool, copy=True)
    incoming[0] = False
    if incoming.any():
        appraisal = before[:, incoming, 0].mean(axis=1)
        appraisal_after = after[:, incoming, 0].mean(axis=1)
        private = np.asarray(private_opinions, dtype=float)
        agreement = 1 - np.abs(private[:, incoming] - private[:, :1]) / 2
        driver_group_alignment = 1 - np.abs(private[:, 0] - private.mean(axis=1)) / 2
        targets = (alpha[incoming, 0][None] * agreement
                   + (1-alpha[incoming, 0])[None] * driver_group_alignment[:, None])
        target = targets.mean(axis=1)
        incoming_error = appraisal_after - ((1-interpersonal_learning_rate)*appraisal+interpersonal_learning_rate*target)
        agreement = agreement.mean(axis=1)
    else:
        # With no incoming links confidence stays unchanged; there is no
        # measured passenger appraisal to correlate or display.
        appraisal = np.full(len(after), np.nan)
        appraisal_after = appraisal.copy()
        target = appraisal.copy()
        agreement = appraisal.copy()
        driver_group_alignment = appraisal.copy()
        incoming_error = np.zeros(len(after))
    effective_target = np.where(np.isfinite(appraisal), appraisal, confidence)
    expected_gain = self_learning_rate*(effective_target-confidence)
    outgoing = before[:, 0, 1:].sum(axis=1)
    return before, dict(confidence_before=confidence, confidence_after=confidence_after,
        incoming_before=appraisal, incoming_after=appraisal_after, outgoing_sum=outgoing,
        own_weight=normalize_batch(before)[:, 0, 0],
        passenger_agreement=agreement, group_alignment=driver_group_alignment,
        incoming_target=target, confidence_gain=confidence_after-confidence,
        confidence_update_error=confidence_after-confidence-expected_gain,
        incoming_update_error=incoming_error)


def replay(trust, private_cognition, private_opinions, tree, mode, rounds, available):
    """Replay one cycle's discussion, using fixed private inputs and raw trust."""
    weights = normalize_batch(trust)
    # consensus.run_degroot re-normalizes the accepted stochastic matrix.
    weights /= weights.sum(axis=2, keepdims=True)
    if mode == 'decision':
        opinion = np.array(private_opinions, dtype=float, copy=True)
        lower, upper = opinion.min(axis=1)[:, None], opinion.max(axis=1)[:, None]
        for _ in range(rounds):
            opinion = np.clip(np.matmul(weights, opinion[..., None])[..., 0], lower, upper)
        return (opinion[:, 0] > 0) & available, weights[:, 0, 0]
    if mode == 'cognition':
        cognition = np.array(private_cognition, dtype=float, copy=True)
        lower, upper = cognition.min(axis=1)[:, None], cognition.max(axis=1)[:, None]
        for _ in range(rounds):
            cognition = np.clip(np.matmul(weights, cognition), lower, upper)
        return tree_predict(tree, cognition[:, 0]) & available, weights[:, 0, 0]
    raise ValueError('Expected decision or cognition influence')


def intervene(trust, private_cognition, private_opinions, tree, mode, rounds, available, levels):
    """Change ONLY driver self-trust, leave all other snapshot inputs fixed.

    These are separate immediate replays, not evolving counterfactual drives.
    No archived state is modified and no replay output is carried forward.
    """
    choices, own_weights = [], []
    for confidence in levels:
        if not 0 <= confidence <= 1:
            raise ValueError('Confidence intervention must lie in [0,1]')
        changed = np.array(trust, dtype=float, copy=True)
        changed[:, 0, 0] = confidence
        choice, weight = replay(changed, private_cognition, private_opinions, tree, mode, rounds, available)
        choices.append(choice)
        own_weights.append(weight)
    return np.asarray(choices), np.asarray(own_weights)
