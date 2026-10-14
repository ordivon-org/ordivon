"""Exact no-effect source-vs-deployed OCI policy preflight, including drift fences."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "consumers/supply-chain/acceptance/cdn-preflight.py"
SOURCE = ROOT / "consumers/supply-chain/config"
HOST = "production.cloudfront.docker.com"
FILENAMES = ("authority.json", "egress.json")

def without_new_host(doc, name):
    data = json.loads(json.dumps(doc))
    if name == "authority.json":
        data["allowedHttpsDomains"].remove(HOST)
    else:
        next(r for r in data["route"]["rules"] if r.get("inbound") == ["supply-chain-oci"])["domain"].remove(HOST)
    return data

def check(stage, source=SOURCE):
    r = subprocess.run(
        ["/usr/bin/python3", str(CLI), "--source-dir", str(source), "--installed-dir", str(stage)],
        text=True, capture_output=True, timeout=10, check=False,
    )
    return r, json.loads(r.stdout.strip())

def test_absent_exact_domain_in_installed_is_narrow_preflight_only():
    with tempfile.TemporaryDirectory() as root:
        root = Path(root)
        for name in FILENAMES:
            (root/name).write_text(json.dumps(without_new_host(json.loads((SOURCE/name).read_text()), name)))
        result, record = check(root)
        assert result.returncode == 0
        assert record["standing"] == "READY_TO_DEPLOY_NARROW_SCOPE"
        assert record["effectAttempted"] is False
        assert record["installedChanged"] is False
        assert record["sourceHeadAuthority"] == HOST
        for name in FILENAMES:
            assert HOST not in (root/name).read_text()

def test_exactly_current_policy_is_already_deployed_without_effect():
    with tempfile.TemporaryDirectory() as root:
        root = Path(root)
        for name in FILENAMES:
            (root/name).write_bytes((SOURCE/name).read_bytes())
        result, record = check(root)
        assert result.returncode == 0
        assert record["standing"] == "ALREADY_DEPLOYED"
        assert record["effectAttempted"] is False

def test_unknown_installed_field_change_cannot_be_auto_overwritten():
    with tempfile.TemporaryDirectory() as root:
        root = Path(root)
        for name in FILENAMES:
            data = without_new_host(json.loads((SOURCE/name).read_text()), name)
            if name == "authority.json": data["directFallback"] = True
            (root/name).write_text(json.dumps(data))
        result, record = check(root)
        assert result.returncode != 0
        assert record["standing"] == "HOLD_UNEXPECTED_DRIFT"

def test_half_applied_policy_must_halt_before_service_restart():
    with tempfile.TemporaryDirectory() as root:
        root = Path(root)
        (root/"authority.json").write_bytes((SOURCE/"authority.json").read_bytes())
        (root/"egress.json").write_text(json.dumps(without_new_host(json.loads((SOURCE/"egress.json").read_text()),"egress.json")))
        result, record = check(root)
        assert result.returncode != 0
        assert record["standing"] == "HOLD_PARTIAL_DEPLOYMENT"

def test_source_wildcard_or_direct_fallback_cannot_be_preflight_ready():
    with tempfile.TemporaryDirectory() as root:
        root = Path(root)
        src = root/"src"; src.mkdir()
        installed = root/"installed"; installed.mkdir()
        for name in FILENAMES:
            data = json.loads((SOURCE/name).read_text())
            if name == "authority.json": data["allowedHttpsDomainSuffixes"].append("docker.com")
            (src/name).write_text(json.dumps(data))
            (installed/name).write_text(json.dumps(without_new_host(json.loads((SOURCE/name).read_text()),name)))
        result, record = check(installed, src)
        assert result.returncode != 0
        assert record["standing"] == "HOLD_SOURCE_INVALID"


def test_retired_network_authority_alias_is_explicit_hold_not_an_auto_upgrade():
    with tempfile.TemporaryDirectory() as root:
        root = Path(root)
        for name in FILENAMES:
            old = without_new_host(json.loads((SOURCE/name).read_text()), name)
            if name == "authority.json":
                old["networkAuthority"]["name"] = "browserless-prod"
            (root/name).write_text(json.dumps(old))
        result, evidence = check(root)
        assert result.returncode != 0
        assert evidence["standing"] == "HOLD_LEGACY_AUTHORITY_ALIAS"
        assert evidence["effectAttempted"] is False
        assert evidence["installedChanged"] is False
        assert json.loads((root/"authority.json").read_text())["networkAuthority"]["name"] == "browserless-prod"
