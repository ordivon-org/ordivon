"""Existing scoped consumer rules, tested without any legacy WG/service requirement."""
import json
from pathlib import Path
import subprocess
import pytest

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT / "consumers" / "acceptance" / "candidate-neutral-route-fixture.py"

@pytest.mark.parametrize("consumer,domain", [
    ("model-provider", "api.deepseek.com"),
    ("supply-chain", "registry-1.docker.io"),
    ("x-reality", "api.x.com"),
])
def test_source_consumer_allowlist_and_unknown_reject_against_loopback_fixture(consumer,domain):
    r=subprocess.run(["/usr/bin/python3",str(FIXTURE),consumer,domain],
        cwd=ROOT,capture_output=True,text=True,timeout=35,check=False)
    assert r.returncode==0,(r.stdout[-600:],r.stderr[-600:])
    d=json.loads(r.stdout.strip())
    assert d["standing"]=="CONSUMER_POLICY_FIXTURE_PASS"
    assert d["consumer"]==consumer
    assert d["allowedDomain"]==domain
    assert d["upstreamConnects"]==1
    assert d["unknownDestinationRejected"] is True
    assert d["usesLegacyWireguard"] is False
    assert d["productionNetworkMutation"] is False
    assert d["gluetunRuntimeProven"] is False
