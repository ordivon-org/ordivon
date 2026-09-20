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


def main() -> int:
    approval = approval_for(INTENT)
    authority = produce(INTENT, approval, now=NOW)
    assert authority["decision"] == "grant"
    assert authority["occurrenceRef"] == INTENT["occurrenceRef"]
    assert authority["provider"] == "github"
    assert authority["accountRef"] == "repo:ordivon-org/ordivon-runtime"
    assert authority["effectName"] == "create_issue"
    assert authority["sourceRef"].startswith("approval:synthetic-test-only-approval:")
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
