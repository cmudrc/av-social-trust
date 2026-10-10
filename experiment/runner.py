
"""Run this file in VS Code: shared tracks, multicore execution, per-model resume."""

from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from contextlib import contextmanager
from dataclasses import asdict
import json
import multiprocessing
from multiprocessing.util import Finalize
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(root),str(root/"src")]

import numpy as np
import scipy

from experiment import config
from experiment.design import compositions,digest,initial_state,personal_starts,total_runs
from experiment.model import run_model
from experiment.participants import load_participants
from experiment.results import ResultStore,check_existing,completed,checkpoint_results
from experiment.tracks.generate_tracks import file_hash,load_tracks

WORKER = None


class StopWhenParentExits:
    def __init__(self,event,parent=None):
        self.event,self.parent = event,os.getppid() if parent is None else parent

    def is_set(self):
        return self.event.is_set() or os.getppid()!=self.parent


def result_definition(settings,people,registry):
    root = config.ROOT.parent
    paths = [config.ROOT/name for name in ("design.py","model.py","participants.py","runner.py","results.py")]
    paths += [root/"src/av_social_trust"/name for name in ("consensus.py","trust.py")]
    inputs = dict(participant_export=file_hash(config.DATA_DIR/"combined_models.mat"),
                  tracks={track["name"]:track["sha256"] for track in registry},
                  code={str(path.relative_to(root)):file_hash(path) for path in paths},
                  environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__))
    return dict(schema_version=1,parameters=asdict(settings),participants=list(people),
                signature=digest(dict(parameters=asdict(settings),inputs=inputs,participants=list(people))),
                inputs=inputs)


@contextmanager
def keep_awake(enabled):
    process = None
    if enabled and sys.platform=="darwin":
        process = subprocess.Popen(["caffeinate","-i","-w",str(os.getpid())],
                                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        yield
    finally:
        if process is not None:
            process.terminate()
            process.wait()


@contextmanager
def runner_lock(directory):
    """One runner owns a result directory. Lock is outside the result archives."""
    import fcntl
    directory = Path(directory)
    directory.parent.mkdir(parents=True,exist_ok=True)
    lock = directory.parent/f".{directory.name}.lock"
    with lock.open("a") as stream:
        try:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another runner is using this RUNS_DIR") from None
        try:
            yield
        finally:
            fcntl.flock(stream,fcntl.LOCK_UN)


def tasks(people,settings,registry,directory,baseline):
    for composition in compositions(people,settings,baseline):
        variants = ("baseline",) if baseline else ("decision","cognition")
        for track in registry:
            done = completed(directory,composition.driver,track["name"],composition.identifier)
            pending = [(start,variant) for start in range(settings.starts) for variant in variants if (start,variant) not in done]
            for offset in range(0,len(pending),config.TASK_RUNS):
                yield composition,track,pending[offset:offset+config.TASK_RUNS]


def worker_initialize(participants,settings,tracks,bank,directory,definition,stop,parent):
    global WORKER
    signal.signal(signal.SIGINT,signal.SIG_IGN)
    signal.signal(signal.SIGTERM,signal.SIG_IGN)
    store = ResultStore(directory,definition)
    Finalize(None,store.close,exitpriority=10)
    WORKER = participants,settings,tracks,bank,store,StopWhenParentExits(stop,parent)


def run_metadata(composition,track,start,variant,initial,settings,arrays):
    trust,cognition = initial["trust"],initial["cognition"]
    count = len(composition.passengers)
    features = dict(driver_self_trust=float(trust[0,0]),driver_automation_trust=float(cognition[0,0]),
                    driver_perceived_risk=float(cognition[0,1]),driver_workload=float(cognition[0,2]),
                    track_persistence=track["persistence"],
                    mean_complexity=track["mean_complexity"],complexity_switches=track["complexity_switches"])
    if count:
        inbound,outbound = trust[1:,0],trust[0,1:]
        features.update(inbound_trust_sum=float(inbound.sum()),inbound_trust_mean=float(inbound.mean()),
            outbound_trust_sum=float(outbound.sum()),outbound_trust_mean=float(outbound.mean()),
            driver_self_plus_inbound_sum=float(trust[0,0]+inbound.sum()),
            driver_initial_self_weight=float(trust[0,0]/trust[0].sum()),
            alpha_inbound_mean=float(initial["alpha"][1:,0].mean()),
            alpha_outbound_mean=float(initial["alpha"][0,1:].mean()),
            passenger_automation_trust_mean=float(cognition[1:,0].mean()),
            passenger_self_trust_mean=float(np.diag(trust)[1:].mean()))
    automation = arrays["automation_on"]
    return dict(model_name=f"{track['code']}_{int(composition.driver[1:])}_{composition.identifier}_{count}_{start}_{variant}",
        driver=composition.driver,passengers=list(composition.passengers),composition_id=composition.identifier,
        track=track["name"],track_difficulty=track["difficulty"],track_replicate=track["replicate"],
        start=start,cognitive_start=start//settings.social_starts,social_start=start%settings.social_starts,
        variant=variant,state_names=["automation_trust","perceived_risk","workload"],features=features,
        summary=dict(automation_fraction=float(automation.mean()),switching_count=int(np.count_nonzero(automation[1:]!=automation[:-1])),
                     driver_clipping_fraction=float(arrays["clipped"][:,0].mean())))


def worker_task(task):
    worker = WORKER
    if worker is None:
        raise RuntimeError("Worker has not been initialized")
    participants,settings,tracks,bank,store,stop = worker
    composition,track,pending = task
    saved = 0
    for start,variant in pending:
        if stop.is_set():
            break
        initial = initial_state(composition,start,settings,bank)
        try:
            arrays = run_model(initial,participants,settings,variant,tracks[track["name"]],stop)
        except InterruptedError:
            break
        metadata = run_metadata(composition,track,start,variant,initial,settings,arrays)
        saved += store.save(composition,start,variant,track["name"],metadata,arrays)
    return saved


def run(settings=None,directory=None,workers=None):
    settings = settings or config.Settings()
    directory = Path(directory or config.RUNS_DIR)
    if config.CPU_CORES_FREE not in (1,2) or config.TASK_RUNS<1:
        raise ValueError("CPU_CORES_FREE must be 1 or 2; TASK_RUNS must be positive")
    workers = max(1,(os.cpu_count() or 1)-config.CPU_CORES_FREE) if workers is None else workers
    if workers<1:
        raise ValueError("Workers must be positive")
    registry,tracks = load_tracks(settings)
    participants = load_participants()
    people = tuple(participants)
    bank = personal_starts(people,settings)
    definition = result_definition(settings,people,registry)
    planned = total_runs(people,settings)
    with runner_lock(directory),keep_awake(config.KEEP_AWAKE):
        saved = check_existing(directory,definition)
        if saved>planned:
            raise ValueError("RUNS_DIR contains results outside this plan")
        print(f"Models: {planned:,}; completed: {saved:,}; remaining: {planned-saved:,}; workers: {workers}",flush=True)
        if saved==planned:
            checkpoint_results(directory)
            return
        context = multiprocessing.get_context("spawn")
        stop = context.Event()
        handlers,environment = {},{}

        def request_stop(signum,frame):
            stop.set()
            print("Stopping: unfinished models are discarded; completed models remain saved.",flush=True)

        try:
            for sig in (signal.SIGINT,signal.SIGTERM):
                handlers[sig] = signal.signal(sig,request_stop)
            for name in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","VECLIB_MAXIMUM_THREADS","BLIS_NUM_THREADS"):
                environment[name] = os.environ.get(name)
                os.environ[name] = "1"
            with ProcessPoolExecutor(max_workers=workers,mp_context=context,initializer=worker_initialize,
                    initargs=(participants,settings,tracks,bank,directory,definition,stop,os.getpid())) as pool:
                reported = time.monotonic()
                for baseline in (True,False):
                    if stop.is_set():
                        break
                    iterator = iter(tasks(people,settings,registry,directory,baseline))
                    active,exhausted = set(),False
                    while True:
                        while not stop.is_set() and not exhausted and len(active)<workers*2:
                            task = next(iterator,None)
                            if task is None:
                                exhausted = True
                                break
                            active.add(pool.submit(worker_task,task))
                        if not active:
                            break
                        done,active = wait(active,timeout=1,return_when=FIRST_COMPLETED)
                        for future in done:
                            try:
                                saved += future.result()
                            except BaseException:
                                stop.set()
                                raise
                        if time.monotonic()-reported>=30:
                            print(f"Completed {saved:,}/{planned:,}; remaining {planned-saved:,}",flush=True)
                            reported = time.monotonic()
            print(f"Saved {saved:,}/{planned:,}. Run this file again to continue.",flush=True)
        except BaseException:
            stop.set()
            raise
        finally:
            checkpoint_results(directory)
            for sig,handler in handlers.items():
                signal.signal(sig,handler)
            for name,value in environment.items():
                if value is None:
                    os.environ.pop(name,None)
                else:
                    os.environ[name] = value


if __name__ == "__main__":
    multiprocessing.freeze_support()
    run()
