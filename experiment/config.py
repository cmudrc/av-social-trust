"""Edit these values, then use VS Code's Run Python File on the relevant script."""

from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
TRACKS_DIR = ROOT / "tracks" / "tracks"
RUNS_DIR = ROOT / "runs"
ANALYSIS_DIR = ROOT / "analysis" / "results"

STEPS = 100
PASSENGER_COMBINATIONS = (25, 200, 200, 200, 200)  # Per driver for counts 1–5.
COGNITIVE_STARTS = 12
SOCIAL_STARTS = 2
SELECTION_SEED = 17
INITIAL_SEED = 2026

TRACK_DIFFICULTIES = (("low", 0.2), ("normal", 0.5), ("high", 0.8))
TRACK_REPLICATES = 1  # Independent repetitions per difficulty–persistence pair.
TRACK_PERSISTENCES = (0.3, 0.6, 0.9)
COMPLEXITY_TOLERANCE = 0.1
AUTOMATION_AVAILABILITY = 1.0
TRACK_SEED = 7301

TRUST_VALUES = (0.01, 0.2, 0.4, 0.6, 0.8, 0.99)
INTERPERSONAL_LEARNING_RATE = 0.1
SELF_LEARNING_RATE = 0.1
DISCUSSION_ROUNDS = 1

CPU_CORES_FREE = 2
KEEP_AWAKE = True  # macOS caffeinate is started automatically by runner.py.
TASK_RUNS = 24  # Scheduling only; each completed model is saved independently.


@dataclass(frozen=True)
class Settings:
    steps: int = STEPS
    passenger_combinations: tuple = PASSENGER_COMBINATIONS
    cognitive_starts: int = COGNITIVE_STARTS
    social_starts: int = SOCIAL_STARTS
    selection_seed: int = SELECTION_SEED
    initial_seed: int = INITIAL_SEED
    track_difficulties: tuple = TRACK_DIFFICULTIES
    track_replicates: int = TRACK_REPLICATES
    track_seed: int = TRACK_SEED
    track_persistences: tuple = TRACK_PERSISTENCES
    complexity_tolerance: float = COMPLEXITY_TOLERANCE
    automation_availability: float = AUTOMATION_AVAILABILITY
    trust_values: tuple = TRUST_VALUES
    interpersonal_learning_rate: float = INTERPERSONAL_LEARNING_RATE
    self_learning_rate: float = SELF_LEARNING_RATE
    discussion_rounds: int = DISCUSSION_ROUNDS

    def __post_init__(self):
        for name in ("steps", "cognitive_starts", "social_starts", "track_replicates"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer.")
        if (len(self.passenger_combinations) != 5 or any(isinstance(v, bool) or not isinstance(v, int)
                or v < 0 for v in self.passenger_combinations)):
            raise ValueError("Provide five nonnegative passenger-combination quotas.")
        if isinstance(self.discussion_rounds, bool) or not isinstance(self.discussion_rounds, int) or self.discussion_rounds < 0:
            raise ValueError("discussion_rounds must be a nonnegative integer.")
        if not self.track_persistences or any(not 0 <= p <= 1 for p in self.track_persistences):
            raise ValueError("Provide at least one persistence in [0, 1].")
        if len(set(self.track_persistences)) != len(self.track_persistences):
            raise ValueError("Track persistence levels must be distinct.")
        for name in ("complexity_tolerance", "automation_availability",
                     "interpersonal_learning_rate", "self_learning_rate"):
            if not 0 <= getattr(self, name) <= 1:
                raise ValueError(f"{name} must be in [0, 1].")
        if not self.trust_values or any(not 0 < value < 1 for value in self.trust_values):
            raise ValueError("Trust values must be strictly between 0 and 1.")
        names = [name for name, _ in self.track_difficulties]
        if not names or len(set(names)) != len(names) or any(not 0 <= p <= 1 for _, p in self.track_difficulties):
            raise ValueError("Track difficulty names must be unique, with probabilities in [0, 1].")

    @property
    def starts(self):
        return self.cognitive_starts * self.social_starts

    def track_parameters(self):
        return {name: asdict(self)[name] for name in ("steps", "track_difficulties", "track_replicates",
                "track_seed", "track_persistences", "complexity_tolerance", "automation_availability")}
