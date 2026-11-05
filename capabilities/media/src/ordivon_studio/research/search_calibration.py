"""R6-A bounded search/replay and null-calibration experiments.

Pure experimental statistics consume a validated registration. The optional
TrialLedger is a typed recorder input; PostgreSQL is not a prerequisite for
source-independent calibration and sealed-holdout reasoning.
"""

from __future__ import annotations

import hashlib
import math
import random
from collections.abc import Iterable, Mapping, Sequence
from statistics import NormalDist
from typing import TYPE_CHECKING, Any

from .grounded_contracts import canonical_digest
from .trial_registration import seed_commitment, validate_registration

if TYPE_CHECKING:
    from .trial_ledger import TrialLedger

NORMAL = NormalDist()



def _seed_int(seed: str, namespace: str) -> int:
    digest = hashlib.sha256(f"{seed}\x00{namespace}".encode()).digest()
    return int.from_bytes(digest[:16], "big")


def _rng(seed: str, namespace: str) -> random.Random:
    return random.Random(_seed_int(seed, namespace))


def one_sided_p(z: float) -> float:
    return max(0.0, min(1.0, 1.0 - NORMAL.cdf(float(z))))


def candidate_identity(config: Mapping[str, Any]) -> str:
    return "creative-candidate://" + canonical_digest(dict(config)).removeprefix("sha256:")


def _record(
    ledger: TrialLedger | None,
    *,
    sequence: int,
    candidate_id: str,
    event_type: str,
    payload: Mapping[str, Any],
) -> None:
    if ledger is not None:
        ledger.append(
            f"trial-attempt://{ledger.search_id.rsplit(':', 1)[-1]}/{sequence:06d}",
            candidate_id,
            event_type,
            payload,
        )


def _static_search_stat(seed: str, budget: int, ledger: TrialLedger | None = None) -> dict[str, Any]:
    rng = _rng(seed, "static-visible-search")
    winner: dict[str, Any] | None = None
    for sequence in range(1, budget + 1):
        config = {"family": "independent-expression-probe", "sequence": sequence}
        candidate_id = candidate_identity(config)
        _record(ledger, sequence=sequence, candidate_id=candidate_id, event_type="trial.proposed", payload={"config": config})
        z = rng.gauss(0.0, 1.0)
        result = {
            "candidateId": candidate_id,
            "config": config,
            "visibleStatisticZ": z,
            "visibleEstimatedDelta": z * 0.10,
            "standardError": 0.10,
        }
        _record(
            ledger,
            sequence=sequence,
            candidate_id=candidate_id,
            event_type="trial.evaluated",
            payload={"visibleStatisticZ": z, "visibleEstimatedDelta": z * 0.10, "standardError": 0.10},
        )
        if winner is None or z > float(winner["visibleStatisticZ"]):
            winner = result
    assert winner is not None
    return winner


def _adaptive_search_stat(seed: str, budget: int, ledger: TrialLedger | None = None) -> dict[str, Any]:
    rng = _rng(seed, "adaptive-visible-search")
    family_count = min(16, max(2, budget // 8))
    rho = 0.60
    shared_scale = math.sqrt(rho)
    idiosyncratic_scale = math.sqrt(1.0 - rho)
    family_latent = {family: rng.gauss(0.0, shared_scale) for family in range(family_count)}
    family_sums = {family: 0.0 for family in range(family_count)}
    family_counts = {family: 0 for family in range(family_count)}
    family_branches = {family: 0 for family in range(family_count)}
    winner: dict[str, Any] | None = None

    for sequence in range(1, budget + 1):
        if sequence <= family_count:
            family = sequence - 1
        else:
            if rng.random() < 0.82:
                family = max(
                    range(family_count),
                    key=lambda item: family_sums[item] / family_counts[item] if family_counts[item] else float("-inf"),
                )
            else:
                family = rng.randrange(family_count)
        family_branches[family] += 1
        config = {
            "family": "adaptive-expression-family",
            "familyId": family,
            "branch": family_branches[family],
            "selectionPolicy": "running-family-mean-82pct-exploit",
        }
        candidate_id = candidate_identity(config)
        _record(ledger, sequence=sequence, candidate_id=candidate_id, event_type="trial.proposed", payload={"config": config})
        z = family_latent[family] + rng.gauss(0.0, idiosyncratic_scale)
        family_sums[family] += z
        family_counts[family] += 1
        result = {
            "candidateId": candidate_id,
            "config": config,
            "visibleStatisticZ": z,
            "visibleEstimatedDelta": z * 0.10,
            "standardError": 0.10,
        }
        _record(
            ledger,
            sequence=sequence,
            candidate_id=candidate_id,
            event_type="trial.evaluated",
            payload={
                "visibleStatisticZ": z,
                "visibleEstimatedDelta": z * 0.10,
                "standardError": 0.10,
                "familyRunningMean": family_sums[family] / family_counts[family],
            },
        )
        if winner is None or z > float(winner["visibleStatisticZ"]):
            winner = result
    assert winner is not None
    winner["searchDiagnostics"] = {
        "familyCount": family_count,
        "withinVisibleFamilyCorrelation": rho,
        "attemptsByFamily": {str(key): value for key, value in family_counts.items()},
    }
    return winner


def run_registered_search(registration: Mapping[str, Any], ledger: TrialLedger | None = None) -> dict[str, Any]:
    registered = validate_registration(registration)
    search = registered["search"]
    mode = str(search["mode"])
    budget = int(search["attemptBudget"])
    visible_seed = str(search["visibleSeed"])
    if mode == "static":
        winner = _static_search_stat(visible_seed, budget, ledger)
    else:
        winner = _adaptive_search_stat(visible_seed, budget, ledger)
    winner.update(
        {
            "schemaVersion": 1,
            "kind": "ordivon.studio.creative-alpha-winner-freeze",
            "experimentId": registered["experimentId"],
            "registrationDigest": registered["registrationDigest"],
            "searchMode": mode,
            "attemptBudget": budget,
            "naiveOneSidedP": one_sided_p(float(winner["visibleStatisticZ"])),
            "holdoutStatus": "sealed-not-observed",
        }
    )
    if ledger is not None:
        _record(
            ledger,
            sequence=budget + 1,
            candidate_id=str(winner["candidateId"]),
            event_type="trial.selected",
            payload={
                "visibleStatisticZ": winner["visibleStatisticZ"],
                "naiveOneSidedP": winner["naiveOneSidedP"],
                "attemptBudget": budget,
            },
        )
        winner["trialLedger"] = ledger.summary()
    winner["winnerDigest"] = canonical_digest({key: value for key, value in winner.items() if key != "winnerDigest"})
    return winner


def _winner_stat_for_replay(mode: str, budget: int, seed: str) -> float:
    if mode == "static":
        return float(_static_search_stat(seed, budget)["visibleStatisticZ"])
    if mode == "adaptive":
        return float(_adaptive_search_stat(seed, budget)["visibleStatisticZ"])
    raise ValueError(mode)


def empirical_tail_probability(observed: float, reference: Sequence[float]) -> float:
    if not reference:
        raise ValueError("reference distribution is empty")
    exceed = sum(value >= observed for value in reference)
    return (exceed + 1.0) / (len(reference) + 1.0)


def _quantile(values: Sequence[float], q: float) -> float:
    if not values:
        raise ValueError("quantile requires values")
    ordered = sorted(values)
    position = q * (len(ordered) - 1)
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return float(ordered[low])
    weight = position - low
    return float(ordered[low] * (1.0 - weight) + ordered[high] * weight)


def search_replay_correction(
    registration: Mapping[str, Any],
    winner: Mapping[str, Any],
    *,
    replay_seed: str,
    replay_count: int = 2000,
) -> dict[str, Any]:
    registered = validate_registration(registration)
    if winner.get("registrationDigest") != registered["registrationDigest"]:
        raise ValueError("winner is not bound to this registration")
    if replay_count < 100:
        raise ValueError("replay_count must be >= 100")
    mode = str(registered["search"]["mode"])
    budget = int(registered["search"]["attemptBudget"])
    maxima = [
        _winner_stat_for_replay(mode, budget, f"{replay_seed}:{index:06d}")
        for index in range(1, replay_count + 1)
    ]
    observed = float(winner["visibleStatisticZ"])
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.creative-alpha-search-replay-correction",
        "experimentId": registered["experimentId"],
        "registrationDigest": registered["registrationDigest"],
        "winnerDigest": winner["winnerDigest"],
        "searchMode": mode,
        "attemptBudget": budget,
        "replayCount": replay_count,
        "observedWinnerZ": observed,
        "naiveOneSidedP": one_sided_p(observed),
        "searchCorrectedP": empirical_tail_probability(observed, maxima),
        "nullMaxSummary": {
            "mean": sum(maxima) / len(maxima),
            "p50": _quantile(maxima, 0.50),
            "p95": _quantile(maxima, 0.95),
            "p99": _quantile(maxima, 0.99),
            "maximum": max(maxima),
        },
        "interpretationLaw": "The reference distribution replays the same complete search procedure in zero-effect worlds. It corrects winner selection, not the outcome scale itself.",
    }
    result["correctionDigest"] = canonical_digest(result)
    return result


def evaluate_sealed_holdout(
    registration: Mapping[str, Any],
    winner: Mapping[str, Any],
    *,
    holdout_seed: str,
    ledger: TrialLedger | None = None,
) -> dict[str, Any]:
    registered = validate_registration(registration)
    if winner.get("registrationDigest") != registered["registrationDigest"]:
        raise ValueError("winner is not bound to this registration")
    if seed_commitment(holdout_seed) != registered["holdout"]["seedCommitment"]:
        raise ValueError("holdout seed does not satisfy the sealed commitment")
    candidate_id = str(winner["candidateId"])
    rng = _rng(holdout_seed, f"holdout:{candidate_id}")
    z = rng.gauss(0.0, 1.0)
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.creative-alpha-holdout-result",
        "experimentId": registered["experimentId"],
        "registrationDigest": registered["registrationDigest"],
        "winnerDigest": winner["winnerDigest"],
        "candidateId": candidate_id,
        "holdoutSeedCommitment": registered["holdout"]["seedCommitment"],
        "holdoutStatisticZ": z,
        "holdoutEstimatedDelta": z * 0.10,
        "standardError": 0.10,
        "holdoutOneSidedP": one_sided_p(z),
        "trueCreativeAlpha": 0.0,
        "holdoutStatus": "revealed-contaminated-for-future-tuning",
        "interpretationLaw": "This holdout is independent of visible search and is evidence only for the already-frozen candidate. Its raw seed was not present in registration or search execution.",
    }
    if ledger is not None:
        budget = int(registered["search"]["attemptBudget"])
        _record(
            ledger,
            sequence=budget + 2,
            candidate_id=candidate_id,
            event_type="trial.holdout_revealed",
            payload={
                "holdoutStatisticZ": z,
                "holdoutOneSidedP": result["holdoutOneSidedP"],
                "holdoutSeedCommitment": result["holdoutSeedCommitment"],
            },
        )
        result["trialLedger"] = ledger.summary()
    result["holdoutDigest"] = canonical_digest(result)
    return result


def calibration_experiment(
    *,
    mode: str,
    budgets: Iterable[int],
    worlds: int = 400,
    reference_replays: int = 1600,
    seed: str = "r6a-calibration-20260811",
    alpha: float = 0.05,
) -> dict[str, Any]:
    if mode not in {"static", "adaptive"}:
        raise ValueError("mode must be static or adaptive")
    if worlds < 100 or reference_replays < 400:
        raise ValueError("calibration requires >=100 worlds and >=400 reference replays")
    rows: dict[str, Any] = {}
    for budget in budgets:
        budget = int(budget)
        reference = [
            _winner_stat_for_replay(mode, budget, f"{seed}:reference:{budget}:{index:06d}")
            for index in range(1, reference_replays + 1)
        ]
        naive_false = 0
        corrected_false = 0
        holdout_false = 0
        dual_evidence_false_promotion = 0
        observed_maxima: list[float] = []
        holdout_zs: list[float] = []
        for index in range(1, worlds + 1):
            observed = _winner_stat_for_replay(mode, budget, f"{seed}:world:{budget}:{index:06d}")
            holdout = _rng(seed, f"holdout-calibration:{mode}:{budget}:{index:06d}").gauss(0.0, 1.0)
            observed_maxima.append(observed)
            holdout_zs.append(holdout)
            naive_p = one_sided_p(observed)
            corrected_p = empirical_tail_probability(observed, reference)
            holdout_p = one_sided_p(holdout)
            naive_false += int(naive_p < alpha)
            corrected_false += int(corrected_p < alpha)
            holdout_false += int(holdout_p < alpha)
            dual_evidence_false_promotion += int(corrected_p < alpha and holdout_p < alpha)
        rows[str(budget)] = {
            "attemptBudget": budget,
            "worldCount": worlds,
            "referenceReplayCount": reference_replays,
            "naiveFalsePositiveRate": naive_false / worlds,
            "searchCorrectedFalsePositiveRate": corrected_false / worlds,
            "sealedHoldoutFalsePositiveRate": holdout_false / worlds,
            "dualEvidenceFalsePromotionRate": dual_evidence_false_promotion / worlds,
            "meanSelectedVisibleZ": sum(observed_maxima) / worlds,
            "p95SelectedVisibleZ": _quantile(observed_maxima, 0.95),
            "meanHoldoutZ": sum(holdout_zs) / worlds,
            "referenceNullMaxP95": _quantile(reference, 0.95),
        }
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.creative-alpha-null-calibration",
        "mode": mode,
        "alpha": alpha,
        "trueCreativeAlpha": 0.0,
        "rows": rows,
        "interpretationLaw": (
            "Naive false-positive rate measures the invalid practice of treating the best searched candidate as if it were preregistered. "
            "Search-corrected rate uses the full search-replay null. Holdout rate evaluates an independent frozen-candidate observation. "
            "Dual-evidence false promotion requires both independent evidence classes to cross the preregistered alpha threshold; it is the R6-A3 promotion gate, not a retroactive rescore of R6-A1/A2."
        ),
    }
    result["calibrationDigest"] = canonical_digest(result)
    return result


def score_null_attack(
    *,
    registration: Mapping[str, Any],
    winner: Mapping[str, Any],
    correction: Mapping[str, Any],
    holdout: Mapping[str, Any],
    calibration: Mapping[str, Any],
) -> dict[str, Any]:
    registered = validate_registration(registration)
    digest = registered["registrationDigest"]
    if any(item.get("registrationDigest") != digest for item in (winner, correction, holdout)):
        raise ValueError("R6-A artifacts do not share one registration")
    rows = calibration.get("rows")
    if not isinstance(rows, dict) or not rows:
        raise ValueError("calibration rows missing")
    largest_budget = str(max(int(key) for key in rows))
    largest = rows[largest_budget]
    corrected_rates = [float(row["searchCorrectedFalsePositiveRate"]) for row in rows.values()]
    holdout_rates = [float(row["sealedHoldoutFalsePositiveRate"]) for row in rows.values()]
    signals = {
        "visibleWinnerLooksNaivelySignificant": float(winner["naiveOneSidedP"]) < 0.05,
        "officialSearchCorrectionRejectsFalseAlpha": float(correction["searchCorrectedP"]) >= 0.05,
        "officialSealedHoldoutRejectsFalseAlpha": float(holdout["holdoutOneSidedP"]) >= 0.05,
        "highBudgetNaiveFalsePositiveInflation": float(largest["naiveFalsePositiveRate"]) >= 0.95,
        "searchCorrectionCalibrated": all(0.015 <= rate <= 0.085 for rate in corrected_rates),
        "sealedHoldoutCalibrated": all(0.015 <= rate <= 0.085 for rate in holdout_rates),
        "holdoutWasIndependentOfVisibleWinner": abs(float(largest["meanHoldoutZ"])) <= 0.20,
    }
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.creative-alpha-r6a-score",
        "experimentId": registered["experimentId"],
        "registrationDigest": digest,
        "acceptanceSignals": signals,
        "accepted": all(signals.values()),
        "observed": {
            "visibleWinnerZ": winner["visibleStatisticZ"],
            "visibleWinnerNaiveP": winner["naiveOneSidedP"],
            "searchCorrectedP": correction["searchCorrectedP"],
            "holdoutZ": holdout["holdoutStatisticZ"],
            "holdoutP": holdout["holdoutOneSidedP"],
            "calibrationMode": calibration.get("mode"),
            "largestBudgetCalibration": largest,
        },
        "decisionLaw": (
            "Passing R6-A means the apparatus exposes selection inflation while maintaining calibrated search-aware and sealed-holdout evidence under a known zero-effect universe. "
            "It does not establish any positive creative law."
        ),
    }
    result["scoreDigest"] = canonical_digest(result)
    return result
