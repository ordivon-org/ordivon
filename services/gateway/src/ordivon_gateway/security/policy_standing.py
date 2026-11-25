"""Bounded qualification of actual Security decision witnesses, not authorization.

The producer owns policy evaluation. This consumer never reads policy data,
counts grants, mints principals or promotes a Gateway release.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from typing import Any

from .authorization_targets import resolve_authorization_target
from .pdp_wire import decode_object

MAX_AGE_MS = 15000
MAX_CLOCK_SKEW_MS = 1000
_SHA = re.compile(r"sha256:[0-9a-f]{64}")
_COMMITMENT = re.compile(r"hmac-sha256:[0-9a-f]{64}")
_PRINCIPAL = re.compile(r"principal:cf-access:[0-9a-f]{64}")
_REVISION = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")


def _matches(pattern: re.Pattern[str], value: Any) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _uuid(value: Any) -> bool:
    try:
        return isinstance(value, str) and str(uuid.UUID(value)) == value
    except ValueError:
        return False


def _sha(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class StandingExpectation:
    policy_sha256: str
    release_revision: str
    issuer: str
    permit_principal: str
    deny_principal: str
    message_ref: str

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> StandingExpectation:
        fields = {
            "policySha256",
            "releaseRevision",
            "issuer",
            "permitPrincipal",
            "denyPrincipal",
            "messageRef",
        }
        if set(document) != fields:
            raise ValueError("invalid standing expectation fields")
        if not all(
            isinstance(v, str)
            and 0 < len(v.encode("utf-8")) <= 512
            and v.strip() == v
            and not any(ord(c) < 32 or ord(c) == 127 for c in v)
            for v in document.values()
        ):
            raise ValueError("invalid standing expectation value")
        if (
            not _matches(_SHA, document["policySha256"])
            or not _matches(_REVISION, document["releaseRevision"])
            or not _matches(_PRINCIPAL, document["permitPrincipal"])
            or not _matches(_PRINCIPAL, document["denyPrincipal"])
            or document["permitPrincipal"] == document["denyPrincipal"]
            or not document["messageRef"].startswith("message:")
        ):
            raise ValueError("standing expectation identities invalid")
        expectation = cls(
            document["policySha256"],
            document["releaseRevision"],
            document["issuer"],
            document["permitPrincipal"],
            document["denyPrincipal"],
            document["messageRef"],
        )
        # Resolve the real existing protected read target, not a duplicate Rego contract.
        expectation.payload(permit=True)
        return expectation

    def payload(self, *, permit: bool) -> bytes:
        target = resolve_authorization_target("message.get", {"messageRef": self.message_ref})
        if target is None or target.capability != "host.legacy-read":
            raise ValueError("exact Host read target is unqualified")
        payload = {
            "subject": {
                "type": "user",
                "id": self.permit_principal if permit else self.deny_principal,
                "properties": {"issuer": self.issuer},
            },
            "resource": target.authzen_resource(),
            "action": {"name": target.capability, "properties": {"gatewayTool": "message.get"}},
        }
        # The Security producer normalizes parsed JSON with these exact options.
        # Sending this representation avoids any ambiguity about numeric or key order.
        return json.dumps(
            payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class DecisionWitness:
    request_id: str
    instance_id: str
    policy_data_commitment: str
    evaluated_at_ms: int
    input_sha256: str


def qualify_decision(
    expectation: StandingExpectation,
    *,
    permit: bool,
    request_id: str,
    response_request_id: str | None,
    cache_control: str | None,
    response: bytes,
    started_ms: int,
    received_ms: int,
) -> DecisionWitness:
    body = decode_object(response)
    context = body.get("context")
    if (
        set(body) != {"decision", "context"}
        or not _uuid(request_id)
        or response_request_id != request_id
        or cache_control != "no-store"
        or body.get("decision") is not permit
        or not isinstance(context, dict)
        or not set(context) <= {"ordivonPolicyStanding", "obligations"}
        or ("obligations" in context and context["obligations"] != [])
    ):
        raise ValueError("standing decision or response correlation invalid")
    row = context.get("ordivonPolicyStanding")
    fields = {
        "schemaVersion",
        "standing",
        "requestId",
        "instanceId",
        "policySha256",
        "policyDataCommitment",
        "inputSha256",
        "declaredReleaseRevision",
        "evaluatedAtEpochMs",
    }
    if (
        not isinstance(row, dict)
        or set(row) != fields
        or type(row["schemaVersion"]) is not int
        or row["schemaVersion"] != 1
        or row["standing"] != "OBSERVED_FOR_DECISION"
        or row["requestId"] != request_id
        or not _uuid(row["instanceId"])
        or row["policySha256"] != expectation.policy_sha256
        or row["declaredReleaseRevision"] != expectation.release_revision
        or not _matches(_COMMITMENT, row["policyDataCommitment"])
        or row["inputSha256"] != _sha(expectation.payload(permit=permit))
    ):
        raise ValueError("standing identity or input binding invalid")
    evaluated = row["evaluatedAtEpochMs"]
    if (
        type(evaluated) is not int
        or received_ms < started_ms
        or received_ms - started_ms > MAX_AGE_MS
        or not started_ms - MAX_CLOCK_SKEW_MS <= evaluated <= received_ms + MAX_CLOCK_SKEW_MS
        or received_ms - evaluated > MAX_AGE_MS
    ):
        raise ValueError("standing freshness invalid")
    return DecisionWitness(
        request_id, row["instanceId"], row["policyDataCommitment"], evaluated, row["inputSha256"]
    )


def qualify_pair(permit: DecisionWitness, deny: DecisionWitness, *, now_ms: int) -> dict[str, Any]:
    if (
        permit.request_id == deny.request_id
        or permit.input_sha256 == deny.input_sha256
        or permit.instance_id != deny.instance_id
        or permit.policy_data_commitment != deny.policy_data_commitment
        or deny.evaluated_at_ms < permit.evaluated_at_ms
        or now_ms - permit.evaluated_at_ms > MAX_AGE_MS
        or deny.evaluated_at_ms > now_ms + MAX_CLOCK_SKEW_MS
    ):
        raise ValueError("standing pair is not one fresh policy observation")
    # No subjects, private data, bearer, or opaque data commitment in report.
    return {
        "standing": "OBSERVED_FOR_EXACT_READ_PAIR",
        "permitRequestId": permit.request_id,
        "denyRequestId": deny.request_id,
        "instanceId": permit.instance_id,
        "evaluatedAtEpochMs": deny.evaluated_at_ms,
        "truthBoundary": "two observed Security decisions, not a grant inventory or release GO",
    }
