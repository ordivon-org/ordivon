"""Non-production sing-box process restart and policy rollback, not systemd."""
import json
from pathlib import Path
import subprocess
import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'consumers/supply-chain/acceptance/cdn-singbox-service-rehearsal.py'

@pytest.mark.parametrize('fault',["before-stop","after-stop","after-new-run"])
def test_original_config_and_policy_restore_after_process_boundary_fault(fault):
    r=subprocess.run(['/usr/bin/python3',str(SCRIPT),'--fault',fault],
        text=True,capture_output=True,timeout=35,check=False,cwd=ROOT)
    assert r.returncode==0,(r.stdout[-400:],r.stderr[-700:])
    x=json.loads(r.stdout.strip())
    assert x['standing']=='SANDBOX_PROCESS_AND_POLICY_RESTORED'
    assert x['faultInjected']==fault
    assert x['oldCdnHostRejectedAfterRestore'] is True
    assert x['oldRegistryHostAllowedAfterRestore'] is True
    assert x['unknownHostRejectedAfterRestore'] is True
    assert x['originalFileBytesRestored'] is True
    assert x['originalSourceReplacedInWorkspace'] is False
    assert x['productionServiceTouched'] is False
    assert x['surfsharkIdentityUsed'] is False
