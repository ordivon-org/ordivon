#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
for path in (
    ROOT,
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r5",
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r6",
):
    sys.path.insert(0, str(path))

from foundry_r5 import InMemorySyntheticWorld, SyntheticIdentity, SyntheticService, SyntheticWorldSpec  # noqa: E402
from foundry_r6 import EffectAttempt, ReferenceEffectProxy  # noqa: E402
from foundry_r7 import SyntheticWorldObserver  # noqa: E402

ENV = "sha256:" + "c" * 64
POLICY = REPO_ROOT / "platform" / "security" / "policies" / "consequence_verification.rego"
QUERY = "data.ordivon.security.v2.consequence.decision"


def evaluate(value: dict[str, object]) -> dict[str, object]:
    completed = subprocess.run(
        ["/usr/bin/opa", "eval", "--format=json", "--data", str(POLICY), "--stdin-input", QUERY],
        input=json.dumps(value),
        text=True,
        capture_output=True,
        check=True,
    )
    output = json.loads(completed.stdout)
    return output["result"][0]["expressions"][0]["value"]


def main() -> None:
    world = InMemorySyntheticWorld(
        SyntheticWorldSpec(
            world_id="world:r7-policy-compat",
            identities=(SyntheticIdentity("agent:test"),),
            services=(SyntheticService("mail:test", "mail"),),
            resources=(),
        )
    )
    observer = SyntheticWorldObserver()
    anchor = observer.start(world, environment_digest=ENV)
    request = EffectAttempt(
        effect_id="effect:r7-policy-compat",
        actor_id="agent:test",
        environment_digest=ENV,
        world_spec_digest=world.spec.digest,
        scope="synthetic_world",
        service_id="mail:test",
        operation="send",
        target="sink@example.test",
        content="policy compatibility",
    )
    receipt = ReferenceEffectProxy(world).handle(request)
    observation = observer.finish(anchor, world, effect_id=request.effect_id, effect_request_digest=request.digest)
    policy_input = {
        "admission": {"admitted": True, "requestId": request.effect_id},
        "executionReceipt": {
            "requestId": request.effect_id,
            "effectExecuted": True,
            "worldEffectVerified": False,
            "stateDigestAfterWrite": receipt.world_after_digest,
        },
        "observation": observation.security_v2_observation(threat_class="synthetic_agent"),
    }
    verified = evaluate(policy_input)
    if verified["standing"] != "VERIFIED_CONSEQUENCE":
        raise SystemExit(f"expected VERIFIED_CONSEQUENCE, got {verified['standing']}")

    tampered = json.loads(json.dumps(policy_input))
    tampered["observation"]["payload"]["stateDigest"] = "sha256:" + "0" * 64
    mismatch = evaluate(tampered)
    if mismatch["standing"] != "CONSEQUENCE_MISMATCH":
        raise SystemExit(f"expected CONSEQUENCE_MISMATCH, got {mismatch['standing']}")

    print(json.dumps({
        "schema": "ordivon.ai-redteam.security-v2-policy-compat.r7",
        "policy": str(POLICY.relative_to(REPO_ROOT)),
        "verifiedStanding": verified["standing"],
        "mismatchStanding": mismatch["standing"],
        "observationDigest": observation.digest,
        "worldStateDigest": observation.after_state_digest,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
