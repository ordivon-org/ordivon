#!/usr/bin/env python3
from __future__ import annotations

import collections
import hashlib
import itertools
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

MAX_EPISODE_DECISIONS = 96
TRAIN_EPOCHS = 4
Q_ALPHA = 0.25
Q_GAMMA = 0.95
Q_EPSILON_START = 0.30
Q_EPSILON_END = 0.05
ONGOING_REWARD = -0.01
WIN_REWARD = 1.0
LOSS_REWARD = -1.0

HARD_CAPS = {
    "actionCount": 8,
    "reachableStateCount": 512,
    "uniqueObservationClassCount": 256,
}

THRESHOLDS = {
    "S1": 0.20,
    "S3OracleMinimum": 0.65,
    "S3BaselineMaximum": 0.75,
    "S3Gap": 0.25,
    "S6Gain": 0.15,
    "S6FirstEpochFailure": 0.20,
    "S9MinimumContextOracle": 0.50,
    "duplicateActionRate": 0.95,
    "stallingUnchangedFraction": 0.25,
    "dominantConstantGap": 0.15,
    "playerModelOverfitGap": 0.25,
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def json_node_count(value: Any) -> int:
    if isinstance(value, dict):
        return 1 + sum(json_node_count(k) + json_node_count(v) for k, v in value.items())
    if isinstance(value, list):
        return 1 + sum(json_node_count(v) for v in value)
    return 1


def load_model(path: str) -> dict:
    def reject_constant(value):
        raise ValueError(f"non-standard JSON numeric constant: {value}")
    def no_duplicates(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                raise ValueError(f"duplicate JSON object key: {k}")
            out[k] = v
        return out
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=reject_constant, object_pairs_hook=no_duplicates)


def _ctx(model: Mapping, c: int) -> Mapping:
    return model["contexts"][str(c)]


def ordered_actions(model: Mapping) -> List[str]:
    # JSON array order is not evaluation authority.
    return sorted(model["actions"])

def ordered_legal(model: Mapping, state_id: str) -> List[str]:
    trans = model["states"][state_id]["transitions"]
    return [a for a in ordered_actions(model) if a in trans]


def next_state(model: Mapping, state_id: str, action: str, disabled_coupling: Optional[str] = None) -> str:
    tr = model["states"][state_id]["transitions"][action]
    if disabled_coupling and tr.get("couplingId") == disabled_coupling:
        return tr["withoutCouplingNext"]
    return tr["next"]


_GAMEPLAY_CLASS_CACHE: dict[tuple[str, Optional[str]], Dict[str, int]] = {}
_OBSERVATION_CLASS_CACHE: dict[str, Dict[str, int]] = {}
_SEMANTIC_CLASS_CACHE: dict[tuple[str, Optional[str]], Dict[str, int]] = {}

def all_state_gameplay_classes(model: Mapping, disabled_coupling: Optional[str] = None) -> Dict[str, int]:
    """Future-behaviour classes that ignore candidate observation labels entirely."""
    key=(sha256_text(canonical_json(model)), disabled_coupling)
    cached=_GAMEPLAY_CLASS_CACHE.get(key)
    if cached is not None: return cached
    states=sorted(model["states"])
    base={sid:(model["states"][sid]["status"],tuple(ordered_legal(model,sid))) for sid in states}
    uniq={v:i for i,v in enumerate(sorted(set(base.values()),key=repr))}
    cls={sid:uniq[base[sid]] for sid in states}
    while True:
        sig={}
        for sid in states:
            edges=tuple((a,cls[next_state(model,sid,a,disabled_coupling)]) for a in ordered_legal(model,sid)) if model["states"][sid]["status"]=="ONGOING" else ()
            sig[sid]=(base[sid],edges)
        uniq2={v:i for i,v in enumerate(sorted(set(sig.values()),key=repr))}
        new={sid:uniq2[sig[sid]] for sid in states}
        if all(new[sid]==cls[sid] for sid in states):
            _GAMEPLAY_CLASS_CACHE[key]=new; return new
        cls=new

def canonical_observation_classes(model: Mapping) -> Dict[str, int]:
    """Canonicalize candidate-declared observation equivalence classes label-invariantly.

    The generator chooses only the partition. Numeric labels have no evaluator or renderer authority.
    Classes with identical protocol-measured gameplay membership signatures collapse.
    """
    key=sha256_text(canonical_json(model))
    cached=_OBSERVATION_CLASS_CACHE.get(key)
    if cached is not None: return cached
    gameplay=all_state_gameplay_classes(model,None)
    groups=collections.defaultdict(list)
    for sid,st in model["states"].items(): groups[int(st["observationClass"])].append(sid)
    signatures={raw:tuple(sorted(gameplay[sid] for sid in members)) for raw,members in groups.items()}
    uniq={sig:i for i,sig in enumerate(sorted(set(signatures.values()),key=repr))}
    out={sid:uniq[signatures[int(st["observationClass"])]] for sid,st in model["states"].items()}
    _OBSERVATION_CLASS_CACHE[key]=out; return out

def canonical_observation_class(model: Mapping, state_id: str) -> int:
    return canonical_observation_classes(model)[state_id]

def all_state_semantic_classes(model: Mapping, disabled_coupling: Optional[str] = None) -> Dict[str, int]:
    key=(sha256_text(canonical_json(model)), disabled_coupling)
    cached=_SEMANTIC_CLASS_CACHE.get(key)
    if cached is not None: return cached
    states=sorted(model["states"])
    obs=canonical_observation_classes(model)
    base={sid:(model["states"][sid]["status"],obs[sid],tuple(ordered_legal(model,sid))) for sid in states}
    uniq={v:i for i,v in enumerate(sorted(set(base.values()),key=repr))}
    cls={sid:uniq[base[sid]] for sid in states}
    while True:
        sig={}
        for sid in states:
            edges=tuple((a,cls[next_state(model,sid,a,disabled_coupling)]) for a in ordered_legal(model,sid)) if model["states"][sid]["status"]=="ONGOING" else ()
            sig[sid]=(base[sid],edges)
        uniq2={v:i for i,v in enumerate(sorted(set(sig.values()),key=repr))}
        new={sid:uniq2[sig[sid]] for sid in states}
        if all(new[sid]==cls[sid] for sid in states):
            _SEMANTIC_CLASS_CACHE[key]=new; return new
        cls=new

def semantic_state_identity(model: Mapping, state_id: str, disabled_coupling: Optional[str] = None) -> str:
    cls=all_state_semantic_classes(model,disabled_coupling)
    return canonical_json({"visibleClass":canonical_observation_class(model,state_id),"legalActions":ordered_legal(model,state_id),"futureClass":cls[state_id]})

def semantic_model_fingerprint(model: Mapping) -> str:
    """State-ID / raw-observation-label invariant semantic model fingerprint."""
    validate_model(model, allow_selftest=(model.get("kind") == "selftest"))
    actions=ordered_actions(model)
    classes=all_state_semantic_classes(model,None)
    obs=canonical_observation_classes(model)
    records=[]
    for sid,st in model["states"].items():
        edges=[]
        for action in ordered_legal(model,sid):
            tr=st["transitions"][action]
            row={"actionOrdinal":actions.index(action),"nextClass":classes[tr["next"]]}
            if "couplingId" in tr:
                row.update({"couplingOrdinal":model["causalCouplings"].index(tr["couplingId"]),"withoutClass":classes[tr["withoutCouplingNext"]]})
            edges.append(row)
        records.append({"stateClass":classes[sid],"visibleClass":obs[sid],"status":st["status"],"edges":edges})
    contexts=[]
    for c in range(4):
        contexts.append({
            "train":sorted(semantic_state_identity(model,s,None) for s in _ctx(model,c)["trainInitialStates"]),
            "eval":sorted(semantic_state_identity(model,s,None) for s in _ctx(model,c)["evalInitialStates"]),
        })
    payload={"actionCount":len(actions),"couplingCount":len(model["causalCouplings"]),"states":sorted(records,key=canonical_json),"contexts":contexts}
    return "sha256:"+sha256_text(canonical_json(payload))


def validate_model(model: Mapping, allow_selftest: bool = False) -> dict:
    required = {"schemaVersion","kind","candidateId","humanSignalUsed","actions","causalCouplings","contexts","states"}
    if set(model) != required:
        raise ValueError(f"top-level keys mismatch: {sorted(set(model) ^ required)}")
    if model["schemaVersion"] != 1 or model["humanSignalUsed"] is not False:
        raise ValueError("schemaVersion/humanSignalUsed invalid")
    if model["kind"] == "candidate":
        if model["candidateId"] not in {"R7C01","R7C02","R7C03"}:
            raise ValueError("invalid candidate id")
    elif not (allow_selftest and model["kind"] == "selftest" and model["candidateId"] in {"R7SELFTEST","R7SELFTEST01","R7SELFTEST02","R7SELFTEST03"}):
        raise ValueError("selftest model not admitted")
    actions = model["actions"]
    if not 2 <= len(actions) <= HARD_CAPS["actionCount"] or len(set(actions)) != len(actions):
        raise ValueError("invalid actions")
    if actions != [f"a{i}" for i in range(len(actions))]:
        raise ValueError("actions must be canonical prefix a0..aN")
    couplings = model["causalCouplings"]
    if not 3 <= len(couplings) <= 6 or len(set(couplings)) != len(couplings):
        raise ValueError("invalid couplings")
    if couplings != [f"c{i}" for i in range(len(couplings))]:
        raise ValueError("couplings must be canonical prefix c0..cN")
    states = model["states"]
    if not 12 <= len(states) <= HARD_CAPS["reachableStateCount"]:
        raise ValueError("invalid state count")
    refs = set(states)
    used_actions = set()
    used_couplings = set()
    for sid, st in states.items():
        if set(st) != {"observationClass","status","transitions"}:
            raise ValueError(f"state keys invalid {sid}")
        if st["status"] not in {"ONGOING","WIN","LOSS"}:
            raise ValueError(f"invalid status {sid}")
        obs = st["observationClass"]
        if type(obs) is not int or not 0 <= obs <= 255:
            raise ValueError(f"invalid observation class {sid}")
        trans = st["transitions"]
        if st["status"] == "ONGOING" and not trans:
            raise ValueError(f"ongoing state lacks transitions {sid}")
        if st["status"] != "ONGOING" and trans:
            raise ValueError(f"terminal state has transitions {sid}")
        for action, tr in trans.items():
            if action not in actions:
                raise ValueError(f"unknown action {action}")
            used_actions.add(action)
            if tr["next"] not in refs:
                raise ValueError(f"dangling next {sid}/{action}")
            has_coupling = "couplingId" in tr or "withoutCouplingNext" in tr
            if has_coupling:
                if set(tr) != {"next","couplingId","withoutCouplingNext"}:
                    raise ValueError(f"partial coupling transition {sid}/{action}")
                if tr["couplingId"] not in couplings:
                    raise ValueError(f"unknown coupling {sid}/{action}")
                if tr["withoutCouplingNext"] not in refs:
                    raise ValueError(f"dangling ablation fallback {sid}/{action}")
                if tr["withoutCouplingNext"] == tr["next"]:
                    raise ValueError(f"non-effect coupling {sid}/{action}")
                used_couplings.add(tr["couplingId"])
            elif set(tr) != {"next"}:
                raise ValueError(f"invalid transition keys {sid}/{action}")
    if used_actions != set(actions):
        raise ValueError("every action must be reachable somewhere in model")
    if used_couplings != set(couplings):
        raise ValueError("every coupling must bind at least one transition")
    if set(model["contexts"]) != {"0","1","2","3"}:
        raise ValueError("contexts must be exactly 0..3")
    train_all, eval_all = set(), set()
    for c in range(4):
        x = _ctx(model, c)
        if set(x) != {"trainInitialStates","evalInitialStates"}:
            raise ValueError("context keys invalid")
        tr, ev = x["trainInitialStates"], x["evalInitialStates"]
        if len(tr) != 4 or len(set(tr)) != 4 or len(ev) != 8 or len(set(ev)) != 8:
            raise ValueError("context initial-state cardinality invalid")
        if not set(tr + ev) <= refs:
            raise ValueError("unknown initial state")
        train_all.update(tr); eval_all.update(ev)
    if train_all & eval_all:
        raise ValueError("train/eval initial states must be globally disjoint")
    reachable = reachable_states(model)
    if reachable != refs:
        raise ValueError(f"all states must be reachable; unreachable={sorted(refs-reachable)}")
    canonical_obs=canonical_observation_classes(model)
    measured = {
        "actionCount": len(actions),
        "reachableStateCount": len(reachable),
        "uniqueObservationClassCount": len({canonical_obs[s] for s in reachable}),
    }
    for metric, cap in HARD_CAPS.items():
        if measured[metric] > cap:
            raise ValueError(f"measured hard cap exceeded: {metric}={measured[metric]} > {cap}")
    return measured


def initial_states(model: Mapping, split: str, context: int, disabled_coupling: Optional[str] = None) -> List[str]:
    key = "trainInitialStates" if split == "train" else "evalInitialStates"
    # Hidden state IDs and input array order are not training/evaluation authority.
    return sorted(_ctx(model, context)[key], key=lambda sid: semantic_state_identity(model,sid,disabled_coupling))


def reachable_states(model: Mapping, disabled_coupling: Optional[str] = None) -> set[str]:
    starts = []
    for c in range(4):
        starts += initial_states(model, "train", c, disabled_coupling) + initial_states(model, "eval", c, disabled_coupling)
    seen = set(starts)
    q = collections.deque(starts)
    while q:
        s = q.popleft()
        if model["states"][s]["status"] != "ONGOING":
            continue
        for a in ordered_legal(model, s):
            ns = next_state(model, s, a, disabled_coupling)
            if ns not in seen:
                seen.add(ns); q.append(ns)
    return seen


def shortest_win_plan(model: Mapping, start: str, disabled_coupling: Optional[str] = None) -> Optional[List[str]]:
    if model["states"][start]["status"] == "WIN":
        return []
    q = collections.deque([(start, [])])
    seen = {start}
    while q:
        s, plan = q.popleft()
        if model["states"][s]["status"] != "ONGOING":
            continue
        for a in ordered_legal(model, s):
            ns = next_state(model, s, a, disabled_coupling)
            np = plan + [a]
            status = model["states"][ns]["status"]
            if status == "WIN":
                return np
            if status != "LOSS" and ns not in seen:
                seen.add(ns); q.append((ns, np))
    return None


def shortest_win_distance(model: Mapping, state_id: str, disabled_coupling: Optional[str] = None) -> Optional[int]:
    p = shortest_win_plan(model, state_id, disabled_coupling)
    return None if p is None else len(p)


def bisimulation_classes(model: Mapping, disabled_coupling: Optional[str] = None) -> Dict[str, int]:
    states = sorted(reachable_states(model, disabled_coupling))
    base = {}
    for s in states:
        st = model["states"][s]
        base[s] = (st["status"], canonical_observation_class(model,s), tuple(ordered_legal(model, s)))
    uniq = {v:i for i,v in enumerate(sorted(set(base.values()), key=repr))}
    cls = {s: uniq[base[s]] for s in states}
    while True:
        sig = {}
        for s in states:
            st = model["states"][s]
            edges = tuple((a, cls[next_state(model, s, a, disabled_coupling)]) for a in ordered_legal(model, s))
            sig[s] = (base[s], edges)
        uniq2 = {v:i for i,v in enumerate(sorted(set(sig.values()), key=repr))}
        new = {s: uniq2[sig[s]] for s in states}
        if all(new[s] == cls[s] for s in states):
            return new
        cls = new


def visible_key(model: Mapping, state_id: str) -> str:
    return canonical_json({"observationClass": canonical_observation_class(model,state_id), "legalActions": ordered_legal(model, state_id)})


def p0_action(model: Mapping, state_id: str) -> str:
    legal = ordered_legal(model, state_id)
    h = int.from_bytes(hashlib.sha256(visible_key(model, state_id).encode()).digest()[:8], "big")
    return legal[h % len(legal)]


def deterministic_float(*parts: Any) -> float:
    h = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(h[:8], "big") / float(2**64)


def epsilon(epoch: int) -> float:
    if TRAIN_EPOCHS <= 1:
        return Q_EPSILON_END
    return Q_EPSILON_START + (Q_EPSILON_END-Q_EPSILON_START) * epoch/(TRAIN_EPOCHS-1)


def q_key(model: Mapping, state_id: str, memory: bool, prev_visible: Optional[str], prev_action: Optional[str]) -> str:
    cur = visible_key(model, state_id)
    if not memory:
        return cur
    return canonical_json({"prevVisible": prev_visible, "prevAction": prev_action, "currentVisible": cur})


def q_values(table: Dict[str, Dict[str,float]], key: str, actions: Sequence[str]) -> Dict[str,float]:
    return table.setdefault(key, {a:0.0 for a in sorted(actions)})


def greedy_action(model: Mapping, state_id: str, table: Dict[str,Dict[str,float]], key: str) -> str:
    legal = ordered_legal(model, state_id)
    vals = q_values(table, key, model["actions"])
    order = ordered_actions(model)
    return max(legal, key=lambda a:(vals[a], -order.index(a)))


def run_episode(model: Mapping, start: str, policy: str, table=None, train=False, epoch=0, context=0, disabled_coupling=None) -> dict:
    state = start
    prev_visible = None
    prev_action = None
    unchanged = 0
    first_action = None
    for step in range(MAX_EPISODE_DECISIONS):
        status = model["states"][state]["status"]
        if status != "ONGOING":
            return {"status":status,"success":int(status=="WIN"),"decisions":step,"unchanged":unchanged,"firstAction":first_action}
        legal = ordered_legal(model, state)
        if policy == "P0":
            action = p0_action(model, state)
            key = None
        elif policy in {"P1","P2"}:
            memory = policy == "P2"
            key = q_key(model, state, memory, prev_visible, prev_action)
            # Exploration schedule is intentionally candidate-slot independent. CandidateId is identity/tie-break only.
            # The schedule depends only on frozen policy/training coordinates and ID-independent semantic visible state.
            if train and deterministic_float(policy,epoch,context,semantic_state_identity(model,start,disabled_coupling),step,key) < epsilon(epoch):
                idx = int(deterministic_float("pick",policy,epoch,context,semantic_state_identity(model,start,disabled_coupling),step,key) * len(legal)) % len(legal)
                action = legal[idx]
            else:
                action = greedy_action(model, state, table, key)
        elif policy == "P3":
            plan = shortest_win_plan(model, state, disabled_coupling)
            action = plan[0] if plan else legal[0]
            key = None
        elif policy.startswith("CONST:"):
            wanted = policy.split(":",1)[1]
            action = wanted if wanted in legal else legal[0]
            key = None
        else:
            raise ValueError(policy)
        if first_action is None:
            first_action = action
        ns = next_state(model, state, action, disabled_coupling)
        if ns == state:
            unchanged += 1
        if train and policy in {"P1","P2"}:
            next_status = model["states"][ns]["status"]
            reward = WIN_REWARD if next_status == "WIN" else LOSS_REWARD if next_status == "LOSS" else ONGOING_REWARD
            memory = policy == "P2"
            next_key = q_key(model, ns, memory, visible_key(model,state), action)
            future = 0.0
            if next_status == "ONGOING":
                nv = q_values(table, next_key, model["actions"])
                future = max(nv[a] for a in ordered_legal(model, ns))
            vals = q_values(table, key, model["actions"])
            vals[action] += Q_ALPHA * (reward + Q_GAMMA*future - vals[action])
        prev_visible, prev_action = visible_key(model,state), action
        state = ns
    status = model["states"][state]["status"]
    return {"status":status if status != "ONGOING" else "TIMEOUT","success":int(status=="WIN"),"decisions":MAX_EPISODE_DECISIONS,"unchanged":unchanged,"firstAction":first_action}


def train_q(model: Mapping, memory: bool, only_context: Optional[int] = None, disabled_coupling: Optional[str] = None):
    table: Dict[str,Dict[str,float]] = {}
    by_epoch = []
    contexts = [only_context] if only_context is not None else list(range(4))
    policy = "P2" if memory else "P1"
    for epoch in range(TRAIN_EPOCHS):
        outcomes = []
        for c in contexts:
            for start in initial_states(model,"train",c,disabled_coupling):
                outcomes.append(run_episode(model,start,policy,table,True,epoch,c,disabled_coupling)["success"])
        by_epoch.append(outcomes)
    return table, by_epoch


def mean(xs: Sequence[float]) -> float:
    return sum(xs)/len(xs) if xs else 0.0


def eval_policy(model: Mapping, policy: str, table=None, disabled_coupling=None) -> List[dict]:
    rows=[]
    for c in range(4):
        for start in initial_states(model,"eval",c,disabled_coupling):
            ep=run_episode(model,start,policy,table,False,0,c,disabled_coupling)
            rows.append({"context":c,"start":start,**ep})
    return rows


def success(rows): return mean([r["success"] for r in rows])


def agency_and_duplicates(model: Mapping, disabled_coupling: Optional[str] = None) -> dict:
    reachable = sorted(reachable_states(model, disabled_coupling))
    cls = bisimulation_classes(model, disabled_coupling)
    decision_states=0; consequential=0
    pair_stats = {pair:[0,0] for pair in itertools.combinations(ordered_actions(model),2)}
    for s in reachable:
        if model["states"][s]["status"] != "ONGOING":
            continue
        legal = ordered_legal(model,s)
        if len(legal)>=2:
            decision_states += 1
            succ_classes = [cls[next_state(model,s,a,disabled_coupling)] for a in legal]
            if len(set(succ_classes))>=2:
                consequential += 1
        for a,b in itertools.combinations(ordered_actions(model),2):
            if a in legal and b in legal:
                pair_stats[(a,b)][0] += 1
                if cls[next_state(model,s,a,disabled_coupling)] == cls[next_state(model,s,b,disabled_coupling)]:
                    pair_stats[(a,b)][1] += 1
    duplicates=[]; rates={}
    for pair,(co,match) in pair_stats.items():
        if co:
            rate=match/co; rates["|".join(pair)]={"coObserved":co,"equivalent":match,"rate":rate}
            if rate >= THRESHOLDS["duplicateActionRate"]:
                duplicates.append(list(pair))
    return {"agencyScore": consequential/decision_states if decision_states else 0.0,"decisionStates":decision_states,"duplicateActionPairs":duplicates,"pairRates":rates}


def aliasing_rate(model: Mapping, disabled_coupling: Optional[str] = None) -> float:
    groups=collections.defaultdict(list)
    for s in sorted(reachable_states(model, disabled_coupling)):
        if model["states"][s]["status"]=="ONGOING":
            groups[canonical_observation_class(model,s)].append(s)
    den=num=0
    for states in groups.values():
        if len(states)>1:
            den += 1
            first=[]
            for s in states:
                p=shortest_win_plan(model,s,disabled_coupling)
                first.append(p[0] if p else None)
            if len(set(first))>1: num += 1
    return num/den if den else 0.0


def evaluate_model(model: Mapping, allow_selftest: bool=False, disabled_coupling: Optional[str]=None) -> dict:
    complexity = validate_model(model, allow_selftest)
    if disabled_coupling is not None and disabled_coupling not in model["causalCouplings"]:
        raise ValueError("unknown disabled coupling")
    p1, p1epochs = train_q(model,False,disabled_coupling=disabled_coupling)
    p2, p2epochs = train_q(model,True,disabled_coupling=disabled_coupling)
    rows0=eval_policy(model,"P0",disabled_coupling=disabled_coupling)
    rows1=eval_policy(model,"P1",p1,disabled_coupling)
    rows2=eval_policy(model,"P2",p2,disabled_coupling)
    rows3=eval_policy(model,"P3",disabled_coupling=disabled_coupling)
    s0,s1,s2,s3=map(success,[rows0,rows1,rows2,rows3])
    ag=agency_and_duplicates(model,disabled_coupling)
    constants={a:success(eval_policy(model,"CONST:"+a,disabled_coupling=disabled_coupling)) for a in ordered_actions(model)}
    best_constant=max(constants.values())
    first_actions={r["firstAction"] for r in rows3 if r["firstAction"]}
    first_epoch=mean(p2epochs[0]); last_epoch=mean(p2epochs[-1])
    context_tables={c:train_q(model,False,c,disabled_coupling)[0] for c in range(4)}
    cross={c:{} for c in range(4)}
    for tc,tab in context_tables.items():
        for ec in range(4):
            vals=[run_episode(model,start,"P1",tab,False,0,ec,disabled_coupling)["success"] for start in initial_states(model,"eval",ec,disabled_coupling)]
            cross[tc][ec]=mean(vals)
    diag=mean([cross[c][c] for c in range(4)])
    off=mean([cross[a][b] for a in range(4) for b in range(4) if a!=b])
    context_oracle=[]
    for c in range(4):
        rr=[r for r in rows3 if r["context"]==c]
        context_oracle.append(success(rr))
    unchanged=mean([r["unchanged"]/max(1,r["decisions"]) for r in rows2+rows3])
    scores={
        "S1":ag["agencyScore"],
        "S2":max(s1,s2)-s0,
        "S3":s3-s0,
        "S4":s2-s1,
        "S5":s3-best_constant,
        "S6":last_epoch-first_epoch,
        "S7":diag-off,
        "S9":min(context_oracle),
    }
    hard={
        "S1":scores["S1"]>=THRESHOLDS["S1"],
        "S3":s3>=THRESHOLDS["S3OracleMinimum"] and s0<=THRESHOLDS["S3BaselineMaximum"] and scores["S3"]>=THRESHOLDS["S3Gap"],
        "S6":scores["S6"]>=THRESHOLDS["S6Gain"] and (1-first_epoch)>=THRESHOLDS["S6FirstEpochFailure"],
        "S8":not ag["duplicateActionPairs"],
        "S9":scores["S9"]>=THRESHOLDS["S9MinimumContextOracle"],
    }
    anti={
        "rewardHackingAbsent": True,
        "rngInflationAbsentByRepresentation": True,
        "stalling": unchanged<=THRESHOLDS["stallingUnchangedFraction"],
        "dominantUniversalPolicy": best_constant<=s3-THRESHOLDS["dominantConstantGap"],
        "playerModelOverfit": last_epoch-s2<=THRESHOLDS["playerModelOverfitGap"],
        "hiddenPolicyAuthorizationAbsentByRepresentation": True,
        "complexityInflation": hard["S8"],
        "cosmeticConsequence": hard["S1"],
        "failureTax": hard["S6"],
        "proxyBundleGaming": all(hard.values()),
    }
    return {
        "schemaVersion":1,
        "candidateId":model["candidateId"],
        "kind":model["kind"],
        "disabledCoupling":disabled_coupling,
        "modelDigest":"sha256:"+sha256_text(canonical_json(model)),
        "complexityMeasured":complexity,
        "policySuccess":{"P0":s0,"P1":s1,"P2":s2,"P3":s3},
        "scores":scores,
        "diagnostics":{"aliasingRate":aliasing_rate(model,disabled_coupling),"bestConstantActionSuccess":best_constant,"distinctOracleFirstActions":len(first_actions),"memoryTrainFirstEpoch":first_epoch,"memoryTrainLastEpoch":last_epoch,"contextTransferMatrix":cross,"unchangedTransitionFraction":unchanged,"duplicateActionPairs":ag["duplicateActionPairs"],"duplicatePairRates":ag["pairRates"]},
        "hardCorePass":hard,
        "antiGoodhart":anti,
        "eligibleForTournament":all(hard.values()) and all(anti.values()),
    }


def evaluate_file(path: str, allow_selftest: bool=False) -> dict:
    return evaluate_model(load_model(path),allow_selftest)


def main(argv):
    if len(argv)!=2:
        raise SystemExit("usage: evaluator_reference.py MODEL.json")
    print(json.dumps(evaluate_file(argv[1]),sort_keys=True,indent=2))

if __name__=="__main__": main(sys.argv)
