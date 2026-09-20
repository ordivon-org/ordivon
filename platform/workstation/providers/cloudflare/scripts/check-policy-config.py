#!/usr/bin/env python3
"""Verify the Worker, runtime policy, and retention configuration remain coupled."""

from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
POLICY = json.loads((ROOT / "config" / "edge-policy.json").read_text())
WRANGLER = json.loads((ROOT / "wrangler.jsonc").read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


require(bool(re.fullmatch(r"[a-z0-9][a-z0-9._-]{1,31}", POLICY["family"])), "invalid policy family")
expected_hosts = ",".join(POLICY["fetch"]["allowed_hosts"])
require(
    WRANGLER["vars"]["FETCH_ALLOWED_HOSTS"] == expected_hosts,
    "FETCH_ALLOWED_HOSTS drifted from config/edge-policy.json",
)

limits = {item["name"]: item["simple"] for item in WRANGLER["ratelimits"]}
for name in ("browser", "fetch"):
    expected = POLICY["rate_limits"][name]
    actual = limits.get(expected["binding"])
    require(actual is not None, f"missing rate limit binding: {expected['binding']}")
    require(actual["limit"] == expected["limit"], f"rate limit drift: {expected['binding']}")
    require(actual["period"] == expected["period"], f"rate period drift: {expected['binding']}")

retention = POLICY["retention_days"]
require(
    retention["idempotency"] == retention["request_state"] == retention["receipt_mirror"],
    "request, receipt, and idempotency retention must match",
)
require(
    retention["artifacts"] > retention["receipt_mirror"],
    "Artifacts must outlive replayable Receipts",
)
require(retention["cleanup_tasks"] >= retention["request_state"], "cleanup tasks expire too early")
print(json.dumps({"ok": True, "policy_family": POLICY["family"], "retention_days": retention}))
