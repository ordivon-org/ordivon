#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from typing import Mapping, Sequence

import evaluator_reference as er

STRICT_EFFECT_DELTA = 0.05
ABLATION_P3_MINIMUM = 0.50
SCALAR_FAMILIES = ("S1","S2","S3","S4","S5","S6","S7","S9")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compare(a: float, b: float, delta: float = STRICT_EFFECT_DELTA) -> int:
    d=float(a)-float(b)
    if d>=delta: return 1
    if d<=-delta: return -1
    return 0


def pairwise_result(a: Mapping,b: Mapping)->dict:
    comps={f:compare(a["scores"][f],b["scores"][f]) for f in SCALAR_FAMILIES}
    better=sum(v==1 for v in comps.values()); worse=sum(v==-1 for v in comps.values())
    return {"comparisons":comps,"aDefeatsB":better>=2 and worse==0,"bDefeatsA":worse>=2 and better==0}


def evaluate_authoritatively(model: Mapping, *, allow_selftest: bool=False, disabled_coupling=None) -> dict:
    # Selection never accepts caller-supplied scores/P3/eligibility. It derives them from exact model bytes through the sibling frozen evaluator.
    return er.evaluate_model(model,allow_selftest=allow_selftest,disabled_coupling=disabled_coupling)


def tournament_select(models: Sequence[Mapping], *, allow_selftest: bool=False) -> dict:
    if not models: raise ValueError("no models")
    evaluations=[evaluate_authoritatively(m,allow_selftest=allow_selftest) for m in models]
    ids=[e["candidateId"] for e in evaluations]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate candidateId")
    eligible=[e for e in evaluations if e["eligibleForTournament"] is True]
    if not eligible: raise ValueError("no eligible candidates")
    stats={e["candidateId"]:{"wins":0,"losses":0} for e in eligible}
    by_id={e["candidateId"]:e for e in eligible}
    for a,b in itertools.combinations(eligible,2):
        r=pairwise_result(a,b)
        if r["aDefeatsB"]: stats[a["candidateId"]]["wins"]+=1; stats[b["candidateId"]]["losses"]+=1
        elif r["bDefeatsA"]: stats[b["candidateId"]]["wins"]+=1; stats[a["candidateId"]]["losses"]+=1
    min_losses=min(v["losses"] for v in stats.values())
    frontier=[cid for cid,v in stats.items() if v["losses"]==min_losses]
    max_wins=max(stats[cid]["wins"] for cid in frontier)
    frontier=[cid for cid in frontier if stats[cid]["wins"]==max_wins]
    frontier.sort(key=sha256_text); winner_id=frontier[0]
    model_by_id={m["candidateId"]:m for m in models}
    return {"winnerModel":model_by_id[winner_id],"winnerEvaluation":by_id[winner_id],"tournamentStats":stats,"allEvaluations":evaluations}


def ablation_rows(model: Mapping, *, allow_selftest: bool=False) -> list[dict]:
    winner=evaluate_authoritatively(model,allow_selftest=allow_selftest)
    rows=[]
    for coupling in sorted(model["causalCouplings"]):
        ablated=evaluate_authoritatively(model,allow_selftest=allow_selftest,disabled_coupling=coupling)
        rows.append({"couplingId":coupling,"winnerEvaluation":winner,"ablationEvaluation":ablated})
    return rows


def ablation_eligible(model: Mapping, coupling: str, *, allow_selftest: bool=False) -> bool:
    if coupling not in model["causalCouplings"]: raise ValueError("unknown coupling")
    ablated=evaluate_authoritatively(model,allow_selftest=allow_selftest,disabled_coupling=coupling)
    return float(ablated["policySuccess"]["P3"])>=ABLATION_P3_MINIMUM


def coupling_effect_fingerprint(model: Mapping, coupling: str) -> str:
    if coupling not in model["causalCouplings"]:
        raise ValueError("unknown coupling")
    records=[]
    actions=er.ordered_actions(model)
    for sid in model["states"]:
        st=model["states"][sid]
        for action,tr in st["transitions"].items():
            if tr.get("couplingId")!=coupling:
                continue
            records.append({
                "source":er.semantic_state_identity(model,sid),
                "actionOrdinal":actions.index(action),
                "normal":er.semantic_state_identity(model,tr["next"]),
                "disabled":er.semantic_state_identity(model,tr["withoutCouplingNext"]),
            })
    if not records:
        raise ValueError("coupling has no bound transitions")
    records.sort(key=er.canonical_json)
    return "sha256:"+sha256_text(er.canonical_json(records))


def choose_ablation(model: Mapping, *, allow_selftest: bool=False) -> dict:
    bound=[]
    for row in ablation_rows(model,allow_selftest=allow_selftest):
        winner=row["winnerEvaluation"]; ablated=row["ablationEvaluation"]; coupling=row["couplingId"]
        if float(ablated["policySuccess"]["P3"])<ABLATION_P3_MINIMUM: continue
        losses=[float(winner["scores"][f])-float(ablated["scores"][f]) for f in SCALAR_FAMILIES]
        count=sum(x>=STRICT_EFFECT_DELTA for x in losses); profile=tuple(sorted(losses,reverse=True))
        bound.append((count,profile,coupling_effect_fingerprint(model,coupling),coupling,row))
    if not bound: raise ValueError("no mechanically eligible ablation")
    best_count=max(x[0] for x in bound); frontier=[x for x in bound if x[0]==best_count]
    best_profile=max(x[1] for x in frontier); frontier=[x for x in frontier if x[1]==best_profile]
    frontier.sort(key=lambda x:(x[2],x[3])); return frontier[0][4]


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("models",nargs="+")
    ap.add_argument("--allow-selftest",action="store_true")
    args=ap.parse_args()
    models=[er.load_model(p) for p in args.models]
    if len(models)==1:
        out=choose_ablation(models[0],allow_selftest=args.allow_selftest)
    else:
        t=tournament_select(models,allow_selftest=args.allow_selftest)
        out={"winnerEvaluation":t["winnerEvaluation"],"tournamentStats":t["tournamentStats"]}
    print(json.dumps(out,sort_keys=True,indent=2))


if __name__=="__main__": main()
