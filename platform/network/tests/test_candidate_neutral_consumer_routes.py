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
    ("finance", "openapi.okx.com"),
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


def test_supply_chain_docker_cdn_redirect_allowed_through_local_policy_fixture():
    """The exact observed blob CDN host traverses the scoped OCI proxy policy."""
    result = subprocess.run(
        ["/usr/bin/python3", str(FIXTURE), "supply-chain", "production.cloudfront.docker.com"],
        cwd=ROOT, capture_output=True, text=True, timeout=35, check=False,
    )
    assert result.returncode == 0, (result.stdout[-400:], result.stderr[-400:])
    evidence = json.loads(result.stdout.strip())
    assert evidence["allowedDomain"] == "production.cloudfront.docker.com"
    assert evidence["upstreamConnects"] == 1
    assert evidence["unknownDestinationRejected"] is True
    assert evidence["productionNetworkMutation"] is False


def test_windows_chrome_existing_ip_denial_rules_without_legacy_carrier():
    """Chrome candidate policy test: public destination forwarded, private IP rejected."""
    r = subprocess.run(
        ["/usr/bin/python3", str(FIXTURE), "windows-real-chrome", "example.com"],
        cwd=ROOT, capture_output=True, text=True, timeout=35, check=False,
    )
    assert r.returncode == 0, (r.stdout[-600:], r.stderr[-600:])
    data = json.loads(r.stdout.strip())
    assert data["standing"] == "CONSUMER_POLICY_FIXTURE_PASS"
    assert data["consumer"] == "windows-real-chrome"
    assert data["privateDestinationRejected"] is True
    assert data["upstreamConnects"] == 1
    assert data["usesLegacyWireguard"] is False
    assert data["gluetunRuntimeProven"] is False


def test_supply_chain_cdn_hostname_nearmiss_is_explicitly_rejected():
    r = subprocess.run(
        ["/usr/bin/python3", str(FIXTURE), "supply-chain", "production.cloudfront.docker.com"],
        cwd=ROOT, capture_output=True, text=True, timeout=35, check=False,
    )
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout.strip())
    assert d["hostSuffixConfusableRejected"] is True
    assert d["unknownDestinationRejected"] is True
    assert d["upstreamConnects"] == 1


@pytest.mark.parametrize("domain,port", [
    ("openapi.okx.com",443),
    ("fapi.binance.com",443),
    ("ws.okx.com",8443),
    ("fstream.binance.com",443),
    ("data-api.binance.vision",443),
    ("data-stream.binance.vision",443),
    ("api.binance.com",443),
])
def test_finance_every_provider_bound_inlet_uses_candidate_neutral_carrier(domain,port):
    r=subprocess.run(["/usr/bin/python3",str(FIXTURE),"finance",domain],
        cwd=ROOT,capture_output=True,text=True,timeout=35,check=False)
    assert r.returncode==0,(domain,r.stdout[-500:],r.stderr[-500:])
    d=json.loads(r.stdout.strip())
    assert d["consumer"]=="finance"
    assert d["allowedDomain"]==domain
    assert d["allowedPort"]==port
    assert d["upstreamConnects"]==1
    assert d["fixtureScope"]=="finance-provider-allowlist-only"
    assert d["usesLegacyWireguard"] is False
