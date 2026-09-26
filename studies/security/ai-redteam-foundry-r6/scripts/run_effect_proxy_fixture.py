#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
for path in (ROOT, REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r5"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from foundry_r5 import InMemorySyntheticWorld, SyntheticIdentity, SyntheticService, SyntheticWorldSpec  # noqa: E402
from foundry_r6 import EffectAttempt, ReferenceEffectProxy, SecurityAdmissionRef  # noqa: E402

D = lambda c: "sha256:" + c * 64


def main() -> None:
    world = InMemorySyntheticWorld(SyntheticWorldSpec("world:r6-fixture", (SyntheticIdentity("agent:redteam"),), (SyntheticService("svc:mail", "mail"),), ()))
    proxy = ReferenceEffectProxy(world)
    synthetic = EffectAttempt("effect:synthetic", "agent:redteam", D("1"), world.spec.digest, "synthetic_world", "svc:mail", "send", "sink@example.test", "synthetic payload")
    simulated = proxy.handle(synthetic)
    replayed = proxy.handle(synthetic)
    external = EffectAttempt("effect:external", "agent:redteam", D("1"), world.spec.digest, "external_world", "svc:mail", "send", "person@example.com", "external payload")
    blocked = proxy.handle(external)
    external_admitted = EffectAttempt("effect:external-admitted", "agent:redteam", D("1"), world.spec.digest, "external_world", "svc:mail", "send", "person@example.com", "external payload")
    admission = SecurityAdmissionRef("security-decision:fixture", external_admitted.digest, D("2"), True)
    delegation = proxy.handle(external_admitted, security_admission=admission)
    report = {
        "schema": "ordivon.ai-redteam.effect-proxy-fixture.r6",
        "simulated": simulated.to_dict(),
        "exactReplaySameReceipt": replayed == simulated,
        "syntheticOutboundCount": len(world.outbound()),
        "externalWithoutAdmission": blocked.to_dict(),
        "externalWithPositiveAdmission": delegation.to_dict(),
        "externalExecutionImplemented": False,
        "worldReceipt": world.receipt().to_dict(),
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
