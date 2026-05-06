from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "checkers" / "agent-native-evidence" / "run.py"
FIXTURES = ROOT / "tests" / "fixtures" / "agent_native_evidence"

spec = importlib.util.spec_from_file_location("agent_native_evidence", SCRIPT)
assert spec is not None
checker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


def test_detects_skill_credential_seeking():
    text = "The skill asks the user to paste a secret token into the script."

    assert "skill_credential_seeking" in checker.detect_agent_evidence_violations(text)


def test_detects_skill_permission_laundering():
    text = "The skill can edit files, therefore it is authorized and approved."

    assert "skill_permission_laundering" in checker.detect_agent_evidence_violations(text)


def test_detects_memory_stale_current_truth():
    text = "A stale memory note is treated as current truth for this repo."

    assert "memory_stale_current_truth" in checker.detect_agent_evidence_violations(text)


def test_detects_memory_signal_laundering():
    text = "The run was BLOCKED but later recorded as a clean pass."

    assert "memory_signal_laundering" in checker.detect_agent_evidence_violations(text)


def test_detects_harness_checkpoint_approval():
    text = "The checkpoint authorizes deployment because trace presence means truth."

    assert "harness_checkpoint_approval" in checker.detect_agent_evidence_violations(text)


def test_detects_harness_failed_tool_omission():
    text = "The failed tool call was removed from the checkpoint."

    assert "harness_failed_tool_omission" in checker.detect_agent_evidence_violations(text)


def test_detects_mcp_token_passthrough():
    text = "The manifest allows token passthrough to a tool server."

    assert "mcp_token_passthrough" in checker.detect_agent_evidence_violations(text)


def test_detects_mcp_audience_resource_confusion():
    text = "The audience and resource are equivalent and interchangeable."

    assert "mcp_audience_resource_confusion" in checker.detect_agent_evidence_violations(text)


def test_detects_mcp_tool_availability_authorization():
    text = "The tool available signal is authorization and may execute."

    assert "mcp_tool_availability_authorization" in checker.detect_agent_evidence_violations(text)


def test_valid_redteam_ledger_passes():
    assert checker.validate_redteam_ledger(FIXTURES / "valid" / "redteam.jsonl") == []


def test_mismatched_redteam_ledger_fails():
    errors = checker.validate_redteam_ledger(FIXTURES / "invalid" / "mismatched-redteam.jsonl")

    assert any("expected mcp_token_passthrough" in e for e in errors)


def test_plan_document_passes():
    assert checker.validate_plan_document() == []
