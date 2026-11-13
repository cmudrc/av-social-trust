"""Count completed results directly; unfinished models have no stored rows."""

from collections import Counter
import json
from pathlib import Path
import sqlite3
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

from experiment.config import RUNS_DIR
from experiment.analysis.shared.output import write_results


def inventory(directory=RUNS_DIR):
    counts=Counter()
    files=list(Path(directory).glob("*.sqlite"))
    for path in files:
        db=sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True)
        try:
            counts.update({variant:number for variant,number in db.execute("SELECT variant,count(*) FROM results GROUP BY variant")})
        finally:
            db.close()
    result=dict(result_archives=len(files),completed_models=sum(counts.values()),by_variant=dict(counts))
    print(json.dumps(result,indent=2))
    return result


def run(directory=RUNS_DIR,output=None):
    result=inventory(directory)
    markdown=[f"Result archives: **{result['result_archives']}**. Completed models: **{result['completed_models']:,}**.",
              "","| Mode | Completed models |","| --- | ---: |"]
    markdown.extend(f"| {variant} | {count:,} |" for variant,count in sorted(result["by_variant"].items()))
    destination=write_results("inventory",result,"\n".join(markdown),output=output)
    print(f"Saved {destination/'summary.json'}; README updated.",flush=True)
    return result


if __name__=="__main__":
    run()
