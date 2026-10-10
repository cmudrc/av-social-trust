"""Run this file to describe the named parameters in matched comparisons."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[2]
    sys.path[:0]=[str(root),str(root/"src")]

from experiment.analysis.common import report

if __name__=="__main__":
    report("track_effects",dict(track_difficulty=None,track_persistence=None,track_replicate=None,track=None,
        mean_complexity=None,complexity_switches=None,passenger_count=None),
        interactions=(("track_difficulty","passenger_count"),("track_difficulty","track_persistence")))

