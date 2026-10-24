"""Owner-native counterexamples for Network local graduation evidence admission.

These tests use only the existing CLI and a disposable output path; neither
the live Network configuration nor the checked-in capability report is changed.
"""
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "capability-report.py"


def invoke(command: str, path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), command, "--output", str(path)],
        check=False,
        text=True,
        capture_output=True,
    )


@pytest.mark.parametrize(
    ("mutation", "failure"),
    (
        (lambda data: data.update(generic={"dnsA": "FAIL"}), "generic"),
        (lambda data: data.update(externalFidelity={"tcNetem": "PASS"}), "externalFidelity"),
        (lambda data: data.update(outsideNetworkBoundary={}), "outsideNetworkBoundary"),
        (lambda data: data.update(platformEvidence={"wsl": False}), "platformEvidence"),
        (lambda data: data.update(schemaVersion=2.0), "schemaVersion"),
    ),
)
def test_mutated_local_graduation_evidence_never_passes(tmp_path, mutation, failure):
    report = tmp_path / "local-network.json"
    assert invoke("write-local", report).returncode == 0
    assert invoke("verify-local", report).returncode == 0
    payload = json.loads(report.read_text())
    mutation(payload)
    report.write_text(json.dumps(payload))
    result = invoke("verify-local", report)
    assert result.returncode != 0, (failure, result.stdout, result.stderr)
    assert failure in result.stderr + result.stdout


def test_duplicate_network_report_members_rejected_before_graduation(tmp_path):
    report = tmp_path / "local-network.json"
    assert invoke("write-local", report).returncode == 0
    raw = report.read_text()
    marker = '"standing": "LOCAL_WSL_GRADUATED"'
    assert raw.count(marker) == 1
    report.write_text(
        raw.replace(
            marker,
            '"standing": "UNVERIFIED", "standing": "LOCAL_WSL_GRADUATED"',
        )
    )
    result = invoke("verify-local", report)
    assert result.returncode != 0, (result.stdout, result.stderr)
    assert "duplicate" in (result.stdout + result.stderr).lower()
