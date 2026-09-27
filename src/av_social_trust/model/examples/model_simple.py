"""Walk through a simulation with one driver and one passenger.

Run from the project root using the project's Python environment:
    python src/av_social_trust/model/examples/model_3.py

Driving situations, cognitive coefficients, and decision thresholds are synthetic.
This example demonstrates the simulation flow, not fitted participant behavior.
Cycles are simulation steps, not calibrated seconds.
"""

import av_social_trust as av


# 1. Choose the occupants and their social connections.
# car_3 defines one driver and one passenger who both listen to each other.
# Their initial cognition and directed social-trust weights are set in that file.
from av_social_trust.car.examples import car_3 as car


# 2. Prepare a reproducible sequence of shared driving conditions.
# Probabilities set long-run frequencies; persistence creates runs of similar
# conditions. Seed 7 repeats this same sequence when the script is rerun.
# Later, a data loader can supply Situation objects in place of this generator.
from av_social_trust.situation.generator.examples import situation_generator_2 as situation_generator


# 3. Create the simulation from an independent copy of the car's initial state.
# Model owns the evolving state and history; the example car is left unchanged.
model = av.Model(car=car)


if __name__ == "__main__":
    number_of_cycles = 20

    print("Simulation: one driver and one passenger")
    print("Synthetic settings; each cycle is one simulation step.\n")
    print("Starting cognitive states (each value is between 0 and 1):")
    for agent_id, cognition in zip(model.state["agents"], model.state["cognitive_states"]):
        role = "Driver" if agent_id == model.state["driver"] else "Passenger"
        print(
            f"  {role} {agent_id}: trust={cognition['automation_trust']:.2f}, "
            f"risk={cognition['perceived_risk']:.2f}, "
            f"workload={cognition['workload']:.2f}"
        )

    situations = situation_generator.generate_series(number_of_cycles)

    print("\nDriver preference: positive favors automation; zero or negative favors manual.")
    print("Private = before discussion. Social = after discussion.")
    print("Automation can be ON only when available and the social preference is positive.\n")
    print("Cycle  Complexity  Available   Private -> Social   Mode")

    # 4. Advance the simulation once per situation, shared by both occupants.
    # Each model.step() performs the complete cycle:
    #   - update each person's cognition using their previous state and complexity;
    #   - turn that cognition into a private automation-use preference;
    #   - apply one DeGroot discussion round using the OLD social-trust weights;
    #   - learn new social trust from private opinions, for the NEXT cycle;
    #   - decide automation use from the DRIVER'S social preference and availability;
    #   - save the resulting state and intermediate values in history.
    # run() consumes the ordered list and calls step() once per Situation.
    model.run(situations)

    for record in model.history:
        state = record["state"]
        situation = record["situation"]

        # Car exports occupants in driver-first order, so index 0 is the driver.
        private_preference = record["private_opinion_vector"][0]
        social_preference = state["opinion_vector"][0]
        complexity = "high" if situation["task_complexity"] == 1 else "low"
        availability = "yes" if situation["automation_available"] else "no"
        mode = "ON" if state["automation_on"] else "OFF"
        print(
            f"{record['cycle']:5}  {complexity:10}  {availability:9}  "
            f"{private_preference:+.3f} -> {social_preference:+.3f}   {mode}"
        )

    # 5. Read the saved history to summarize what happened.
    # Keep unavailability separate from the driver's preference for manual use.
    automation_cycles = sum(record["state"]["automation_on"] for record in model.history)
    unavailable_cycles = sum(
        not record["situation"]["automation_available"] for record in model.history
    )
    manual_choice_cycles = sum(
        record["situation"]["automation_available"] and not record["state"]["automation_on"]
        for record in model.history
    )
    print(f"\nCompleted {model.cycle} cycles:")
    print(f"  Automation ON: {automation_cycles}")
    print(f"  Automation OFF because unavailable: {unavailable_cycles}")
    print(f"  Automation OFF by driver preference while available: {manual_choice_cycles}")
    print("Detailed per-cycle results are stored in model.history.")
