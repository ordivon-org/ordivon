"""HAP-3: HarnessTaskPlan schema and fixture tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "scripts" / "validate_hap_payload.py"
TP_DIR = ROOT / "examples" / "hap" / "task-plan"


def _validate(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(VALIDATOR), str(path)],
                          capture_output=True, text=True, timeout=10, cwd=str(ROOT))


class TestTaskPlanSchema:
    def test_schema_exists(self):
        path = ROOT / "src/ordivon_verify/schemas/hap-task-plan.schema.json"
        assert path.exists()

    def test_schema_parses(self):
        path = ROOT / "src/ordivon_verify/schemas/hap-task-plan.schema.json"
        json.loads(path.read_text())


class TestTaskPlanFixturesValidate:
    def test_safe_c0_validates(self):
        r = _validate(TP_DIR / "safe-c0-docs-only.json")
        assert r.returncode == 0, f"FAIL: {r.stdout}"

    def test_safe_c2_validates(self):
        r = _validate(TP_DIR / "safe-c2-protected-path.json")
        assert r.returncode == 0, f"FAIL: {r.stdout}"

    def test_blocked_c3_validates(self):
        r = _validate(TP_DIR / "blocked-c3-shell-risk.json")
        assert r.returncode == 0, f"FAIL: {r.stdout}"

    def test_blocked_c4_validates(self):
        r = _validate(TP_DIR / "blocked-c4-external-credential.json")
        assert r.returncode == 0, f"FAIL: {r.stdout}"

    def test_no_go_c5_validates(self):
        r = _validate(TP_DIR / "no-go-c5-live.json")
        assert r.returncode == 0, f"FAIL: {r.stdout}"


class TestTaskPlanBoundaries:
    def test_c4_defaults_blocked(self):
        plan = json.loads((TP_DIR / "blocked-c4-external-credential.json").read_text())
        assert plan["capability_class"] == "C4"
        assert plan["planned_status"] == "BLOCKED"

    def test_c5_defaults_no_go(self):
        plan = json.loads((TP_DIR / "no-go-c5-live.json").read_text())
        assert plan["capability_class"] == "C5"
        assert plan["planned_status"] == "NO_GO"

    def test_plan_is_not_execution_permission(self):
        for f in TP_DIR.glob("*.json"):
            plan = json.loads(f.read_text())
            stmt = plan.get("no_action_authorization_statement", "").lower()
            if plan["planned_status"] in ("PLAN_ONLY", "BLOCKED", "NO_GO"):
                continue
            if "unsafe" in f.name:
                continue  # Intentionally unsafe fixtures tested separately
            assert "does not authorize" in stmt or "not authorization" in stmt or "not execution" in stmt, \
                f"{f.name}: plan missing authorization denial"

    def test_credential_access_planned_is_false(self):
        for f in TP_DIR.glob("*.json"):
            plan = json.loads(f.read_text())
            assert plan.get("credential_access_planned") is False, \
                f"{f.name}: credential_access_planned must be false"

    def test_no_can_access_secrets(self):
        for f in TP_DIR.glob("*.json"):
            content = f.read_text()
            assert "can_access_secrets" not in content

    def test_unsafe_plan_claims_execution(self):
        plan = json.loads((TP_DIR / "unsafe-plan-claims-execution.json").read_text())
        stmt = plan["no_action_authorization_statement"].lower()
        assert "execution authorized" in stmt or "approved" in stmt, \
            "Unsafe fixture should contain execution claim for testing"
