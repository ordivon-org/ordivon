"""Durable effect evidence is not interchangeable with prompt-text matching."""

from __future__ import annotations

import hashlib
from unittest.mock import Mock

import pytest
import rfc8785

from tests.test_conversation_adopt import config
import agent_automation_browserless as browserless
import postgres_wake_turn_map as pg_wake

CAMPAIGN = "sha256:" + "a" * 64
PROMPT = "sha256:" + "b" * 64
TURN = "018f0000-0000-7000-8000-000000000001"
RESOURCE = "https://chatgpt.com/c/12345678-1234-1234-1234-123456789abc"
WAKE = "wake:synthetic"


def digest(value):
    return "sha256:" + hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def mapping():
    return {
        "schemaVersion": 1,
        "kind": "ordivon.wake-turn-mapping",
        "disposition": "existing",
        "campaignRef": CAMPAIGN,
        "agentId": "A01",
        "wakeIntentId": WAKE,
        "turnRequestId": TURN,
        "promptDigest": PROMPT,
        "createdAtMs": 10,
        "providerEffectAttempted": False,
    }


def effect():
    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.browserless-turn-receipt",
        "turnRequestId": TURN,
        "promptDigest": PROMPT,
        "targetResource": RESOURCE,
        "connectorKind": "browserless",
        "browserlessEndpointId": "isolated-test",
        "observedResourceBeforeSend": RESOURCE,
        "historyHydratedBeforeSend": True,
        "observedResourceAfterSend": RESOURCE,
        "targetStillBoundAfterSend": True,
        "composerCleared": True,
        "generationStarted": True,
        "assistantOutputRead": False,
        "observedUserAppendWitness": {
            "schemaVersion": 1,
            "kind": "ordivon.dom-user-append-witness",
            "evidenceScope": "OBSERVED_DOM_APPEND_ONLY",
            "targetResource": RESOURCE,
            "promptDigest": PROMPT,
            "domUserMessageId": "synthetic-new-user",
            "previousUserCount": 1,
            "observedUserCount": 2,
            "previousUserIdentityDigest": "sha256:" + "c" * 64,
            "observedUserIdentityDigest": "sha256:" + "d" * 64,
        },
    }
    receipt["receiptDigest"] = digest(receipt)
    return {
        "promptDigest": PROMPT,
        "targetCoordinate": RESOURCE,
        "state": "COMPLETED",
        "receipt": receipt,
        "updatedAtMs": 20,
    }


def reseal(row):
    r = row["receipt"]
    r.pop("receiptDigest", None)
    r["receiptDigest"] = digest(r)
    return row


def resolve(m, e):
    from wake_result_identity import resolve_wake_result_identity

    return resolve_wake_result_identity(CAMPAIGN, "A01", WAKE, m, e)


def test_qualified_identity_preserves_exact_connector_and_does_not_deliver_output():
    result = resolve(mapping(), effect())
    assert result["standing"] == "OBSERVATION_IDENTITY_QUALIFIED"
    assert result["turnRequestId"] == TURN
    assert result["domUserMessageId"] == "synthetic-new-user"
    assert result["connectorKind"] == "browserless"
    assert result["connectorRef"] == "isolated-test"
    assert result["effectReceiptDigest"] == effect()["receipt"]["receiptDigest"]
    assert result["providerEffectAttempted"] is False
    assert result["assistantOutputRead"] is False
    assert "assistantOutput" not in result


@pytest.mark.parametrize(
    "field", ["campaignRef", "agentId", "wakeIntentId", "turnRequestId", "promptDigest"]
)
def test_wrong_wake_or_effect_identity_rejected(field):
    m = mapping()
    m[field] = "wrong"
    with pytest.raises(ValueError):
        resolve(m, effect())


@pytest.mark.parametrize(
    "change",
    [
        "unknown",
        "missing",
        "legacy",
        "digest",
        "target",
        "generation",
        "witness-target",
        "witness-prompt",
        "witness-count",
        "witness-id",
        "scope",
        "carrier",
    ],
)
def test_incomplete_or_conflicting_evidence_cannot_qualify(change):
    e = effect()
    if change == "missing":
        e = None
    elif change == "unknown":
        e["state"] = "UNKNOWN"
    elif change == "legacy":
        e["receipt"].pop("observedUserAppendWitness")
        reseal(e)
    elif change == "digest":
        e["receipt"]["browserlessEndpointId"] = "tampered"
    elif change == "target":
        e["receipt"]["targetResource"] = "https://chatgpt.com/c/another-conversation"
        reseal(e)
    elif change == "generation":
        e["receipt"]["generationStarted"] = False
        reseal(e)
    elif change == "carrier":
        e["receipt"]["sessionId"] = TURN
        reseal(e)
    else:
        field = {
            "witness-target": "targetResource",
            "witness-prompt": "promptDigest",
            "witness-count": "observedUserCount",
            "witness-id": "domUserMessageId",
            "scope": "evidenceScope",
        }[change]
        e["receipt"]["observedUserAppendWitness"][field] = (
            "wrong id" if change == "witness-id" else "wrong"
        )
        reseal(e)
    result = resolve(mapping(), e)
    assert result["standing"] != "OBSERVATION_IDENTITY_QUALIFIED"
    assert result.get("domUserMessageId") is None
    assert result["assistantOutputRead"] is False
    assert result["providerEffectAttempted"] is False


def test_old_effect_without_witness_does_not_become_failed_or_resend_permission():
    e = effect()
    e["receipt"].pop("observedUserAppendWitness")
    result = resolve(mapping(), reseal(e))
    assert result["standing"] == "SEND_OBSERVED_RESULT_IDENTITY_UNAVAILABLE"
    assert result["safeToResend"] is False


def test_service_read_uses_pg_authority_and_no_writer_or_fallback(tmp_path, monkeypatch):
    svc = browserless.BrowserlessAutomationService(
        browserless.BrowserlessAutomationConfig.from_dict(config(tmp_path))
    )
    monkeypatch.setenv("ORDIVON_WAKE_TURN_POSTGRES_DSN", "postgresql://test/wake")
    monkeypatch.setenv("ORDIVON_TURN_EFFECT_POSTGRES_DSN", "postgresql://test/effect")
    monkeypatch.setattr(pg_wake.PostgresWakeTurnMap, "read_existing", Mock(return_value=mapping()))
    monkeypatch.setattr(
        pg_wake.PostgresWakeTurnMap,
        "__init__",
        Mock(side_effect=AssertionError("writer forbidden")),
    )
    reader = Mock(return_value=effect())
    monkeypatch.setattr(svc, "_read_pg_turn_effect_row", reader)
    monkeypatch.setattr(svc, "launch_continue", Mock(side_effect=AssertionError("SEND forbidden")))
    monkeypatch.setattr(
        svc, "conversation_affinity", Mock(side_effect=AssertionError("carrier lookup forbidden"))
    )
    result = svc.wake_result_identity(CAMPAIGN, "A01", wake_intent_id=WAKE)
    assert result["standing"] == "OBSERVATION_IDENTITY_QUALIFIED"
    pg_wake.PostgresWakeTurnMap.read_existing.assert_called_once_with(
        "postgresql://test/wake", WAKE
    )
    reader.assert_called_once_with("postgresql://test/effect", TURN, strict_receipt=True)
    assert not svc.launch_continue.called


def test_wrong_owner_is_rejected_before_effect_lookup(tmp_path, monkeypatch):
    svc = browserless.BrowserlessAutomationService(
        browserless.BrowserlessAutomationConfig.from_dict(config(tmp_path))
    )
    monkeypatch.setenv("ORDIVON_WAKE_TURN_POSTGRES_DSN", "postgresql://test/wake")
    monkeypatch.setenv("ORDIVON_TURN_EFFECT_POSTGRES_DSN", "postgresql://test/effect")
    bad = {**mapping(), "agentId": "A02"}
    monkeypatch.setattr(pg_wake.PostgresWakeTurnMap, "read_existing", Mock(return_value=bad))
    reader = Mock(side_effect=AssertionError("must not read unrelated effect"))
    monkeypatch.setattr(svc, "_read_pg_turn_effect_row", reader)
    with pytest.raises(ValueError):
        svc.wake_result_identity(CAMPAIGN, "A01", wake_intent_id=WAKE)
    reader.assert_not_called()


def test_missing_pg_requires_no_legacy_fallback(tmp_path, monkeypatch):
    svc = browserless.BrowserlessAutomationService(
        browserless.BrowserlessAutomationConfig.from_dict(config(tmp_path))
    )
    monkeypatch.delenv("ORDIVON_WAKE_TURN_POSTGRES_DSN", raising=False)
    monkeypatch.delenv("ORDIVON_TURN_EFFECT_POSTGRES_DSN", raising=False)
    monkeypatch.setattr(svc, "_turn_effect_row", Mock(side_effect=AssertionError("no legacy read")))
    with pytest.raises(browserless.BrowserlessAutomationConflict, match="PG"):
        svc.wake_result_identity(CAMPAIGN, "A01", wake_intent_id=WAKE)


def test_duplicate_persisted_receipt_keys_do_not_qualify(tmp_path, monkeypatch):
    import json
    import postgres_turn_effects as pg_effect

    svc = browserless.BrowserlessAutomationService(
        browserless.BrowserlessAutomationConfig.from_dict(config(tmp_path))
    )
    monkeypatch.setenv("ORDIVON_WAKE_TURN_POSTGRES_DSN", "postgresql://test/wake")
    monkeypatch.setenv("ORDIVON_TURN_EFFECT_POSTGRES_DSN", "postgresql://test/effect")
    monkeypatch.setattr(pg_wake.PostgresWakeTurnMap, "read_existing", Mock(return_value=mapping()))
    receipt = json.dumps(effect()["receipt"])
    # Last-wins JSON decoding would recover the otherwise qualified object.
    raw = '{"targetResource":"unrelated",' + receipt[1:]
    monkeypatch.setattr(
        pg_effect.PostgresTurnEffects,
        "read_existing",
        Mock(
            return_value={
                "turn_request_id": TURN,
                "prompt_digest": PROMPT,
                "target_coordinate": RESOURCE,
                "state": "COMPLETED",
                "receipt_json": raw,
                "updated_at_ms": 20,
            }
        ),
    )
    monkeypatch.setattr(
        svc, "_turn_effect_row", Mock(side_effect=AssertionError("legacy-capable read forbidden"))
    )
    result = svc.wake_result_identity(CAMPAIGN, "A01", wake_intent_id=WAKE)
    assert result["standing"] == "EFFECT_EVIDENCE_INVALID"
    assert result["assistantOutputRead"] is False
    pg_effect.PostgresTurnEffects.read_existing.assert_called_once_with(
        "postgresql://test/effect", TURN
    )


def test_native_pg_wake_result_join_with_read_only_recipient(tmp_path, monkeypatch):
    """Opt-in dedicated empty PG DB and a SELECT-only role; no real provider."""
    import os
    import psycopg
    from postgres_turn_effects import PostgresTurnEffects

    dsn = os.environ.get("ORDIVON_PG_WAKE_RESULT_TEST_DSN")
    read_dsn = os.environ.get("ORDIVON_PG_WAKE_RESULT_READ_TEST_DSN")
    if not dsn or not read_dsn:
        pytest.skip("dedicated disposable PG result-identity test DB/reader not provisioned")
    wake = pg_wake.PostgresWakeTurnMap(dsn)
    effects = PostgresTurnEffects(dsn)
    wake.activate_empty_fresh(tmp_path / "absent-wake.sqlite")
    effects.activate_empty_fresh(tmp_path / "absent-effects.sqlite")
    svc = browserless.BrowserlessAutomationService(
        browserless.BrowserlessAutomationConfig.from_dict(config(tmp_path))
    )
    monkeypatch.setenv("ORDIVON_WAKE_TURN_POSTGRES_DSN", read_dsn)
    monkeypatch.setenv("ORDIVON_TURN_EFFECT_POSTGRES_DSN", read_dsn)

    def observe(wake_id=WAKE, agent="A01"):
        return svc.wake_result_identity(CAMPAIGN, agent, wake_intent_id=wake_id)

    assert observe()["standing"] == "WAKE_NOT_OBSERVED"
    mapped = wake.allocate(
        campaign_ref=CAMPAIGN, agent_id="A01", wake_intent_id=WAKE, prompt_digest=PROMPT
    )
    turn = mapped["turnRequestId"]
    assert observe()["standing"] == "EFFECT_NOT_OBSERVED"
    assert effects.claim_before_send(turn, PROMPT, RESOURCE)["admittedToSend"]
    assert observe()["standing"] == "EFFECT_UNKNOWN"
    assert observe()["safeToResend"] is False
    receipt = effect()
    receipt["receipt"]["turnRequestId"] = turn
    effects.record_after_send(turn, PROMPT, RESOURCE, "COMPLETED", reseal(receipt)["receipt"])
    result = observe()
    assert result["standing"] == "OBSERVATION_IDENTITY_QUALIFIED"
    assert result["turnRequestId"] == turn
    assert result["domUserMessageId"] == "synthetic-new-user"
    assert result["assistantOutputRead"] is False and result["releaseAuthorized"] is False
    with pytest.raises(ValueError):
        observe(agent="A02")

    legacy = wake.allocate(
        campaign_ref=CAMPAIGN, agent_id="A01", wake_intent_id="wake:legacy", prompt_digest=PROMPT
    )
    legacy_turn = legacy["turnRequestId"]
    effects.claim_before_send(legacy_turn, PROMPT, RESOURCE)
    row = effect()
    row["receipt"]["turnRequestId"] = legacy_turn
    row["receipt"].pop("observedUserAppendWitness")
    effects.record_after_send(legacy_turn, PROMPT, RESOURCE, "COMPLETED", reseal(row)["receipt"])
    assert observe("wake:legacy")["standing"] == "SEND_OBSERVED_RESULT_IDENTITY_UNAVAILABLE"
    assert not svc.config.turn_ledger.exists()
    with psycopg.connect(read_dsn) as db:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            db.execute("UPDATE ordivon_harness.turn_effects SET state='UNKNOWN'")
