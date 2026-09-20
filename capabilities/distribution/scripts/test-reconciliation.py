#!/usr/bin/env python
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "contracts/reconciliation-input.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)
REF = "sha256:" + "c" * 64

CASES = [
    ("ambiguous-unknown-no-proof", "ambiguous", "unknown", "none", "reconcile_required", False),
    ("ambiguous-absent-no-proof", "ambiguous", "absent", "none", "reconcile_required", False),
    ("ambiguous-present", "ambiguous", "present", "none", "effect_confirmed", False),
    ("ambiguous-idempotent", "ambiguous", "unknown", "provider_idempotency", "retry_permitted", True),
    ("ambiguous-authoritative-absence", "ambiguous", "absent", "authoritative_absence", "retry_permitted", True),
    ("acknowledged-unknown", "provider_acknowledged", "unknown", "none", "reconcile_required", False),
    ("acknowledged-absent", "provider_acknowledged", "absent", "none", "manual_review_required", False),
    ("definitely-rejected", "definitely_rejected", "unknown", "none", "no_effect_confirmed", False),
]


def decision(value: dict) -> dict:
    VALIDATOR.validate(value)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(value, handle)
        path = Path(handle.name)
    try:
        result = subprocess.run(
            ["opa", "eval", "--format", "json", "--data", str(ROOT / "policy/reconciliation.rego"), "--input", str(path), "data.ordivon.distribution.reconciliation.decision"],
            check=True, text=True, capture_output=True,
        )
        payload = json.loads(result.stdout)
        return payload["result"][0]["expressions"][0]["value"]
    finally:
        path.unlink(missing_ok=True)


def main() -> int:
    for name, dispatch, readback, proof, expected_action, expected_retry in CASES:
        value = {
            "schemaVersion": 1,
            "occurrenceRef": REF,
            "dispatchStanding": dispatch,
            "providerReadback": readback,
            "retryProof": proof,
        }
        result = decision(value)
        if result["action"] != expected_action or result["retryPermitted"] is not expected_retry:
            raise AssertionError(f"{name}: {result}")
        print(f"PASS {name} -> {result['action']} retry={str(result['retryPermitted']).lower()}")
    print("PASS Distribution v2 reconciliation semantics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
