"""Run this file to describe the named parameters in matched comparisons."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

from experiment.analysis.shared.common import report


def run(directory=None,output=None):
    return report("passenger_count_effects",dict(passenger_count=None,track_difficulty=None),
        interactions=(("passenger_count","track_difficulty"),),directory=directory,output=output)


if __name__=="__main__":
    run()

