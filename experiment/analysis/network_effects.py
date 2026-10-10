"""Run this file to describe the named parameters in matched comparisons."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[2]
    sys.path[:0]=[str(root),str(root/"src")]

from experiment.analysis.common import report

unit=[0,0.2,0.4,0.6,0.8,1]
if __name__=="__main__":
    report("network_effects",dict(inbound_trust_mean=unit,outbound_trust_mean=unit,
        driver_initial_self_weight=unit,alpha_inbound_mean=unit,alpha_outbound_mean=unit,
        passenger_count=None,driver_self_plus_inbound_sum=[0,0.5,1,2,3,4,5,6]),
        interactions=(("passenger_count","driver_initial_self_weight"),))

