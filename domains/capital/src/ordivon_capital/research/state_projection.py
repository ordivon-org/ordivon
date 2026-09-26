from __future__ import annotations

from datetime import datetime
from typing import Any


class DecisionStateProjectionError(ValueError):
    pass


def _dt(value: Any, *, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise DecisionStateProjectionError(f"{field} must be a non-empty timestamp")
    try:
        out = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DecisionStateProjectionError(f"{field} must be ISO-8601") from exc
    if out.tzinfo is None:
        raise DecisionStateProjectionError(f"{field} must be timezone-aware")
    return out


def validate_state_claim_registry(registry: Any) -> dict[str, Any]:
    if not isinstance(registry, dict):
        raise DecisionStateProjectionError("registry must be an object")
    if registry.get("schemaVersion") != 1:
        raise DecisionStateProjectionError("registry schemaVersion mismatch")
    if registry.get("kind") != "ordivon.capital.decision-state-claim-registry":
        raise DecisionStateProjectionError("registry kind mismatch")
    rows = registry.get("claims")
    if not isinstance(rows, list) or not rows:
        raise DecisionStateProjectionError("registry claims must be non-empty")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise DecisionStateProjectionError("registry claim must be an object")
        required = {"claimKey", "stateTag", "producerClasses", "requiredEvidenceKind"}
        if set(row) != required:
            raise DecisionStateProjectionError("registry claim keys mismatch")
        key = row["claimKey"]
        if not isinstance(key, str) or not key or key in seen:
            raise DecisionStateProjectionError("registry claimKey invalid or duplicate")
        seen.add(key)
        if not isinstance(row["stateTag"], str) or not row["stateTag"]:
            raise DecisionStateProjectionError("stateTag must be non-empty")
        if not isinstance(row["requiredEvidenceKind"], str) or not row["requiredEvidenceKind"]:
            raise DecisionStateProjectionError("requiredEvidenceKind must be non-empty")
        producers = row["producerClasses"]
        if not isinstance(producers, list) or not producers or any(not isinstance(x, str) or not x for x in producers):
            raise DecisionStateProjectionError("producerClasses must be non-empty strings")
    return registry


def _claim_reason(claim: Any, rule: dict[str, Any], as_of: datetime) -> str | None:
    if not isinstance(claim, dict):
        return "CLAIM_NOT_OBJECT"
    required = {"claimId", "claimKey", "producerId", "producerClass", "evidenceKind", "evidenceDigest", "observedAt", "validUntil", "standing"}
    if set(claim) != required:
        return "CLAIM_KEYS_MISMATCH"
    if claim["standing"] != "ACTIVE":
        return "CLAIM_NOT_ACTIVE"
    if claim["producerClass"] not in rule["producerClasses"]:
        return "PRODUCER_CLASS_NOT_ADMITTED"
    if claim["evidenceKind"] != rule["requiredEvidenceKind"]:
        return "EVIDENCE_KIND_MISMATCH"
    digest = claim["evidenceDigest"]
    if not isinstance(digest, str) or not digest.startswith("sha256:") or len(digest) != 71:
        return "EVIDENCE_DIGEST_INVALID"
    try:
        observed = _dt(claim["observedAt"], field="observedAt")
        valid_until = _dt(claim["validUntil"], field="validUntil")
    except DecisionStateProjectionError:
        return "CLAIM_TIME_INVALID"
    if valid_until < observed:
        return "VALIDITY_WINDOW_INVALID"
    if observed > as_of:
        return "CLAIM_FROM_FUTURE"
    if as_of > valid_until:
        return "CLAIM_EXPIRED"
    for field in ("claimId", "producerId"):
        if not isinstance(claim[field], str) or not claim[field]:
            return f"{field.upper()}_INVALID"
    return None


def project_decision_state(*, as_of: str, claims: list[dict[str, Any]], registry: dict[str, Any]) -> dict[str, Any]:
    """Project routing tags from explicit, time-bounded evidence claims."""

    moment = _dt(as_of, field="asOf")
    validate_state_claim_registry(registry)
    if not isinstance(claims, list):
        raise DecisionStateProjectionError("claims must be an array")
    rules = {row["claimKey"]: row for row in registry["claims"]}
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    tags: set[str] = set()
    seen_ids: set[str] = set()
    for claim in claims:
        key = claim.get("claimKey") if isinstance(claim, dict) else None
        rule = rules.get(key)
        if rule is None:
            rejected.append({"claimId": str(claim.get("claimId", "")) if isinstance(claim, dict) else "", "reason": "UNREGISTERED_CLAIM_KEY"})
            continue
        claim_id = claim.get("claimId") if isinstance(claim, dict) else None
        if isinstance(claim_id, str) and claim_id in seen_ids:
            rejected.append({"claimId": claim_id, "reason": "DUPLICATE_CLAIM_ID"})
            continue
        reason = _claim_reason(claim, rule, moment)
        if reason is not None:
            rejected.append({"claimId": str(claim_id or ""), "reason": reason})
            continue
        seen_ids.add(claim_id)
        tags.add(rule["stateTag"])
        accepted.append({
            "claimId": claim["claimId"],
            "claimKey": claim["claimKey"],
            "stateTag": rule["stateTag"],
            "producerId": claim["producerId"],
            "producerClass": claim["producerClass"],
            "evidenceKind": claim["evidenceKind"],
            "evidenceDigest": claim["evidenceDigest"],
            "observedAt": claim["observedAt"],
            "validUntil": claim["validUntil"],
        })
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.decision-state-projection",
        "truthRole": "ROUTING_CONTEXT_DERIVED_FROM_EXPLICIT_CLAIMS_NOT_MARKET_TRUTH",
        "asOf": as_of,
        "stateTags": sorted(tags),
        "acceptedClaims": accepted,
        "rejectedClaims": rejected,
        "investmentRecommendationProduced": False,
        "executionAuthorityGranted": False,
    }
