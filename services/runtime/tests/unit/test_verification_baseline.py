"""Unit tests for the Verification Baseline Runner.

Tests validate that the runner correctly orchestrates all gates, classifies
them as hard/escalation/advisory, and produces proper output.

Tests use the runner module directly (import) rather than subprocess to
avoid double-test-nesting.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"

# Ensure project root + scripts dir are importable
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _make_fake_result(stdout="", stderr="", returncode=0):
    """Create a fake subprocess.CompletedProcess."""
    result = MagicMock()
    result.stdout = stdout
    result.stderr = stderr
    result.returncode = returncode
    return result


class TestVerificationBaselineGates:
    """Test that the runner includes all expected gates."""

    def test_runner_includes_eval_gate(self):
        from scripts.run_verification_baseline import run_all_gates

        with patch("scripts.run_verification_baseline.subprocess.run") as mock_run:
            mock_run.return_value = _make_fake_result(stdout="24/24 passed")
            summary = run_all_gates()
            gate_names = [r.name for r in summary.results]
            assert any("Eval corpus" in n for n in gate_names), f"Missing eval gate in: {gate_names}"

    def test_runner_includes_architecture_gate(self):
        from scripts.run_verification_baseline import run_all_gates

        with patch("scripts.run_verification_baseline.subprocess.run") as mock_run:
            mock_run.return_value = _make_fake_result(stdout="Architecture boundaries clean")
            summary = run_all_gates()
            gate_names = [r.name for r in summary.results]
            assert any("Architecture" in n for n in gate_names), f"Missing architecture gate in: {gate_names}"

    def test_runner_includes_runtime_evidence_gate(self):
        from scripts.run_verification_baseline import run_all_gates

        with patch("scripts.run_verification_baseline.subprocess.run") as mock_run:
            mock_run.return_value = _make_fake_result(stdout="integrity verified")
            summary = run_all_gates()
            gate_names = [r.name for r in summary.results]
            assert any("Runtime evidence" in n for n in gate_names), f"Missing runtime evidence gate in: {gate_names}"

    def test_runner_includes_db_audit_gate(self):
        from scripts.run_verification_baseline import run_all_gates

        with patch("scripts.run_verification_baseline.subprocess.run") as mock_run:
            mock_run.return_value = _make_fake_result(stdout="evidence chain intact")
            summary = run_all_gates()
            gate_names = [r.name for r in summary.results]
            assert any("DB-backed audit" in n for n in gate_names), f"Missing DB audit gate in: {gate_names}"

    def test_runner_includes_repo_cli_smoke_gate(self):
        from scripts.run_verification_baseline import run_all_gates

        with patch("scripts.run_verification_baseline.subprocess.run") as mock_run:
            mock_run.return_value = _make_fake_result(
                stdout=json.dumps({"decision": "execute", "side_effects": {"file_writes": False}})
            )
            summary = run_all_gates()
            gate_names = [r.name for r in summary.results]
            assert sum(1 for n in gate_names if "Repo CLI smoke" in n) == 2, (
                f"Missing repo CLI smoke gates in: {gate_names}"
            )

    def test_runner_includes_unit_integration_contract_tests(self):
        from scripts.run_verification_baseline import run_all_gates

        with patch("scripts.run_verification_baseline.subprocess.run") as mock_run:
            mock_run.return_value = _make_fake_result(stdout="passed")
            summary = run_all_gates()
            gate_names = [r.name for r in summary.results]
            assert any("Unit tests" in n for n in gate_names)
            assert any("Integration tests" in n for n in gate_names)
            assert any("Contract tests" in n for n in gate_names)


class TestGateClassification:
    """Test that gates are correctly classified."""

    def test_failure_in_hard_gate_makes_runner_fail(self):
        from scripts.run_verification_baseline import run_all_gates

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Make the first hard gate fail
            if call_count == 1:
                return _make_fake_result(stdout="error", returncode=1)
            return _make_fake_result(stdout="ok", returncode=0)

        with patch("scripts.run_verification_baseline.subprocess.run") as mock_run:
            mock_run.side_effect = side_effect
            summary = run_all_gates()
            assert not summary.overall_ready, "Runner should be BLOCKED when hard gate fails"

    def test_escalation_gate_does_not_block(self):
        import json

        from scripts.run_verification_baseline import run_all_gates

        # DB audit is escalation — should not block even if exit_code != 0
        # But we must also return valid JSON for the repo CLI smoke gates
        valid_json = json.dumps({"decision": "execute", "side_effects": {"file_writes": False}})
        reject_json = json.dumps({"decision": "reject", "side_effects": {"file_writes": False}})

        def side_effect(cmd, **kwargs):
            cmd_str = " ".join(cmd)
            is_ruff = "ruff" in cmd_str
            # Match primary script argument, not file arguments to ruff
            if str(SCRIPTS / "audit_runtime_evidence_db.py") in cmd and not is_ruff:
                result = MagicMock()
                result.stdout = "violations found"
                result.stderr = ""
                result.returncode = 1
                return result
            if str(SCRIPTS / "repo_governance_cli.py") in cmd and ".env" not in cmd_str:
                result = MagicMock()
                result.stdout = valid_json
                result.stderr = ""
                result.returncode = 0
                return result
            if str(SCRIPTS / "repo_governance_cli.py") in cmd and ".env" in cmd_str:
                result = MagicMock()
                result.stdout = reject_json
                result.stderr = ""
                result.returncode = 3
                return result
            result = MagicMock()
            result.stdout = "ok"
            result.stderr = ""
            result.returncode = 0
            return result

        with patch("scripts.run_verification_baseline.subprocess.run") as mock_run:
            mock_run.side_effect = side_effect
            summary = run_all_gates()
            assert summary.overall_ready, (
                f"Runner should be READY when only escalation gates have issues. Hard failed: {summary.hard_failed}"
            )

    def test_hard_gates_are_majority(self):
        from scripts.run_verification_baseline import run_all_gates

        with patch("scripts.run_verification_baseline.subprocess.run") as mock_run:
            mock_run.return_value = _make_fake_result(stdout="ok")
            summary = run_all_gates()
            hard_count = summary.hard_total
            esc_count = sum(1 for r in summary.results if r.gate_class == "escalation")
            # Hard gates should outnumber escalation
            assert hard_count > esc_count, f"Hard={hard_count}, Escalation={esc_count}"


class TestRunnerSideEffects:
    """Test that the runner has no forbidden side effects."""

    def test_runner_does_not_write_db(self):
        """Runner uses subprocess — no direct DB access."""
        from scripts.run_verification_baseline import run_all_gates

        with patch("scripts.run_verification_baseline.subprocess.run") as mock_run:
            mock_run.return_value = _make_fake_result(stdout="ok")
            run_all_gates()
        # The runner module itself has no sqlalchemy import
        import scripts.run_verification_baseline as rvb

        src = Path(rvb.__file__).read_text()
        assert "sqlalchemy" not in src, "Runner must not import sqlalchemy"

    def test_runner_does_not_invoke_shell_directly(self):
        """Runner uses subprocess.run with list args (no shell=True)."""
        from scripts.run_verification_baseline import run_all_gates

        with patch("scripts.run_verification_baseline.subprocess.run") as mock_run:
            mock_run.return_value = _make_fake_result(stdout="ok")
            run_all_gates()
            for call_args in mock_run.call_args_list:
                kwargs = call_args[1]
                # shell should never be True
                assert kwargs.get("shell") is not True, f"shell=True found: {call_args}"

    def test_runner_output_contains_json_summary(self):
        from scripts.run_verification_baseline import run_all_gates

        with patch("scripts.run_verification_baseline.subprocess.run") as mock_run:
            mock_run.return_value = _make_fake_result(stdout="ok")
            summary = run_all_gates()
        assert isinstance(summary.overall_ready, bool)
        assert len(summary.results) > 5
