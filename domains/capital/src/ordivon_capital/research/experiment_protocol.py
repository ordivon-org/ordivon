"""Pure, non-trading evidence boundary for agent-proposed finance experiments.

This gate verifies declared temporal/provenance consistency. It cannot attest that a
provider actually published the inputs, that trials were exhaustively disclosed, or
that an investment edge exists. Independent replication and governance own those
separate claims. Nothing returned here can authorize an order.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")

_PLAN_FIELDS = frozenset({
    "schemaVersion", "kind", "hypothesisId", "effectBoundary", "frozenAt",
    "codeRevision", "configDigest", "environmentDigest", "trialsPlanned",
    "baselineId", "metricDefinition", "partitions", "historicalSources",
})
_RESULT_FIELDS = frozenset({
    "planDigest", "evaluatedAt", "observedThrough", "availableAt",
    "holdoutDigest", "trialsEvaluated", "multiplicityControl",
    "costModelDigest", "benchmarkEvidenceDigest", "independentReproduction",
})
_FROZEN_FIELDS = frozenset({
    "schemaVersion", "kind", "planDigest", "plan", "authority", "attestation",
})


class ExperimentContractError(ValueError):
    """A plan is not structurally suitable for freezing."""


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ExperimentContractError(f"{field} must be a timestamp string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ExperimentContractError(f"{field} invalid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ExperimentContractError(f"{field} must have a UTC offset")
    return parsed.astimezone(UTC)


def _date(value: Any, field: str) -> date:
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        raise ExperimentContractError(f"{field} must be YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ExperimentContractError(f"{field} invalid ISO date") from exc


def _digest(value: Any, field: str) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ExperimentContractError(f"{field} requires canonical sha256:<64 lowercase hex>")


def _nonblank(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ExperimentContractError(f"{field} must be a nonempty string")


def freeze_experiment_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Bind a declared pre-holdout research cut to exact, replayable bytes.

    Plan digests provide local content identity, not an external timestamp
    attestation. The caller must persist this artifact before holdout observation.
    """
    if not isinstance(plan, Mapping):
        raise ExperimentContractError("plan must be an object")
    if set(plan) != _PLAN_FIELDS:
        raise ExperimentContractError("plan keys must match the declared research contract")
    if type(plan.get("schemaVersion")) is not int or plan["schemaVersion"] != 1 or plan.get("kind") != "ordivon.capital.research.plan":
        raise ExperimentContractError("unsupported plan identity")
    if plan.get("effectBoundary") != "RESEARCH_ONLY":
        raise ExperimentContractError("a research plan cannot request external effects")
    for field in ("hypothesisId", "baselineId", "metricDefinition"):
        _nonblank(plan.get(field), field)
    revision = plan.get("codeRevision")
    if not isinstance(revision, str) or _COMMIT.fullmatch(revision) is None:
        raise ExperimentContractError("codeRevision must be a 40-character Git SHA-1")
    for field in ("configDigest", "environmentDigest"):
        _digest(plan.get(field), field)
    trials = plan.get("trialsPlanned")
    if type(trials) is not int or trials < 1:
        raise ExperimentContractError("trialsPlanned must be a positive integer")

    frozen_at = _timestamp(plan.get("frozenAt"), "frozenAt")
    partitions = plan.get("partitions")
    if not isinstance(partitions, Mapping) or set(partitions) != {"train", "validation", "holdout"}:
        raise ExperimentContractError("partitions must contain only train, validation and holdout")
    spans: dict[str, tuple[date, date]] = {}
    for stage in ("train", "validation", "holdout"):
        row = partitions.get(stage)
        if not isinstance(row, Mapping) or set(row) != {"start", "end"}:
            raise ExperimentContractError(f"partition {stage} must have exact start/end")
        start = _date(row.get("start"), f"{stage}.start")
        end = _date(row.get("end"), f"{stage}.end")
        if start > end:
            raise ExperimentContractError(f"{stage} has reversed bounds")
        spans[stage] = start, end
    if not (spans["train"][1] < spans["validation"][0] and
            spans["validation"][1] < spans["holdout"][0]):
        raise ExperimentContractError("train, validation and holdout must not overlap")
    if spans["validation"][1] > frozen_at.date():
        raise ExperimentContractError("validation cannot contain future observations")
    if spans["holdout"][0] <= frozen_at.date():
        raise ExperimentContractError("prospective holdout must start after the freeze date")

    sources = plan.get("historicalSources")
    if not isinstance(sources, list) or not sources:
        raise ExperimentContractError("historicalSources must be nonempty")
    identities: set[str] = set()
    for index, row in enumerate(sources):
        if not isinstance(row, Mapping) or set(row) != {
            "sourceId", "snapshotDigest", "observedThrough", "availableAt"
        }:
            raise ExperimentContractError(f"source {index} must have exact provenance fields")
        source_id = row.get("sourceId")
        _nonblank(source_id, f"source {index}.sourceId")
        if source_id in identities:
            raise ExperimentContractError("duplicate historical source identity")
        identities.add(source_id)
        _digest(row.get("snapshotDigest"), f"source {index}.snapshotDigest")
        observed = _timestamp(row.get("observedThrough"), f"source {index}.observedThrough")
        available = _timestamp(row.get("availableAt"), f"source {index}.availableAt")
        if observed > available or available > frozen_at:
            raise ExperimentContractError("historical source unavailable at frozen research cut")

    try:
        canonical = json.dumps(plan, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ExperimentContractError("plan must be canonical JSON") from exc
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.research.frozen-plan",
        "planDigest": f"sha256:{digest}",
        "plan": json.loads(canonical),
        "authority": "NONE",
        "attestation": "CALLER_DECLARED_NOT_INDEPENDENTLY_VERIFIED",
    }


def assess_holdout_evidence(
    frozen: Mapping[str, Any], result: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Return UNKNOWN, REJECTED, or REVIEW_REQUIRED; never authorize trading."""
    reasons: list[str] = []
    status = "UNKNOWN"
    if (
        not isinstance(frozen, Mapping)
        or set(frozen) != _FROZEN_FIELDS
        or type(frozen.get("schemaVersion")) is not int
        or frozen["schemaVersion"] != 1
        or frozen.get("kind") != "ordivon.capital.research.frozen-plan"
        or frozen.get("authority") != "NONE"
        or frozen.get("attestation") != "CALLER_DECLARED_NOT_INDEPENDENTLY_VERIFIED"
    ):
        return _assessment("REJECTED", ["FROZEN_RECEIPT_IDENTITY_INVALID"])
    try:
        expected = freeze_experiment_plan(frozen.get("plan", {}))["planDigest"]
    except ExperimentContractError:
        return _assessment("REJECTED", ["FROZEN_PLAN_CONTRACT_INVALID"])
    if frozen.get("planDigest") != expected:
        return _assessment("REJECTED", ["FROZEN_PLAN_DIGEST_MISMATCH"])
    if not isinstance(result, Mapping):
        return _assessment("UNKNOWN", ["NO_HOLDOUT_EVIDENCE"])
    if set(result) != _RESULT_FIELDS:
        return _assessment("UNKNOWN", ["UNSUPPORTED_OR_MISSING_RESULT_FIELDS"])
    if result.get("planDigest") != expected:
        return _assessment("REJECTED", ["RESULT_PLAN_IDENTITY_MISMATCH"])

    plan = frozen["plan"]
    try:
        evaluated = _timestamp(result.get("evaluatedAt"), "evaluatedAt")
        observed = _timestamp(result.get("observedThrough"), "observedThrough")
        available = _timestamp(result.get("availableAt"), "availableAt")
        holdout_end = _date(plan["partitions"]["holdout"]["end"], "holdout.end")
        if observed.date() < holdout_end or observed > available or available > evaluated:
            return _assessment("REJECTED", ["HOLDOUT_TEMPORAL_EVIDENCE_CONTRADICTION"])
        if evaluated <= _timestamp(plan["frozenAt"], "frozenAt"):
            return _assessment("REJECTED", ["EVALUATION_PRECEDES_FREEZE"])
        _digest(result.get("holdoutDigest"), "holdoutDigest")
    except ExperimentContractError:
        reasons.append("HOLDOUT_PROVENANCE_INCOMPLETE")

    trials = result.get("trialsEvaluated")
    planned = plan["trialsPlanned"]
    if type(trials) is not int or trials < planned:
        reasons.append("TRIAL_DISCLOSURE_INCOMPLETE")
    elif trials > 1 and result.get("multiplicityControl") != "DOCUMENTED":
        reasons.append("MULTIPLE_TESTING_UNRESOLVED")

    for field, reason in (
        ("costModelDigest", "COST_EVIDENCE_INCOMPLETE"),
        ("benchmarkEvidenceDigest", "BENCHMARK_EVIDENCE_INCOMPLETE"),
    ):
        try:
            _digest(result.get(field), field)
        except ExperimentContractError:
            reasons.append(reason)

    independent = result.get("independentReproduction")
    if independent is False:
        return _assessment("REJECTED", ["INDEPENDENT_REPRODUCTION_FAILED", *reasons])
    if independent is not True:
        reasons.append("INDEPENDENT_REPRODUCTION_UNKNOWN")
    if not reasons:
        status = "REVIEW_REQUIRED"
    return _assessment(status, reasons)


def _assessment(standing: str, reasons: list[str]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.research.evidence-assessment",
        "standing": standing,
        "reasons": reasons,
        "externalWriteAllowed": False,
        "capitalAllocationAuthorized": False,
    }



# This is a thin source-only composition of the existing frozen research
# protocol with the existing byte-verified candidate evaluator.  It is not a
# second backtester, model-validation platform, or independent witness.
_PRECOMMIT_FIELDS = frozenset({
    "schemaVersion", "kind", "candidateId", "hypothesis", "frozenAt",
    "trialCount", "currency", "costCoverage",
    "strategyAssetWeight", "benchmarkExpenseFraction",
})
_COST_FIELDS = frozenset({"fees", "slippage", "financing", "taxes"})


def _policy_decimal(value: Any, label: str) -> str:
    if type(value) is not str:
        raise ExperimentContractError(f"{label} must be a decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ExperimentContractError(f"{label} must be a finite decimal") from exc
    if not parsed.is_finite() or not Decimal(0) <= parsed <= Decimal(1):
        raise ExperimentContractError(f"{label} outside [0,1]")
    return str(parsed.normalize())


def candidate_policy_digest(candidate: Mapping[str, Any]) -> str:
    """Commit to candidate weights, fees and trial family BEFORE seeing holdout.

    Only the precommitment projection is included. Future source/holdout
    digests must NOT be in the policy because they cannot exist at freeze time.
    """
    if not isinstance(candidate, Mapping) or not _PRECOMMIT_FIELDS <= set(candidate):
        raise ExperimentContractError("candidate precommitment fields incomplete")
    if candidate.get("schemaVersion") != 2 or candidate.get("kind") != (
        "ordivon.capital.finance.replayable-research-candidate"
    ):
        raise ExperimentContractError("replayable candidate v2 required")
    for key in ("candidateId", "hypothesis"):
        _nonblank(candidate.get(key), key)
    if type(candidate.get("trialCount")) is not int or candidate["trialCount"] < 1:
        raise ExperimentContractError("trialCount must be positive integer")
    if not isinstance(candidate.get("currency"), str) or re.fullmatch(
        r"[A-Z]{3}", candidate["currency"]
    ) is None:
        raise ExperimentContractError("currency must be uppercase three-letter code")
    costs = candidate.get("costCoverage")
    if (
        type(costs) is not list
        or len(costs) != len(_COST_FIELDS)
        or not all(type(item) is str for item in costs)
        or set(costs) != _COST_FIELDS
    ):
        raise ExperimentContractError("costCoverage must list all four unique costs")
    policy = {key: candidate[key] for key in _PRECOMMIT_FIELDS}
    policy["frozenAt"] = _timestamp(candidate["frozenAt"], "frozenAt").isoformat()
    policy["strategyAssetWeight"] = _policy_decimal(
        candidate["strategyAssetWeight"], "strategyAssetWeight"
    )
    policy["benchmarkExpenseFraction"] = _policy_decimal(
        candidate["benchmarkExpenseFraction"], "benchmarkExpenseFraction"
    )
    policy["costCoverage"] = sorted(costs)
    encoded = json.dumps(policy, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def review_replayed_candidate(
    *,
    frozen: Mapping[str, Any],
    manifest: Mapping[str, Any],
    source_bytes: bytes,
    holdout_bytes: bytes,
    evaluated_at: str,
) -> dict[str, Any]:
    """Compose TWO existing owners' pure evaluations with exact policy identity.

    Honest standing is at most UNKNOWN without provider and independent
    reproduction attestations. Same-repo recomputation is not independent.
    """
    from .investment_candidate import CandidateEvidenceError, evaluate_investment_candidate

    def reject(reason: str) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.capital.research.composed-review",
            "standing": "REJECTED",
            "reasons": [reason],
            "capitalAuthority": "NONE",
            "externalWriteAllowed": False,
        }

    receipt = assess_holdout_evidence(frozen, None)
    if receipt["standing"] == "REJECTED":
        return reject("INVALID_FROZEN_EXPERIMENT")
    if not isinstance(manifest, Mapping) or type(manifest.get("schemaVersion")) is not int:
        return reject("UNSUPPORTED_CANDIDATE")
    if manifest.get("schemaVersion") != 2:
        return reject("V2_SOURCE_REPLAY_REQUIRED")
    plan = frozen["plan"]
    if manifest.get("candidateId") != plan["hypothesisId"]:
        return reject("CANDIDATE_ID_NOT_PRECOMMITTED")
    if manifest.get("trialCount") != plan["trialsPlanned"]:
        return reject("TRIAL_FAMILY_CHANGED_AFTER_FREEZE")
    try:
        if _timestamp(manifest.get("frozenAt"), "candidate.frozenAt") != _timestamp(
            plan["frozenAt"], "plan.frozenAt"
        ):
            return reject("FREEZE_TIME_IDENTITY_MISMATCH")
        if candidate_policy_digest(manifest) != plan["configDigest"]:
            return reject("PRECOMMITTED_POLICY_MISMATCH")
        evaluation = evaluate_investment_candidate(
            manifest=dict(manifest),
            source_bytes=source_bytes,
            holdout_bytes=holdout_bytes,
        )
    except (ExperimentContractError, CandidateEvidenceError, TypeError, ValueError):
        return reject("SOURCE_REPLAY_OR_POLICY_INVALID")

    # The evaluator has already checked strict row identities and chronological
    # instants. Read only the accepted timestamp projection; do not recompute
    # investment economics or invent continuous daily-market observations.
    records = json.loads(holdout_bytes)
    start = _date(plan["partitions"]["holdout"]["start"], "holdout.start")
    end = _date(plan["partitions"]["holdout"]["end"], "holdout.end")
    observations = [
        _timestamp(row["periodEndAt"], "periodEndAt") for row in records
    ]
    if observations[0].date() < start or observations[-1].date() > end:
        return reject("CANDIDATE_OBSERVATIONS_OUTSIDE_PRECOMMITTED_HOLDOUT")
    if observations[-1].date() < end:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.capital.research.composed-review",
            "standing": "UNKNOWN",
            "reasons": ["PROSPECTIVE_HOLDOUT_INCOMPLETE"],
            "frozenPlanDigest": frozen["planDigest"],
            "candidateId": manifest["candidateId"],
            "capitalAuthority": "NONE",
            "externalWriteAllowed": False,
        }
    available = max(
        _timestamp(row["availableAt"], "holdout.availableAt") for row in records
    )
    cost_projection = [
        {key: row[key] for key in sorted(_COST_FIELDS)} for row in records
    ]
    cost_bytes = json.dumps(cost_projection, sort_keys=True, separators=(",", ":")).encode()
    # Source bytes are not attested market observations: this digest only
    # binds the content the local source-replay evaluator consumed.
    source_digest = "sha256:" + hashlib.sha256(source_bytes).hexdigest()
    result = {
        "planDigest": frozen["planDigest"],
        "evaluatedAt": evaluated_at,
        "observedThrough": observations[-1].isoformat(),
        "availableAt": available.isoformat(),
        "holdoutDigest": "sha256:" + hashlib.sha256(holdout_bytes).hexdigest(),
        "trialsEvaluated": manifest["trialCount"],
        "multiplicityControl": "UNKNOWN",
        "costModelDigest": "sha256:" + hashlib.sha256(cost_bytes).hexdigest(),
        "benchmarkEvidenceDigest": source_digest,
        "independentReproduction": None,
    }
    assessment = assess_holdout_evidence(frozen, result)
    if assessment["standing"] == "REJECTED":
        return reject("PROSPECTIVE_EVIDENCE_TEMPORAL_CONTRADICTION")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.research.composed-review",
        "standing": "UNKNOWN",
        "reasons": assessment["reasons"] + [
            "PROVIDER_AND_FREEZE_ATTESTATION_UNVERIFIED"
        ],
        "frozenPlanDigest": frozen["planDigest"],
        "candidateId": manifest["candidateId"],
        "sourceToReturnRecomputationVerified": evaluation[
            "sourceToReturnRecomputationVerified"
        ],
        "sourceObservationProvenanceVerified": False,
        "economicSummary": evaluation["economicSummary"],
        "capitalAuthority": "NONE",
        "externalWriteAllowed": False,
    }
