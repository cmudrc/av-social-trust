"""Count solo-driving regimes and clipping in the completed baseline results."""

from collections import Counter
import json
from pathlib import Path
import sqlite3
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[2]
    sys.path[:0]=[str(root),str(root/"src")]

from experiment.config import ANALYSIS_DIR,RUNS_DIR
from experiment.design import canonical


def summarize(directory=RUNS_DIR,output=ANALYSIS_DIR):
    totals,drivers=Counter(),{}
    for path in sorted(Path(directory).glob("*.sqlite")):
        db=sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True)
        try:
            for raw, in db.execute("SELECT metadata FROM results WHERE variant='baseline'"):
                meta=json.loads(raw)
                fraction=meta["summary"]["automation_fraction"]
                regime="always_off" if fraction==0 else "always_on" if fraction==1 else "varying"
                local=drivers.setdefault(meta["driver"],Counter())
                for count in (totals,local):
                    count["baselines"]+=1
                    count[regime]+=1
                    count["with_clipping"]+=meta["summary"]["driver_clipping_fraction"]>0
        finally:
            db.close()
    result=dict(totals=dict(totals),drivers={key:dict(value) for key,value in drivers.items()})
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    (output/"baseline_quality.json").write_text(canonical(result)+"\n")
    print(json.dumps(result["totals"],indent=2))
    return result


if __name__=="__main__":
    summarize()
