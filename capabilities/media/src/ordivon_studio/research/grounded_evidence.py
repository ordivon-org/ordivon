"""Grounded R5 typed evidence and result contracts; provider-independent.

Evidence identity, source locator and allowed claim relations remain explicit.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .grounded_contracts import RELATION_LABELS


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    evidence_id: str
    modality: str
    source_id: str
    locator: dict[str, Any]
    observed: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidenceId": self.evidence_id,
            "modality": self.modality,
            "sourceId": self.source_id,
            "locator": dict(self.locator),
            "observed": self.observed,
        }


def _strict_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be a non-empty trimmed string")
    return value


def validate_evidence_catalog(items: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    for raw in items:
        item = dict(raw)
        evidence_id = _strict_text(item.get("evidenceId"), "evidenceId")
        if evidence_id in catalog:
            raise ValueError(f"duplicate evidence identity: {evidence_id}")
        _strict_text(item.get("modality"), "evidence modality")
        _strict_text(item.get("sourceId"), "evidence sourceId")
        _strict_text(item.get("observed"), "evidence observed text")
        locator = item.get("locator")
        if not isinstance(locator, dict) or not locator:
            raise ValueError("evidence locator must be a non-empty object")
        if "startMs" in locator or "endMs" in locator:
            start = locator.get("startMs")
            end = locator.get("endMs")
            if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
                raise ValueError("time locator must be a positive half-open millisecond range")
        catalog[evidence_id] = item
    return catalog


def validate_grounded_result(result: Mapping[str, Any], evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    catalog = validate_evidence_catalog(evidence)
    value = dict(result)
    claims = value.get("claims", [])
    relations = value.get("relations", [])
    if not isinstance(claims, list) or not isinstance(relations, list):
        raise ValueError("grounded result claims/relations must be arrays")
    known_claims: set[str] = set()
    for raw in claims:
        if not isinstance(raw, dict):
            raise ValueError("grounded claim must be an object")
        claim_id = _strict_text(raw.get("claimId"), "claimId")
        if claim_id in known_claims:
            raise ValueError(f"duplicate claim identity: {claim_id}")
        known_claims.add(claim_id)
        _strict_text(raw.get("statement"), "claim statement")
        refs = raw.get("evidenceIds")
        if not isinstance(refs, list) or not refs or any(ref not in catalog for ref in refs):
            raise ValueError(f"claim {claim_id} has invalid or empty grounding")
    for raw in relations:
        if not isinstance(raw, dict):
            raise ValueError("grounded relation must be an object")
        relation = raw.get("relation")
        if relation not in RELATION_LABELS:
            raise ValueError(f"unsupported experimental relation label: {relation}")
        source = raw.get("sourceClaimId")
        target = raw.get("targetClaimId")
        if source not in known_claims or target not in known_claims:
            raise ValueError("grounded relation references an unknown claim")
        refs = raw.get("evidenceIds")
        if not isinstance(refs, list) or not refs or any(ref not in catalog for ref in refs):
            raise ValueError("grounded relation has invalid or empty evidence grounding")
    return value


def _relation_result_schema(probes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    probe_ids = [str(item["probeId"]) for item in probes]
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "judgments": {
                "type": "array",
                "minItems": len(probe_ids),
                "maxItems": len(probe_ids),
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "probeId": {"type": "string", "enum": probe_ids},
                        "relation": {"type": "string", "enum": list(RELATION_LABELS)},
                        "evidenceIds": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 8,
                            "items": {"type": "string"},
                        },
                        "uncertainty": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                        },
                    },
                    "required": ["probeId", "relation", "evidenceIds", "uncertainty"],
                },
            }
        },
        "required": ["judgments"],
    }
