"""SQLite contention and resume compatibility checks using fabricated models."""

from dataclasses import asdict
import json
import hashlib
import multiprocessing
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from experiment.config import Settings
from experiment.design import Composition, digest
from experiment.results import (ResultStore, archive_path, checkpoint_results,
                                check_existing, enable_wal, prepare_archives,
                                resume_definition)
from experiment.runtime_compatibility import (RUNTIME_PATHS, RUNTIME_REVISIONS,
                                            definitions_match)


def fixture_writer(directory, definition, number, barrier):
    store = ResultStore(directory, definition, max_connections=1)
    try:
        barrier.wait(timeout=30)
        car = Composition("P01", (), number + 1)
        arrays = dict(step=np.array([1]), automation_on=np.array([True]))
        for start in range(12):
            for track in ("first", "second"):
                store.save(car, start, "baseline", track, dict(writer=number), arrays)
    finally:
        store.close()


def definition_for(revision):
    value = dict(schema_version=1, parameters=asdict(Settings(steps=1)),
                 participants=["P01"],
                 inputs=dict(code={**dict(zip(RUNTIME_PATHS, revision)),
                                   "experiment/model.py": "fixture-scientific-code"},
                             tracks={"first": "fixture-track"},
                             participant_export="fixture-data",
                             environment={"python": "fixture-python"}))
    value["signature"] = digest(dict(parameters=value["parameters"],
                                     inputs=value["inputs"], participants=value["participants"]))
    return value


class SQLiteRuntimeTests(unittest.TestCase):
    def test_reviewed_revision_matches_current_source(self):
        root = Path(__file__).resolve().parents[2]
        actual = tuple(hashlib.sha256((root/path).read_bytes()).hexdigest()
                       for path in RUNTIME_PATHS)
        self.assertEqual(actual, RUNTIME_REVISIONS[-1])

    def test_journal_transition_retries_actual_read_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"locked.sqlite"
            reader = sqlite3.connect(path)
            reader.execute("CREATE TABLE fixture(value)")
            reader.execute("BEGIN")
            reader.execute("SELECT * FROM fixture").fetchall()
            writer = sqlite3.connect(path, timeout=0)
            try:
                with patch("experiment.results.time.sleep", side_effect=lambda _: reader.rollback()) as retry:
                    enable_wal(writer)
                self.assertGreaterEqual(retry.call_count, 1)
                self.assertEqual(writer.execute("PRAGMA journal_mode").fetchone()[0], "wal")
            finally:
                reader.close()
                writer.close()

    def test_twelve_processes_write_and_resume_without_journal_race(self):
        with tempfile.TemporaryDirectory() as directory:
            definition = dict(parameters={"steps": 1}, signature="fixture-only")
            registry = [dict(name=name) for name in ("first", "second")]
            context = multiprocessing.get_context("spawn")
            environment = {name: "1" for name in
                           ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                            "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS")}
            with patch.dict(os.environ, environment):
                for restart in range(2):
                    prepare_archives(("P01",), registry, directory, definition)
                    barrier = context.Barrier(12)
                    processes = [context.Process(target=fixture_writer,
                                 args=(directory, definition, restart*12+number, barrier))
                                 for number in range(12)]
                    try:
                        for process in processes:
                            process.start()
                        for process in processes:
                            process.join(timeout=30)
                            self.assertEqual(process.exitcode, 0)
                    finally:
                        for process in processes:
                            if process.is_alive():
                                process.terminate()
                                process.join()
                    self.assertEqual(check_existing(directory, definition), (restart+1)*288)
                    checkpoint_results(directory)

    def test_only_reviewed_runtime_revisions_are_compatible(self):
        old, current = map(definition_for, RUNTIME_REVISIONS)
        self.assertTrue(definitions_match(old, current))
        for changed in ("settings", "data", "track", "environment", "code", "model", "signature"):
            value = json.loads(json.dumps(current))
            if changed == "settings":
                value["parameters"]["steps"] = 2
            elif changed == "data":
                value["inputs"]["participant_export"] = "changed"
            elif changed == "track":
                value["inputs"]["tracks"]["first"] = "changed"
            elif changed == "environment":
                value["inputs"]["environment"]["python"] = "changed"
            elif changed == "code":
                value["inputs"]["code"][RUNTIME_PATHS[0]] = "unreviewed"
            elif changed == "model":
                value["inputs"]["code"]["experiment/model.py"] = "changed"
            value["signature"] = digest(dict(parameters=value["parameters"],
                                             inputs=value["inputs"], participants=value["participants"]))
            if changed == "signature":
                value["signature"] = "invalid"
            self.assertFalse(definitions_match(old, value), changed)

    def test_resume_retains_original_definition_and_accepts_new_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            old, current = map(definition_for, RUNTIME_REVISIONS)
            store = ResultStore(directory, old)
            arrays = dict(step=np.array([1]), automation_on=np.array([True]))
            car = Composition("P01", (), 0)
            store.save(car, 0, "baseline", "first", {}, arrays)
            store.close()
            self.assertEqual(check_existing(directory, current), 1)
            original = resume_definition(directory, current)
            self.assertEqual(original, json.loads(json.dumps(old)))
            store = ResultStore(directory, current)
            store.save(car, 1, "baseline", "first", {}, arrays)
            store.close()
            db = sqlite3.connect(archive_path(directory, "P01", "first"))
            try:
                saved = json.loads(db.execute("SELECT value FROM metadata WHERE key='definition'").fetchone()[0])
                self.assertEqual(saved, original)
            finally:
                db.close()
            self.assertEqual(check_existing(directory, current), 2)


if __name__ == "__main__":
    unittest.main()
