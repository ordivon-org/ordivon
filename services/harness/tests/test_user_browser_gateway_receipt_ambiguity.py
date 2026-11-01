from __future__ import annotations

import json

import pytest

from ordivon_harness.user_browser_gateway import UserBrowserGatewayController


def valid_attempt() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.windows-user-browser-attempt",
        "effectId": "effect-bound-1",
        "standing": "bound",
        "providerResource": "https://chatgpt.com/c/test-valid",
        "evidenceDigest": "sha256:" + "a" * 64,
        "detail": "bound to conversation",
        "providerEffectAttempted": True,
    }


def valid_classification() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.windows-user-browser-classification",
        "standing": "READY",
        "detail": "ready",
        "providerEffectAttempted": False,
    }


def test_attempt_rejects_boolean_schema_version():
    payload = valid_attempt()
    payload["schemaVersion"] = True
    with pytest.raises(RuntimeError, match="schema"):
        UserBrowserGatewayController._parse_payload(
            json.dumps(payload), effect_id="effect-bound-1"
        )


def test_attempt_rejects_nonhex_evidence_digest():
    payload = valid_attempt()
    payload["evidenceDigest"] = "sha256:" + "g" * 64
    with pytest.raises(RuntimeError, match="digest"):
        UserBrowserGatewayController._parse_payload(
            json.dumps(payload), effect_id="effect-bound-1"
        )


def test_attempt_rejects_duplicate_effect_identity_even_when_last_wins():
    raw = json.dumps(valid_attempt())[:-1] + ', "effectId":"effect-bound-1"}'
    with pytest.raises(RuntimeError, match="duplicate"):
        UserBrowserGatewayController._parse_payload(raw, effect_id="effect-bound-1")


def test_classification_rejects_boolean_schema_version():
    payload = valid_classification()
    payload["schemaVersion"] = True
    with pytest.raises(RuntimeError, match="schema"):
        UserBrowserGatewayController._parse_classification(json.dumps(payload))


def test_classification_rejects_duplicate_standing_even_when_last_wins():
    raw = json.dumps(valid_classification())[:-1] + ', "standing":"READY"}'
    with pytest.raises(RuntimeError, match="duplicate"):
        UserBrowserGatewayController._parse_classification(raw)


def test_downstream_attempt_rejects_noncanonical_digest_without_gateway():
    from scripts.windows_user_browser_materialization_target import UserBrowserAttemptResult

    with pytest.raises(ValueError, match="digest"):
        UserBrowserAttemptResult(
            standing="unknown",
            provider_resource=None,
            evidence_digest="sha256:" + "G" * 64,
            detail="no confirmed send",
            provider_effect_attempted=True,
        )


def test_downstream_attempt_rejects_nonboolean_effect_flag():
    from scripts.windows_user_browser_materialization_target import UserBrowserAttemptResult

    with pytest.raises(ValueError, match="boolean"):
        UserBrowserAttemptResult(
            standing="unknown",
            provider_resource=None,
            evidence_digest="sha256:" + "2" * 64,
            detail="no confirmed send",
            provider_effect_attempted=1,
        )
