# av-social-trust
Simulating how passengers shape a driver's trust in automation. Couples individual trust dynamics with social influence to predict mode switching.

## Setup

With Python 3.13.8 installed through pyenv and the pyenv-virtualenv plugin available,
create the environment once, then install the project from the repository root:

```sh
pyenv virtualenv 3.13.8 av-social-trust
pyenv local av-social-trust
python -m pip install -e .
```

The `.python-version` file selects `av-social-trust` when working in this repository.
Dependencies are declared in `pyproject.toml`.

Import the public package with:

```python
import av_social_trust as av

car = av.Car()
```

Consensus functions are available from `av_social_trust.consensus`.
Source code lives in `src/av_social_trust`. After changing package configuration,
run `python -m pip install -e .` again to refresh the editable installation.

Run DeGroot updates with a fixed influence matrix:

```python
from av_social_trust.consensus import normalize_trust_matrix, run_degroot

state = car.to_state()  # After adding a driver and any passengers/connections.
weights = normalize_trust_matrix(state["trust_matrix"])
opinions = state["opinion_vector"]

fixed = run_degroot(opinions, weights, steps=50)
result = run_degroot(opinions, weights, tol=1e-6, max_steps=10_000)
print(result["opinion_vector"], result["steps"], result["converged"])
```

The tolerance bounds the largest opinion change in one step. The returned
`consensus_reached` flag separately checks whether the opinion spread is within
that tolerance. If the step limit is reached, inspect `converged` before assuming
the process has stabilized. Use `degroot_step` when trust changes between updates.

## Trust updates

`av_social_trust.trust` updates raw trust separately from opinion consensus:

```python
from av_social_trust.trust import trust_step

state = car.to_state()
state["trust_matrix"] = trust_step(
    opinion_vector=state["opinion_vector"],
    trust_matrix=state["trust_matrix"],
    learning_rate_matrix=state["learning_rate_matrix"],
    homophilic_normative_tradeoff_matrix=state["homophilic_normative_tradeoff_matrix"],
    connection_mask_matrix=state["connection_mask_matrix"],
)
```

For opinions in `[-1, 1]`, homophily is `1 - abs(x_i - x_j) / 2`.
The normative score is `1 - abs(x_j - mean(x)) / 2`, using the arithmetic
mean of all supplied agents' opinions, including the evaluator and target.
The tradeoff weights homophily: `1` selects homophily and `0` selects normative
agreement. Each relationship moves toward the blended score at its learning rate.
These scores are modeling choices; neither requires a ground-truth outcome.

Self-trust moves toward average incoming interpersonal trust using the diagonal
learning rate. It has no homophilic tradeoff. Absent connections and self-appraisals
are excluded from the average; existing connections with zero trust are included.
Self-trust stays unchanged when there are no incoming connections.

Both updates use the same pre-update raw trust, preserve their inputs, and return
a new matrix without normalization. The caller supplies the opinions to evaluate;
using opinions after full consensus makes both interpersonal scores equal to one.
The returned state is separate from `Car`; changing it does not update the graph.
The two updates can also be called separately with `update_interpersonal_trust`
and `update_self_trust`.

Run a three-agent trust-update example with:

```sh
python -m av_social_trust.trust
```

## Simulation cycle

After populating a `Car`, create an independent simulation:

```python
model = av.Model(car)
state = model.step(av.Situation(task_complexity=0))  # One complete cycle.
situations = [av.Situation(0), av.Situation(1), av.Situation(1)]
state = model.run(situations)  # Three additional cycles, in list order.
print(state["opinion_vector"])
print(model.history[-1])
```

Each cycle uses the old raw trust for social influence and the private opinions
for trust learning. The new raw trust affects the next cycle. `model.history`
records the private opinions, influence matrix, and resulting state for each
completed cycle. The original `Car` remains unchanged.

`step()` requires one `Situation`; `run()` requires a list of them. The list
can come from `SituationGenerator.generate_series(...)` or a recorded-data
loader. Its length sets the number of additional cycles; an empty list runs none.

Each person's cognition evolves using synthetic affine coefficients and the shared
task complexity. Private usage preferences are calculated from cognition before
discussion. Automation is enabled only when available and the driver's social
preference is positive. Pass driving conditions to `model.step(situation=...)`.
All occupants receive the same driving conditions; distraction is not modeled.
Cycles have no assigned physical duration until fitted parameters are integrated.

Run the tests:

```sh
python -m unittest discover -s tests -v
```
