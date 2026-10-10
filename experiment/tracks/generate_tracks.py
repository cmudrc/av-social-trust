"""Run this file to generate shared tracks using experiment/config.py."""

import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from collections.abc import Iterator
from typing import TypedDict

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[2]
    sys.path[:0] = [str(root), str(root/"src")]

import numpy as np

from av_social_trust.situation import Situation
from av_social_trust.situation.generator.generator import SituationGenerator
from experiment.config import Settings, TRACKS_DIR
from experiment.design import canonical, stable_seed


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class TrackSpec(TypedDict):
    name: str
    difficulty: str
    probability: float
    persistence_index: int
    persistence: float
    replicate: int


def track_specs(settings: Settings) -> Iterator[TrackSpec]:
    for difficulty, probability in settings.track_difficulties:
        for persistence_index, persistence in enumerate(settings.track_persistences):
            for replicate in range(settings.track_replicates):
                yield TrackSpec(name=f"{difficulty}_p{persistence_index}_{replicate}",
                           difficulty=difficulty,probability=probability,
                           persistence_index=persistence_index,persistence=persistence,replicate=replicate)


def generate(settings=None, directory=TRACKS_DIR):
    settings = settings or Settings()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    tracks = []
    for specification in track_specs(settings):
        name = specification["name"]
        difficulty, probability = specification["difficulty"], specification["probability"]
        persistence, replicate = specification["persistence"], specification["replicate"]
        base_seed = stable_seed(settings.track_seed, difficulty, persistence, replicate)
        tolerance = max(settings.complexity_tolerance, 0.5/settings.steps)
        for attempt in range(10000):
            seed = base_seed if attempt == 0 else stable_seed(base_seed, "complexity_acceptance", attempt)
            generator = SituationGenerator(rng_seed=seed, task_complexity_probability=probability,
                automation_availability_probability=settings.automation_availability,
                task_complexity_persistence=persistence)
            situations = generator.generate_series(settings.steps)
            complexity = np.array([s.task_complexity for s in situations])
            if abs(float(complexity.mean())-probability) <= tolerance+1e-12:
                break
        else:
            raise ValueError(f"Could not generate {name} in its intended difficulty range.")
        path = directory/f"{name}.csv"
        descriptor, temporary = tempfile.mkstemp(prefix=".track_", dir=directory)
        try:
            with os.fdopen(descriptor, "w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(("step", "task_complexity", "automation_available"))
                writer.writerows((i, s.task_complexity, int(s.automation_available))
                                 for i, s in enumerate(situations, 1))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)
        tracks.append(dict(code=len(tracks), name=name, difficulty=difficulty, replicate=replicate,
            persistence=persistence,persistence_index=specification["persistence_index"],
            seed=seed, base_seed=base_seed, generation_attempt=attempt, sha256=file_hash(path),
            mean_complexity=float(complexity.mean()),
            complexity_switches=int(np.count_nonzero(complexity[1:]!=complexity[:-1]))))
    manifest = dict(parameters=settings.track_parameters(), tracks=tracks)
    descriptor, temporary = tempfile.mkstemp(prefix=".manifest_", dir=directory)
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(canonical(manifest)+"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, directory/"manifest.json")
    finally:
        Path(temporary).unlink(missing_ok=True)
    print(f"Saved {len(tracks)} shared {settings.steps}-step tracks in {directory}")
    return manifest


def load_tracks(settings, directory=TRACKS_DIR):
    directory = Path(directory)
    try:
        manifest = json.loads((directory/"manifest.json").read_text())
    except FileNotFoundError:
        raise FileNotFoundError("Run experiment/tracks/generate_tracks.py first.") from None
    if canonical(manifest["parameters"]) != canonical(settings.track_parameters()):
        raise ValueError("Track settings changed. Run experiment/tracks/generate_tracks.py again.")
    tracks = {}
    expected = list(track_specs(settings))
    if [t["name"] for t in manifest["tracks"]] != [t["name"] for t in expected]:
        raise ValueError("Shared track manifest has unexpected tracks.")
    for track, specification in zip(manifest["tracks"],expected):
        if any(track.get(key) != specification.get(key) for key in ("difficulty","persistence","persistence_index","replicate")):
            raise ValueError("Shared track manifest has unexpected persistence levels.")
        path = directory/f"{track['name']}.csv"
        if file_hash(path) != track["sha256"]:
            raise ValueError(f"Track changed outside the generator: {path}")
        with path.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        if len(rows)!=settings.steps or any(row["step"]!=str(i) for i,row in enumerate(rows,1)):
            raise ValueError(f"Wrong step count/order in {path}")
        if any(row["task_complexity"] not in ("0","1") or row["automation_available"] not in ("0","1") for row in rows):
            raise ValueError(f"Invalid situation in {path}")
        tracks[track["name"]] = [Situation(int(row["task_complexity"]), row["automation_available"]=="1") for row in rows]
    return manifest["tracks"], tracks


if __name__ == "__main__":
    generate()
