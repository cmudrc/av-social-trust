# Situation sources and cognitive updates

`Situation` is the data for one cycle: task complexity and automation
availability. Construct it directly for a controlled scenario, or obtain it
from `SituationGenerator` for a reproducible random time series. The cognitive
update receives a `Situation` and does not need to know where it came from.

The cognitive update package separates three responsibilities:

- `parameters.py`: the `CognitiveParameters` data class and labeled synthetic
  defaults. Parameters describe a person's response, not a driving situation.
- `individual_model.py`: the affine equations that calculate the next
  `CognitiveState` from previous cognition, a situation, and parameters.
- `update.py`: the public `update_cognitive_state()` entry point used by `Model`.

```python
from av_social_trust.cognitive import CognitiveState, update_cognitive_state
from av_social_trust.cognitive.update import SYNTHETIC_PARAMETERS
from av_social_trust.situation import Situation, SituationGenerator

cognition = CognitiveState(0.75, 0.6, 0.4)
parameters = SYNTHETIC_PARAMETERS

# A manually chosen situation.
cognition = update_cognitive_state(cognition, Situation(1), parameters=parameters)

# A generated series, continuing from the previous cognitive state.
generator = SituationGenerator(rng_seed=7)
for situation in generator.generate_series(20):
    cognition = update_cognitive_state(cognition, situation, parameters=parameters)
```

Generate one situation per shared vehicle cycle and pass that same situation to
all occupants. Each person has their own cognitive state. Reuse their parameter
set across cycles; do not randomly regenerate cognition or coefficients at each
step. Automation availability affects the vehicle decision, not the cognitive
equations.

When Sibi's materials arrive, a separate loader can translate driving records
into `Situation` objects and fitted coefficients into `CognitiveParameters`.
If the equations are unchanged, the update implementation stays the same. If
his forward model differs, replace the implementation behind `advance_cognition`.
Confirm timestep, scaling, and boundary handling before using fitted values.
The full `Model` currently uses the shared synthetic defaults for every person;
per-participant parameter selection in the loop remains a future integration.

Run the complete standalone example from the project root:

```bash
python src/av_social_trust/cognitive/update/examples/update_1.py
```
