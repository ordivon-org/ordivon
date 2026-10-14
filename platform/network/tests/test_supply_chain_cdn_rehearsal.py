"""Actual local-file replacement and byte-for-byte restore after fault injection.

The test-only runner is prohibited from touching systemd or /etc; this is NOT
live WireGuard or Supply-Chain service rollback acceptance.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT / "consumers/supply-chain/acceptance/cdn-file-rollback-rehearsal.py"
SOURCE=ROOT / "consumers/supply-chain/config"
MARKER="NETWORK_V2_CDN_NONPRODUCTION_FIXTURE_ONLY"

def setup(root):
    (root/MARKER).touch()
    before={}
    for name in ("authority.json","egress.json"):
        old=json.loads((SOURCE/name).read_text())
        if name=="authority.json": old["allowedHttpsDomains"].remove("production.cloudfront.docker.com")
        else: next(r for r in old["route"]["rules"] if r.get("inbound")==["supply-chain-oci"])["domain"].remove("production.cloudfront.docker.com")
        file=root/name
        file.write_text(json.dumps(old,separators=(",",":"))+"\n")
        os.chmod(file,0o640)
        before[name]=(file.read_bytes(),file.stat().st_mode & 0o777)
    return before

def run(root, fault):
    result=subprocess.run([
        "/usr/bin/python3",str(SCRIPT),"--fixture-root",str(root),
        "--source-dir",str(SOURCE),"--fault",fault,
    ],capture_output=True,text=True,timeout=12,check=False)
    return result,json.loads(result.stdout.strip()) if result.stdout.strip() else {}

def test_staged_source_file_restore_is_byte_exact_after_each_injected_fault():
    for fault in ("after-authority","after-egress","after-fake-restart"):
        with tempfile.TemporaryDirectory(prefix="nv2-r5-sandbox-") as base:
            root=Path(base)
            original=setup(root)
            outcome,receipt=run(root,fault)
            assert outcome.returncode==0,(fault,outcome.stderr)
            assert receipt["standing"]=="SANDBOX_PREIMAGE_RESTORED"
            assert receipt["faultInjected"]==fault
            assert receipt["productionServiceTouched"] is False
            for name,(content,mode) in original.items():
                assert (root/name).read_bytes()==content
                assert (root/name).stat().st_mode & 0o777==mode

def test_fixture_cannot_target_unmarked_or_system_installed_path():
    with tempfile.TemporaryDirectory(prefix="nv2-r5-sandbox-") as base:
        root=Path(base)
        result,_=run(root,"after-authority")
        assert result.returncode!=0
        assert not list(root.glob('*.json'))

def test_fixture_rejects_unexpected_authority_drift_before_replacement():
    with tempfile.TemporaryDirectory(prefix="nv2-r5-sandbox-") as base:
        root=Path(base)
        originals=setup(root)
        p=root/"authority.json"
        data=json.loads(p.read_text())
        data["networkAuthority"]["name"]="browserless-prod"
        p.write_text(json.dumps(data))
        modified=p.read_bytes()
        result,record=run(root,"after-egress")
        assert result.returncode!=0
        assert record["standing"]=="HOLD_PREIMAGE_DRIFT"
        assert p.read_bytes()==modified
        assert (root/"egress.json").read_bytes()==originals["egress.json"][0]
