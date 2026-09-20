#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import itertools
from typing import Mapping, Sequence

STRICT_EFFECT_DELTA = 0.05
ABLATION_P3_MINIMUM = 0.50
SCALAR_FAMILIES = ("S1","S2","S3","S4","S5","S6","S7","S9")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compare(a: float, b: float, delta: float = STRICT_EFFECT_DELTA) -> int:
    d = float(a) - float(b)
    if d >= delta:
        return 1
    if d <= -delta:
        return -1
    return 0


def pairwise_result(a: Mapping, b: Mapping) -> dict:
    comps = {f: compare(a["scores"][f], b["scores"][f]) for f in SCALAR_FAMILIES}
    better = sum(v == 1 for v in comps.values())
    worse = sum(v == -1 for v in comps.values())
    return {
        "comparisons": comps,
        "aDefeatsB": better >= 2 and worse == 0,
        "bDefeatsA": worse >= 2 and better == 0,
    }


def tournament_select(entries: Sequence[Mapping]) -> Mapping:
    eligible = [e for e in entries if e.get("eligibleForTournament") is True]
    if not eligible:
        raise ValueError("no eligible entries")
    if len({e["candidateId"] for e in eligible}) != len(eligible):
        raise ValueError("duplicate candidateId")
    stats = {e["candidateId"]: {"wins": 0, "losses": 0} for e in eligible}
    by_id = {e["candidateId"]: e for e in eligible}
    for a, b in itertools.combinations(eligible, 2):
        r = pairwise_result(a, b)
        if r["aDefeatsB"]:
            stats[a["candidateId"]]["wins"] += 1
            stats[b["candidateId"]]["losses"] += 1
        elif r["bDefeatsA"]:
            stats[b["candidateId"]]["wins"] += 1
            stats[a["candidateId"]]["losses"] += 1
    min_losses = min(x["losses"] for x in stats.values())
    frontier = [cid for cid, s in stats.items() if s["losses"] == min_losses]
    max_wins = max(stats[cid]["wins"] for cid in frontier)
    frontier = [cid for cid in frontier if stats[cid]["wins"] == max_wins]
    frontier.sort(key=sha256_text)
    return by_id[frontier[0]]


def _bound_ablation_row(row: Mapping) -> tuple[Mapping, Mapping, str]:
    if set(row) != {"couplingId", "winnerEvaluation", "ablationEvaluation"}:
        raise ValueError("ablation row requires exactly couplingId/winnerEvaluation/ablationEvaluation")
    coupling = row["couplingId"]
    winner = row["winnerEvaluation"]
    ablated = row["ablationEvaluation"]
    if winner["candidateId"] != ablated["candidateId"]:
        raise ValueError("winner/ablation candidate mismatch")
    if winner["modelDigest"] != ablated["modelDigest"]:
        raise ValueError("winner/ablation model digest mismatch")
    if winner.get("disabledCoupling") is not None:
        raise ValueError("winner evaluation must be unablated")
    if ablated.get("disabledCoupling") != coupling:
        raise ValueError("ablation disabledCoupling mismatch")
    if set(winner["scores"]) != set(SCALAR_FAMILIES) or set(ablated["scores"]) != set(SCALAR_FAMILIES):
        raise ValueError("scalar family set mismatch")
    return winner, ablated, coupling


def ablation_eligible(row: Mapping) -> bool:
    _, ablated, _ = _bound_ablation_row(row)
    return float(ablated["policySuccess"]["P3"]) >= ABLATION_P3_MINIMUM


def choose_ablation(rows: Sequence[Mapping]) -> Mapping:
    bound = []
    for row in rows:
        winner, ablated, coupling = _bound_ablation_row(row)
        if float(ablated["policySuccess"]["P3"]) >= ABLATION_P3_MINIMUM:
            losses = [float(winner["scores"][f]) - float(ablated["scores"][f]) for f in SCALAR_FAMILIES]
            count = sum(x >= STRICT_EFFECT_DELTA for x in losses)
            profile = tuple(sorted(losses, reverse=True))
            bound.append((count, profile, sha256_text(coupling), row))
    if not bound:
        raise ValueError("no mechanically eligible ablation")
    best_count = max(x[0] for x in bound)
    frontier = [x for x in bound if x[0] == best_count]
    best_profile = max(x[1] for x in frontier)
    frontier = [x for x in frontier if x[1] == best_profile]
    frontier.sort(key=lambda x: x[2])
    return frontier[0][3]


if __name__ == "__main__":
    print("R4_SELECTION_REFERENCE=READY")
