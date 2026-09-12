#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from ordivon_security_v2.admission import ReplayBinding, canonical_digest


CASES = [
    {
        "name": "admitted",
        "actorIds": ["actor:red", "actor:blue"],
        "request": {
            "requestId": "range-effect-request:red-admitted",
            "actorId": "actor:red",
            "authorityId": "range-authority:red",
            "zoneRef": "zone:battlefield",
            "capability": "range-network",
            "effectType": "fabric.replace-peer",
            "payload": {"peer": "b"},
        },
    },
    {
        "name": "unknown-actor",
        "actorIds": ["actor:red"],
        "request": {
            "requestId": "range-effect-request:ghost",
            "actorId": "actor:ghost",
            "authorityId": "range-authority:fake",
            "zoneRef": "zone:battlefield",
            "capability": "range-network",
            "effectType": "fabric.replace-peer",
            "payload": {},
        },
    },
    {
        "name": "unknown-authority",
        "actorIds": ["actor:red"],
        "request": {
            "requestId": "range-effect-request:red-fake",
            "actorId": "actor:red",
            "authorityId": "range-authority:fake",
            "zoneRef": "zone:battlefield",
            "capability": "range-network",
            "effectType": "fabric.replace-peer",
            "payload": {},
        },
    },
    {
        "name": "authority-actor-mismatch",
        "actorIds": ["actor:red", "actor:blue"],
        "request": {
            "requestId": "range-effect-request:red-using-blue",
            "actorId": "actor:red",
            "authorityId": "range-authority:blue",
            "zoneRef": "zone:battlefield",
            "capability": "range-network",
            "effectType": "fabric.replace-peer",
            "payload": {},
        },
    },
    {
        "name": "zone-not-granted",
        "actorIds": ["actor:red"],
        "request": {
            "requestId": "range-effect-request:red-zone",
            "actorId": "actor:red",
            "authorityId": "range-authority:red",
            "zoneRef": "zone:elsewhere",
            "capability": "range-network",
            "effectType": "fabric.replace-peer",
            "payload": {},
        },
    },
    {
        "name": "capability-not-granted",
        "actorIds": ["actor:red"],
        "request": {
            "requestId": "range-effect-request:red-cap",
            "actorId": "actor:red",
            "authorityId": "range-authority:red",
            "zoneRef": "zone:battlefield",
            "capability": "destroy-world",
            "effectType": "fabric.replace-peer",
            "payload": {},
        },
    },
]


def authority(actor_id: str) -> dict[str, Any]:
    suffix = actor_id.removeprefix("actor:")
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.security.range-authority",
        "authorityId": f"range-authority:{suffix}",
        "revision": "1",
        "actorId": actor_id,
        "zoneRefs": ["zone:battlefield"],
        "capabilities": ["native-execution", "range-network"],
        "externalBoundary": "denied",
        "metadata": {},
    }
    value["authorityDigest"] = canonical_digest(value)
    return value


def request_with_old_shape(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.security.range-effect-request",
        **value,
    }


def old_results(old_repo: Path) -> dict[str, Any]:
    code = r'''
import json, sys
from ordivon_security.range import BackendCheckpoint, RangeAuthority, RangeEffectRequest, RangeSession, RangeSessionInstance, RangeSessionSpec

class Backend:
    range_id = "range:memory-war-s0"
    @property
    def execution_identity(self): return {"rangeId": self.range_id, "implementationRevision": "differential"}
    def create(self, spec): return RangeSessionInstance(instance_id="range-instance:diff", session_id=spec.session_id)
    def inspect(self, instance): return {"instanceId": instance.instance_id}
    def events(self, instance, *, after_cursor): return ()
    def checkpoint(self, instance, label): return BackendCheckpoint(checkpoint_ref="memory:diff", details={})
    def terminate(self, instance, reason): return {"terminated": True}
    def destroy(self, instance): return {"destroyed": True}

def authority(actor_id):
    suffix = actor_id.removeprefix("actor:")
    return RangeAuthority(authority_id=f"range-authority:{suffix}", revision="1", actor_id=actor_id, zone_refs=("zone:battlefield",), capabilities=("native-execution","range-network"), external_boundary="denied")

payload=json.load(sys.stdin)
out={}
for case in payload:
    spec=RangeSessionSpec(session_id=f"range-session:diff-{case['name']}", revision="1", range_id="range:memory-war-s0", actor_ids=tuple(case['actorIds']), authorities=tuple(authority(a) for a in case['actorIds']))
    session=RangeSession(Backend(), spec); session.start()
    r=case['request']
    req=RangeEffectRequest(request_id=r['requestId'], actor_id=r['actorId'], authority_id=r['authorityId'], zone_ref=r['zoneRef'], capability=r['capability'], effect_type=r['effectType'], payload=r['payload'])
    admission=session.admit_effect(req, logical_time=2)
    replay=session.admit_effect(req, logical_time=99)
    changed_error=None
    try:
        changed=RangeEffectRequest(request_id=r['requestId'], actor_id=r['actorId'], authority_id=r['authorityId'], zone_ref=r['zoneRef'], capability=r['capability'] + "-changed", effect_type=r['effectType'], payload=r['payload'])
        session.admit_effect(changed, logical_time=3)
    except ValueError as exc:
        changed_error=str(exc)
    out[case['name']]={"decision": admission.to_dict(), "exactReplayEqual": replay == admission, "changedReplayError": changed_error}
json.dump(out, sys.stdout, sort_keys=True)
'''
    env = os.environ.copy()
    env["PYTHONPATH"] = str(old_repo / "src")
    proc = subprocess.run(
        [str(old_repo / ".venv/bin/python"), "-c", code],
        input=json.dumps(CASES),
        text=True,
        capture_output=True,
        env=env,
        check=True,
    )
    return json.loads(proc.stdout)


def opa_decision(policy: Path, payload: dict[str, Any]) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json") as f:
        json.dump(payload, f)
        f.flush()
        proc = subprocess.run(
            ["/usr/bin/opa", "eval", "--format", "raw", "-d", str(policy), "-i", f.name, "data.ordivon.security.v2.effect_admission.decision"],
            text=True,
            capture_output=True,
            check=True,
        )
    return json.loads(proc.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-repo", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=Path("policies/effect_admission.rego"))
    args = parser.parse_args()

    old = old_results(args.old_repo)
    summary: dict[str, Any] = {"cases": {}, "passed": True}
    for case in CASES:
        authorities = [authority(actor_id) for actor_id in case["actorIds"]]
        request = request_with_old_shape(case["request"])
        request_digest = canonical_digest(request)
        policy_request = {**case["request"], "requestDigest": request_digest}
        v2 = opa_decision(args.policy, {"actorIds": case["actorIds"], "authorities": authorities, "request": policy_request})
        expected = old[case["name"]]["decision"]
        equal = v2 == expected
        replay = ReplayBinding()
        first, first_replayed = replay.bind(request=request, admission=v2)
        second, second_replayed = replay.bind(request=dict(request), admission={"should": "not replace"})
        changed_error = None
        changed = dict(request)
        changed["capability"] = str(changed["capability"]) + "-changed"
        try:
            replay.bind(request=changed, admission=v2)
        except ValueError as exc:
            changed_error = str(exc)
        replay_ok = (
            not first_replayed
            and second_replayed
            and first == second == v2
            and old[case["name"]]["exactReplayEqual"] is True
            and isinstance(old[case["name"]]["changedReplayError"], str)
            and changed_error is not None
        )
        summary["cases"][case["name"]] = {
            "decisionEqual": equal,
            "replayInvariantEqual": replay_ok,
            "reason": v2["reason"],
        }
        summary["passed"] = summary["passed"] and equal and replay_ok

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
