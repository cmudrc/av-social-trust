"""Run once to speed up resume lookups in existing result archives.

Only a SQLite index is added. Model rows, metadata and experiment signatures
are unchanged. SQLite coordinates this operation with any active runner.
"""

from pathlib import Path
import sqlite3
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiment import config


def add_resume_index(path):
    db = sqlite3.connect(path, timeout=60)
    try:
        tables = {row[0] for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if "results" not in tables:
            return False
        with db:
            db.execute("CREATE INDEX IF NOT EXISTS result_completion "
                       "ON results(composition,start,variant)")
        return True
    finally:
        db.close()


def repair(directory=None):
    directory = Path(directory or config.RUNS_DIR)
    paths = sorted(directory.glob("*.sqlite"))
    print(f"Preparing fast resume lookups in {len(paths)} archives...", flush=True)
    started = reported = time.monotonic()
    indexed = 0
    for number, path in enumerate(paths, 1):
        indexed += add_resume_index(path)
        if time.monotonic() - reported >= 10:
            print(f"Checked {number}/{len(paths)} archives", flush=True)
            reported = time.monotonic()
    print(f"Ready: {indexed} archives in {time.monotonic() - started:.1f}s. "
          "Saved models are unchanged.", flush=True)


if __name__ == "__main__":
    repair()
