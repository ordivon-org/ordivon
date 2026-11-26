"""Deterministic search sampling; no candidate identity, JSON or ledger effects."""

from __future__ import annotations

import hashlib
import math
import random
from collections.abc import Iterator
from typing import NamedTuple


def _seed_int(seed: str, namespace: str) -> int:
    digest = hashlib.sha256(f"{seed}\x00{namespace}".encode()).digest()
    return int.from_bytes(digest[:16], "big")


def _rng(seed: str, namespace: str) -> random.Random:
    return random.Random(_seed_int(seed, namespace))


class TrialSample(NamedTuple):
    sequence: int
    family: int | None
    branch: int
    z: float
    running_mean: float | None


def adaptive_family_count(budget: int) -> int:
    return min(16, max(2, budget // 8))


def search_samples(mode: str, seed: str, budget: int) -> Iterator[TrialSample]:
    """One sampling policy for registered search and null replay.

    RNG namespace, draw order, Gaussian cache, first-family tie breaking and
    running-mean arithmetic are part of the historical protocol.
    """
    if mode == "static":
        rng = _rng(seed, "static-visible-search")
        for sequence in range(1, budget + 1):
            yield TrialSample(sequence, None, sequence, rng.gauss(0.0, 1.0), None)
        return
    if mode != "adaptive":
        raise ValueError(mode)
    rng = _rng(seed, "adaptive-visible-search")
    count = adaptive_family_count(budget)
    latent = [rng.gauss(0.0, math.sqrt(0.60)) for _ in range(count)]
    scale = math.sqrt(1.0 - 0.60)
    sums = [0.0] * count
    counts = [0] * count
    for sequence in range(1, budget + 1):
        if sequence <= count:
            family = sequence - 1
        elif rng.random() < 0.82:
            family = max(
                range(count),
                key=lambda item: sums[item] / counts[item] if counts[item] else float("-inf"),
            )
        else:
            family = rng.randrange(count)
        z = latent[family] + rng.gauss(0.0, scale)
        sums[family] += z
        counts[family] += 1
        yield TrialSample(sequence, family, counts[family], z, sums[family] / counts[family])
