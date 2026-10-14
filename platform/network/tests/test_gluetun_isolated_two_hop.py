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


def test_isolated_fixture_upstream_proxy_failure_stays_fail_closed():
    script = ROOT / "capabilities/gluetun/acceptance/isolated-two-hop-fixture.py"
    result = subprocess.run(
        ["/usr/bin/python3", str(script), "--fault=upstream-offline"],
        cwd=ROOT, text=True, capture_output=True, timeout=30, check=False,
    )
    assert result.returncode == 0, (result.stdout[-500:], result.stderr[-500:])
    evidence = json.loads(result.stdout.strip())
    assert evidence["standing"] == "FIXTURE_FAULT_PASS"
    assert evidence["upstreamUnavailableFailClosed"] is True
    assert evidence["upstreamFixtureRequests"] == 0
    assert evidence["providerIdentityUsed"] is False
    assert evidence["productionNetworkMutation"] is False
    assert evidence["gluetunContainerPortProven"] is False


def test_offline_oracle_requires_direct_destination_witness_and_exact_status():
    script = ROOT / "capabilities/gluetun/acceptance/isolated-two-hop-fixture.py"
    result = subprocess.run(
        ["/usr/bin/python3", str(script), "--fault=upstream-offline"],
        cwd=ROOT, text=True, capture_output=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stderr
    record = json.loads(result.stdout.strip())
    assert record["directWitnessConnections"] == 0
    assert record["privateWitnessConnections"] == 0
    assert record["clientHttpStatus"] in (0, 502, 503, 504)
    assert record["clientHttpStatus"] not in (403, 404)


def test_403_on_leaky_direct_target_is_caught_even_if_curl_fail_returns_error():
    script = ROOT / "capabilities/gluetun/acceptance/isolated-two-hop-fixture.py"
    result = subprocess.run(
        ["/usr/bin/python3", str(script), "--fault=direct-http-error-leak"],
        cwd=ROOT, text=True, capture_output=True, timeout=30, check=False,
    )
    assert result.returncode != 0
    record = json.loads(result.stdout.strip())
    assert record["standing"] == "DIRECT_LEAK_DETECTED"
    assert record["directWitnessConnections"] == 1
    assert record["clientHttpStatus"] == 403
    assert record["curlFailExit"] == 22
    assert record["providerIdentityUsed"] is False
    assert record["productionNetworkMutation"] is False
