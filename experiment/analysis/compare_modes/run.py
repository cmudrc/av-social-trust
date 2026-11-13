"""Extract matched comparisons with bounded batches, checkpoints and progress."""

import json
from pathlib import Path
import sqlite3
import sys
import time

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(root), str(root/"src")]

import numpy as np

from experiment.config import RUNS_DIR
from experiment.design import canonical, digest
from experiment.analysis.shared import metrics
from experiment.analysis.shared.output import comparison_directory, write_results

BATCH_SIZE = 1000


def decisions(blob, steps):
    return np.unpackbits(np.frombuffer(blob,dtype=np.uint8))[:steps].astype(bool)


def provenance_for(definition):
    return digest(dict(definition=definition,metrics_source=Path(metrics.__file__).read_text()))


def extract(directory=RUNS_DIR, output=None):
    output = comparison_directory(output)
    output.mkdir(parents=True,exist_ok=True)
    paths = sorted(Path(directory).glob("*.sqlite"))
    cache = output/"comparisons.sqlite"
    print(f"Opening comparison cache: {cache}",flush=True)
    db = sqlite3.connect(cache,timeout=60)
    added, checked = 0, 0
    started = reported = time.monotonic()
    current_archive = None
    initial = 0

    def publish(status):
        result = dict(status=status,new_comparisons=added,cached_comparisons=initial+added,
                      archives_checked=checked,result_archives=len(paths),
                      current_archive=current_archive,elapsed_seconds=round(time.monotonic()-started,1))
        markdown = (f"Status: **{status}**.\n\n"
                    f"- Cached matched comparisons: **{initial+added:,}**\n"
                    f"- Added in this run: **{added:,}**\n"
                    f"- Archives checked: **{checked}/{len(paths)}**\n"
                    f"- Current archive: `{current_archive or '—'}`\n\n"
                    "Each comparison matches decision influence, cognition influence and a solo baseline. "
                    "Missing partners or baselines are skipped. Completed batches remain saved if interrupted.\n\n"
                    "Data: [comparisons.sqlite](results/comparisons.sqlite).")
        write_results("compare_modes",result,markdown,output=output)

    try:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS comparisons(driver TEXT NOT NULL,track TEXT NOT NULL,
                composition INTEGER NOT NULL,start INTEGER NOT NULL,features TEXT NOT NULL,metrics TEXT NOT NULL,
                PRIMARY KEY(driver,track,composition,start)) WITHOUT ROWID;
        """)
        initial = db.execute("SELECT count(*) FROM comparisons").fetchone()[0]
        print(f"Found {len(paths)} result archives; cached comparisons: {initial:,}. Checking missing pairs...",flush=True)
        publish("running")
        for number,path in enumerate(paths,1):
            current_archive = path.name
            print(f"[{number}/{len(paths)}] {path.name}; added {added:,}; cached {initial+added:,}",flush=True)
            source = sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True,timeout=60)
            try:
                source.execute("ATTACH DATABASE ? AS cached",(cache.resolve().as_uri()+"?mode=ro",))
                saved = source.execute("SELECT value FROM metadata WHERE key='definition'").fetchone()
                if saved is None:
                    continue
                definition = json.loads(saved[0])
                provenance = provenance_for(definition)
                with db:
                    db.execute("INSERT OR IGNORE INTO metadata VALUES ('provenance',?)",(provenance,))
                    if db.execute("SELECT value FROM metadata WHERE key='provenance'").fetchone()[0] != provenance:
                        raise ValueError(f"Analysis inputs/metrics changed. Use a new output directory instead of {output}.")
                steps = definition["parameters"]["steps"]
                baseline = {start:(json.loads(meta),decisions(on,steps)) for start,meta,on in source.execute(
                    "SELECT start,metadata,automation_on FROM results WHERE composition=0 AND variant='baseline'")}
                if not baseline:
                    continue
                driver,track = path.stem.split("_",1)
                placeholders = ",".join("?" for _ in baseline)
                # Both variant indexes contain model keys. Check the cache before
                # SQLite reads metadata/decisions from the large trajectory table.
                query = f"""WITH missing AS MATERIALIZED (
                        SELECT c.composition,c.start
                        FROM results AS c INDEXED BY result_variants
                        JOIN results AS d INDEXED BY result_variants
                            ON c.composition=d.composition AND c.start=d.start
                        WHERE c.variant='cognition' AND d.variant='decision'
                            AND c.start IN ({placeholders})
                            AND NOT EXISTS (SELECT 1 FROM cached.comparisons AS previous
                                WHERE previous.driver=? AND previous.track=?
                                    AND previous.composition=c.composition AND previous.start=c.start)
                    )
                    SELECT missing.composition,missing.start,c.metadata,c.automation_on,d.metadata,d.automation_on
                    FROM missing JOIN results AS c
                        ON c.composition=missing.composition AND c.start=missing.start AND c.variant='cognition'
                    JOIN results AS d
                        ON d.composition=missing.composition AND d.start=missing.start AND d.variant='decision'
                    ORDER BY missing.composition,missing.start"""
                cursor = source.execute(query,(*baseline,driver,track))
                while rows := cursor.fetchmany(BATCH_SIZE):
                    calculated = metrics.comparison_batch(rows,baseline,steps,driver,track)
                    before = db.total_changes
                    with db:
                        db.executemany("INSERT OR IGNORE INTO comparisons VALUES (?,?,?,?,?,?)",
                            ((d,t,c,s,canonical(f),canonical(m)) for d,t,c,s,f,m in calculated))
                    added += db.total_changes-before
                    if time.monotonic()-reported >= 5:
                        elapsed = time.monotonic()-started
                        print(f"  Added {added:,}; cached {initial+added:,}; {added/max(elapsed,0.001):,.0f} new comparisons/s",flush=True)
                        publish("running")
                        reported = time.monotonic()
            finally:
                source.close()
                checked = number
            if time.monotonic()-reported >= 5:
                publish("running")
                reported = time.monotonic()
        publish("complete")
        print(f"Added {added:,} comparisons; cached total {initial+added:,}. Saved in {output}; README updated.",flush=True)
        return added,initial+added
    except KeyboardInterrupt:
        publish("interrupted")
        print(f"Stopped; {initial+added:,} comparisons remain saved. Run again to continue.",flush=True)
        raise
    except BaseException:
        publish("failed")
        raise
    finally:
        db.close()


def run(directory=RUNS_DIR, output=None):
    return extract(directory,output)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        pass
