"""Social-layer analysis: pressure measures, composition decoding and reports on synthetic tables."""

from dataclasses import replace
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from av_social_trust.situation import Situation
from experiment.config import Settings
from experiment.design import Composition,compositions,initial_state,personal_starts
from experiment.model import run_model,tree_decision
from experiment.analysis.shared.stats import variance_shares
from experiment.analysis.shared.table import cognitive_pull,disagreement,passengers,tree_predict
from experiment.analysis.occupant_disagreement.run import run as occupant_disagreement
from experiment.analysis.pressure_conversion.run import run as pressure_conversion
from experiment.analysis.influence_timing.run import run as influence_timing
from experiment.analysis.participant_susceptibility.run import summarize as participants_summary
from experiment.analysis.when_social_matters.run import run as when_social_matters
from experiment.analysis.example_cases.run import choose
from experiment.analysis.example_cases.plot import render as draw_cases
from experiment.analysis.shared.output import write_results
from experiment.analysis.shared import rules
from experiment.analysis.baseline_similarity.run import categories,run as baseline_similarity


def leaf(label):
    return {"class":label,"probability":[1.-label,float(label)]}


def person(threshold, feature=0):
    return dict(state_indices=np.arange(3),A=0.9*np.eye(3),B=np.full(3,0.05),c=np.full(3,0.04),class_names=[0,1],
                tree=dict(feature_index=feature,threshold=threshold,left=leaf(0),right=leaf(1)))


def synthetic_table(rows=600, seed=3):
    random = np.random.default_rng(seed)
    count = random.integers(1,6,rows)
    table = dict(driver=random.integers(0,3,rows),track=random.integers(0,2,rows),composition=np.arange(rows),
                 start=random.integers(0,2,rows),track_difficulty=random.integers(0,3,rows),passenger_count=count,
                 track_persistence=random.choice([0.3,0.6,0.9],rows))
    for name in ("driver_self_trust","driver_automation_trust","driver_perceived_risk","driver_workload",
                 "driver_initial_self_weight","inbound_trust_mean","outbound_trust_mean","alpha_inbound_mean",
                 "alpha_outbound_mean","passenger_automation_trust_mean","passenger_self_trust_mean","solo_opposition_share",
                 "passenger_solo_automation"):
        table[name] = random.random(rows)
    table["baseline_automation_fraction"] = random.choice([0.,0.3,1.],rows)
    for name in ("solo_disagreement","solo_outvoted","solo_cognitive_pull"):
        table[f"{name}_cycles"] = random.integers(0,100,rows)
    for name in ("solo_outvoted","solo_cognitive_pull"):
        table[f"{name}_early_cycles"] = np.minimum(table[f"{name}_cycles"],random.integers(0,21,rows))
    for name in ("solo_unanimous_disagreement_cycles","solo_outvoted_off_cycles","solo_outvoted_on_cycles","driver_solo_switches"):
        table[name] = random.integers(0,50,rows)
    for mode in ("decision","cognition","cross"):
        table[f"{mode}_mismatch_cycles"] = random.integers(0,100,rows)
        for name in ("switched_on","switched_off"):
            table[f"{mode}_{name}"] = random.integers(0,50,rows)
        table[f"{mode}_delta_automation_fraction"] = random.random(rows)-0.5
        table[f"{mode}_early_agreement"] = random.random(rows)
        table[f"{mode}_late_agreement"] = random.random(rows)
        first = random.integers(1,101,rows).astype(float)
        first[table[f"{mode}_mismatch_cycles"]==0] = np.nan
        table[f"{mode}_first_divergence_cycle"] = first
    seats = np.full((rows,5),-1,dtype=np.int8)
    for i,k in enumerate(count):
        seats[i,:k] = random.choice(3,k)
    table["passenger_seats"] = seats
    table["_drivers"],table["_tracks"] = ["P01","P02","P03"],["low_0","high_0"]
    return table


class SocialLayerTests(unittest.TestCase):
    def test_composition_identifiers_decode_to_their_passengers(self):
        people = tuple(f"P{i:02d}" for i in range(1,8))
        settings = Settings(passenger_combinations=(3,4,4,4,4))
        for composition in compositions(people,settings):
            self.assertEqual(passengers(list(people),composition.driver,composition.identifier),composition.passengers)

    def test_equal_weight_vote_counts_ties_as_manual(self):
        driver = np.array([[1,1,0,0,1]],dtype=bool)
        seats = np.array([[[0,1,1,0,1],[1,1,1,1,0]]],dtype=bool)
        counts = disagreement(driver,seats,np.array([[True,True]]))
        # Opposed per cycle: 1,0,2,1,1 of three voters, so cycle 3 is outvoted; ties are impossible.
        self.assertEqual(counts["solo_disagreement_cycles"][0],4)
        self.assertEqual(counts["solo_outvoted_cycles"][0],1)
        self.assertEqual(counts["solo_unanimous_disagreement_cycles"][0],1)
        one = disagreement(np.array([[1,0]],dtype=bool),np.array([[[0,1]]],dtype=bool),np.array([[True]]))
        # Two voters split 1–1: the zero opinion is manual, which only overrules an automated driver.
        self.assertEqual(one["solo_outvoted_cycles"][0],1)
        self.assertEqual(one["solo_outvoted_off_cycles"][0],1)

    def test_vectorized_tree_and_cognitive_pull_match_the_model(self):
        tree = dict(feature_index=1,threshold=0.4,left=leaf(0),
                    right=dict(feature_index=0,threshold=0.7,left=leaf(1),right=leaf(0)))
        states = np.random.default_rng(1).random((50,3))
        expected = [tree_decision(dict(tree=tree,class_names=[0,1]),state)[0] for state in states]
        np.testing.assert_array_equal(tree_predict(tree,states),np.array(expected,dtype=bool))
        driver_states = np.array([[[0.2,0,0],[0.9,0,0]]])
        passenger_states = np.array([[[[0.9,0,0],[0.1,0,0]]]])
        solo = tree_predict(person(0.5)["tree"],driver_states)
        pulled = cognitive_pull([person(0.5)["tree"]],np.array([0]),solo,driver_states,passenger_states,np.array([[True]]))
        np.testing.assert_array_equal(pulled,[[True,False]])  # Means 0.55 and 0.5 sit on the right of 0.5.

    def test_decision_votes_equal_solo_runs_and_changes_need_disagreement(self):
        settings = replace(Settings(steps=30,cognitive_starts=1,social_starts=2),discussion_rounds=1)
        people = ("P01","P02","P03")
        models = {"P01":person(0.5),"P02":person(0.45,1),"P03":person(0.6,2)}
        situations = [Situation(int(i%7<3),True) for i in range(settings.steps)]
        bank = personal_starts(people,settings)
        for start in range(settings.starts):
            solo = {p:run_model(initial_state(Composition(p,(),0),start,settings,bank),models,settings,"baseline",situations)
                    for p in people}
            car = run_model(initial_state(Composition("P01",("P02","P03"),1),start,settings,bank),models,settings,"decision",situations)
            for seat,p in enumerate(people):
                np.testing.assert_array_equal(car["private_decisions"][:,seat],solo[p]["automation_on"])
            driver = solo["P01"]["automation_on"]
            others = np.stack([solo["P02"]["automation_on"],solo["P03"]["automation_on"]])[None]
            counts = disagreement(driver[None],others,np.ones((1,2),dtype=bool))
            self.assertLessEqual(int(np.count_nonzero(car["automation_on"]!=driver)),counts["solo_disagreement_cycles"][0])

    def test_variance_shares_isolate_the_informative_input(self):
        random = np.random.default_rng(5)
        table = dict(useful=random.random(4000),noise=random.random(4000))
        table["y"] = 3*table["useful"]+0.1*random.standard_normal(4000)
        shares = variance_shares(table,"y",("useful","noise"),chunk=700)
        self.assertGreater(shares["r2"],0.95)
        self.assertGreater(shares["unique"]["useful"],0.9)
        self.assertLess(shares["unique"]["noise"],0.01)

    def test_questions_write_results_figures_and_readmes(self):
        table = synthetic_table()
        cycles = {name:np.random.default_rng(2).random((3,100)) for name in
                  ("decision_change","cognition_change","outvoted","cognitive_pull")}
        cycles["cars"] = np.array([10,10,10])
        sample = (cycles,dict(per_archive=1,seed=0,cars=30))
        with tempfile.TemporaryDirectory() as temporary, \
                patch("experiment.analysis.influence_timing.run.cycle_profiles",return_value=sample):
            for name,question in (("occupant_disagreement",occupant_disagreement),("pressure_conversion",pressure_conversion),
                                  ("influence_timing",influence_timing),("when_social_matters",when_social_matters)):
                output = Path(temporary)/name/"results"
                with patch(f"experiment.analysis.{name}.run.load",return_value=table):
                    result = question(output=output)
                self.assertEqual(result["comparison_rows"],len(table["driver"]))
                self.assertTrue((output/"summary.json").exists())
                self.assertTrue(any((output/"figures").glob("*.png")))
                self.assertTrue(any((output/"figures").glob("*.pdf")))
                self.assertIn("Latest results",(output.parent/"README.md").read_text())
                # plot.py redraws from the saved results alone.
                for figure in (output/"figures").iterdir():
                    figure.unlink()
                __import__(f"experiment.analysis.{name}.plot",fromlist=["render"]).render(output)
                self.assertTrue(any((output/"figures").glob("*.png")))
        models = {p:person(0.5) for p in table["_drivers"]}
        summary = participants_summary(table,models)
        self.assertEqual(summary["participants"],3)
        self.assertEqual(sum(row["cars_as_driver"] for row in summary["rows"]),len(table["driver"]))

    def test_rule_tree_recovers_a_two_feature_rule(self):
        random = np.random.default_rng(8)
        features = dict(a=random.random(20000),b=random.random(20000),noise=random.random(20000))
        y = (features["a"]>=0.3).astype(int)*2+(features["b"]>=0.6).astype(int)
        tree = rules.fit(features,y,["low a, low b","low a, high b","high a, low b","high a, high b"],depth=2)
        self.assertGreater(np.mean(rules.predict(tree,features)==y),0.97)
        self.assertEqual({tree["root"]["feature"],tree["root"]["left"]["feature"]},{"a","b"})
        self.assertEqual(len(rules.leaves(tree)),4)

    def test_baseline_similarity_categories_dataset_and_figures(self):
        np.testing.assert_array_equal(categories(np.array([0,5,6,9]),np.array([5,9,0,6])),[0,1,2,3])
        table = synthetic_table()
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)/"baseline_similarity"/"results"
            with patch("experiment.analysis.baseline_similarity.run.load",return_value=table):
                result = baseline_similarity(output=output)
            self.assertAlmostEqual(sum(result["overall"][c] for c in result["categories"]),1.0)
            import gzip
            with gzip.open(output/"similarity_dataset.csv.gz","rt") as stream:
                lines = stream.read().splitlines()
            self.assertEqual(len(lines),len(table["driver"])+1)
            self.assertEqual(lines[0].split(","),result["dataset"]["columns"])
            for figure in (output/"figures").iterdir():
                figure.unlink()
            __import__("experiment.analysis.baseline_similarity.plot",fromlist=["render"]).render(output)
            self.assertEqual(len(list((output/"figures").glob("*.pdf"))),5)

    def test_example_cases_choose_agreeing_and_diverging_cars_and_draw_them(self):
        table = synthetic_table()
        table["baseline_automation_fraction"][:] = 0.5
        table["driver_solo_switches"][:] = 6
        table["passenger_count"][:] = 5
        table["solo_disagreement_cycles"][:] = 30
        table["driver"][:],table["track"][:] = 1,0
        for mode,(agree,diverge) in dict(decision=(0,40),cognition=(1,50),cross=(0,45)).items():
            table[f"{mode}_mismatch_cycles"][:] = 20
            table[f"{mode}_mismatch_cycles"][7] = agree
            table[f"{mode}_mismatch_cycles"][9] = diverge
        self.assertEqual(choose(table),dict(agree=7,disagree=9))
        random = np.random.default_rng(4)
        arrays,cases = {},{}
        for label in ("agree","disagree"):
            cases[label] = dict(driver="P02",passengers=["P01","P03"],track="low_0",composition=1,start=0,
                                modeled_states=["automation_trust"],tree_splits=[["automation_trust",0.5]],
                                changed_cycles=dict(decision_vs_solo=1,cognition_vs_solo=2,decision_vs_cognition=1),
                                outvoted_cycles=3,cognitive_pull_cycles=4,solo_disagreement_cycles=5)
            arrays.update({f"{label}__complexity":random.integers(0,2,100),
                           **{f"{label}__{name}":random.random(100)>0.5 for name in ("solo_on","decision_on","cognition_on")},
                           f"{label}__solo_cognition":random.random((100,3)),f"{label}__cognition_cognition":random.random((100,3)),
                           f"{label}__decision_opinion":random.random(100)*2-1,
                           f"{label}__passenger_solo_on":random.random((2,100))>0.5})
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)/"example_cases"/"results"
            write_results("example_cases",dict(selection="automatic",cases=cases),"Cases",output=output)
            np.savez_compressed(output/"cases.npz",**arrays)
            draw_cases(output)
            self.assertTrue((output/"figures"/"example_cases.pdf").exists())


if __name__ == "__main__":
    unittest.main()
