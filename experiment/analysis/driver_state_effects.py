"""Run this file to describe the named parameters in matched comparisons."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[2]
    sys.path[:0]=[str(root),str(root/"src")]

from experiment.analysis.common import report

unit=[0,0.2,0.4,0.6,0.8,1]
if __name__=="__main__":
    report("driver_state_effects",dict(driver_self_trust=None,driver_automation_trust=unit,
        driver_perceived_risk=unit,driver_workload=unit,passenger_count=None),
        interactions=(("passenger_count","driver_self_trust"),))

