"""
Synchronous DeGroot opinion updates using a row-stochastic matrix.
"""

from numbers import Integral, Real

import numpy as np


def _as_nonnegative_square_matrix(matrix) -> np.ndarray:
    matrix = np.array(matrix, dtype=float, copy=True)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Matrix must be nonempty and square.")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("Matrix entries must be finite.")
    if np.any(matrix < 0):
        raise ValueError("Matrix entries must be nonnegative.")
    return matrix


def validate_row_stochastic(matrix) -> np.ndarray:
    """
    Return a validated float copy, or raise ValueError.

    Rows must sum to one within an absolute tolerance of 1e-10.
    This checks influence weights; it does not normalize raw trust.
    """
    matrix = _as_nonnegative_square_matrix(matrix)
    if not np.allclose(matrix.sum(axis=1), 1.0, rtol=0.0, atol=1e-10):
        raise ValueError("Each influence-matrix row must sum to one.")
    return matrix


def normalize_trust_matrix(trust_matrix) -> np.ndarray:
    """
    Derive influence weights without changing raw trust.

    Row i describes how agent i weights every agent's opinion. A zero
    row becomes an identity row, retaining that agent's current opinion.
    This fallback does not change the agent's stored self-trust.
    """
    matrix = _as_nonnegative_square_matrix(trust_matrix)
    # Scaling first avoids overflow when summing large finite weights.
    row_maxima = matrix.max(axis=1)
    active = row_maxima > 0
    matrix[active] /= row_maxima[active, None]
    matrix[active] /= matrix[active].sum(axis=1, keepdims=True)
    inactive_indices = np.flatnonzero(~active)
    matrix[inactive_indices, inactive_indices] = 1.0
    return matrix


def _prepare_degroot(opinion_vector, influence_matrix):
    matrix = validate_row_stochastic(influence_matrix)
    opinions = np.array(opinion_vector, dtype=float, copy=True)
    if opinions.shape != (matrix.shape[0],):
        raise ValueError("Opinion vector must have one entry per matrix row.")
    if not np.all(np.isfinite(opinions)):
        raise ValueError("Opinions must be finite.")
    if np.any((opinions < -1.0) | (opinions > 1.0)):
        raise ValueError("Opinions must lie between -1 and 1.")

    # Remove accepted row-sum roundoff so repeated steps remain convex averages.
    matrix /= matrix.sum(axis=1, keepdims=True)
    return opinions, matrix


def degroot_step(opinion_vector, influence_matrix) -> np.ndarray:
    """
    Return x(t+1) = W(t) @ x(t), leaving both inputs unchanged.

    Agent ordering must match between the vector and both matrix axes.
    W is validated on each call so changing trust can be used safely.
    Opinions must be finite and lie in the car model's [-1, 1] range.
    Trust learning is separate from this update.
    A stochastic matrix alone does not guarantee eventual consensus.
    """
    opinions, matrix = _prepare_degroot(opinion_vector, influence_matrix)
    return np.clip(matrix @ opinions, opinions.min(), opinions.max())


def run_degroot(
    opinion_vector,
    influence_matrix,
    *,
    steps: int | None = None,
    tol: float = 1e-6,
    max_steps: int = 10_000,
) -> dict:
    """
    Run repeated updates with a fixed influence matrix.

    With steps set, perform exactly that many updates (zero is allowed).
    Otherwise stop when max(abs(x_next - x)) <= tol, or after max_steps.
    The matrix is copied and validated once; inputs are never modified.

    Returns opinion_vector, the number of steps performed, max_change in
    the final step, converged, and consensus_reached. Converged means the
    final step changed no opinion by more than tol; it is a numerical
    stopping criterion, not a bound on distance to the limiting opinion.
    Consensus_reached means max(x) - min(x) <= tol. Stable disagreement
    is possible. A zero-step run has max_change=None and converged=False.

    In fixed-step mode tol only affects the reported flags; max_steps is
    unused. To update trust between steps, use degroot_step instead.
    """
    if steps is not None and (
        isinstance(steps, bool) or not isinstance(steps, Integral) or steps < 0
    ):
        raise ValueError("steps must be a nonnegative integer or None.")
    if steps is None and (
        isinstance(max_steps, bool)
        or not isinstance(max_steps, Integral)
        or max_steps <= 0
    ):
        raise ValueError("max_steps must be a positive integer.")
    if (
        isinstance(tol, bool)
        or not isinstance(tol, Real)
        or not np.isfinite(tol)
        or tol <= 0
    ):
        raise ValueError("tol must be a finite positive number.")

    opinions, matrix = _prepare_degroot(opinion_vector, influence_matrix)
    limit = max_steps if steps is None else steps
    completed_steps = 0
    max_change = None
    converged = False

    for _ in range(limit):
        updated = np.clip(matrix @ opinions, opinions.min(), opinions.max())
        max_change = float(np.max(np.abs(updated - opinions)))
        opinions = updated
        completed_steps += 1
        converged = max_change <= tol
        if steps is None and converged:
            break

    return {
        "opinion_vector": opinions,
        "steps": completed_steps,
        "max_change": max_change,
        "converged": converged,
        "consensus_reached": bool(np.ptp(opinions) <= tol),
    }


if __name__ == "__main__":
    # Three agents: row i contains agent i's influence weights.
    opinions = np.array([-0.8, 0.2, 0.9])
    weights = np.array([
        [0.5, 0.3, 0.2],
        [0.2, 0.5, 0.3],
        [0.3, 0.2, 0.5],
    ])  # Each row sums to one.

    print("Initial opinions:", opinions)
    print("Influence matrix:\n", weights)

    fixed = run_degroot(opinions, weights, steps=5)
    print("After 5 steps:", fixed["opinion_vector"])

    # Start again from the initial opinions and stop when changes are small.
    result = run_degroot(opinions, weights, tol=1e-6, max_steps=1_000)
    print(f"After {result['steps']} steps:", result["opinion_vector"])
    print("Converged:", result["converged"])
    print("Consensus reached:", result["consensus_reached"])
