from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_websocket_exact_contract_keeps_protocol_and_ordivon_authority_separate():
    contract = json.loads(
        (ROOT / "contracts/websocket-client-mechanics-v1.json").read_text()
    )
    assert contract["standing"] == "ACTIVE_EXACT_CONTRACT"
    assert "HTTP Upgrade client handshake" in contract["implementationOwnerScope"]
    assert "venue payload parsing and normalization" in contract["ordivonOwnedScope"]
    assert "Network v2 route selection and failover" in contract["ordivonOwnedScope"]
    assert contract["externalFinancialWritesAllowed"] is False


def test_r17_raw_wire_falsification_passes():
    out = subprocess.check_output(
        [str(ROOT / "scripts/run-websockets-owner-requalification-r17")],
        cwd=ROOT,
        text=True,
    )
    result = json.loads(out)
    assert result["standing"] == "PASS_RETAIN_WEBSOCKETS_NARROW_PROTOCOL_OWNER"
    assert result["version"] == "17.1"
    assert result["python3147ExecutableQualification"] == "PASS"
    assert result["thirdPartyDependencies"] == 0
    assert all(result["rawWireFalsification"].values())
    assert result["localBaseline"]["stdlibWebSocketClientAvailable"] is False
    assert result["localBaseline"]["contractEquivalentLocalBaselineCredible"] is False
    assert result["externalOwnerAdmitted"] is True
    assert result["externalFinancialWriteAttempted"] is False
