"""Per-question artifacts and a replaceable results section in its README."""

from datetime import datetime
import json
import os
from pathlib import Path
import tempfile
from zoneinfo import ZoneInfo

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
START = "<!-- analysis-results:start -->"
END = "<!-- analysis-results:end -->"


def result_directory(question):
    return ANALYSIS_ROOT/question/"results"


def comparison_directory(directory=None):
    if directory is not None:
        return Path(directory)
    current = result_directory("compare_modes")
    legacy = ANALYSIS_ROOT/"results"
    return current if (current/"comparisons.sqlite").exists() or not (legacy/"comparisons.sqlite").exists() else legacy


def atomic_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.",dir=path.parent)
    try:
        with os.fdopen(descriptor,"w") as stream:
            stream.write(text)
        os.replace(temporary,path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def write_results(question, result, markdown, output=None, readme=None):
    directory = Path(output) if output is not None else result_directory(question)
    stamp = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M:%S %Z")
    atomic_text(directory/"summary.json",json.dumps(result,indent=2,allow_nan=False)+"\n")
    body = f"Updated: {stamp}\n\n{markdown.rstrip()}\n"
    atomic_text(directory/"summary.md",body.replace("](results/", "]("))
    if readme is None:
        readme = directory.parent/"README.md"
    readme = Path(readme)
    original = readme.read_text() if readme.exists() else f"# {question.replace('_',' ').title()}\n"
    relative = Path(os.path.relpath(directory,readme.parent)).as_posix()
    section = f"{START}\n## Latest results\n\n{body}\nFull output: [summary.json]({relative}/summary.json), [summary.md]({relative}/summary.md).\n{END}"
    if START in original and END in original:
        before, remainder = original.split(START,1)
        _, after = remainder.split(END,1)
        updated = before+section+after
    else:
        updated = original.rstrip()+"\n\n"+section+"\n"
    atomic_text(readme,updated)
    return directory


def read_results(question, output=None):
    """Load a question's saved summary.json; plot.py scripts draw from this, not from raw runs."""
    directory = Path(output) if output is not None else result_directory(question)
    path = directory/"summary.json"
    if not path.exists():
        raise FileNotFoundError(f"Run experiment/analysis/{question}/run.py first; {path} is missing")
    return json.loads(path.read_text()),directory


def grouped_markdown(result):
    rows = [f"Matched comparisons: **{result['comparison_rows']:,}**.",
            "",result["interpretation"],"",
            "Agreement is the percentage of cycles with the same automation decision.","",
            "| Feature | Group | Models | Drivers | Decision / solo | Cognition / solo | Decision / cognition |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for group in result["groups"][:40]:
        means = group["means"]
        percentages = [f"{100*means[key]:.1f}%" if key in means else "—" for key in
                       ("decision_vs_baseline.agreement","cognition_vs_baseline.agreement","decision_vs_cognition.agreement")]
        label = str(group["bin"]).replace("|",r"\|")
        rows.append(f"| {group['feature']} | {label} | {group['n']:,} | {group['drivers']} | "+" | ".join(percentages)+" |")
    if len(result["groups"])>40:
        rows.extend(["",f"Showing 40 of {len(result['groups'])} groups; all groups are in summary.json and groups.jsonl."])
    return "\n".join(rows)
