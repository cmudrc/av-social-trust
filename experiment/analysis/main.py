"""Run selected questions in sequence; comment out calls in main() to skip them.

Set REDRAW_ONLY = True to redraw every figure from saved results without running
any analysis (each question's plot.py reads its results/ folder).
"""

from pathlib import Path
import sys
import time

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[2]
    sys.path[:0] = [str(root),str(root/"src")]

from experiment.analysis.inventory.run import run as inventory
from experiment.analysis.baseline_quality.run import run as baseline_quality
from experiment.analysis.compare_modes.run import run as compare_modes
from experiment.analysis.passenger_count_effects.run import run as passenger_count_effects
from experiment.analysis.network_effects.run import run as network_effects
from experiment.analysis.driver_state_effects.run import run as driver_state_effects
from experiment.analysis.track_effects.run import run as track_effects
from experiment.analysis.social_importance.run import run as social_importance
from experiment.analysis.occupant_disagreement.run import run as occupant_disagreement
from experiment.analysis.pressure_conversion.run import run as pressure_conversion
from experiment.analysis.influence_timing.run import run as influence_timing
from experiment.analysis.participant_susceptibility.run import run as participant_susceptibility
from experiment.analysis.when_social_matters.run import run as when_social_matters
from experiment.analysis.example_cases.run import run as example_cases
from experiment.analysis.baseline_similarity.run import run as baseline_similarity
from experiment.analysis.track_social_effects.run import run as track_social_effects
from experiment.analysis.network_dynamics.run import run as network_dynamics
from experiment.analysis.driver_confidence.run import run as driver_confidence
from experiment.analysis.trust_learning.run import run as trust_learning
from experiment.analysis.network_confidence.run import run as network_confidence
from experiment.analysis.social_direction.run import run as social_direction
from experiment.analysis.complexity_pressure.run import run as complexity_pressure
from experiment.analysis.tree_features.run import run as tree_features

REDRAW_ONLY = False
# Questions whose figures are drawn by a separate plot.py from saved results.
PLOTTED = ("occupant_disagreement","pressure_conversion","influence_timing",
           "participant_susceptibility","when_social_matters","example_cases","baseline_similarity",
           "track_social_effects","network_dynamics","driver_confidence","trust_learning","network_confidence",
           "social_direction")


def run_question(name, question):
    print(f"\nRunning {name}...",flush=True)
    started = time.monotonic()
    result = question()
    print(f"Finished {name} in {time.monotonic()-started:.1f}s.",flush=True)
    return result


def main():
    # Comment out any call you do not want to run. Questions run in this order.
    run_question("inventory", inventory)
    run_question("baseline_quality", baseline_quality)

    # Prepare/refresh the cache before questions below. Skip if it is up to date.
    run_question("compare_modes", compare_modes)

    run_question("passenger_count_effects", passenger_count_effects)
    run_question("network_effects", network_effects)
    run_question("driver_state_effects", driver_state_effects)
    run_question("track_effects", track_effects)
    run_question("social_importance", social_importance)

    # When does the social layer matter? The first of these builds the shared
    # analysis table after a cache update; the rest load it in seconds.
    run_question("occupant_disagreement", occupant_disagreement)
    run_question("pressure_conversion", pressure_conversion)
    run_question("influence_timing", influence_timing)
    run_question("participant_susceptibility", participant_susceptibility)
    run_question("when_social_matters", when_social_matters)
    run_question("example_cases", example_cases)
    run_question("baseline_similarity", baseline_similarity)

    # Direct paper questions: full paired track comparison, then a balanced
    # trajectory sample of changing directed network influence.
    run_question("track_social_effects", track_social_effects)
    run_question("network_dynamics", network_dynamics)
    run_question("driver_confidence", driver_confidence)
    run_question("network_confidence", network_confidence)
    run_question("trust_learning", trust_learning)

    # Additions for the journal paper: direction of the social effect, pressure by
    # complexity, and which cognitive states the participant trees use.
    run_question("social_direction", social_direction)
    run_question("complexity_pressure", complexity_pressure)
    run_question("tree_features", tree_features)


def redraw():
    from importlib import import_module
    for name in PLOTTED:
        print(f"\nRedrawing {name}...",flush=True)
        try:
            import_module(f"experiment.analysis.{name}.plot").render()
        except FileNotFoundError as error:
            print(f"Skipped: {error}",flush=True)


if __name__ == "__main__":
    try:
        redraw() if REDRAW_ONLY else main()
    except KeyboardInterrupt:
        print("\nAnalysis sequence stopped; completed outputs remain saved.",flush=True)
