"""Directed influence measures: W[i,j] is how much i listens to j."""
import numpy as np


def network_measures(weights, discussion_rounds=1):
    w = np.asarray(weights, dtype=float)
    if w.ndim != 3 or w.shape[1] != w.shape[2] or w.shape[1] < 2:
        raise ValueError('Expected cycles × occupants × occupants for a social car')
    if not np.isfinite(w).all() or (w < 0).any() or not np.allclose(w.sum(axis=2), 1):
        raise ValueError('Influence weights must be finite, nonnegative and row-stochastic')
    if not isinstance(discussion_rounds, int) or discussion_rounds < 0:
        raise ValueError('Discussion rounds must be a nonnegative integer')
    n = w.shape[1]
    # The experiment normally uses one round. Effective weights also support
    # zero/multiple rounds without treating W[0,0] as the retained own weight.
    effective = np.linalg.matrix_power(w, discussion_rounds)
    # Left stationary distribution: pi = pi W. Rows are listeners, columns
    # are opinion sources, so a RIGHT eigenvector would give the wrong answer.
    # Strictly positive matrices have a unique stationary distribution.
    if (w <= 0).any():
        raise ValueError('Frozen-network influence currently requires strictly positive connected weights')
    system = w.transpose(0, 2, 1) - np.eye(n)
    system[:, -1, :] = 1
    rhs = np.zeros((len(w), n))
    rhs[:, -1] = 1
    stationary = np.linalg.solve(system, rhs[..., None])[..., 0]
    if (stationary < -1e-9).any() or not np.allclose(np.einsum('ti,tij->tj', stationary, w), stationary):
        raise ValueError('Could not determine stationary influence')
    return dict(self_weight=effective[:, 0, 0],
                passenger_attention=effective[:, 1:, 0].mean(axis=1),
                relative_influence=n * stationary[:, 0])


def residualize(values, groups):
    """Subtract means within comparison groups; works with multidimensional keys."""
    _, code = np.unique(np.asarray(groups), axis=0, return_inverse=True)
    values = np.asarray(values, dtype=float)
    count = np.bincount(code)
    means = np.bincount(code, weights=values) / count
    return values - means[code]


def opposing_weight(weights, private_choices, discussion_rounds=1):
    """Effective driver weight assigned to passengers with an opposite private vote."""
    effective = np.linalg.matrix_power(np.asarray(weights, dtype=float), discussion_rounds)
    choices = np.asarray(private_choices, dtype=bool)
    if choices.shape != effective.shape[:2]:
        raise ValueError('Private votes must match cycles and occupants')
    return np.sum(effective[:, 0, 1:] * (choices[:, 1:] != choices[:, :1]), axis=1)


def group_bins(x, edges):
    return np.clip(np.searchsorted(edges, x, side='right') - 1, 0, len(edges) - 2)
