"""Analysis metrics, incremental extraction and generated reports on fixtures."""

from contextlib import redirect_stdout
import io
import json
import sqlite3
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from experiment.analysis.compare_modes.run import extract
from experiment.analysis.baseline_quality.run import run as baseline_quality
from experiment.analysis.inventory.run import run as inventory
from experiment.analysis.social_importance.run import run as social_importance
from experiment.analysis.shared.common import report
from experiment.analysis.shared.metrics import similarities, similarity
from experiment.analysis.shared.output import START, write_results
from experiment.design import Composition
from experiment.results import ResultStore
from experiment.tests import test_pipeline as pipeline


class AnalysisOutputTests(unittest.TestCase):
    def setUp(self):
        self.fixture = pipeline.PipelineTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.output = Path(self.fixture.temp.name)/"compare_modes"/"results"

    def save_models(self):
        store = ResultStore(self.fixture.directory,self.fixture.definition)
        try:
            solo,car = Composition("P01",(),0),Composition("P01",("P02",),1)
            for composition,variant,on in ((solo,"baseline",[0,1,0,1]),
                                          (car,"decision",[0,1,0,0]),
                                          (car,"cognition",[1,1,0,1])):
                metadata,arrays = self.fixture.fixture(composition,0,variant,on)
                store.save(composition,0,variant,"low_0",metadata,arrays)
        finally:
            store.close()

    def test_batched_metrics_equal_scalar_metrics_including_edge_cases(self):
        random = np.random.default_rng(178)
        for steps in (1,4,20,21,100,128):
            left = random.integers(0,2,(100,steps)).astype(bool)
            right = random.integers(0,2,(100,steps)).astype(bool)
            left[:3] = False
            right[:2] = False
            left[3:6] = True
            right[3:5] = True
            self.assertEqual(similarities(left,right),[similarity(a,b) for a,b in zip(left,right)])

    def test_readme_section_replaces_results_and_preserves_authored_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)/"question"
            folder.mkdir()
            readme = folder/"README.md"
            readme.write_text("# My question\n\nHuman-authored explanation.\n")
            write_results("question",{"n":1},"One result",folder/"results")
            write_results("question",{"n":2},"Two results",folder/"results")
            text = readme.read_text()
            self.assertIn("Human-authored explanation.",text)
            self.assertEqual(text.count(START),1)
            self.assertNotIn("One result",text)
            self.assertIn("Two results",text)
            self.assertEqual(json.loads((folder/"results"/"summary.json").read_text()),{"n":2})

    def test_extraction_reports_progress_and_resumes_without_recalculating(self):
        self.save_models()
        terminal = io.StringIO()
        with redirect_stdout(terminal):
            self.assertEqual(extract(self.fixture.directory,self.output),(1,1))
            with patch("experiment.analysis.shared.metrics.comparison_batch",side_effect=AssertionError("cached pair recalculated")):
                self.assertEqual(extract(self.fixture.directory,self.output),(0,1))
        self.assertIn("Checking missing pairs",terminal.getvalue())
        self.assertIn("[1/1]",terminal.getvalue())
        result = json.loads((self.output/"summary.json").read_text())
        self.assertEqual(result["status"],"complete")
        self.assertEqual(result["cached_comparisons"],1)
        self.assertEqual(result["new_comparisons"],0)
        db=sqlite3.connect(self.output/"comparisons.sqlite")
        try:
            saved=json.loads(db.execute("SELECT metrics FROM comparisons").fetchone()[0])
        finally:
            db.close()
        self.assertEqual(saved["decision_vs_cognition"],similarity([1,1,0,1],[0,1,0,0]))

    def test_question_outputs_are_separate_and_readable(self):
        self.save_models()
        extract(self.fixture.directory,self.output)
        root = Path(self.fixture.temp.name)
        baseline = root/"baseline_quality"/"results"
        result = baseline_quality(self.fixture.directory,baseline)
        self.assertEqual(result["totals"]["baselines"],1)
        self.assertTrue((baseline/"figures"/"baseline_regimes.png").exists())
        self.assertIn("Always automated",(baseline.parent/"README.md").read_text())
        inventory_output = root/"inventory"/"results"
        self.assertEqual(inventory(self.fixture.directory,inventory_output)["completed_models"],3)
        grouped = root/"passenger_count_effects"/"results"
        result = report("passenger_count_effects",{"passenger_count":None},directory=self.output,output=grouped)
        self.assertEqual(result["comparison_rows"],1)
        self.assertEqual(len((grouped/"groups.jsonl").read_text().splitlines()),1)
        social = root/"social_importance"/"results"
        self.assertEqual(social_importance(self.output,social)["comparison_rows"],1)
        for folder in (baseline,inventory_output,grouped,social):
            self.assertTrue((folder/"summary.json").exists())
            self.assertTrue((folder/"summary.md").exists())
            self.assertIn(START,(folder.parent/"README.md").read_text())

    def test_interrupt_propagates_to_the_sequence_and_cache_can_resume(self):
        self.save_models()
        with patch("experiment.analysis.shared.metrics.comparison_batch",side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                extract(self.fixture.directory,self.output)
        result=json.loads((self.output/"summary.json").read_text())
        self.assertEqual(result["status"],"interrupted")
        self.assertEqual(extract(self.fixture.directory,self.output),(1,1))


if __name__ == "__main__":
    unittest.main()
