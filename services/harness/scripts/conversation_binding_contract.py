#!/usr/bin/env python3

"""Storage-neutral conversation binding identity, digest and receipt semantics.

No SQL driver is imported here. Concrete PG/SQLite owners share these rules.

"""

from __future__ import annotations

import hashlib

import json

import re

from typing import Any



try:

    from chatgpt_provider_resource import normalize_provider_resource

    from standard_identifiers import require_uuid7

except ModuleNotFoundError:

    from scripts.chatgpt_provider_resource import normalize_provider_resource

    from scripts.standard_identifiers import require_uuid7



_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

class ConversationBindingConflict(RuntimeError):
    pass

def _text(value: str, label: str, *, max_bytes: int = 4096) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value.encode("utf-8")) > max_bytes
    ):
        raise ValueError(f"{label} must be non-empty, trimmed, and <= {max_bytes} UTF-8 bytes")
    return value

def _digest(value: str, label: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be canonical sha256:<lowercase-hex>")
    return value

def _canonical_digest(value: object) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()

def binding_receipt(row: Any) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.conversation-binding",
            "bindingStanding": "ADOPTED",
            "campaignRef": row["campaign_ref"],
            "agentId": row["agent_id"],
            "providerResource": row["provider_resource"],
            "sessionId": row["session_id"],
            "evidenceDigest": row["evidence_digest"],
            "requestId": row["request_id"],
            "bindingDigest": row["binding_digest"],
            "createdAtMs": int(row["created_at_ms"]),
        }

def validate_binding_payload(
        *,
        campaign_ref: str,
        agent_id: str,
        provider_resource: str,
        session_id: str,
        evidence_digest: str,
        request_id: str,
    ) -> dict[str, str]:
        campaign_ref = _text(campaign_ref, "campaignRef")
        agent_id = _text(agent_id, "agentId", max_bytes=128)
        request_id = _text(request_id, "adoption requestId")
        session_id = require_uuid7(session_id, "sessionId")
        evidence_digest = _digest(evidence_digest, "evidenceDigest")
        provider_resource = normalize_provider_resource(
            _text(provider_resource, "providerResource", max_bytes=8192)
        )
        return {
            "campaignRef": campaign_ref,
            "agentId": agent_id,
            "providerResource": provider_resource,
            "sessionId": session_id,
            "evidenceDigest": evidence_digest,
            "requestId": request_id,
        }
