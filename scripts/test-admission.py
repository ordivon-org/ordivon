#!/usr/bin/env python
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tempfile

from admission import AdmissionError, normalize
from bound_refs import effect_authority_ref, occurrence_ref, provider_observation_ref

ROOT = Path(__file__).resolve().parent.parent
NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)


def envelope(*, mode="read", supported=True, execution="api", requirements=None, interactions=None, authority=False):
    intent = {
        "schemaVersion": 2,
        "intentId": "intent:test:1",
        "occurrenceRef": "sha256:" + "0" * 64,
        "artifact": {"sha256": "sha256:" + "a" * 64},
        "carrier": {"adapter": "test-adapter", "provider": "test-provider", "accountRef": "account:test"},
        "effect": {"name": "publish" if mode != "read" else "read_back"},
    }
    intent["occurrenceRef"] = occurrence_ref(intent)
    provider = {
        "schemaVersion": 2,
        "observationRef": "sha256:" + "0" * 64,
        "occurrenceRef": intent["occurrenceRef"],
        "provider": intent["carrier"]["provider"],
        "accountRef": intent["carrier"]["accountRef"],
        "adapter": intent["carrier"]["adapter"],
        "effectName": intent["effect"]["name"],
        "effectMode": mode,
        "effectSupported": supported,
        "executionMode": execution,
        "missingProviderRequirements": requirements or [],
        "missingInteractions": interactions or [],
        "sourceKind": "provider_api",
        "sourceRef": "provider:test:observation:1",
        "observedAt": "2026-09-11T11:00:00Z",
        "validUntil": "2026-09-11T13:00:00Z",
    }
    provider["observationRef"] = provider_observation_ref(provider)
    auth = None
    if authority:
        auth = {
            "schemaVersion": 2,
            "authorityRef": "sha256:" + "0" * 64,
            "occurrenceRef": intent["occurrenceRef"],
            "principalRef": "principal:test",
            "provider": intent["carrier"]["provider"],
            "accountRef": intent["carrier"]["accountRef"],
            "effectName": intent["effect"]["name"],
            "decision": "grant",
            "issuedAt": "2026-09-11T11:30:00Z",
            "validUntil": "2026-09-11T12:30:00Z",
            "sourceRef": "runtime-authority:test:1",
        }
        auth["authorityRef"] = effect_authority_ref(auth)
    return {"schemaVersion": 2, "intent": intent, "providerObservation": provider, "effectAuthority": auth}


def opa_action(normalized: dict) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(normalized, handle)
        path = Path(handle.name)
    try:
        result = subprocess.run(
            ["opa", "eval", "--format", "raw", "--data", str(ROOT / "policy/distribution.rego"), "--input", str(path), "data.ordivon.distribution.decision.action"],
            check=True, text=True, capture_output=True,
        )
        return result.stdout.strip()
    finally:
        path.unlink(missing_ok=True)


def expect_action(name: str, value: dict, expected: str) -> None:
    actual = opa_action(normalize(value, NOW))
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected}, got {actual}")
    print(f"PASS {name} -> {actual}")


def expect_deny(name: str, value: dict, contains: str) -> None:
    try:
        normalize(value, NOW)
    except AdmissionError as exc:
        if contains not in str(exc):
            raise AssertionError(f"{name}: wrong denial: {exc}") from exc
        print(f"PASS {name} admission denied")
        return
    raise AssertionError(f"{name}: expected admission denial")


def main() -> int:
    expect_action("read-ready", envelope(), "preflight_ready")
    expect_action("write-needs-authority", envelope(mode="write"), "user_action_required")
    expect_action("write-bound-authority", envelope(mode="write", authority=True), "preflight_ready")
    expect_action("provider-access-missing", envelope(requirements=["provider-access"]), "provider_access_required")
    expect_action("human-handoff", envelope(execution="human_handoff"), "user_action_required")
    expect_action("unsupported", envelope(supported=False), "capability_unavailable")

    missing = envelope()
    missing["intent"].pop("intentId")
    expect_deny("schema-missing-intent-id", missing, "validation failed")

    bad_occ = envelope()
    bad_occ["intent"]["intentId"] = "changed-after-occurrence"
    expect_deny("occurrence-mismatch", bad_occ, "occurrenceRef")

    bad_provider_binding = envelope()
    bad_provider_binding["providerObservation"]["accountRef"] = "account:other"
    bad_provider_binding["providerObservation"]["observationRef"] = provider_observation_ref(bad_provider_binding["providerObservation"])
    expect_deny("provider-binding-mismatch", bad_provider_binding, "not bound to intent")

    bad_provider_digest = envelope()
    bad_provider_digest["providerObservation"]["sourceRef"] = "tampered"
    expect_deny("provider-observation-digest-mismatch", bad_provider_digest, "digest mismatch")

    bad_authority_binding = envelope(mode="write", authority=True)
    bad_authority_binding["effectAuthority"]["accountRef"] = "account:other"
    bad_authority_binding["effectAuthority"]["authorityRef"] = effect_authority_ref(bad_authority_binding["effectAuthority"])
    expect_deny("authority-binding-mismatch", bad_authority_binding, "not bound to intent")

    bad_authority_digest = envelope(mode="write", authority=True)
    bad_authority_digest["effectAuthority"]["principalRef"] = "tampered"
    expect_deny("authority-digest-mismatch", bad_authority_digest, "digest mismatch")

    expired = envelope()
    expired["providerObservation"]["validUntil"] = "2026-09-11T11:30:00Z"
    expired["providerObservation"]["observationRef"] = provider_observation_ref(expired["providerObservation"])
    expect_deny("expired-provider-observation", expired, "expired")

    print("PASS Distribution v2 R2 authority-bound admission suite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
