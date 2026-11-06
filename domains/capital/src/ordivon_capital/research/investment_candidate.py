"""Read-only evidence gate for a frozen investment research candidate.

Verifies the submitted bytes and envelope; never proves profitable alpha,
independent replication, genuine historical precommitment or capital authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MANIFEST_KEYS = frozenset({
    "schemaVersion", "kind", "candidateId", "hypothesis", "frozenAt",
    "featureDataLatestAvailableAt", "sourceSha256", "holdoutSha256",
    "trialCount", "currency", "costCoverage",
})
_ROW_KEYS = frozenset({
    "periodEndAt", "availableAt", "strategyGrossReturn", "benchmarkNetReturn",
    "fees", "slippage", "financing", "taxes",
})
_COST_KEYS = frozenset({"fees", "slippage", "financing", "taxes"})
_REPLAY_MANIFEST_KEYS = _MANIFEST_KEYS | frozenset({
    "strategyAssetWeight", "benchmarkExpenseFraction",
})
_SOURCE_ROW_KEYS = frozenset({
    "periodEndAt", "availableAt", "assetGrossReturn",
    "cashGrossReturn", "benchmarkGrossReturn",
})



class CandidateEvidenceError(ValueError):
    """Evidence is inconsistent, malformed, or not the committed bytes."""


def _object(value: Any, keys: frozenset[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        raise CandidateEvidenceError(f"{label}: required keys differ from actual keys")
    return value


def _utc(value: Any, label: str) -> datetime:
    if type(value) is not str:
        raise CandidateEvidenceError(f"{label}: timestamp must be a string")
    try:
        instant = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CandidateEvidenceError(f"{label}: invalid timestamp") from exc
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise CandidateEvidenceError(f"{label}: timezone required")
    return instant.astimezone(UTC)


def _decimal(value: Any, label: str) -> Decimal:
    if type(value) is not str:
        raise CandidateEvidenceError(f"{label}: decimal must be a string")
    try:
        out = Decimal(value)
    except InvalidOperation as exc:
        raise CandidateEvidenceError(f"{label}: invalid decimal") from exc
    if not out.is_finite():
        raise CandidateEvidenceError(f"{label}: nonfinite decimal")
    return out


def _read_json(raw: bytes, label: str) -> Any:
    def no_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=no_duplicate_pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")),
        )
    except (ValueError, UnicodeError) as exc:
        raise CandidateEvidenceError(f"{label}: invalid UTF-8 JSON") from exc


def _check_digest(value: Any, raw: bytes, label: str) -> None:
    if type(value) is not str or not _SHA256.fullmatch(value):
        raise CandidateEvidenceError(f"{label}: expected lowercase sha256 digest")
    if hashlib.sha256(raw).hexdigest() != value:
        raise CandidateEvidenceError(f"{label}: source bytes differ from commitment")


def evaluate_investment_candidate(
    *,
    manifest: dict[str, Any],
    source_bytes: bytes,
    holdout_bytes: bytes,
) -> dict[str, Any]:
    """Validate submitted aligned holdout returns; never admit live authority."""
    if type(manifest) is not dict or type(manifest.get("schemaVersion")) is not int:
        raise CandidateEvidenceError("candidate: schemaVersion must be integer")
    version = manifest["schemaVersion"]
    if version not in (1, 2):
        raise CandidateEvidenceError("candidate: unsupported schemaVersion")
    replayed = version == 2
    data = _object(
        manifest,
        _REPLAY_MANIFEST_KEYS if replayed else _MANIFEST_KEYS,
        "candidate",
    )
    expected_kind = (
        "ordivon.capital.finance.replayable-research-candidate"
        if replayed else "ordivon.capital.finance.frozen-research-candidate"
    )
    if data["kind"] != expected_kind:
        raise CandidateEvidenceError("candidate: unsupported kind")
    for field in ("candidateId", "hypothesis"):
        if type(data[field]) is not str or not data[field].strip():
            raise CandidateEvidenceError(f"candidate: nonempty {field} required")
    if type(data["currency"]) is not str or not re.fullmatch(r"[A-Z]{3}", data["currency"]):
        raise CandidateEvidenceError("candidate: ISO-style three-letter currency required")
    if type(data["trialCount"]) is not int or data["trialCount"] < 1:
        raise CandidateEvidenceError("candidate: positive integer trialCount required")
    if (type(data["costCoverage"]) is not list
            or any(type(k) is not str for k in data["costCoverage"])
            or set(data["costCoverage"]) != _COST_KEYS):
        raise CandidateEvidenceError("candidate: complete cost coverage required")
    if len(data["costCoverage"]) != len(_COST_KEYS):
        raise CandidateEvidenceError("candidate: duplicate cost coverage")

    frozen = _utc(data["frozenAt"], "frozenAt")
    feature_available = _utc(
        data["featureDataLatestAvailableAt"], "featureDataLatestAvailableAt"
    )
    if feature_available > frozen:
        raise CandidateEvidenceError("candidate: features unavailable at declared freeze")

    _check_digest(data["sourceSha256"], source_bytes, "sourceSha256")
    _check_digest(data["holdoutSha256"], holdout_bytes, "holdoutSha256")
    rows = _read_json(holdout_bytes, "holdout")
    if type(rows) is not list or not rows:
        raise CandidateEvidenceError("holdout: nonempty paired period list required")

    source_rows: list[Any] | None = None
    strategy_weight: Decimal | None = None
    benchmark_expense: Decimal | None = None
    if replayed:
        strategy_weight = _decimal(data["strategyAssetWeight"], "strategyAssetWeight")
        benchmark_expense = _decimal(
            data["benchmarkExpenseFraction"], "benchmarkExpenseFraction"
        )
        if not 0 <= strategy_weight <= 1 or not 0 <= benchmark_expense <= 1:
            raise CandidateEvidenceError("source: strategy weight/benchmark expense outside [0,1]")
        decoded = _read_json(source_bytes, "source")
        if type(decoded) is not list or len(decoded) != len(rows):
            raise CandidateEvidenceError("source and holdout must have same length")
        source_rows = decoded

    strategy_wealth = Decimal(1)
    benchmark_wealth = Decimal(1)
    peak_wealth = Decimal(1)
    max_drawdown = Decimal(0)
    total_cost = Decimal(0)
    previous_end = frozen
    for index, raw_row in enumerate(rows):
        row = _object(raw_row, _ROW_KEYS, f"holdout[{index}]")
        period_end = _utc(row["periodEndAt"], f"holdout[{index}].periodEndAt")
        available = _utc(row["availableAt"], f"holdout[{index}].availableAt")
        if period_end <= previous_end:
            raise CandidateEvidenceError("holdout: periods must be unique, ordered and post-freeze")
        if available < period_end:
            raise CandidateEvidenceError("holdout: return available before period end")
        previous_end = period_end

        gross = _decimal(row["strategyGrossReturn"], "strategyGrossReturn")
        baseline = _decimal(row["benchmarkNetReturn"], "benchmarkNetReturn")
        if source_rows is not None:
            assert strategy_weight is not None and benchmark_expense is not None
            source = _object(source_rows[index], _SOURCE_ROW_KEYS, f"source[{index}]")
            source_end = _utc(source["periodEndAt"], f"source[{index}].periodEndAt")
            source_available = _utc(source["availableAt"], f"source[{index}].availableAt")
            if source_end != period_end:
                raise CandidateEvidenceError("source: holdout period end mismatch")
            if not period_end <= source_available <= available:
                raise CandidateEvidenceError("source: invalid observation availability")
            asset = _decimal(source["assetGrossReturn"], "assetGrossReturn")
            cash = _decimal(source["cashGrossReturn"], "cashGrossReturn")
            bench = _decimal(source["benchmarkGrossReturn"], "benchmarkGrossReturn")
            if min(asset, cash, bench) < -1:
                raise CandidateEvidenceError("source: impossible simple return")
            recomputed_gross = strategy_weight * asset + (1 - strategy_weight) * cash
            recomputed_baseline = bench - benchmark_expense
            if gross != recomputed_gross or baseline != recomputed_baseline:
                raise CandidateEvidenceError("source: claimed returns do not match source replay")
        costs = tuple(_decimal(row[k], k) for k in ("fees", "slippage", "financing", "taxes"))
        if any(c < 0 for c in costs):
            raise CandidateEvidenceError("holdout: costs must be nonnegative")
        cost = sum(costs, Decimal(0))
        net = gross - cost
        if gross < -1 or net < -1 or baseline < -1:
            raise CandidateEvidenceError("holdout: simple returns cannot lose more than 100%")
        strategy_wealth *= 1 + net
        benchmark_wealth *= 1 + baseline
        total_cost += cost
        peak_wealth = max(peak_wealth, strategy_wealth)
        max_drawdown = max(max_drawdown, (peak_wealth - strategy_wealth) / peak_wealth)

    return {
        "schemaVersion": version,
        "kind": "ordivon.capital.finance.research-evaluation",
        "candidateId": data["candidateId"],
        "standing": (
            "SOURCE_REPLAYED_PROVIDER_NOT_ATTESTED"
            if replayed else "STRUCTURALLY_REVIEWABLE_NOT_INDEPENDENTLY_VERIFIED"
        ),
        "capitalAuthority": "NONE",
        "holdoutPeriods": len(rows),
        "declaredTrials": data["trialCount"],
        "sourceBytesDigestVerified": True,
        "holdoutBytesDigestVerified": True,
        "featureTimeDeclarationChecked": True,
        "freezeAttestationVerified": False,
        "sourceToReturnRecomputationVerified": replayed,
        "statisticalGeneralizationVerified": False,
        "economicSummary": {
            "currency": data["currency"],
            "strategyNetGrowth": str(strategy_wealth),
            "benchmarkNetGrowth": str(benchmark_wealth),
            "strategyNetTotalReturn": str(strategy_wealth - 1),
            "benchmarkNetTotalReturn": str(benchmark_wealth - 1),
            "strategyMaxDrawdown": str(max_drawdown),
            "sumOfPerPeriodCostFractions": str(total_cost),
            "relativeGrowth": (
                str(strategy_wealth / benchmark_wealth - 1)
                if benchmark_wealth > 0 else None
            ),
        },
        "requiredNextEvidence": [
            "Externally witnessed hypothesis freeze and point-in-time provenance",
            (
                "Independent verification of market source and cost observations"
                if replayed else
                "Independent recomputation of returns from committed source"
            ),
            "Multiple-trial selection-bias evaluation and untouched holdout",
            "Independent model/risk review and distinct capital authorization",
        ],
        **({"sourceObservationProvenanceVerified": False} if replayed else {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Finance research evidence gate")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--holdout", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = evaluate_investment_candidate(
            manifest=_read_json(args.manifest.read_bytes(), "manifest"),
            source_bytes=args.source.read_bytes(),
            holdout_bytes=args.holdout.read_bytes(),
        )
    except (CandidateEvidenceError, OSError) as exc:
        print(json.dumps({
            "standing": "REJECTED",
            "capitalAuthority": "NONE",
            "reason": str(exc) if isinstance(exc, CandidateEvidenceError) else "input unreadable",
        }, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
