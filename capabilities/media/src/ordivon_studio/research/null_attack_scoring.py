"""Pure R6-A evidence scoring: separate final judgment from search generation.

This file consumes already-registered, already-frozen artifacts; it neither
samples search candidates nor reads/writes the PostgreSQL trial ledger.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .grounded_contracts import canonical_digest
from .trial_registration import admit_frozen_winner, validate_registration


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
    admit_frozen_winner(registered, winner)
    if correction.get("winnerDigest") != winner["winnerDigest"] or holdout.get("winnerDigest") != winner["winnerDigest"]:
        raise ValueError("R6-A correction/holdout does not consume the frozen winner")
    for label, artifact, digest_field in (
        ("search correction", correction, "correctionDigest"),
        ("sealed holdout", holdout, "holdoutDigest"),
        ("calibration", calibration, "calibrationDigest"),
    ):
        observed = artifact.get(digest_field)
        source = {key: value for key, value in artifact.items() if key != digest_field}
        if observed != canonical_digest(source):
            raise ValueError(f"R6-A {label} source digest mismatch")
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
