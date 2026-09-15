#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import itertools
from typing import Mapping, Sequence

STRICT_EFFECT_DELTA = 0.05
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
    eligible = [e for e in entries if e.get("eligibleForTournament")]
    if not eligible:
        raise ValueError("no eligible entries")
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


def choose_ablation(rows: Sequence[Mapping]) -> Mapping:
    eligible = [r for r in rows if r["playable"]]
    if not eligible:
        raise ValueError("no playable ablation")
    def key(r):
        losses = [float(r["winnerScores"][f]) - float(r["ablationScores"][f]) for f in SCALAR_FAMILIES]
        count = sum(x >= STRICT_EFFECT_DELTA for x in losses)
        profile = tuple(sorted(losses, reverse=True))
        return (count, profile, tuple(-int(sha256_text(r["couplingId"])[i:i+8], 16) for i in range(0, 32, 8)))
    return max(eligible, key=key)


if __name__ == "__main__":
    print("R3_SELECTION_REFERENCE=READY")
