"""Count solo-driving regimes and clipping in the completed baseline results."""

from collections import Counter
import json
from pathlib import Path
import sqlite3
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[3]
    sys.path[:0]=[str(root),str(root/"src")]

from experiment.config import RUNS_DIR
from experiment.analysis.shared.output import result_directory,write_results


def summarize(directory=RUNS_DIR,output=None):
    print("Reading solo-driver baselines...",flush=True)
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
    output=Path(output) if output is not None else result_directory("baseline_quality")
    output.mkdir(parents=True,exist_ok=True)
    total=totals["baselines"]
    markdown=[f"Completed solo baselines: **{total:,}**.","",
              "| Automation behavior | Models | Share |","| --- | ---: | ---: |"]
    for key,label in (("always_off","Always manual"),("varying","Varying"),("always_on","Always automated")):
        percentage=100*totals[key]/total if total else 0
        markdown.append(f"| {label} | {totals[key]:,} | {percentage:.1f}% |")
    markdown.extend(["",f"Models with cognitive clipping: **{totals['with_clipping']:,}** "
                     f"({100*totals['with_clipping']/total if total else 0:.1f}%).",""])
    save_figure(totals,output)
    markdown.extend(["![Solo baseline regimes](results/figures/baseline_regimes.png)","",
                     "| Driver | Baselines | Always manual | Varying | Always automated | With clipping |",
                     "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for driver,counts in sorted(drivers.items()):
        markdown.append(f"| {driver} | "+" | ".join(f"{counts[key]:,}" for key in
                        ("baselines","always_off","varying","always_on","with_clipping"))+" |")
    write_results("baseline_quality",result,"\n".join(markdown),output=output)
    print(json.dumps(result["totals"],indent=2))
    print(f"Saved {output/'summary.json'}, figure and README results section.",flush=True)
    return result


def save_figure(totals,output):
    import os
    import tempfile
    os.environ.setdefault("MPLCONFIGDIR",str(Path(tempfile.gettempdir())/"av-social-trust-matplotlib"))
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    figures=output/"figures"
    figures.mkdir(parents=True,exist_ok=True)
    figure=Figure(figsize=(6.4,3.8),dpi=160)
    FigureCanvasAgg(figure)
    axis=figure.subplots()
    values=[totals[key] for key in ("always_off","varying","always_on")]
    bars=axis.bar(["Always manual","Varying","Always automated"],values,
                  color=["#64748b","#2563eb","#0f766e"])
    axis.bar_label(bars,labels=[f"{value:,}" for value in values],padding=4)
    axis.set_ylabel("Completed solo models")
    axis.set_title("Solo-driver automation behavior")
    axis.set_ylim(0,max(max(values,default=0)*1.18,1))
    axis.spines[["top","right"]].set_visible(False)
    figure.tight_layout()
    figure.savefig(figures/"baseline_regimes.png")


def run(directory=RUNS_DIR,output=None):
    return summarize(directory,output)


if __name__=="__main__":
    run()
