"""Participant-specific affine cognition and trees with two influence modes.

Preserves the exploratory paper experiment: discrete updates, clipping to [0,1],
carry/mix for unselected dimensions, binary voting and a star social network.
Driver models are also used for passengers; this is a modeling assumption.
"""

import numpy as np

from av_social_trust.consensus import normalize_trust_matrix, run_degroot
from av_social_trust.trust import trust_step

STATE_NAMES = ("automation_trust", "perceived_risk", "workload")
VARIANTS = ("baseline", "decision", "cognition")


def tree_decision(person, state):
    node = person["tree"]
    while "feature_index" in node:
        node = node["left"] if state[node["feature_index"]]<node["threshold"] else node["right"]
    return int(node["class"]), float(node["probability"][person["class_names"].index(1)])


def opinions(people, states):
    evaluated = [tree_decision(person,state) for person,state in zip(people,states)]
    decisions = np.array([v[0] for v in evaluated],dtype=bool)
    probabilities = np.array([v[1] for v in evaluated])
    return decisions, probabilities, 2*decisions.astype(float)-1


def run_model(initial, participants, settings, variant, situations, stop=None):
    """Return one complete trajectory or raise InterruptedError; never save steps."""
    if variant not in VARIANTS or (variant=="baseline" and len(initial["agents"])!=1):
        raise ValueError("Invalid model variant/occupants")
    if len(situations)!=settings.steps:
        raise ValueError("Shared track length must equal config.STEPS")
    people = [participants[person] for person in initial["agents"]]
    cognition, trust = initial["cognition"].copy(), initial["trust"].copy()
    history = []
    for step,situation in enumerate(situations,1):
        if stop is not None and stop.is_set():
            raise InterruptedError("Unfinished model discarded")
        raw = cognition.copy()
        for i,person in enumerate(people):
            selected = person["state_indices"]
            raw[i,selected] = person["A"]@cognition[i,selected]+person["B"]*situation.task_complexity+person["c"]
        if not np.isfinite(raw).all():
            raise ValueError("Non-finite cognitive prediction")
        private = np.clip(raw,0,1)
        private_decisions,private_probability,private_opinions = opinions(people,private)
        weights = normalize_trust_matrix(trust)
        social = private.copy()
        if variant=="cognition":
            for component in range(3):
                social[:,component] = run_degroot(private[:,component],weights,steps=settings.discussion_rounds)["opinion_vector"]
            decisions,probability,final_opinions = opinions(people,social)
            trust_opinions = final_opinions
        elif variant=="decision":
            final_opinions = run_degroot(private_opinions,weights,steps=settings.discussion_rounds)["opinion_vector"]
            decisions,probability = final_opinions>0,private_probability
            trust_opinions = private_opinions
        else:
            decisions,probability,final_opinions = private_decisions,private_probability,private_opinions
            trust_opinions = private_opinions
        final_decisions = decisions&situation.automation_available
        trust = trust_step(trust_opinions,trust,initial["rates"],initial["alpha"],initial["mask"])
        cognition = social.copy()
        history.append(dict(step=step,raw_private_cognition=raw,private_cognition=private,
            social_cognition=social,clipped=(raw<0)|(raw>1),private_decisions=private_decisions,
            private_automation_probability=private_probability,final_tree_automation_probability=probability,
            private_opinions=private_opinions,final_opinions=final_opinions,final_decisions=final_decisions,
            automation_on=bool(final_decisions[0]),influence_matrix=weights,trust=trust))
    # Shared situation columns are intentionally not duplicated in each result.
    arrays = {key:np.asarray([row[key] for row in history]) for key in history[0]}
    arrays.update(initial_cognition=initial["cognition"],initial_trust=initial["trust"],
                  initial_alpha=initial["alpha"],connection_mask=initial["mask"])
    return arrays
