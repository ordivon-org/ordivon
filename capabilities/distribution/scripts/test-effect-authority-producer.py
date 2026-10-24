#!/usr/bin/env python
from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from bound_refs import occurrence_ref
from produce_effect_authority import AuthorityProducerError, produce

ROOT = Path(__file__).resolve().parent.parent
INTENT = json.loads((ROOT / "evidence/r3-github-create-issue-intent.json").read_text())
NOW = datetime(2026, 9, 12, 0, 20, tzinfo=UTC)


def approval_for(intent: dict) -> dict:
    return {
        "schemaVersion": 1,
        "approvalId": "synthetic-test-only-approval",
        "principalRef": "principal:test-only",
        "occurrenceRef": intent["occurrenceRef"],
        "decision": "grant",
        "issuedAt": "2026-09-12T00:15:00Z",
        "validUntil": "2026-09-12T00:30:00Z",
        "sourceKind": "explicit_user_effect_approval",
        "sourceRef": "test-fixture:not-production-authority",
    }


def expect_deny(name: str, intent: dict, approval: dict, contains: str, now: datetime = NOW) -> None:
    try:
        produce(intent, approval, now=now)
    except AuthorityProducerError as exc:
        if contains not in str(exc):
            raise AssertionError(f"{name}: wrong denial {exc}") from exc
        print(f"PASS {name} denied")
        return
    raise AssertionError(f"{name}: expected denial")


def check_authority_contract(authority: dict) -> None:
    """Exact approval-to-effect consumer oracle; remains active under python -O."""
    expected = {
        "decision": "grant",
        "occurrenceRef": INTENT["occurrenceRef"],
        "provider": "github",
        "accountRef": "repo:ordivon-org/ordivon-runtime",
        "effectName": "create_issue",
    }
    for key, value in expected.items():
        if authority.get(key) != value:
            raise AssertionError(
                f"effect authority contract: {key} expected {value!r}, got {authority.get(key)!r}"
            )
    source_ref = authority.get("sourceRef")
    if not isinstance(source_ref, str) or not source_ref.startswith(
        "approval:synthetic-test-only-approval:"
    ):
        raise AssertionError("effect authority contract: sourceRef must bind the exact approval")


def main() -> int:
    approval = approval_for(INTENT)
    authority = produce(INTENT, approval, now=NOW)
    check_authority_contract(authority)

    # Falsification: a forged producer output must not pass the test oracle.
    invalid_outputs = (
        ("provider", "other-provider"),
        ("accountRef", "repo:unrelated/repository"),
        ("decision", "deny"),
        ("sourceRef", "approval:unrelated:something"),
    )
    for field, invalid in invalid_outputs:
        wrong = deepcopy(authority)
        wrong[field] = invalid
        try:
            check_authority_contract(wrong)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"contract oracle accepted a wrong {field}")
    print("PASS synthetic exact approval translates to exact EffectAuthority")

    swapped = deepcopy(INTENT)
    swapped["effect"]["payload"]["title"] += " changed"
    swapped["occurrenceRef"] = occurrence_ref(swapped)
    expect_deny("payload-swap-invalidates-approval", swapped, approval, "not bound to this exact occurrence")

    wrong = deepcopy(approval)
    wrong["occurrenceRef"] = "sha256:" + "f" * 64
    expect_deny("wrong-occurrence-approval", INTENT, wrong, "not bound to this exact occurrence")

    expired_now = datetime(2026, 9, 12, 0, 31, tzinfo=UTC)
    expect_deny("expired-approval", INTENT, approval, "outside its validity window", expired_now)
    print("PASS Distribution v2 exact effect authority producer tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
