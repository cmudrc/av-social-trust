# av-social-trust
Simulating how passengers influence a driver's decision to use automation.
The model combines personal cognition, social opinion influence, and trust learning.
Current coefficients and decision thresholds are synthetic sanity-check settings;
the simulation is not yet calibrated to participant data.

## Setup

Requires Python 3.11 or newer, as declared in `pyproject.toml`. Use your preferred
Python installation and environment manager. With that environment active,
install from the repository root:

```sh
python -m pip install -e .
```

Dependencies are declared in `pyproject.toml`.

If you need an environment, Python's built-in `venv` is one option:

```sh
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell (use instead of the line above):
# .venv\Scripts\Activate.ps1
python -m pip install -e .
```

Source code lives in `src/av_social_trust`. After changing package configuration,
run `python -m pip install -e .` again to refresh the editable installation.

## Run a synthetic simulation

Run the walkthrough from the repository root:

```sh
python src/av_social_trust/model/examples/model_3.py
```

It prepares a car with one driver and one passenger, generates 20 situations,
runs the simulation, and prints the driver's preferences and automation use.
The car's starting cognition and social connections are defined in
[`car_3.py`](src/av_social_trust/car/examples/car_3.py).

For your own script:

```python
import av_social_trust as av
from av_social_trust.car.examples import car_3 as car
from av_social_trust.situation import SituationGenerator

generator = SituationGenerator(
    rng_seed=7,
    task_complexity_probability=0.4,
    automation_availability_probability=0.8,
    task_complexity_persistence=0.8,
    automation_availability_persistence=0.9,
)
situations = generator.generate_series(20)
model = av.Model(car)
state = model.run(situations)
print(state["opinion_vector"])
print(state["automation_on"])
```

The generator produces persistent binary time series. Probabilities set long-run
frequencies; persistence controls how strongly successive conditions resemble
each other. The seed makes a sequence reproducible. Generation happens outside
`Model`, so the simulation accepts the same inputs from other sources.

## Consensus on its own

Consensus functions are available from `av_social_trust.consensus`. The following
examples use the populated `car` imported above.

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

## Supply real-world data

Recorded driving conditions can already replace generated situations. Prepare an
ordered list of `Situation` objects and pass it to `model.run(situations)`, or
feed one object at a time to `model.step(situation)`.

| Input | Current representation |
| --- | --- |
| Driving conditions per cycle | `Situation(task_complexity=0 or 1, automation_available=True or False)` |
| Each person's starting cognition | `CognitiveState(automation_trust, perceived_risk, workload)`, each in `[0, 1]` |
| Cognitive response coefficients | Nine values in `CognitiveParameters`; accepted by the standalone cognitive updater |
| Decision thresholds | Trust, risk, and workload thresholds; accepted by `cognitive_to_opinion()` |
| Social relationships | Self-trust, directed interpersonal trust, learning rates, and homophilic/normative tradeoffs configured on `Car` |

For example, a loader could produce the following records. These values are
illustrative, not observations from a participant:

```python
import av_social_trust as av

# Replace these records with your data, ordered by time before conversion.
# This example schema uses integer complexity and actual Python booleans.
records = [
    {"task_complexity": 0, "automation_available": True},
    {"task_complexity": 1, "automation_available": True},
    {"task_complexity": 1, "automation_available": False},
]
situations = [av.Situation(**record) for record in records]

# Replace these starting values with the participant's initial measurements.
initial_cognition = av.CognitiveState(
    automation_trust=0.75, perceived_risk=0.6, workload=0.4,
)
car = av.Car()
car.add_driver(
    agent_id=0,
    self_trust=0.9,
    cognitive_state=initial_cognition,
    self_trust_learning_rate=0.1,
)
# Add passengers and directed connections for a social simulation; see car_3.py.
model = av.Model(car)
state = model.run(situations)
print(model.history[-1])
```

Your loader is responsible for mapping the dataset's labels and units to these
fields. Complexity currently supports only low (`0`) and high (`1`). Automation
availability means the system can be used, not that the driver used it. Parse
text flags explicitly: `bool("False")` evaluates to `True`. `Situation` does not
store timestamps, so retain them separately and align records to the update
interval; each list entry advances cognition once.

**Recorded inputs do not yet make this a fitted participant simulation.** The
full `Model` still uses the same synthetic cognitive coefficients and default
decision thresholds for everyone. It does not yet accept participant-specific
parameter sets, load a dataset, or replay measured cognitive trajectories.
Supplying initial measurements sets the starting point; later cognitive states
are predictions from the update equations.

For calibrated forward simulation, estimate cognitive coefficients and decision
thresholds from observations, or obtain existing fitted values. Coefficients
cannot simply be read off a single cognitive measurement. Confirm state scaling,
timestep, and boundary handling, then connect each participant's parameters to
the model loop. Social parameters require their own evidence or explicit
assumptions. Reserve observations for checking predicted cognition and automation
use against measurements.

The standalone `update_cognitive_state(..., parameters=...)` already supports
custom `CognitiveParameters`. See the
[cognitive update guide](src/av_social_trust/cognitive/update/README.md) for the
separation between parameter data and update equations. Synthetic and fitted
parameters can use the same equations; wiring per-person coefficients and
thresholds into `Model` is the remaining integration step.

## Tests

Run all tests from the repository root using your chosen Python environment:

```sh
python tests/tests.py
```
