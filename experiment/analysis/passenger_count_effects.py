"""Run this file to describe the named parameters in matched comparisons."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[2]
    sys.path[:0]=[str(root),str(root/"src")]

from experiment.analysis.common import report

if __name__=="__main__":
    report("passenger_count_effects",dict(passenger_count=None,track_difficulty=None),
        interactions=(("passenger_count","track_difficulty"),))

