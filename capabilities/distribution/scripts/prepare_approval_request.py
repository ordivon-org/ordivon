#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from bound_refs import effect_payload_ref, occurrence_ref


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("intent", type=Path)
    parser.add_argument("--requested-at")
    parser.add_argument("--ttl-minutes", type=int, default=30)
    args = parser.parse_args()
    intent = json.loads(args.intent.read_text())
    if "intent" in intent:
        intent = intent["intent"]
    actual = occurrence_ref(intent)
    if intent.get("occurrenceRef") != actual:
        raise SystemExit("intent occurrenceRef mismatch")
    now = datetime.fromisoformat(args.requested_at.replace("Z", "+00:00")) if args.requested_at else datetime.now(UTC)
    expires = now + timedelta(minutes=args.ttl_minutes)
    value = {
        "schemaVersion": 1,
        "requestId": "approval-request:" + str(uuid.uuid4()),
        "occurrenceRef": actual,
        "provider": intent["carrier"]["provider"],
        "accountRef": intent["carrier"]["accountRef"],
        "effectName": intent["effect"]["name"],
        "effectPayloadRef": effect_payload_ref(intent),
        "requestedAt": now.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "expiresAt": expires.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "standing": "approval_required_no_effect_authority",
    }
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
