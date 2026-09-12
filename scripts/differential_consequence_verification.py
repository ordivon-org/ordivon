#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any


EXPECTED_STANDINGS = {
    "admission-only": "ADMITTED_NOT_EXECUTED",
    "execution-only": "EXECUTED_UNVERIFIED",
    "verified": "VERIFIED_CONSEQUENCE",
    "self-verified-receipt": "EXECUTION_RECEIPT_INVALID",
    "sensor-observation": "OBSERVATION_NOT_AUTHORITATIVE",
    "digest-mismatch": "CONSEQUENCE_MISMATCH",
    "request-mismatch": "EXECUTION_BINDING_ERROR",
    "rejected": "NOT_ADMITTED",
}


def old_oracle(old_repo: Path) -> dict[str, Any]:
    code = r'''
import json, tempfile
from pathlib import Path
from ordivon_security._canonical import canonical_digest
from ordivon_security.cli_agent_first_deception_acceptance import (
    _LocalServiceRange, _authority, _ACTOR_ID, _CAPABILITY, _EFFECT_TYPE, _ZONE_REF
)
from ordivon_security.range import RangeSession, RangeSessionSpec, RangeEffectRequest

with tempfile.TemporaryDirectory() as raw:
    root=Path(raw)/"world"
    authority=_authority(); backend=_LocalServiceRange(root, compromised=True)
    session=RangeSession(backend, RangeSessionSpec(session_id="range-session:af3-v2-diff", revision="1", range_id=backend.range_id, actor_ids=(_ACTOR_ID,), authorities=(authority,)))
    session.start(); session.update_actor_presence(_ACTOR_ID,"active",logical_time=1)
    request=RangeEffectRequest(request_id="range-effect-request:af3-v2-diff", actor_id=_ACTOR_ID, authority_id=authority.authority_id, zone_ref=_ZONE_REF, capability=_CAPABILITY, effect_type=_EFFECT_TYPE, payload={})
    admission=session.admit_effect(request, logical_time=2)
    before=backend.inspect(session.instance)
    receipt=backend.apply_quarantine(session.instance, admission, logical_time=3)
    before_poll_events=[event.to_dict() for event in session.events]
    polled=[event.to_dict() for event in session.poll_backend()]
    final=backend.inspect(session.instance)
    rejected=session.admit_effect(RangeEffectRequest(request_id="range-effect-request:af3-rejected", actor_id=_ACTOR_ID, authority_id=authority.authority_id, zone_ref=_ZONE_REF, capability="service.not-granted", effect_type=_EFFECT_TYPE, payload={}), logical_time=4)
    rejected_execute_error=None
    try:
        backend.apply_quarantine(session.instance, rejected, logical_time=5)
    except ValueError as exc:
        rejected_execute_error=str(exc)
    print(json.dumps({
        "admission": admission.to_dict(),
        "initialState": before,
        "executionReceipt": receipt,
        "eventsBeforePoll": before_poll_events,
        "observation": polled[0],
        "finalState": final,
        "finalStateDigest": canonical_digest(final),
        "rejectedAdmission": rejected.to_dict(),
        "rejectedExecutionError": rejected_execute_error,
    }, sort_keys=True))
'''
    env = os.environ.copy()
    env["PYTHONPATH"] = str(old_repo / "src")
    proc = subprocess.run(
        [str(old_repo / ".venv/bin/python"), "-c", code],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    return json.loads(proc.stdout)


def opa_decision(policy: Path, value: dict[str, Any]) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json") as handle:
        json.dump(value, handle)
        handle.flush()
        proc = subprocess.run(
            ["/usr/bin/opa", "eval", "--format", "raw", "-d", str(policy), "-i", handle.name, "data.ordivon.security.v2.consequence.decision"],
            capture_output=True,
            text=True,
            check=True,
        )
    return json.loads(proc.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-repo", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=Path("policies/consequence_verification.rego"))
    args = parser.parse_args()

    old = old_oracle(args.old_repo)
    admission = old["admission"]
    receipt = old["executionReceipt"]
    observation = old["observation"]

    old_invariants = {
        "admissionDoesNotExecute": old["initialState"].get("quarantined") is False,
        "receiptDoesNotClaimWorldTruth": receipt.get("effectExecuted") is True and receipt.get("worldEffectVerified") is False,
        "observationArrivesOnlyAfterPoll": not any(event.get("eventType") == "service.quarantine-observed" for event in old["eventsBeforePoll"]),
        "observationIsWorldTruthPlane": observation.get("plane") == "world-truth",
        "receiptDigestMatchesObservation": receipt.get("stateDigestAfterWrite") == observation.get("payload", {}).get("stateDigest"),
        "observationDigestMatchesFinalState": observation.get("payload", {}).get("stateDigest") == old["finalStateDigest"],
        "rejectedAdmissionCannotExecute": old["rejectedAdmission"].get("admitted") is False and isinstance(old["rejectedExecutionError"], str),
    }

    cases: dict[str, dict[str, Any]] = {
        "admission-only": {"admission": admission, "executionReceipt": None, "observation": None},
        "execution-only": {"admission": admission, "executionReceipt": receipt, "observation": None},
        "verified": {"admission": admission, "executionReceipt": receipt, "observation": observation},
        "rejected": {"admission": old["rejectedAdmission"], "executionReceipt": None, "observation": None},
    }

    self_verified = copy.deepcopy(receipt); self_verified["worldEffectVerified"] = True
    cases["self-verified-receipt"] = {"admission": admission, "executionReceipt": self_verified, "observation": observation}
    sensor = copy.deepcopy(observation); sensor["plane"] = "sensor"
    cases["sensor-observation"] = {"admission": admission, "executionReceipt": receipt, "observation": sensor}
    mismatch = copy.deepcopy(observation); mismatch["payload"]["stateDigest"] = "sha256:" + "f" * 64
    cases["digest-mismatch"] = {"admission": admission, "executionReceipt": receipt, "observation": mismatch}
    other_request = copy.deepcopy(receipt); other_request["requestId"] = "range-effect-request:other"
    cases["request-mismatch"] = {"admission": admission, "executionReceipt": other_request, "observation": observation}

    results: dict[str, Any] = {}
    passed = all(old_invariants.values())
    for name, value in cases.items():
        decision = opa_decision(args.policy, value)
        expected = EXPECTED_STANDINGS[name]
        ok = decision.get("standing") == expected
        results[name] = {"standing": decision.get("standing"), "expected": expected, "passed": ok}
        passed = passed and ok

    verified = opa_decision(args.policy, cases["verified"])
    passed = passed and verified.get("verifiedConsequence") == observation.get("payload")

    print(json.dumps({
        "oldRevision": subprocess.run(["git", "-C", str(args.old_repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip(),
        "oldInvariants": old_invariants,
        "cases": results,
        "verifiedConsequenceEqualOldObservationPayload": verified.get("verifiedConsequence") == observation.get("payload"),
        "passed": passed,
    }, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
