"""Run in VS Code to extract complete matched triples; repeat to add new results."""

import json
from pathlib import Path
import sqlite3
import sys

if __package__ in (None, ""):
    root=Path(__file__).resolve().parents[2]
    sys.path[:0]=[str(root),str(root/"src")]

import numpy as np

from experiment.config import ANALYSIS_DIR,RUNS_DIR
from experiment.design import canonical,digest
from experiment.analysis.common import similarity


def decisions(blob,steps):
    return np.unpackbits(np.frombuffer(blob,dtype=np.uint8))[:steps].astype(bool)


def extract(directory=RUNS_DIR,output=ANALYSIS_DIR):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(output/"comparisons.sqlite")
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS comparisons(driver TEXT NOT NULL,track TEXT NOT NULL,
            composition INTEGER NOT NULL,start INTEGER NOT NULL,features TEXT NOT NULL,metrics TEXT NOT NULL,
            PRIMARY KEY(driver,track,composition,start)) WITHOUT ROWID;
    """)
    added=0
    try:
        for path in sorted(Path(directory).glob("*.sqlite")):
            source=sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True)
            try:
                saved=source.execute("SELECT value FROM metadata WHERE key='definition'").fetchone()
                if saved is None:
                    continue
                definition=json.loads(saved[0])
                provenance=digest(dict(definition=definition,similarity_source=Path(__file__).with_name("common.py").read_text(),
                                       extraction_source=Path(__file__).read_text()))
                with db:
                    db.execute("INSERT OR IGNORE INTO metadata VALUES ('provenance',?)",(provenance,))
                    if db.execute("SELECT value FROM metadata WHERE key='provenance'").fetchone()[0]!=provenance:
                        raise ValueError("Analysis inputs/metrics changed. Use an empty ANALYSIS_DIR.")
                steps=definition["parameters"]["steps"]
                baseline={start:(json.loads(meta),decisions(on,steps)) for start,meta,on in source.execute(
                    "SELECT start,metadata,automation_on FROM results WHERE composition=0 AND variant='baseline'")}
                # Read only metadata and packed driver decisions, never entire
                # trajectories, for these comparisons.
                query="""SELECT c.composition,c.start,c.metadata,c.automation_on,d.metadata,d.automation_on
                    FROM results c JOIN results d ON c.composition=d.composition AND c.start=d.start
                    WHERE c.variant='cognition' AND d.variant='decision' ORDER BY c.composition,c.start"""
                driver,track=path.stem.split("_",1)
                done=set(db.execute("SELECT composition,start FROM comparisons WHERE driver=? AND track=?",(driver,track)))
                for composition,start,c_meta,c_on,d_meta,d_on in source.execute(query):
                    if (composition,start) in done or start not in baseline:
                        continue
                    cognition_meta,decision_meta=json.loads(c_meta),json.loads(d_meta)
                    base_meta,base=baseline[start]
                    if cognition_meta["features"]!=decision_meta["features"]:
                        raise ValueError("Influence variants have different initial conditions")
                    for key in ("driver_self_trust","driver_automation_trust","driver_perceived_risk","driver_workload"):
                        if base_meta["features"][key]!=cognition_meta["features"][key]:
                            raise ValueError("Driver initialization differs from baseline")
                    cognition,decision=decisions(c_on,steps),decisions(d_on,steps)
                    metrics=dict(decision_vs_baseline=similarity(base,decision),
                        cognition_vs_baseline=similarity(base,cognition),decision_vs_cognition=similarity(cognition,decision),
                        all_three_agreement=float(np.mean((base==decision)&(decision==cognition))),
                        baseline_automation_fraction=float(base.mean()))
                    for name,meta in (("baseline",base_meta),("decision",decision_meta),("cognition",cognition_meta)):
                        metrics[f"{name}_driver_clipping_fraction"]=meta["summary"]["driver_clipping_fraction"]
                    features=dict(cognition_meta["features"],passenger_count=len(cognition_meta["passengers"]),
                        track=track,track_difficulty=cognition_meta["track_difficulty"],
                        track_replicate=cognition_meta["track_replicate"],cognitive_start=cognition_meta["cognitive_start"],
                        social_start=cognition_meta["social_start"])
                    db.execute("INSERT INTO comparisons VALUES (?,?,?,?,?,?)",(driver,track,composition,start,canonical(features),canonical(metrics)))
                    added+=1
                    if added%1000==0:
                        db.commit()
                db.commit()
            finally:
                source.close()
        total=db.execute("SELECT count(*) FROM comparisons").fetchone()[0]
        print(f"Added {added:,} comparisons; cached total {total:,}")
        return added,total
    finally:
        db.close()


if __name__=="__main__":
    extract()
