"""Only completed models are stored; one result archive per driver and track.

SQLite transactions are the per-model checkpoint. No pending/running rows,
partial trajectories, study copies, input copies or execution-history files.
"""

from collections import OrderedDict
import io
import json
from pathlib import Path
import sqlite3
import time

import numpy as np

from experiment.design import canonical
from experiment.runtime_compatibility import definitions_match


def archive_path(directory, driver, track):
    return Path(directory)/f"{driver}_{track}.sqlite"


def pack_trajectory(arrays):
    buffer = io.BytesIO()
    np.savez_compressed(buffer,**arrays)
    return buffer.getvalue()


def unpack_trajectory(blob):
    with np.load(io.BytesIO(blob),allow_pickle=False) as saved:
        return {name:saved[name].copy() for name in saved.files}


def enable_wal(db, timeout=60):
    """Journal-mode transitions can return SQLITE_BUSY without a busy wait."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            if db.execute("PRAGMA journal_mode").fetchone()[0] == "wal":
                return
            if db.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal":
                return
            raise sqlite3.OperationalError("Could not enable WAL journal mode")
        except sqlite3.OperationalError as exc:
            if (getattr(exc, "sqlite_errorcode", None) not in
                    (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED)
                    or time.monotonic() >= deadline):
                raise
            time.sleep(0.05)


class ResultStore:
    def __init__(self, directory, definition, max_connections=8):
        self.directory = Path(directory)
        self.definition = json.loads(canonical(definition))
        self.connections = OrderedDict()
        self.max_connections = max_connections

    def connection(self, driver, track):
        key = driver,track
        if key in self.connections:
            db = self.connections.pop(key)
            self.connections[key] = db
            return db
        self.directory.mkdir(parents=True,exist_ok=True)
        db = sqlite3.connect(archive_path(self.directory,driver,track),timeout=60)
        try:
            enable_wal(db)
            db.execute("PRAGMA synchronous=FULL")
            db.execute("PRAGMA cache_size=-256")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS results(
                    composition INTEGER NOT NULL,start INTEGER NOT NULL,variant TEXT NOT NULL,
                    metadata TEXT NOT NULL,automation_on BLOB NOT NULL,trajectory BLOB NOT NULL,
                    PRIMARY KEY(composition,start,variant)) WITHOUT ROWID;
                CREATE INDEX IF NOT EXISTS result_variants ON results(variant,composition,start);
                CREATE INDEX IF NOT EXISTS result_completion ON results(composition,start,variant);
            """)
            with db:
                db.execute("INSERT OR IGNORE INTO metadata VALUES ('definition',?)",(canonical(self.definition),))
                definition = json.loads(db.execute("SELECT value FROM metadata WHERE key='definition'").fetchone()[0])
                if not definitions_match(definition,self.definition):
                    raise ValueError("Results use different settings/code/inputs. Choose an empty RUNS_DIR to start fresh.")
            self.connections[key] = db
            if len(self.connections)>self.max_connections:
                _,old = self.connections.popitem(last=False)
                old.close()
            return db
        except BaseException:
            db.close()
            raise

    def save(self, composition, start, variant, track, metadata, arrays):
        steps = self.definition["parameters"]["steps"]
        if not np.array_equal(arrays["step"],np.arange(1,steps+1)):
            raise ValueError("An unfinished trajectory cannot be saved")
        if np.asarray(arrays["automation_on"]).shape!=(steps,):
            raise ValueError("Driver decisions must span the whole model")
        # Compression finishes before the transaction; interrupted computations
        # leave no row. INSERT is atomic even if the process is killed mid-write.
        trajectory = pack_trajectory(arrays)
        decisions = np.packbits(arrays["automation_on"]).tobytes()
        db = self.connection(composition.driver,track)
        with db:
            cursor = db.execute("INSERT OR IGNORE INTO results VALUES (?,?,?,?,?,?)",
                (composition.identifier,start,variant,canonical(metadata),decisions,trajectory))
        return cursor.rowcount==1

    def close(self):
        for db in self.connections.values():
            db.close()
        self.connections.clear()


def completed(directory, driver, track, composition):
    path = archive_path(directory,driver,track)
    if not path.exists():
        return set()
    db = sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True,timeout=60)
    try:
        return set(db.execute("SELECT start,variant FROM results WHERE composition=?",(composition,)))
    except sqlite3.OperationalError as exc:
        if "no such table: results" in str(exc):
            return set()  # A worker is initializing this archive for the first time.
        raise
    finally:
        db.close()


def check_existing(directory, definition):
    count = 0
    for path in sorted(Path(directory).glob("*.sqlite")):
        db = sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True)
        try:
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "results" not in tables:
                continue  # A crash during archive initialization saved no models.
            models = db.execute("SELECT count(*) FROM results").fetchone()[0]
            saved = db.execute("SELECT value FROM metadata WHERE key='definition'").fetchone() if "metadata" in tables else None
            if saved is None and models==0:
                continue
            if saved is None or not definitions_match(json.loads(saved[0]),definition):
                raise ValueError(f"{path.name} belongs to different settings/code/inputs. Use an empty RUNS_DIR.")
            count += models
        finally:
            db.close()
    return count


def resume_definition(directory, definition):
    """Retain the original archive provenance after a vetted runtime-only fix."""
    for path in sorted(Path(directory).glob("*.sqlite")):
        db = sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True)
        try:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata' AND type='table'").fetchone():
                continue
            row = db.execute("SELECT value FROM metadata WHERE key='definition'").fetchone()
            if row is not None:
                saved = json.loads(row[0])
                if not definitions_match(saved,definition):
                    raise ValueError(f"{path.name} belongs to different settings/code/inputs. Use an empty RUNS_DIR.")
                return saved
        finally:
            db.close()
    return definition


def prepare_archives(people, registry, directory, definition, stop=None):
    """Only the coordinator switches journal mode and initializes archives."""
    store = ResultStore(directory,definition,max_connections=1)
    count, total = 0, len(people)*len(registry)
    reported = time.monotonic()
    print(f"Preparing {total} result archives before starting workers...",flush=True)
    try:
        for person in people:
            for track in registry:
                if stop is not None and stop.is_set():
                    return
                store.connection(person,track["name"])
                count += 1
                if time.monotonic()-reported >= 10:
                    print(f"Prepared {count}/{total} archives",flush=True)
                    reported = time.monotonic()
    finally:
        store.close()
    print(f"Prepared {count}/{total} archives; starting workers.",flush=True)


def read_result(path, composition, start, variant):
    """Read a completed model's metadata and all NumPy progress arrays."""
    db = sqlite3.connect(Path(path).resolve().as_uri()+"?mode=ro",uri=True)
    try:
        row = db.execute("SELECT metadata,trajectory FROM results WHERE composition=? AND start=? AND variant=?",
                         (composition,start,variant)).fetchone()
        if row is None:
            raise KeyError((composition,start,variant))
        return json.loads(row[0]),unpack_trajectory(row[1])
    finally:
        db.close()


def checkpoint_results(directory):
    """After workers stop, fold committed WAL pages into the result archives.

    Never delete a WAL directly: it may contain completed model results.
    SQLite performs recovery/checkpointing and removes idle auxiliary files.
    """
    for path in sorted(Path(directory).glob("*.sqlite")):
        db=sqlite3.connect(path,timeout=60)
        closed_archive=False
        try:
            busy,_,_=db.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            if not busy:
                try:
                    # Use ordinary closed archives between invocations. The
                    # next writer enables WAL again for parallel execution.
                    closed_archive=db.execute("PRAGMA journal_mode=DELETE").fetchone()[0]=="delete"
                except sqlite3.OperationalError as exc:
                    if "locked" not in str(exc):
                        raise
        finally:
            db.close()
        if closed_archive:
            # Some SQLite builds retain a stale shared-memory index. After a
            # successful switch out of WAL mode it contains no live data.
            Path(str(path)+"-shm").unlink(missing_ok=True)
