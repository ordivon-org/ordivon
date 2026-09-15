#!/usr/bin/env python3
"""Frozen R2 generic evaluator.

Candidate modules implement the deterministic adapter contract described in the R2
protocol. No candidate-provided reward is read. Policy identity is never passed into a
candidate. All ordering, budgets and thresholds live in this protocol code/JSON.
"""
from __future__ import annotations

import collections
import copy
import hashlib
import importlib.util
import itertools
import json
import math
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from selection_reference import (
    CONTEXTS,
    EVAL_SAMPLES_PER_CONTEXT,
    TRAIN_SAMPLES_PER_CONTEXT,
    canonical_json,
    derive_seed,
    required_families,
)

MAX_EPISODE_DECISIONS = 96
ORACLE_MAX_DEPTH = 24
ORACLE_MAX_NODES = 50_000
TRAIN_EPOCHS = 4
Q_ALPHA = 0.25
Q_GAMMA = 0.95
Q_EPSILON_START = 0.30
Q_EPSILON_END = 0.05
ONGOING_REWARD = -0.01
WIN_REWARD = 1.0
LOSS_REWARD = -1.0
SAMPLED_STATE_CAP = 128

THRESHOLDS = {
    "S1": {"agencyScore": 0.20},
    "S2": {"learnabilityDelta": 0.15},
    "S3": {"oracleMinimum": 0.65, "randomMaximum": 0.75, "competenceGap": 0.25},
    "S4": {"memoryOverReactive": 0.10, "aliasingRate": 0.10},
    "S5": {"oracleOverBestConstant": 0.15, "minDistinctOracleFirstActions": 2},
    "S6": {"failureRecoveryGain": 0.15, "firstEpochFailureRate": 0.20},
    "S7": {"contextTransferPenalty": 0.10, "minDistinctContextFirstActions": 2},
    "S8": {"maxDuplicateActionPairRate": 0.95},
    "S9": {"minimumOracleGroupSuccess": 0.50},
}

COMPLEXITY_CAPS = {
    "actionCount": 8,
    "observationFieldCount": 12,
    "playerFacingRuleCount": 12,
    "uiModeCount": 4,
    "maxEpisodeDecisions": MAX_EPISODE_DECISIONS,
}


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_candidate(path: str):
    p = Path(path)
    spec = importlib.util.spec_from_file_location("r2_candidate_adapter", p)
    if not spec or not spec.loader:
        raise RuntimeError("unable to load candidate module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not isinstance(getattr(mod, "MANIFEST", None), dict):
        raise RuntimeError("candidate module must export MANIFEST dict")
    if not callable(getattr(mod, "create_game", None)):
        raise RuntimeError("candidate module must export create_game(seed:int, context:int)")
    return mod


def status(game) -> str:
    s = game.status()
    if s not in {"ONGOING", "WIN", "LOSS"}:
        raise RuntimeError(f"invalid status {s!r}")
    return s


def legal(game, action_order: Sequence[str]) -> List[str]:
    got = list(game.legal_actions())
    if len(got) != len(set(got)):
        raise RuntimeError("duplicate legal action ids")
    unknown = set(got) - set(action_order)
    if unknown:
        raise RuntimeError(f"unknown legal actions: {sorted(unknown)}")
    allowed = set(got)
    return [a for a in action_order if a in allowed]


def observation_key(game) -> str:
    return canonical_json(game.observe())


def state_key(game) -> str:
    return canonical_json(game.full_state())


def terminal_reward(s: str) -> float:
    if s == "WIN":
        return WIN_REWARD
    if s == "LOSS":
        return LOSS_REWARD
    return ONGOING_REWARD


@dataclass
class Episode:
    outcome: str
    decisions: int
    unchanged: int
    visited: List[Any] = field(default_factory=list)
    first_action: Optional[str] = None

    @property
    def success(self) -> int:
        return int(self.outcome == "WIN")


class QTable:
    def __init__(self, action_order: Sequence[str], memory: bool):
        self.action_order = tuple(action_order)
        self.memory = memory
        self.q: Dict[str, Dict[str, float]] = {}

    def _key(self, obs: str, prev_obs: Optional[str], prev_action: Optional[str]) -> str:
        if not self.memory:
            return obs
        return canonical_json({"obs": obs, "prevObs": prev_obs, "prevAction": prev_action})

    def values(self, key: str) -> Dict[str, float]:
        return self.q.setdefault(key, {a: 0.0 for a in self.action_order})

    def greedy(self, key: str, legal_actions: Sequence[str]) -> str:
        vals = self.values(key)
        return max(legal_actions, key=lambda a: (vals[a], -self.action_order.index(a)))


def epsilon_for_episode(index: int, total: int) -> float:
    if total <= 1:
        return Q_EPSILON_END
    t = index / (total - 1)
    return Q_EPSILON_START + (Q_EPSILON_END - Q_EPSILON_START) * t


def episode_rng(seed: int, policy_id: str, epoch: int) -> random.Random:
    h = hashlib.sha256(f"r2-policy|{policy_id}|{seed}|{epoch}".encode()).digest()
    return random.Random(int.from_bytes(h[:8], "big"))


def run_hash_episode(mod, manifest: Mapping, seed: int, context: int, capture=False) -> Episode:
    game = mod.create_game(seed=seed, context=context)
    actions = manifest["actionIds"]
    unchanged = 0
    visited = []
    first = None
    for t in range(MAX_EPISODE_DECISIONS):
        s = status(game)
        if s != "ONGOING":
            return Episode(s, t, unchanged, visited, first)
        la = legal(game, actions)
        if not la:
            return Episode("LOSS", t, unchanged, visited, first)
        obs = observation_key(game)
        idx = int.from_bytes(hashlib.sha256(f"{obs}|{seed}|{context}|{t}".encode()).digest()[:8], "big") % len(la)
        action = la[idx]
        if first is None:
            first = action
        before = state_key(game)
        if capture and len(visited) < SAMPLED_STATE_CAP:
            visited.append(game.clone())
        game.step(action)
        if state_key(game) == before:
            unchanged += 1
    return Episode(status(game) if status(game) != "ONGOING" else "LOSS", MAX_EPISODE_DECISIONS, unchanged, visited, first)


def run_q_episode(mod, manifest: Mapping, table: QTable, seed: int, context: int, train: bool,
                  epsilon: float, epoch: int, capture=False) -> Episode:
    game = mod.create_game(seed=seed, context=context)
    actions = manifest["actionIds"]
    rng = episode_rng(seed, "memory-q" if table.memory else "reactive-q", epoch)
    prev_obs = None
    prev_action = None
    unchanged = 0
    visited = []
    first = None
    for t in range(MAX_EPISODE_DECISIONS):
        s = status(game)
        if s != "ONGOING":
            return Episode(s, t, unchanged, visited, first)
        la = legal(game, actions)
        if not la:
            return Episode("LOSS", t, unchanged, visited, first)
        obs = observation_key(game)
        key = table._key(obs, prev_obs, prev_action)
        if train and rng.random() < epsilon:
            action = la[rng.randrange(len(la))]
        else:
            action = table.greedy(key, la)
        if first is None:
            first = action
        before = state_key(game)
        if capture and len(visited) < SAMPLED_STATE_CAP:
            visited.append(game.clone())
        game.step(action)
        after_status = status(game)
        next_obs = observation_key(game)
        if state_key(game) == before:
            unchanged += 1
        if train:
            reward = terminal_reward(after_status)
            next_key = table._key(next_obs, obs, action)
            next_legal = legal(game, actions) if after_status == "ONGOING" else []
            future = max((table.values(next_key)[a] for a in next_legal), default=0.0)
            qv = table.values(key)[action]
            table.values(key)[action] = qv + Q_ALPHA * (reward + Q_GAMMA * future - qv)
        prev_obs, prev_action = obs, action
    return Episode(status(game) if status(game) != "ONGOING" else "LOSS", MAX_EPISODE_DECISIONS, unchanged, visited, first)


def train_q(mod, manifest: Mapping, memory: bool, only_context: Optional[int] = None):
    table = QTable(manifest["actionIds"], memory=memory)
    outcomes_by_epoch: List[List[int]] = [[] for _ in range(TRAIN_EPOCHS)]
    contexts = [only_context] if only_context is not None else list(CONTEXTS)
    total = TRAIN_EPOCHS * len(contexts) * TRAIN_SAMPLES_PER_CONTEXT
    ordinal = 0
    for epoch in range(TRAIN_EPOCHS):
        for context in contexts:
            for i in range(TRAIN_SAMPLES_PER_CONTEXT):
                seed = derive_seed(manifest["candidateId"], "train", context, i)
                eps = epsilon_for_episode(ordinal, total)
                ep = run_q_episode(mod, manifest, table, seed, context, True, eps, epoch)
                outcomes_by_epoch[epoch].append(ep.success)
                ordinal += 1
    return table, outcomes_by_epoch


def shortest_win_plan(game, action_order: Sequence[str], max_depth=ORACLE_MAX_DEPTH, max_nodes=ORACLE_MAX_NODES):
    if status(game) == "WIN":
        return []
    root = game.clone()
    q = collections.deque([(root, [])])
    seen = {state_key(root)}
    nodes = 1
    while q:
        node, plan = q.popleft()
        if len(plan) >= max_depth:
            continue
        for action in legal(node, action_order):
            nxt = node.clone()
            nxt.step(action)
            nodes += 1
            if nodes > max_nodes:
                return None
            ns = status(nxt)
            np = plan + [action]
            if ns == "WIN":
                return np
            if ns == "LOSS":
                continue
            key = state_key(nxt)
            if key not in seen:
                seen.add(key)
                q.append((nxt, np))
    return None


def run_oracle_episode(mod, manifest: Mapping, seed: int, context: int, capture=False) -> Episode:
    game = mod.create_game(seed=seed, context=context)
    actions = manifest["actionIds"]
    plan = shortest_win_plan(game, actions)
    if plan is None:
        # Defined fail-closed behavior: first legal action sequence, no invented heuristic.
        plan = []
    unchanged = 0
    visited = []
    first = plan[0] if plan else None
    for t in range(MAX_EPISODE_DECISIONS):
        s = status(game)
        if s != "ONGOING":
            return Episode(s, t, unchanged, visited, first)
        la = legal(game, actions)
        if not la:
            return Episode("LOSS", t, unchanged, visited, first)
        action = plan[t] if t < len(plan) and plan[t] in la else la[0]
        before = state_key(game)
        if capture and len(visited) < SAMPLED_STATE_CAP:
            visited.append(game.clone())
        game.step(action)
        if state_key(game) == before:
            unchanged += 1
    return Episode(status(game) if status(game) != "ONGOING" else "LOSS", MAX_EPISODE_DECISIONS, unchanged, visited, first)


def run_constant_episode(mod, manifest, seed, context, action_id):
    game = mod.create_game(seed=seed, context=context)
    actions = manifest["actionIds"]
    for t in range(MAX_EPISODE_DECISIONS):
        s = status(game)
        if s != "ONGOING":
            return int(s == "WIN")
        la = legal(game, actions)
        if not la:
            return 0
        game.step(action_id if action_id in la else la[0])
    return int(status(game) == "WIN")


def rate(xs: Sequence[int]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def evaluate_policy_matrix(mod, manifest, reactive, memory, capture=False):
    rows = []
    state_clones = {}
    for context in CONTEXTS:
        for i in range(EVAL_SAMPLES_PER_CONTEXT):
            seed = derive_seed(manifest["candidateId"], "eval", context, i)
            p0 = run_hash_episode(mod, manifest, seed, context, capture=capture)
            p1 = run_q_episode(mod, manifest, reactive, seed, context, False, 0.0, 0, capture=capture)
            p2 = run_q_episode(mod, manifest, memory, seed, context, False, 0.0, 0, capture=capture)
            p3 = run_oracle_episode(mod, manifest, seed, context, capture=capture)
            for ep in (p2, p3):
                for g in ep.visited:
                    state_clones.setdefault(digest(g.full_state()), g)
            rows.append({"context": context, "seedIndex": i, "seed": seed, "P0": p0, "P1": p1, "P2": p2, "P3": p3})
    return rows, state_clones


def policy_success(rows, pid):
    return rate([r[pid].success for r in rows])


def oracle_distance(game, actions):
    plan = shortest_win_plan(game, actions)
    return None if plan is None else len(plan)


def agency_metrics(states: Mapping[str, Any], actions: Sequence[str]):
    examined = consequential = 0
    action_signatures: Dict[str, List[str]] = {a: [] for a in actions}
    alias_groups: Dict[str, List[Tuple[str, Optional[str]]]] = {}
    for _, game in sorted(states.items())[:SAMPLED_STATE_CAP]:
        la = legal(game, actions)
        if len(la) >= 2:
            examined += 1
        outcomes = []
        plan = shortest_win_plan(game, actions)
        optimal_first = plan[0] if plan else None
        alias_groups.setdefault(observation_key(game), []).append((state_key(game), optimal_first))
        for a in la:
            nxt = game.clone()
            nxt.step(a)
            ns = status(nxt)
            dist = 0 if ns == "WIN" else (None if ns == "LOSS" else oracle_distance(nxt, actions))
            outcomes.append((ns, dist))
            action_signatures[a].append(digest({"before": state_key(game), "after": state_key(nxt), "status": ns}))
        if len(la) >= 2:
            for x, y in itertools.combinations(outcomes, 2):
                terminal_diff = x[0] != y[0]
                reach_diff = (x[1] is None) != (y[1] is None)
                distance_diff = x[1] is not None and y[1] is not None and abs(x[1] - y[1]) >= 2
                if terminal_diff or reach_diff or distance_diff:
                    consequential += 1
                    break
    alias_den = alias_num = 0
    for group in alias_groups.values():
        unique_states = {x[0] for x in group}
        if len(unique_states) > 1:
            alias_den += 1
            if len({x[1] for x in group}) > 1:
                alias_num += 1
    duplicate_pairs = []
    for a, b in itertools.combinations(actions, 2):
        sa, sb = action_signatures[a], action_signatures[b]
        n = min(len(sa), len(sb))
        if n and sum(sa[i] == sb[i] for i in range(n)) / n >= THRESHOLDS["S8"]["maxDuplicateActionPairRate"]:
            duplicate_pairs.append([a, b])
    return {
        "agencyScore": consequential / examined if examined else 0.0,
        "examinedDecisionStates": examined,
        "observationAliasingRate": alias_num / alias_den if alias_den else 0.0,
        "duplicateActionPairs": duplicate_pairs,
    }


def determinism_probe(mod, manifest):
    actions = manifest["actionIds"]
    seed = derive_seed(manifest["candidateId"], "eval", 0, 0)
    traces = []
    for _ in range(2):
        game = mod.create_game(seed=seed, context=0)
        trace = []
        for t in range(32):
            trace.append((state_key(game), status(game)))
            if status(game) != "ONGOING":
                break
            la = legal(game, actions)
            if not la:
                break
            game.step(la[t % len(la)])
        traces.append(trace)
    return traces[0] == traces[1]


def evaluate(module_path: str) -> Dict:
    mod = load_candidate(module_path)
    m = copy.deepcopy(mod.MANIFEST)
    actions = tuple(m["actionIds"])
    if len(actions) != m["adapter"]["actionCount"]:
        raise RuntimeError("manifest actionCount mismatch")

    reactive, reactive_epochs = train_q(mod, m, memory=False)
    memory, memory_epochs = train_q(mod, m, memory=True)
    rows, states = evaluate_policy_matrix(mod, m, reactive, memory, capture=True)

    p0 = policy_success(rows, "P0")
    p1 = policy_success(rows, "P1")
    p2 = policy_success(rows, "P2")
    p3 = policy_success(rows, "P3")
    am = agency_metrics(states, actions)

    constant_rates = {}
    for action in actions:
        vals = []
        for context in CONTEXTS:
            for i in range(EVAL_SAMPLES_PER_CONTEXT):
                seed = derive_seed(m["candidateId"], "eval", context, i)
                vals.append(run_constant_episode(mod, m, seed, context, action))
        constant_rates[action] = rate(vals)
    max_constant = max(constant_rates.values(), default=0.0)

    first_actions = [r["P3"].first_action for r in rows if r["P3"].first_action is not None]
    distinct_first = len(set(first_actions))

    first_epoch = rate(memory_epochs[0])
    last_epoch = rate(memory_epochs[-1])

    # Context-specific reactive policies for S7.
    context_tables = {c: train_q(mod, m, memory=False, only_context=c)[0] for c in CONTEXTS}
    cross = {c: {} for c in CONTEXTS}
    for train_context, table in context_tables.items():
        for eval_context in CONTEXTS:
            vals = []
            for i in range(EVAL_SAMPLES_PER_CONTEXT):
                seed = derive_seed(m["candidateId"], "eval", eval_context, i)
                vals.append(run_q_episode(mod, m, table, seed, eval_context, False, 0.0, 0).success)
            cross[train_context][eval_context] = rate(vals)
    diag = rate([cross[c][c] for c in CONTEXTS])
    off = rate([cross[a][b] for a in CONTEXTS for b in CONTEXTS if a != b])

    context_first = {}
    for c in CONTEXTS:
        fs = [r["P3"].first_action for r in rows if r["context"] == c and r["P3"].first_action]
        if fs:
            context_first[c] = collections.Counter(fs).most_common(1)[0][0]

    group_rates = []
    for context in CONTEXTS:
        for g in range(4):
            start, end = g * 6, (g + 1) * 6
            vals = [r["P3"].success for r in rows if r["context"] == context and start <= r["seedIndex"] < end]
            group_rates.append(rate(vals))

    unchanged_fraction = rate([
        ep.unchanged / max(1, ep.decisions)
        for r in rows for ep in (r["P2"], r["P3"])
    ])

    complexity_ok = all(m["adapter"][k] <= cap for k, cap in COMPLEXITY_CAPS.items())

    scores = {
        "S1": am["agencyScore"],
        "S2": max(p1, p2) - p0,
        "S3": p3 - p0,
        "S4": p2 - p1,
        "S5": p3 - max_constant,
        "S6": last_epoch - first_epoch,
        "S7": diag - off,
        "S9": min(group_rates) if group_rates else 0.0,
    }
    passes = {
        "S1": scores["S1"] >= THRESHOLDS["S1"]["agencyScore"],
        "S2": scores["S2"] >= THRESHOLDS["S2"]["learnabilityDelta"],
        "S3": p3 >= THRESHOLDS["S3"]["oracleMinimum"] and p0 <= THRESHOLDS["S3"]["randomMaximum"] and scores["S3"] >= THRESHOLDS["S3"]["competenceGap"],
        "S4": scores["S4"] >= THRESHOLDS["S4"]["memoryOverReactive"] and am["observationAliasingRate"] >= THRESHOLDS["S4"]["aliasingRate"],
        "S5": scores["S5"] >= THRESHOLDS["S5"]["oracleOverBestConstant"] and distinct_first >= THRESHOLDS["S5"]["minDistinctOracleFirstActions"],
        "S6": scores["S6"] >= THRESHOLDS["S6"]["failureRecoveryGain"] and (1.0 - first_epoch) >= THRESHOLDS["S6"]["firstEpochFailureRate"],
        "S7": scores["S7"] >= THRESHOLDS["S7"]["contextTransferPenalty"] and len(set(context_first.values())) >= THRESHOLDS["S7"]["minDistinctContextFirstActions"],
        "S8": complexity_ok and not am["duplicateActionPairs"],
        "S9": scores["S9"] >= THRESHOLDS["S9"]["minimumOracleGroupSuccess"],
    }
    applicable = required_families(m["descriptors"])
    required_pass = all(passes[f] for f in applicable)

    anti_goodhart = {
        "determinism": determinism_probe(mod, m),
        "stalling": unchanged_fraction <= 0.25,
        "dominantUniversalPolicy": max_constant <= p3 - 0.15,
        "playerModelOverfit": last_epoch - p2 <= 0.25,
        "hiddenAuthorizationByPolicyIdentity": m["adapter"]["policyIdentityVisible"] is False,
        "candidateRewardIgnored": m["adapter"]["candidateRewardExposed"] is False,
        "complexityInflation": complexity_ok and not am["duplicateActionPairs"],
        "cosmeticConsequence": passes["S1"],
        "failureTax": passes["S6"],
        "proxyBundleGaming": required_pass,
    }

    return {
        "schemaVersion": 1,
        "candidateId": m["candidateId"],
        "manifestDigest": digest(m),
        "policySuccess": {"P0_HASH": p0, "P1_REACTIVE_Q": p1, "P2_MEMORY_Q": p2, "P3_ORACLE_BFS": p3},
        "scores": scores,
        "passes": passes,
        "applicableFamilies": list(applicable),
        "requiredFamiliesPass": required_pass,
        "agency": am,
        "constantActionSuccess": constant_rates,
        "distinctOracleFirstActions": distinct_first,
        "memoryTrainingFirstEpoch": first_epoch,
        "memoryTrainingLastEpoch": last_epoch,
        "contextTransfer": {"diagonal": diag, "offDiagonal": off, "matrix": cross, "oracleModalFirstAction": context_first},
        "robustnessGroupRates": group_rates,
        "unchangedTransitionFraction": unchanged_fraction,
        "antiGoodhart": anti_goodhart,
        "antiGoodhartPass": all(anti_goodhart.values()),
        "eligibleForTournament": required_pass and all(anti_goodhart.values()),
        "uncertaintyTreatment": "NONE_FROZEN_EVAL_MATRIX_IS_BENCHMARK_CENSUS_NOT_POPULATION_SAMPLE",
    }


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: evaluator_reference.py CANDIDATE_ADAPTER.py")
    print(json.dumps(evaluate(argv[1]), sort_keys=True, indent=2))


if __name__ == "__main__":
    main(sys.argv)
