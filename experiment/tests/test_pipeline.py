"""No participant simulations or shared-track generation are run by these tests."""

from dataclasses import asdict,replace
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

import numpy as np

from experiment.config import Settings
from experiment.design import Composition,compositions,initial_state,personal_starts,total_runs
from experiment.results import ResultStore,archive_path,check_existing,completed,read_result,checkpoint_results
from experiment.runner import StopWhenParentExits,keep_awake,run_metadata,tasks,worker_task
from experiment.analysis.compare_modes import extract
from experiment.analysis.common import similarity
from experiment.tracks.generate_tracks import generate,load_tracks,track_specs
from av_social_trust.situation import Situation


class PipelineTests(unittest.TestCase):
    def test_each_difficulty_uses_three_persistence_levels(self):
        settings=Settings(steps=10,track_replicates=1)
        directory=Path(self.temp.name)/"tracks"
        class FixtureGenerator:
            def __init__(self,**kwargs):
                self.probability=kwargs["task_complexity_probability"]
            def generate_series(self,steps):
                count=round(self.probability*steps)
                return [Situation(int(i<count),True) for i in range(steps)]
        with patch("experiment.tracks.generate_tracks.SituationGenerator",side_effect=FixtureGenerator) as generator:
            manifest=generate(settings,directory)
        self.assertEqual(len(manifest["tracks"]),9)
        self.assertEqual([call.kwargs["task_complexity_persistence"] for call in generator.call_args_list],
                         [0.3,0.6,0.9]*3)
        registry,tracks=load_tracks(settings,directory)
        for difficulty,_ in settings.track_difficulties:
            self.assertEqual([t["persistence"] for t in registry if t["difficulty"]==difficulty],[0.3,0.6,0.9])
        self.assertEqual(len(tracks),9)
        repeated=replace(settings,track_replicates=2)
        with patch("experiment.tracks.generate_tracks.SituationGenerator",side_effect=FixtureGenerator):
            manifest=generate(repeated,directory)
        registry,tracks=load_tracks(repeated,directory)
        self.assertEqual(len(tracks),18)
        self.assertEqual(len({t["base_seed"] for t in registry}),18)
        self.assertEqual(len(list(track_specs(repeated))),18)
        self.assertEqual(total_runs(tuple(f"P{i:02d}" for i in range(1,27)),repeated),18544032)
        with self.assertRaisesRegex(ValueError,"at least one persistence"):
            Settings(track_persistences=())

    def test_worker_task_requires_initialization(self):
        with patch("experiment.runner.WORKER",None):
            with self.assertRaisesRegex(RuntimeError,"Worker has not been initialized"):
                worker_task(None)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="experiment_checks_")
        self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name)/"runs"
        self.settings=Settings(steps=4,cognitive_starts=1,social_starts=2,track_replicates=1,track_persistences=(0.3,))
        self.definition=dict(parameters=asdict(self.settings),signature="fixture-only")
        self.track=dict(name="low_0",code=0,difficulty="low",replicate=0,persistence=0.3,mean_complexity=0.25,complexity_switches=1)

    def fixture(self,composition,start,variant,on):
        bank=personal_starts(("P01","P02"),self.settings)
        initial=initial_state(composition,start,self.settings,bank)
        n=len(initial["agents"])
        arrays=dict(step=np.arange(1,5),automation_on=np.array(on,dtype=bool),
                    clipped=np.zeros((4,n,3),dtype=bool),initial_cognition=initial["cognition"],
                    initial_trust=initial["trust"])
        metadata=run_metadata(composition,self.track,start,variant,initial,self.settings,arrays)
        return metadata,arrays

    def test_default_design_is_balanced_and_has_expected_count(self):
        people=tuple(f"P{i:02d}" for i in range(1,27))
        settings=Settings()
        selected=list(compositions(people,settings))
        self.assertEqual(len(selected),21450)
        self.assertEqual(len(set(selected)),21450)
        self.assertEqual(total_runs(people,settings),9272016)
        for person in people:
            counts={size:sum(c.driver==person and len(c.passengers)==size for c in selected) for size in range(1,6)}
            self.assertEqual(counts,{1:25,2:200,3:200,4:200,5:200})

    def test_cognition_shared_across_social_starts_and_roles(self):
        settings=Settings()
        bank=personal_starts(("P01","P02"),settings)
        for i in range(0,settings.starts,2):
            self.assertEqual(bank["P01"][i]["cognition"],bank["P01"][i+1]["cognition"])
        self.assertEqual(sorted(v["self_trust"] for v in bank["P01"]),sorted(settings.trust_values*4))
        solo=initial_state(Composition("P01",(),0),0,settings,bank)
        car=initial_state(Composition("P01",("P02",),1),0,settings,bank)
        np.testing.assert_array_equal(solo["cognition"][0],car["cognition"][0])
        self.assertEqual(solo["trust"][0,0],car["trust"][0,0])
        other=personal_starts(("P01",),replace(settings,social_starts=3))
        for i in range(settings.cognitive_starts):
            self.assertEqual(bank["P01"][i*2]["cognition"],other["P01"][i*3]["cognition"])

    def test_unfinished_models_are_rejected_and_no_partial_files_exist(self):
        store=ResultStore(self.directory,self.definition)
        self.addCleanup(store.close)
        car=Composition("P01",("P02",),1)
        meta,arrays=self.fixture(car,0,"decision",[0,1,0,1])
        arrays["step"]=np.arange(1,4)
        with self.assertRaisesRegex(ValueError,"unfinished"):
            store.save(car,0,"decision","low_0",meta,arrays)
        self.assertFalse(self.directory.exists())

    def test_restart_skips_complete_models_and_failed_transaction_rolls_back(self):
        car=Composition("P01",("P02",),1)
        meta,arrays=self.fixture(car,0,"decision",[0,1,0,1])
        store=ResultStore(self.directory,self.definition)
        self.assertTrue(store.save(car,0,"decision","low_0",meta,arrays))
        db=store.connection("P01","low_0")
        with self.assertRaises(RuntimeError):
            with db:
                db.execute("INSERT INTO results SELECT composition,1,variant,metadata,automation_on,trajectory FROM results")
                raise RuntimeError("interrupted before commit")
        store.close()
        store=ResultStore(self.directory,self.definition)
        self.addCleanup(store.close)
        self.assertFalse(store.save(car,0,"decision","low_0",meta,arrays))
        self.assertEqual(completed(self.directory,"P01","low_0",1),{(0,"decision")})
        self.assertEqual(check_existing(self.directory,self.definition),1)
        loaded_meta,loaded=read_result(archive_path(self.directory,"P01","low_0"),1,0,"decision")
        self.assertEqual(loaded_meta,meta)
        for key in arrays:
            np.testing.assert_array_equal(loaded[key],arrays[key])
        store.close()
        checkpoint_results(self.directory)
        self.assertEqual(list(self.directory.iterdir()),[archive_path(self.directory,"P01","low_0")])

    def test_modified_config_is_rejected(self):
        store=ResultStore(self.directory,self.definition)
        car=Composition("P01",(),0)
        meta,arrays=self.fixture(car,0,"baseline",[0,0,0,0])
        store.save(car,0,"baseline","low_0",meta,arrays)
        store.close()
        with self.assertRaisesRegex(ValueError,"different"):
            check_existing(self.directory,dict(self.definition,signature="changed"))

    def test_pairs_extract_once_with_matching_baselines(self):
        store=ResultStore(self.directory,self.definition)
        solo,car=Composition("P01",(),0),Composition("P01",("P02",),1)
        for composition,variant,on in ((solo,"baseline",[0,1,0,1]),(car,"decision",[1,1,0,0]),(car,"cognition",[1,1,1,1])):
            meta,arrays=self.fixture(composition,0,variant,on)
            store.save(composition,0,variant,"low_0",meta,arrays)
        store.close()
        output=Path(self.temp.name)/"analysis"
        self.assertEqual(extract(self.directory,output),(1,1))
        self.assertEqual(extract(self.directory,output),(0,1))
        with sqlite3.connect(output/"comparisons.sqlite") as db:
            metrics=json.loads(db.execute("SELECT metrics FROM comparisons").fetchone()[0])
        self.assertEqual(metrics["decision_vs_baseline"]["mismatch_cycles"],2)
        self.assertEqual(metrics["cognition_vs_baseline"]["switched_on"],2)

    def test_planner_keeps_only_missing_models(self):
        people=("P01","P02")
        store=ResultStore(self.directory,self.definition)
        car=Composition("P01",("P02",),1)
        meta,arrays=self.fixture(car,0,"decision",[0,1,0,1])
        store.save(car,0,"decision","low_0",meta,arrays)
        store.close()
        pending=list(tasks(people,self.settings,[self.track],self.directory,False))
        p01=[item for composition,track,items in pending if composition.driver=="P01" for item in items]
        self.assertNotIn((0,"decision"),p01)
        self.assertIn((0,"cognition"),p01)
        self.assertEqual(len(p01),3)

    def test_stop_detects_parent_exit_and_caffeinate_is_not_cli_dependent(self):
        event=threading.Event()
        with patch("experiment.runner.os.getppid",return_value=123):
            stop=StopWhenParentExits(event)
            self.assertFalse(stop.is_set())
        with patch("experiment.runner.os.getppid",return_value=1):
            self.assertTrue(stop.is_set())
            self.assertTrue(StopWhenParentExits(event,parent=123).is_set())
        with patch("experiment.runner.sys.platform","darwin"),patch("experiment.runner.subprocess.Popen") as popen:
            with keep_awake(True):
                self.assertEqual(popen.call_args[0][0][:3],["caffeinate","-i","-w"])
            popen.return_value.terminate.assert_called_once()
            popen.return_value.wait.assert_called_once()

    def test_all_off_is_not_automation_engagement_agreement(self):
        metrics=similarity([0,0],[0,0])
        self.assertEqual(metrics["agreement"],1)
        self.assertIsNone(metrics["on_jaccard"])


if __name__=="__main__":
    unittest.main()
