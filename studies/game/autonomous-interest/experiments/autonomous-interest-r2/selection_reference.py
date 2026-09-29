#!/usr/bin/env python3
"""Frozen R2 candidate-independent selection primitives.

This module contains no candidate content. It is part of the protocol authority and must
be committed before any R2 candidate generation.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

SEED_DOMAIN = "ordivon-autonomous-interest-r2-20260915-seed-v1"
SLOT_IDS = tuple(f"R2C{i:02d}" for i in range(1, 13))
CONTEXTS = tuple(range(4))
TRAIN_SAMPLES_PER_CONTEXT = 8
EVAL_SAMPLES_PER_CONTEXT = 24
STRICT_EFFECT_DELTA = 0.05

AXIS_ORDER = (
    "agencyMode",
    "improvementCarrier",
    "consequenceHorizon",
    "failureValue",
)

UNIVERSAL_FAMILIES = ("S1", "S3", "S6", "S8", "S9")
TOURNAMENT_SCALAR_FAMILIES = ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S9")


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(value) -> str:
    if not isinstance(value, (bytes, bytearray)):
        value = str(value).encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def derive_seed(candidate_id: str, split: str, context: int, sample_index: int) -> int:
    if candidate_id not in SLOT_IDS and candidate_id != "R2SELFTEST":
        raise ValueError("unknown R2 candidate slot")
    if split not in {"train", "eval"}:
        raise ValueError("split must be train/eval")
    if context not in CONTEXTS:
        raise ValueError("context out of range")
    limit = TRAIN_SAMPLES_PER_CONTEXT if split == "train" else EVAL_SAMPLES_PER_CONTEXT
    if not 0 <= sample_index < limit:
        raise ValueError("sample index out of range")
    msg = f"{SEED_DOMAIN}|{candidate_id}|{split}|{context}|{sample_index}".encode()
    # Stable positive 31-bit seed; zero is shifted to one.
    value = int.from_bytes(hashlib.sha256(msg).digest()[:8], "big") % 2147483647
    return value or 1


def seed_matrix(candidate_id: str) -> Dict[str, Dict[int, List[int]]]:
    return {
        split: {
            c: [derive_seed(candidate_id, split, c, i) for i in range(n)]
            for c in CONTEXTS
        }
        for split, n in (("train", TRAIN_SAMPLES_PER_CONTEXT), ("eval", EVAL_SAMPLES_PER_CONTEXT))
    }


def required_families(descriptors: Mapping[str, str]) -> Tuple[str, ...]:
    req = set(UNIVERSAL_FAMILIES)
    carrier = descriptors["improvementCarrier"]
    agency = descriptors["agencyMode"]
    horizon = descriptors["consequenceHorizon"]
    if carrier != "execution-skill":
        req.add("S2")
    if agency in {"informational", "social-simulated", "mixed"}:
        req.add("S4")
    if agency in {"economic-resource", "compositional", "social-simulated", "mixed"} or carrier in {
        "planning", "authored-construction", "adaptation", "mixed"
    }:
        req.add("S5")
    if horizon == "multi-loop":
        req.add("S7")
    return tuple(sorted(req, key=lambda x: int(x[1:])))


def descriptor_distance(a: Mapping[str, str], b: Mapping[str, str]) -> int:
    return sum(a[k] != b[k] for k in AXIS_ORDER)


def _subset_diversity_key(subset: Sequence[Mapping]) -> Tuple:
    pairs = [descriptor_distance(a["descriptors"], b["descriptors"]) for a, b in itertools.combinations(subset, 2)]
    # Maximize the weakest separation first; a sorted distance profile is exact and weight-free.
    distance_profile = tuple(sorted(pairs))
    coverage = tuple(len({c["descriptors"][axis] for c in subset}) for axis in AXIS_ORDER)
    # Prefer cheaper declared substrate only after diversity is exhausted.
    cost_rank = {"web-ts": 0, "godot-2d": 1}
    costs = tuple(sorted(cost_rank[c["implementationCarrier"]] for c in subset))
    ids = tuple(sorted(c["candidateId"] for c in subset))
    hash_tie = sha256_hex("|".join(ids))
    return distance_profile, coverage, tuple(-x for x in costs), tuple(-int(hash_tie[i:i+8], 16) for i in range(0, 32, 8))


def choose_diverse_subset(candidates: Sequence[Mapping], limit: int) -> List[Mapping]:
    if limit < 1:
        raise ValueError("limit must be positive")
    ordered = sorted(candidates, key=lambda c: c["candidateId"])
    if len(ordered) <= limit:
        return ordered
    best = None
    best_key = None
    for subset in itertools.combinations(ordered, limit):
        key = _subset_diversity_key(subset)
        if best is None or key > best_key:
            best, best_key = subset, key
    return list(best)


def complexity_vector(candidate_manifest: Mapping) -> Tuple[int, int, int, int, int]:
    a = candidate_manifest["adapter"]
    return (
        int(a["actionCount"]),
        int(a["observationFieldCount"]),
        int(a["playerFacingRuleCount"]),
        int(a["uiModeCount"]),
        int(a["maxEpisodeDecisions"]),
    )


def compare_family_score(a: float, b: float, delta: float = STRICT_EFFECT_DELTA) -> int:
    d = float(a) - float(b)
    if d >= delta:
        return 1
    if d <= -delta:
        return -1
    return 0


def pairwise_result(a: Mapping, b: Mapping) -> Dict:
    common = sorted(
        (set(a["applicableFamilies"]) & set(b["applicableFamilies"]) & set(TOURNAMENT_SCALAR_FAMILIES)),
        key=lambda x: int(x[1:]),
    )
    comparisons = {f: compare_family_score(a["scores"][f], b["scores"][f]) for f in common}
    better = sum(v == 1 for v in comparisons.values())
    worse = sum(v == -1 for v in comparisons.values())
    a_defeats_b = better >= 2 and worse == 0
    b_defeats_a = worse >= 2 and better == 0
    return {
        "families": common,
        "comparisons": comparisons,
        "aDefeatsB": a_defeats_b,
        "bDefeatsA": b_defeats_a,
    }


def tournament_select(entries: Sequence[Mapping]) -> Mapping:
    if not entries:
        raise ValueError("no tournament entries")
    stats = {e["candidateId"]: {"wins": 0, "losses": 0} for e in entries}
    by_id = {e["candidateId"]: e for e in entries}
    for a, b in itertools.combinations(entries, 2):
        r = pairwise_result(a, b)
        if r["aDefeatsB"]:
            stats[a["candidateId"]]["wins"] += 1
            stats[b["candidateId"]]["losses"] += 1
        elif r["bDefeatsA"]:
            stats[b["candidateId"]]["wins"] += 1
            stats[a["candidateId"]]["losses"] += 1
    min_losses = min(v["losses"] for v in stats.values())
    frontier = [cid for cid, s in stats.items() if s["losses"] == min_losses]
    max_wins = max(stats[cid]["wins"] for cid in frontier)
    frontier = [cid for cid in frontier if stats[cid]["wins"] == max_wins]
    if len(frontier) > 1:
        min_complexity = min(complexity_vector(by_id[cid]["manifest"]) for cid in frontier)
        frontier = [cid for cid in frontier if complexity_vector(by_id[cid]["manifest"]) == min_complexity]
    if len(frontier) > 1:
        frontier.sort(key=lambda cid: sha256_hex(by_id[cid]["candidateSpecDigest"]))
    return by_id[frontier[0]]


def normalized_loop_similarity(a: Sequence[str], b: Sequence[str]) -> float:
    """Cyclic Levenshtein similarity over controlled-vocabulary loop verbs."""
    if not a or not b:
        return 0.0

    def lev(x, y):
        prev = list(range(len(y) + 1))
        for i, xv in enumerate(x, 1):
            cur = [i]
            for j, yv in enumerate(y, 1):
                cur.append(min(cur[-1] + 1, prev[j] + 1, prev[j - 1] + (xv != yv)))
            prev = cur
        return prev[-1]

    best = 0.0
    for k in range(len(b)):
        rb = list(b[k:]) + list(b[:k])
        d = lev(list(a), rb)
        sim = 1.0 - d / max(len(a), len(rb))
        best = max(best, sim)
    return best


if __name__ == "__main__":
    # Candidate-independent smoke evidence only.
    seeds = seed_matrix("R2C01")
    assert len(seeds["train"]) == 4 and len(seeds["eval"]) == 4
    assert not ({x for v in seeds["train"].values() for x in v} & {x for v in seeds["eval"].values() for x in v})
    print("R2_SELECTION_REFERENCE_SELFTEST=PASS")
