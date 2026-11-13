"""Numeric comparison columns plus the occupants' solo disagreement, cached once.

Decision influence leaves every occupant's cognition unchanged, so each private
vote in a decision model equals that person's solo baseline at the same track and
start. The solo-disagreement columns therefore describe exactly which votes the
driver hears in decision mode, and how differently the occupants would act alone
in cognition mode.

Two equal-weight counterfactuals summarize the pressure each mode can exert:
an unweighted vote of all occupants' solo choices (ties are manual, as in the
model), and the driver's own tree applied to the mean of all occupants' solo
cognitive states. Both ignore trust weights and feedback; comparing them with
the simulated changes shows how much the dynamics add or remove.
"""

from math import comb
from pathlib import Path
import sqlite3
import time

import numpy as np

from experiment.config import RUNS_DIR
from experiment.participants import load_participants
from experiment.design import unrank
from experiment.analysis.shared.output import comparison_directory
from experiment.results import unpack_trajectory

TABLE_VERSION = 3
EARLY_CYCLES = 20  # Matches metrics.similarity()'s early window.
DIFFICULTIES = ("low","normal","high")
FEATURES = ("track_persistence","passenger_count","driver_self_trust","driver_automation_trust",
            "driver_perceived_risk","driver_workload","driver_initial_self_weight","inbound_trust_mean",
            "outbound_trust_mean","alpha_inbound_mean","alpha_outbound_mean",
            "passenger_automation_trust_mean","passenger_self_trust_mean")
PAIRS = dict(decision="decision_vs_baseline",cognition="cognition_vs_baseline",cross="decision_vs_cognition")
PAIR_METRICS = ("mismatch_cycles","switched_on","switched_off","delta_automation_fraction",
                "early_agreement","late_agreement","first_divergence_cycle")
MISSING = -1.0


def column_paths():
    columns = {"track_difficulty":None}
    columns.update({name:f"$.{name}" for name in FEATURES})
    metrics = {"baseline_automation_fraction":"$.baseline_automation_fraction"}
    for short,pair in PAIRS.items():
        metrics.update({f"{short}_{name}":f"$.{pair}.{name}" for name in PAIR_METRICS})
    return columns,metrics


def people_order(drivers):
    return sorted(drivers,key=lambda person:int(person[1:]))


def passengers(people, driver, identifier):
    """Invert design.compositions(): identifiers enumerate every size-ranked combination."""
    pool = tuple(person for person in people if person!=driver)
    first = 1
    for size in range(1,len(pool)+1):
        count = comb(len(pool),size)
        if identifier<first+count:
            return unrank(pool,size,identifier-first)
        first += count
    raise IndexError(f"Composition {identifier} is outside {driver}'s combinations")


def solo_runs(runs, people, tracks, starts, steps):
    """Solo decisions (person, track, start, cycle) and private cognition (..., cycle, state)."""
    solo = np.zeros((len(people),len(tracks),starts,steps),dtype=bool)
    cognition = np.zeros((*solo.shape,3),dtype=np.float64)
    found = np.zeros(solo.shape[:3],dtype=bool)
    for p,person in enumerate(people):
        for t,track in enumerate(tracks):
            path = Path(runs)/f"{person}_{track}.sqlite"
            if not path.exists():
                continue
            db = sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True)
            try:
                for start,blob,trajectory in db.execute(
                        "SELECT start,automation_on,trajectory FROM results WHERE composition=0 AND variant='baseline'"):
                    if start<starts:
                        solo[p,t,start] = np.unpackbits(np.frombuffer(blob,dtype=np.uint8))[:steps].astype(bool)
                        cognition[p,t,start] = unpack_trajectory(trajectory)["private_cognition"][:steps,0,:]
                        found[p,t,start] = True
            finally:
                db.close()
    return solo,cognition,found


def tree_predict(node, states):
    """Vectorized model.tree_decision(): automation choices for states of shape (..., 3)."""
    if "feature_index" not in node:
        return np.full(states.shape[:-1],bool(int(node["class"])))
    left = states[...,node["feature_index"]]<node["threshold"]
    return np.where(left,tree_predict(node["left"],states),tree_predict(node["right"],states))


def opposition(driver_solo, passenger_solo, valid):
    """Per cycle: how many passengers would decide differently, and whether an equal-weight vote overrules the driver."""
    opposed = ((passenger_solo!=driver_solo[:,None,:])&valid[:,:,None]).sum(axis=1)
    voters = valid.sum(axis=1)[:,None]+1
    # Equal-weight vote of the whole car; a tie gives zero opinion, which is manual.
    return opposed,(2*opposed>voters)|((2*opposed==voters)&driver_solo)


def disagreement(driver_solo, passenger_solo, valid):
    """Count cycles by how many passengers would decide differently from the driver alone.

    driver_solo has shape (rows, cycles); passenger_solo (rows, seats, cycles);
    valid (rows, seats) marks occupied seats.
    """
    opposed,outvoted = opposition(driver_solo,passenger_solo,valid)
    seats = valid.sum(axis=1)[:,None]
    any_opposed = opposed>0
    on = driver_solo
    return dict(solo_disagreement_cycles=any_opposed.sum(axis=1),
                solo_outvoted_cycles=outvoted.sum(axis=1),
                solo_outvoted_early_cycles=outvoted[:,:EARLY_CYCLES].sum(axis=1),
                solo_unanimous_disagreement_cycles=(opposed==seats).sum(axis=1),
                solo_opposition_share=(opposed/seats).mean(axis=1),
                solo_pull_off_cycles=(any_opposed&on).sum(axis=1),
                solo_pull_on_cycles=(any_opposed&~on).sum(axis=1),
                solo_outvoted_off_cycles=(outvoted&on).sum(axis=1),
                solo_outvoted_on_cycles=(outvoted&~on).sum(axis=1),
                passenger_solo_automation=np.where(valid[:,:,None],passenger_solo,False).sum(axis=(1,2))/(seats[:,0]*on.shape[1]),
                driver_solo_switches=(on[:,1:]!=on[:,:-1]).sum(axis=1))


def cognitive_pull(trees, driver, driver_solo, driver_cognition, passenger_cognition, valid):
    """Per cycle: does the driver's tree flip on the equal-weight mean of the occupants' solo states?"""
    total = driver_cognition+np.where(valid[:,:,None,None],passenger_cognition,0).sum(axis=1)
    mean = total/(valid.sum(axis=1)+1)[:,None,None]
    pulled = np.zeros(driver_solo.shape,dtype=bool)
    for person in np.unique(driver):
        rows = driver==person
        pulled[rows] = tree_predict(trees[person],mean[rows])!=driver_solo[rows]
    return pulled


def cache_key(cache):
    parts = [str(TABLE_VERSION)]
    for path in (cache,Path(f"{cache}-wal")):
        if path.exists():
            stat = path.stat()
            parts.append(f"{path.name}:{stat.st_size}:{stat.st_mtime_ns}")
    return "|".join(parts)


def build(cache, runs, steps):
    columns,metrics = column_paths()
    db = sqlite3.connect(cache.resolve().as_uri()+"?mode=ro",uri=True)
    try:
        tracks = sorted(row[0] for row in db.execute("SELECT DISTINCT track FROM comparisons"))
        drivers = people_order(row[0] for row in db.execute("SELECT DISTINCT driver FROM comparisons"))
        total = db.execute("SELECT count(*) FROM comparisons").fetchone()[0]
        driver_case = "CASE driver "+" ".join(f"WHEN '{d}' THEN {i}" for i,d in enumerate(drivers))+" END"
        track_case = "CASE track "+" ".join(f"WHEN '{t}' THEN {i}" for i,t in enumerate(tracks))+" END"
        difficulty_case = ("CASE json_extract(features,'$.track_difficulty') "
                           +" ".join(f"WHEN '{d}' THEN {i}" for i,d in enumerate(DIFFICULTIES))+" END")
        selected = [driver_case,track_case,"composition","start",difficulty_case]
        selected += [f"json_extract(features,'{path}')" for name,path in columns.items() if path]
        selected += [f"ifnull(json_extract(metrics,'{path}'),{MISSING})" for path in metrics.values()]
        names = ["driver","track","composition","start",*columns,*metrics]
        print(f"Building the analysis table from {total:,} comparisons (once per cache update)...",flush=True)
        blocks,read,reported = [],0,time.monotonic()
        cursor = db.execute(f"SELECT {','.join(selected)} FROM comparisons")
        while rows := cursor.fetchmany(250_000):
            blocks.append(np.array(rows,dtype=np.float64))
            read += len(rows)
            if time.monotonic()-reported>=5:
                print(f"  Read {read:,}/{total:,} comparisons",flush=True)
                reported = time.monotonic()
    finally:
        db.close()
    data = np.concatenate(blocks) if blocks else np.zeros((0,len(names)))
    table = {name:data[:,i] for i,name in enumerate(names)}
    for name in metrics:
        if name.endswith(("first_divergence_cycle","late_agreement")):
            table[name] = np.where(table[name]==MISSING,np.nan,table[name])
    for name in ("driver","track","composition","start","track_difficulty","passenger_count"):
        table[name] = table[name].astype(np.int32)
    for name in metrics:
        if name.endswith(("mismatch_cycles","switched_on","switched_off")):
            table[name] = table[name].astype(np.int16)
    table.update(add_disagreement(table,drivers,tracks,runs,steps))
    return table,drivers,tracks


def add_disagreement(table, drivers, tracks, runs, steps):
    print("Reading solo baselines to measure how differently each car's occupants would decide alone...",flush=True)
    people = drivers
    index = {person:i for i,person in enumerate(people)}
    participants = load_participants()
    trees = [participants[person]["tree"] for person in people]
    starts = int(table["start"].max())+1 if len(table["start"]) else 0
    solo,cognition,found = solo_runs(runs,people,tracks,starts,steps)
    pairs,inverse = np.unique(np.stack([table["driver"],table["composition"]],axis=1),axis=0,return_inverse=True)
    seats = np.full((len(pairs),5),-1,dtype=np.int32)
    for row,(driver,composition) in enumerate(pairs):
        members = [index[p] for p in passengers(people,people[driver],int(composition))]
        seats[row,:len(members)] = members
    seats = seats[inverse.ravel()]
    if not np.array_equal((seats>=0).sum(axis=1),table["passenger_count"]):
        raise ValueError("Decoded compositions disagree with recorded passenger counts")
    output,reported = {},time.monotonic()
    for begin in range(0,len(seats),100_000):
        part = slice(begin,begin+100_000)
        driver,track,start,members = table["driver"][part],table["track"][part],table["start"][part],seats[part]
        valid = members>=0
        safe = np.where(valid,members,0)
        if not found[driver,track,start].all() or not found[safe,track[:,None],start[:,None]][valid].all():
            raise ValueError("A required solo baseline is missing from the result archives")
        own = solo[driver,track,start]
        counts = disagreement(own,solo[safe,track[:,None],start[:,None]],valid)
        pulled = cognitive_pull(trees,driver,own,cognition[driver,track,start],
                                cognition[safe,track[:,None],start[:,None]],valid)
        counts["solo_cognitive_pull_cycles"] = pulled.sum(axis=1)
        counts["solo_cognitive_pull_early_cycles"] = pulled[:,:EARLY_CYCLES].sum(axis=1)
        for name,value in counts.items():
            output.setdefault(name,[]).append(value)
        if time.monotonic()-reported>=5:
            print(f"  Measured {min(begin+100_000,len(seats)):,}/{len(seats):,} cars",flush=True)
            reported = time.monotonic()
    output = {name:np.concatenate(values).astype(np.float32 if name in ("solo_opposition_share","passenger_solo_automation") else np.int16)
              for name,values in output.items()}
    output["passenger_seats"] = seats.astype(np.int8)
    return output


def load(directory=None, runs=RUNS_DIR, steps=100):
    """Return the analysis columns as NumPy arrays; rebuild only when the cache changed."""
    cache = comparison_directory(directory)/"comparisons.sqlite"
    if not cache.exists():
        raise FileNotFoundError("Run experiment/analysis/compare_modes/run.py first")
    stored = cache.parent/"analysis_table.npz"
    key = cache_key(cache)
    if stored.exists():
        with np.load(stored,allow_pickle=False) as saved:
            if str(saved["_key"])==key:
                table = {name:saved[name] for name in saved.files if not name.startswith("_")}
                table["_drivers"],table["_tracks"] = list(saved["_drivers"]),list(saved["_tracks"])
                print(f"Loaded {len(table['driver']):,} comparisons from {stored}",flush=True)
                return table
    started = time.monotonic()
    table,drivers,tracks = build(cache,runs,steps)
    temporary = stored.with_name(".analysis_table.tmp.npz")
    np.savez(temporary,_key=np.array(key),_drivers=np.array(drivers),_tracks=np.array(tracks),**table)
    temporary.replace(stored)
    print(f"Saved the analysis table ({time.monotonic()-started:.0f}s): {stored}",flush=True)
    table["_drivers"],table["_tracks"] = drivers,tracks
    return table
