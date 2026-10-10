"""Deterministic composition selection and independent cognitive/social starts."""

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from math import comb
import random

import numpy as np
from scipy.stats import qmc


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def stable_seed(*parts):
    return int(digest(parts)[:16], 16)


def grid_value(settings, parts, start):
    values = list(settings.trust_values)
    block, offset = divmod(start, len(values))
    random.Random(stable_seed(settings.initial_seed, *parts, block)).shuffle(values)
    return values[offset]


def personal_starts(people, settings):
    bank = {}
    for person in people:
        seed = stable_seed(settings.initial_seed, "expanded_cognition", person)
        states = qmc.LatinHypercube(d=3, rng=np.random.default_rng(seed)).random(settings.cognitive_starts)
        bank[person] = [dict(cognition=states[i//settings.social_starts].tolist(),
                            self_trust=grid_value(settings, ("self_trust", person), i))
                        for i in range(settings.starts)]
    return bank


def unrank(pool, size, rank):
    if not 0 <= rank < comb(len(pool), size):
        raise IndexError("Combination rank out of range.")
    result, first = [], 0
    for remaining in range(size, 0, -1):
        for index in range(first, len(pool)-remaining+1):
            count = comb(len(pool)-index-1, remaining-1)
            if rank < count:
                result.append(pool[index])
                first = index+1
                break
            rank -= count
    return tuple(result)


@dataclass(frozen=True)
class Composition:
    driver: str
    passengers: tuple
    identifier: int


def compositions(people, settings, baseline=False):
    if baseline:
        yield from (Composition(person, (), 0) for person in people)
        return
    blocks = []
    for driver in people:
        pool = tuple(person for person in people if person != driver)
        first = 1
        for size, quota in enumerate(settings.passenger_combinations, 1):
            count = comb(len(pool), size) if size <= len(pool) else 0
            rng = random.Random(stable_seed(settings.selection_seed, driver, size))
            ranks = rng.sample(range(count), min(quota, count))
            blocks.append([Composition(driver, unrank(pool, size, rank), first+rank) for rank in ranks])
            first += count
    for index in range(max(map(len, blocks), default=0)):
        for block in blocks:
            if index < len(block):
                yield block[index]


def total_runs(people, settings):
    social = len(people) * sum(min(quota, comb(len(people)-1, size))
        for size, quota in enumerate(settings.passenger_combinations, 1) if size < len(people))
    return (len(people)+social*2) * len(settings.track_difficulties) * len(settings.track_persistences) * settings.track_replicates * settings.starts


@lru_cache(maxsize=4096)
def alpha_values(seed, starts):
    return qmc.LatinHypercube(d=1, rng=np.random.default_rng(seed)).random(starts)[:, 0]


def initial_state(composition, start, settings, bank):
    agents = [composition.driver, *composition.passengers]
    n = len(agents)
    trust, alpha = np.zeros((n, n)), np.zeros((n, n))
    mask = np.eye(n, dtype=bool)
    rates = np.eye(n)*settings.self_learning_rate
    for i, person in enumerate(agents):
        trust[i, i] = bank[person][start]["self_trust"]
    for passenger in range(1, n):
        for i, j in ((0, passenger), (passenger, 0)):
            parts = ("interpersonal", *agents, agents[i], agents[j])
            trust[i, j] = grid_value(settings, parts, start)
            seed = stable_seed(settings.initial_seed, "alpha", *agents, agents[i], agents[j])
            alpha[i, j] = alpha_values(seed, settings.starts)[start]
            mask[i, j], rates[i, j] = True, settings.interpersonal_learning_rate
    return dict(agents=agents,
                cognition=np.array([bank[person][start]["cognition"] for person in agents]),
                trust=trust, alpha=alpha, mask=mask, rates=rates)
