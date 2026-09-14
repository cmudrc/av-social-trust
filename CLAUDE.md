# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

`av-social-trust` simulates how passengers shape a driver's trust in vehicle
automation. It couples per-agent trust dynamics with DeGroot social influence over
a directed graph of vehicle occupants, with the eventual goal of predicting the
driver's reliance on automation (mode switching).

This is a research model under active construction, not a product. Several
modules are deliberate stubs pending an external collaborator's data and code
(see "Current state" below). Prefer making the modeling assumptions explicit over
making the simulation feature-complete.

## Environment and commands

Python 3.13.8 via pyenv + pyenv-virtualenv. `.python-version` selects the
`av-social-trust` virtualenv automatically in this directory.

```sh
python -m pip install -e .          # re-run after changing package config
python -m unittest discover -s tests -v   # run the suite (30 tests, all passing)
python -m unittest tests.test_trust       # run one module
python -m av_social_trust.trust           # each core module has a __main__ demo
python -m av_social_trust.car.examples.car_2
```

Running a module with `python -m` prints a harmless `RuntimeWarning` about the
module already being in `sys.modules` — the package `__init__` imports these
modules eagerly. Run the file by path (`python src/av_social_trust/trust.py`) to
avoid it. Nothing is wrong.

Tests use the stdlib `unittest`, **not** pytest — there is no pytest dependency,
and test files use `unittest.TestCase` with `np.testing.assert_allclose`. Follow
that convention when adding tests. Dependencies are `networkx` and `numpy` only;
do not add a dataframe or plotting library without a concrete need.

## Layout

```
src/av_social_trust/
    __init__.py       # public surface: Car, Model
    car/car.py        # Car: builds the occupant graph, exports state snapshots
    car/examples/     # car_1 (solo driver), car_2 (one-way link), car_3 (mutual)
    consensus.py      # DeGroot opinion updates, trust -> influence normalization
    trust.py          # interpersonal and self-trust learning
    model/model.py    # Model: the simulation loop over one Car's state
    model/examples/   # model_1
    observe.py        # EMPTY STUB - the planned driving-evidence bridge
tests/                # test_consensus.py, test_model.py, test_trust.py
docs/architecture.md          # proposed full architecture, data contracts, validation plan
docs/sibi-integration.md      # how to wrap the collaborator's individual cognitive model
```

Only `Car` and `Model` are re-exported from the package root. Consensus and trust
functions are imported from their modules directly
(`from av_social_trust.consensus import ...`).

## Core data model

`Car` holds a `networkx.DiGraph`. Nodes are agents (one `driver`, any number of
`passenger`s); edges are directed social connections. `Car.to_state()` exports an
independent plain-Python snapshot; `Model` owns that snapshot and never mutates
the `Car`.

State dict keys: `driver`, `agents`, `opinion_vector`, `attention_vector`,
`connection_mask_matrix`, `trust_matrix`, `learning_rate_matrix`,
`homophilic_normative_tradeoff_matrix`.

These invariants are load-bearing across every module — violating one silently
breaks the model rather than raising:

- **Agent order is driver-first.** `agents == [driver, *passengers]`, and every
  vector and matrix axis follows that order. Agent IDs are arbitrary ints and are
  not array indices.
- **`trust_matrix[i][j]` is agent i's trust in agent j.** Row = the truster.
- **The diagonal is self-trust**, meaning trust in one's own judgment in the
  discussion. It is not trust in automation and not manual-driving confidence.
- **Raw trust is never row-normalized in storage.** `normalize_trust_matrix()`
  derives influence weights `W` for DeGroot on demand; raw `T` is what gets
  learned and persisted. Keep the two distinct in names and in flow.
- **Opinions are in `[-1, 1]`** (opinion = trust in automation). Trust, learning
  rates, attention, and the tradeoff are in `[0, 1]`. Conversion to a collaborator's
  `[0, 1]` trust scale is `opinion = 2 * tau - 1`.
- **A zero-trust connection and an absent connection differ.** The
  `connection_mask_matrix` marks which relationships exist; an existing connection
  with trust 0.0 still participates in self-trust appraisal averages, an absent one
  does not. An all-zero trust row normalizes to an identity row, keeping that
  agent's opinion.
- **The tradeoff diagonal is unused** and stays 0.0; self-trust has no homophilic
  component.
- **`attention_vector` is exported but not yet consumed** by consensus or trust.
  That is deliberate — see `docs/sibi-integration.md` on not applying attention twice.

## Simulation loop

`Model.step()` runs one cycle as a sequence of named phases
(`src/av_social_trust/model/model.py`). Refer to them by name, not by position —
only part of the ordering is forced, and numbering hides which part:

- **Observation** — private opinion update from driving experience. **Currently a
  no-op** (TODO: the collaborator's cognitive model).
- **Discussion** — `W = normalize_trust_matrix(T_old)`, then **one**
  `degroot_step`. Deliberately one step, not `run_degroot` to convergence: the
  finite discussion budget gives driving evidence, social influence, and trust
  learning explicit relative time scales.
- **Trust learning** — `trust_step(private_opinions, T_old, ...)`, reading the
  **private, pre-consensus** opinions and the **old** trust. Learning from
  post-consensus opinions would drive every homophily score to 1.0 by construction.
- **Decision** — whether the driver uses automation. **Currently a no-op** (TODO).
- **Commit** — adopt the new opinions and trust together, then append a **History**
  snapshot.

What the ordering does and does not require:

- **Observation before Discussion** is convention, not logic: evidence accumulates,
  then occupants discuss it.
- **Discussion before Decision is forced.** Per `docs/sibi-integration.md`,
  "applying social influence after a finalized decision would leave the current
  decision unaffected by passengers" — the effect the project exists to measure.
- **Trust learning floats.** It sits before Decision here and in
  `docs/architecture.md` §7, and after it in `docs/sibi-integration.md`. The two do
  not interact within a cycle, so its position is free; its *inputs* are not.

Discussion and Trust learning both read the same pre-update `T_old`; new trust
affects the next cycle only. Because all mutation happens in Commit, a validation
failure mid-cycle leaves `state`, `cycle`, and `history` untouched —
`test_model.py` asserts this, so preserve the commit-last structure.

`cycle` is a counter, not a physical timestep. Learning rates mean "per trust
update," not "per second."

## Conventions to follow

- **Never mutate inputs.** Every public function copies (`np.array(..., copy=True)`,
  `deepcopy` at state boundaries) and returns new objects. Tests explicitly check
  that inputs and history snapshots do not alias.
- **State dicts hold plain Python lists; math functions return numpy arrays.**
  `Model.step` calls `.tolist()` before committing. Keep the boundary crisp so
  state stays comparable with `==` and JSON-friendly.
- **Validate eagerly and raise `ValueError`** with a message naming the parameter
  and its allowed range. Use `validate_range` in `car/car.py` and the
  `_unit_matrix` / `_as_nonnegative_square_matrix` helpers in the math modules.
- **Reject `bool` explicitly** before `Integral`/`Real` checks
  (`isinstance(steps, bool) or not isinstance(steps, Integral)`), since `True` is
  an `int` in Python.
- **Docstrings state invariants and modeling choices, not just behavior.** The
  existing ones say what is a deliberate convention, what is unmeasured, and what
  callers must do (for example "normalize the returned matrix separately"). Match
  that register — this is a research codebase where an undocumented assumption is
  a correctness bug.
- Do not describe a modeling choice as a measured or validated effect. Homophily
  and the group-mean normative score are choices; neither requires a ground truth.
- Core modules end with an `if __name__ == "__main__":` demo using small inline
  matrices. Reusable scenarios go in an `examples/` subpackage as module-level
  objects.

## Current state

Implemented and tested: `Car`, `consensus.py`, `trust.py`, and the `Model` loop
skeleton.

Stubs and gaps, all intentional:

- `src/av_social_trust/observe.py` is empty. `docs/architecture.md` asks that the
  implementation be named `observer.py` when written.
- `Car.from_state()` is `pass`.
- `Model.step()` steps 1 and 4 are TODOs awaiting the collaborator's cognitive
  model and reliance decision rule.
- `docs/architecture.md` proposes `data.py`, `decision.py`, and `adapters/`
  (`synthetic.py`, `sibi.py`) that do not exist yet.

**Read `docs/architecture.md` and `docs/sibi-integration.md` before extending the
model.** They record decisions that are easy to unknowingly reverse — keeping raw
`T` separate from normalized `W`, not identifying the fitted temporal coefficient
`A` with the social self-weight `W_ii`, not initializing the self-trust diagonal
from manual-driving confidence, and not treating the 37-participant study and the
16-participant hybrid-model paper as one dataset. No participant data is in this
repository, and none should be committed to it.

## Notes

- Commit messages in this repo are short, lowercase, and descriptive
  ("car class is complete").
