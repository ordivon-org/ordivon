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
