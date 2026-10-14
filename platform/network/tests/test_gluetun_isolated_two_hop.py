"""Contract for genuine two-proxy execution using only loopback fixture endpoints."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_isolated_fixture_two_hop_executes_and_never_claims_gluetun_production():
    script = ROOT / "capabilities/gluetun/acceptance/isolated-two-hop-fixture.py"
    result = subprocess.run(
        ["/usr/bin/python3", str(script)],
        cwd=ROOT, text=True, capture_output=True, timeout=30, check=False,
    )
    assert result.returncode == 0, (result.stdout[-600:], result.stderr[-600:])
    evidence = json.loads(result.stdout.strip())
    assert evidence["standing"] == "FIXTURE_PASS"
    assert evidence["twoHopExecutionProven"] is True
    assert evidence["providerIdentityUsed"] is False
    assert evidence["productionNetworkMutation"] is False
    assert evidence["gluetunContainerPortProven"] is False
    assert evidence["gluetunFirewallRuntimeProven"] is False
    assert evidence["upstreamFixtureRequests"] == 1
    assert evidence["privateDestinationRejected"] is True
