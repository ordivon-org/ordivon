"""Join existing wake and SEND evidence for a future exact-result observation.

This module neither observes a browser nor authorizes a provider action. DOM
append evidence is corroboration, not a provider-issued identity certificate.
"""

from __future__ import annotations

import hashlib
import re

import rfc8785

try:
    from chatgpt_provider_resource import canonical_chatgpt_resource
    from standard_identifiers import require_uuid7
except ModuleNotFoundError:
    from scripts.chatgpt_provider_resource import canonical_chatgpt_resource
    from scripts.standard_identifiers import require_uuid7


def _digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None


def _bounded(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", value) is not None


def require_wake_mapping(
    campaign_ref: str, agent_id: str, wake_intent_id: str, mapping: dict
) -> str:
    if (
        not _digest(campaign_ref)
        or not isinstance(agent_id, str)
        or not agent_id
        or agent_id != agent_id.strip()
        or not isinstance(wake_intent_id, str)
        or not wake_intent_id
        or wake_intent_id != wake_intent_id.strip()
        or not isinstance(mapping, dict)
        or type(mapping.get("schemaVersion")) is not int
        or mapping["schemaVersion"] != 1
        or mapping.get("kind") != "ordivon.wake-turn-mapping"
        or mapping.get("disposition") != "existing"
        or mapping.get("providerEffectAttempted") is not False
        or (mapping.get("campaignRef"), mapping.get("agentId"), mapping.get("wakeIntentId"))
        != (campaign_ref, agent_id, wake_intent_id)
        or not _digest(mapping.get("promptDigest"))
    ):
        raise ValueError("wake result mapping identity conflict")
    return require_uuid7(mapping.get("turnRequestId"), "turnRequestId")


def resolve_wake_result_identity(
    campaign_ref: str,
    agent_id: str,
    wake_intent_id: str,
    mapping: dict | None,
    effect: dict | None,
) -> dict:
    """Return a scoped read plan, never provider content or release authority."""
    if (
        not _digest(campaign_ref)
        or not isinstance(agent_id, str)
        or not agent_id.strip()
        or not isinstance(wake_intent_id, str)
        or not wake_intent_id.strip()
    ):
        raise ValueError("wake result request identity invalid")
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.wake-result-identity",
        "campaignRef": campaign_ref,
        "agentId": agent_id,
        "wakeIntentId": wake_intent_id,
        "turnRequestId": None,
        "promptDigest": None,
        "targetResource": None,
        "domUserMessageId": None,
        "connectorKind": None,
        "connectorRef": None,
        "effectReceiptDigest": None,
        "evidenceScope": None,
        "standing": "WAKE_NOT_OBSERVED",
        "providerEffectAttempted": False,
        "assistantOutputRead": False,
        "safeToResend": False,
        "releaseAuthorized": False,
    }
    if mapping is None:
        return result
    turn_id = require_wake_mapping(campaign_ref, agent_id, wake_intent_id, mapping)
    prompt_digest = mapping["promptDigest"]
    result.update(turnRequestId=turn_id, promptDigest=prompt_digest, standing="EFFECT_NOT_OBSERVED")
    if effect is None:
        return result
    if not isinstance(effect, dict):
        return {**result, "standing": "EFFECT_EVIDENCE_INVALID"}
    if effect.get("promptDigest") != prompt_digest:
        raise ValueError("wake and effect prompt identities conflict")
    if effect.get("state") == "UNKNOWN":
        return {**result, "standing": "EFFECT_UNKNOWN"}
    result["standing"] = "EFFECT_EVIDENCE_INVALID"
    if effect.get("state") != "COMPLETED":
        return result
    target = effect.get("targetCoordinate")
    try:
        if not isinstance(target, str) or canonical_chatgpt_resource(target) != target:
            return result
    except ValueError:
        return result
    receipt = effect.get("receipt")
    if not isinstance(receipt, dict):
        return result
    recorded_digest = receipt.get("receiptDigest")
    if not _digest(recorded_digest):
        return result
    try:
        calculated = (
            "sha256:"
            + hashlib.sha256(
                rfc8785.dumps(
                    {key: value for key, value in receipt.items() if key != "receiptDigest"}
                )
            ).hexdigest()
        )
    except ValueError, TypeError, UnicodeError:
        return result
    if (
        calculated != recorded_digest
        or type(receipt.get("schemaVersion")) is not int
        or receipt["schemaVersion"] != 1
        or receipt.get("kind") != "ordivon.browserless-turn-receipt"
        or (
            receipt.get("turnRequestId"),
            receipt.get("promptDigest"),
            receipt.get("targetResource"),
        )
        != (turn_id, prompt_digest, target)
        or receipt.get("observedResourceBeforeSend") != target
        or receipt.get("observedResourceAfterSend") != target
        or not all(
            receipt.get(key) is True
            for key in (
                "historyHydratedBeforeSend",
                "composerCleared",
                "generationStarted",
                "targetStillBoundAfterSend",
            )
        )
        or receipt.get("assistantOutputRead") is not False
    ):
        return result
    connector = receipt.get("connectorKind")
    if connector == "browserless":
        connector_ref = receipt.get("browserlessEndpointId")
        if not _bounded(connector_ref) or "sessionId" in receipt:
            return result
    elif connector == "cft-human-session":
        if "browserlessEndpointId" in receipt:
            return result
        try:
            connector_ref = require_uuid7(receipt.get("sessionId"), "sessionId")
        except ValueError:
            return result
    else:
        return result

    result.update(
        targetResource=target,
        effectReceiptDigest=recorded_digest,
        standing="SEND_OBSERVED_RESULT_IDENTITY_UNAVAILABLE",
    )
    witness = receipt.get("observedUserAppendWitness")
    if witness is None:
        return result
    result["standing"] = "RESULT_WITNESS_INVALID"
    if not isinstance(witness, dict):
        return result
    prior = witness.get("previousUserCount")
    after = witness.get("observedUserCount")
    message_id = witness.get("domUserMessageId")
    if (
        type(witness.get("schemaVersion")) is not int
        or witness["schemaVersion"] != 1
        or witness.get("kind") != "ordivon.dom-user-append-witness"
        or witness.get("evidenceScope") != "OBSERVED_DOM_APPEND_ONLY"
        or (witness.get("targetResource"), witness.get("promptDigest")) != (target, prompt_digest)
        or not _bounded(message_id)
        or type(prior) is not int
        or prior < 1
        or type(after) is not int
        or after != prior + 1
        or not _digest(witness.get("previousUserIdentityDigest"))
        or not _digest(witness.get("observedUserIdentityDigest"))
        or witness["previousUserIdentityDigest"] == witness["observedUserIdentityDigest"]
    ):
        return result
    return {
        **result,
        "standing": "OBSERVATION_IDENTITY_QUALIFIED",
        "evidenceScope": "OBSERVED_DOM_APPEND_ONLY",
        "connectorKind": connector,
        "connectorRef": connector_ref,
        "domUserMessageId": message_id,
    }
