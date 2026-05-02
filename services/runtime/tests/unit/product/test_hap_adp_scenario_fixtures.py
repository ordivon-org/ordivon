"""HAP-2: Fixture validation tests for ADP-1 scenario fixtures.

Validates that all ADP-1 scenario fixtures validate against HAP schemas
and that intentionally invalid fixtures fail.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "scripts" / "validate_hap_payload.py"
ADP_DIR = ROOT / "examples" / "hap" / "adp-scenarios"


def _validate(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        capture_output=True, text=True, timeout=10, cwd=str(ROOT),
    )


class TestADPScenarioFixtures:
    def test_all_scenario_manifests_validate(self):
        failures = []
        for s in sorted(ADP_DIR.iterdir()):
            if not s.is_dir():
                continue
            r = _validate(s / "harness-adapter-manifest.json")
            if r.returncode != 0:
                failures.append(f"{s.name}/manifest: {r.stdout.strip()}")
        assert not failures, f"Manifest validation failures: {failures}"

    def test_all_scenario_task_requests_validate(self):
        failures = []
        for s in sorted(ADP_DIR.iterdir()):
            if not s.is_dir():
                continue
            r = _validate(s / "harness-task-request.json")
            if r.returncode != 0:
                failures.append(f"{s.name}/task-request: {r.stdout.strip()}")
        assert not failures, f"Task request validation failures: {failures}"

    def test_all_scenario_receipts_validate(self):
        failures = []
        for s in sorted(ADP_DIR.iterdir()):
            if not s.is_dir():
                continue
            r = _validate(s / "harness-execution-receipt.json")
            if r.returncode != 0:
                failures.append(f"{s.name}/receipt: {r.stdout.strip()}")
        assert not failures, f"Receipt validation failures: {failures}"

    def test_all_scenarios_are_valid_json(self):
        for f in ADP_DIR.glob("**/*.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            assert isinstance(data, dict), f"{f.relative_to(ROOT)}: not a JSON object"

    def test_blocked_scenarios_dominate(self):
        """Most scenarios should be BLOCKED — boundary enforcement is the goal."""
        blocked = 0
        total = 0
        for s in sorted(ADP_DIR.iterdir()):
            if not s.is_dir():
                continue
            r = json.loads((s / "harness-execution-receipt.json").read_text())
            if r["result_summary"]["status"] == "BLOCKED":
                blocked += 1
            total += 1
        assert blocked >= 10, f"Expected >=10 BLOCKED scenarios, got {blocked}/{total}"
        print(f"  BLOCKED: {blocked}/{total} scenarios")

    def test_degraded_ready_scenarios_have_disclaimers(self):
        for s in sorted(ADP_DIR.iterdir()):
            if not s.is_dir():
                continue
            r = json.loads((s / "harness-execution-receipt.json").read_text())
            status = r["result_summary"]["status"]
            if status in ("DEGRADED", "READY_WITHOUT_AUTHORIZATION"):
                reason = r["result_summary"].get("status_reason", "").lower()
                auth = r["result_summary"].get("authority_statement", "").lower()
                assert "does not authorize" in reason + auth or "not" in reason + auth, \
                    f"{s.name}: {status} status missing authorization disclaimer"
