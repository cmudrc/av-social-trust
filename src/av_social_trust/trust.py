"""
Updates to raw interpersonal trust and self-trust.

T[i, j] is agent i's trust in agent j. The diagonal stores self-trust.
Attention to driving events belongs to the separate experience model.
Interpersonal trust combines opinion similarity with the target agent's
agreement with the arithmetic mean group opinion. These scores are modeling
choices, not comparisons against an observed ground truth.
"""

import numpy as np


def _unit_matrix(values, name, shape=None):
    matrix = np.array(values, dtype=float, copy=True)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"{name} must be a nonempty square matrix.")
    if shape is not None and matrix.shape != shape:
        raise ValueError(f"{name} must have shape {shape}.")
    if not np.all(np.isfinite(matrix)) or np.any((matrix < 0) | (matrix > 1)):
        raise ValueError(f"{name} entries must be finite and between 0 and 1.")
    return matrix


def _trust_inputs(trust_matrix, learning_rate_matrix, connection_mask_matrix):
    trust = _unit_matrix(trust_matrix, "trust_matrix")
    rates = _unit_matrix(learning_rate_matrix, "learning_rate_matrix", trust.shape)
    if connection_mask_matrix is None:
        connections = np.ones(trust.shape, dtype=bool)
    else:
        connections = np.array(connection_mask_matrix, copy=True)
        if connections.shape != trust.shape or connections.dtype.kind != "b":
            raise ValueError("connection_mask_matrix must be boolean and match trust_matrix.")
    np.fill_diagonal(connections, False)
    return trust, rates, connections


def update_self_trust(
    trust_matrix,
    learning_rate_matrix,
    connection_mask_matrix=None,
) -> np.ndarray:
    """Return raw trust with only its self-trust diagonal updated.

    Self-trust moves toward the mean incoming interpersonal trust:
    s_i_next = (1 - eta_ii) * s_i + eta_ii * mean_j(T[j, i]).
    The mean includes existing zero-trust connections, excludes the agent
    itself and absent connections, and uses the supplied pre-update trust.
    Without incoming connections, self-trust stays unchanged. No tradeoff
    parameter is needed. With no mask, all interpersonal connections exist.
    All inputs are left unchanged; the returned matrix is not normalized.
    """
    trust, rates, connections = _trust_inputs(
        trust_matrix, learning_rate_matrix, connection_mask_matrix
    )
    self_trust = np.diag(trust).copy()
    counts = connections.sum(axis=0)
    appraisals = np.divide(
        np.where(connections, trust, 0.0).sum(axis=0),
        counts,
        out=self_trust.copy(),
        where=counts > 0,
    )
    self_rates = np.diag(rates)
    updated = trust.copy()
    np.fill_diagonal(updated, (1 - self_rates) * self_trust + self_rates * appraisals)
    return updated


def update_interpersonal_trust(
    opinion_vector,
    trust_matrix,
    learning_rate_matrix,
    homophilic_normative_tradeoff_matrix,
    connection_mask_matrix=None,
) -> np.ndarray:
    """Return raw trust with only existing interpersonal connections updated.

    Opinions x are in [-1, 1]. For the arithmetic mean m of all supplied
    opinions (including i and j), define scores in [0, 1]:
      H[i, j] = 1 - abs(x[i] - x[j]) / 2
      N[j] = 1 - abs(x[j] - m) / 2
      target[i, j] = alpha[i, j] * H[i, j] + (1 - alpha[i, j]) * N[j]
      T_next[i, j] = (1 - eta[i, j]) * T[i, j] + eta[i, j] * target[i, j]

    Alpha is the homophilic_normative_tradeoff: 1 is purely homophilic,
    0 purely normative. Each directed connection has its own alpha and eta.
    The mask restricts which relationships update; it does not change the
    group mean. With no mask, all off-diagonal connections exist. Existing
    zero-trust relationships can gain trust. Diagonal rates and tradeoffs
    are unused here; self-trust is left unchanged. Inputs are not modified.
    """
    trust, rates, connections = _trust_inputs(
        trust_matrix, learning_rate_matrix, connection_mask_matrix
    )
    tradeoffs = _unit_matrix(
        homophilic_normative_tradeoff_matrix,
        "homophilic_normative_tradeoff_matrix",
        trust.shape,
    )
    opinions = np.asarray(opinion_vector, dtype=float)
    if opinions.shape != (trust.shape[0],):
        raise ValueError("opinion_vector must have one entry per trust-matrix row.")
    if not np.all(np.isfinite(opinions)) or np.any((opinions < -1) | (opinions > 1)):
        raise ValueError("Opinions must be finite and between -1 and 1.")

    homophilic = 1 - np.abs(opinions[:, None] - opinions[None, :]) / 2
    normative = 1 - np.abs(opinions - opinions.mean()) / 2
    targets = tradeoffs * homophilic + (1 - tradeoffs) * normative[None, :]
    updated = trust.copy()
    updated[connections] = (
        (1 - rates[connections]) * trust[connections]
        + rates[connections] * targets[connections]
    )
    return updated


def trust_step(
    opinion_vector,
    trust_matrix,
    learning_rate_matrix,
    homophilic_normative_tradeoff_matrix,
    connection_mask_matrix=None,
) -> np.ndarray:
    """Update interpersonal and self-trust synchronously, returning raw trust.

    Both updates use the original trust matrix: self-trust does not use
    the interpersonal trust calculated during this step. Self-trust has
    no homophilic component; the tradeoff diagonal is unused. The caller
    chooses whether the supplied opinions precede or follow consensus.
    Normalize the returned matrix separately when computing influence.
    """
    updated = update_interpersonal_trust(
        opinion_vector,
        trust_matrix,
        learning_rate_matrix,
        homophilic_normative_tradeoff_matrix,
        connection_mask_matrix,
    )
    self_updated = update_self_trust(
        trust_matrix, learning_rate_matrix, connection_mask_matrix
    )
    np.fill_diagonal(updated, np.diag(self_updated))
    return updated


if __name__ == "__main__":
    opinions = [-0.8, 0.2, 0.9]
    trust = np.array([
        [0.8, 0.2, 0.1],
        [0.6, 0.5, 0.3],
        [0.4, 0.7, 0.6],
    ])
    rates = np.full((3, 3), 0.2)
    tradeoffs = np.full((3, 3), 0.5)
    np.fill_diagonal(tradeoffs, 0.0)  # Unused by the self-trust rule.

    print("Raw trust before:\n", trust)
    print("Raw trust after:\n", trust_step(opinions, trust, rates, tradeoffs))
