from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"capabilities/gluetun/acceptance/m4-systemd-manager-sandbox.sh"

pytestmark = pytest.mark.skipif(
    os.environ.get("NETWORK_V2_RUN_M4_SYSTEMD_SANDBOX") != "1",
    reason="effectful disposable host-systemd acceptance runs only when explicitly selected",
)

@pytest.mark.parametrize("mode",["candidate-exit","candidate-sigkill"])
def test_pid1_owns_failure_recovery_after_initiator_dies(mode):
    r=subprocess.run(
        ["/usr/bin/bash",str(SCRIPT),"--mode",mode],
        cwd=ROOT,text=True,capture_output=True,timeout=40,check=False,
    )
    assert r.returncode==0,(r.stdout[-1000:],r.stderr[-1400:])
    receipt=json.loads(r.stdout.strip().splitlines()[-1])
    assert receipt["standing"]=="PASS"
    assert receipt["systemManager"]=="systemd-pid1"
    assert receipt["initiatorKilled"] is True
    assert receipt["candidateFailureObserved"] is True
    assert receipt["managerOnFailureTriggered"] is True
    assert receipt["candidateAbsentBeforeFallback"] is True
    assert receipt["legacyBeforeConsumer"] is True
    assert receipt["consumerBeforeProducer"] is True
    assert receipt["productionProviderIdentityUsed"] is False
    assert receipt["productionNetworkMutation"] is False
    assert receipt["sandboxUnitsRemoved"] is True
