#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SECURITY_ROOT = Path(__file__).resolve().parents[2]
AGENT_POLICY = SECURITY_ROOT / "policies" / "agent_admission.rego"
EFFECT_POLICY = SECURITY_ROOT / "policies" / "effect_admission.rego"
OPA = Path("/usr/bin/opa")


def _opa(policy: Path, query: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = subprocess.run(
        [
            str(OPA),
            "eval",
            "--format=json",
            "--data",
            str(policy),
            "--stdin-input",
            query,
        ],
        input=json.dumps(payload, separators=(",", ":")),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"OPA failed: {result.stderr.strip()}")
    parsed = json.loads(result.stdout)
    try:
        value = parsed["result"][0]["expressions"][0]["value"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("OPA decision is undefined") from exc
    if not isinstance(value, dict):
        raise RuntimeError("OPA decision is not an object")
    return value


def _effect_input(projection: dict[str, Any]) -> dict[str, Any]:
    return {
        "actorIds": [projection["actorId"]],
        "authorities": [
            {
                "authorityId": projection["authorityId"],
                "actorId": projection["actorId"],
                "zoneRefs": [projection["zoneRef"]],
                "capabilities": [projection["capability"]],
                "authorityDigest": projection["authorityDigest"],
            }
        ],
        "request": projection,
    }


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    agent = _opa(
        AGENT_POLICY,
        "data.ordivon.security.v2.agent_admission.decision",
        payload,
    )
    effect = None
    if agent.get("outcome") == "ALLOW":
        projection = agent.get("authorityProjection")
        if not isinstance(projection, dict):
            raise RuntimeError("ALLOW decision is missing authorityProjection")
        effect = _opa(
            EFFECT_POLICY,
            "data.ordivon.security.v2.effect_admission.decision",
            _effect_input(projection),
        )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.security.agent-admission-chain",
        "agent": agent,
        "effect": effect,
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        json.dump(evaluate(payload), sys.stdout, separators=(",", ":"))
        sys.stdout.write("\n")
        return 0
    except Exception as exc:  # contract process boundary
        json.dump(
            {
                "schemaVersion": 1,
                "kind": "ordivon.security.agent-admission-error",
                "error": type(exc).__name__,
                "detail": str(exc),
            },
            sys.stderr,
            separators=(",", ":"),
        )
        sys.stderr.write("\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
