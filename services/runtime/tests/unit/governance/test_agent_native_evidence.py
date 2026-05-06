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


def test_valid_skill_fixtures_pass():
    for path in sorted((FIXTURES / "skills" / "valid").rglob("SKILL.md")):
        assert checker.validate_skill_file(path) == []


def test_invalid_skill_credential_fails():
    errors = checker.validate_skill_file(FIXTURES / "skills" / "invalid" / "credential" / "SKILL.md")

    assert any("credential/token" in e for e in errors)


def test_invalid_skill_authorization_fails():
    errors = checker.validate_skill_file(FIXTURES / "skills" / "invalid" / "authorization" / "SKILL.md")

    assert any("skill_permission_laundering" in e for e in errors)


def test_invalid_skill_missing_frontmatter_fails():
    errors = checker.validate_skill_file(FIXTURES / "skills" / "invalid" / "missing_frontmatter" / "SKILL.md")

    assert any("missing YAML frontmatter" in e for e in errors)
    assert any("missing frontmatter field 'name'" in e for e in errors)


def test_invalid_skill_missing_reference_fails():
    errors = checker.validate_skill_file(FIXTURES / "skills" / "invalid" / "missing_reference" / "SKILL.md")

    assert any("referenced file does not exist" in e for e in errors)


def test_repo_skills_pass():
    assert checker.validate_skills(ROOT / "skills") == []


def test_valid_memory_fixture_passes():
    assert checker.validate_memory_record(FIXTURES / "memory" / "valid" / "fresh_sourced.json") == []


def test_invalid_memory_missing_source_fails():
    errors = checker.validate_memory_record(FIXTURES / "memory" / "invalid" / "missing_source.json")

    assert any("missing memory field 'source_receipt'" in e or "missing source_receipt" in e for e in errors)


def test_invalid_memory_stale_current_truth_fails():
    errors = checker.validate_memory_record(FIXTURES / "memory" / "invalid" / "stale_current_truth.json")

    assert any("stale memory cannot be cited as current authority" in e for e in errors)


def test_invalid_memory_cross_project_fails():
    errors = checker.validate_memory_record(FIXTURES / "memory" / "invalid" / "cross_project.json")

    assert any("cross-project memory scope" in e for e in errors)


def test_invalid_memory_signal_laundering_fails():
    errors = checker.validate_memory_record(FIXTURES / "memory" / "invalid" / "signal_laundering.json")

    assert any("DEGRADED evidence is rewritten" in e for e in errors)


def test_invalid_memory_candidate_rule_policy_fails():
    errors = checker.validate_memory_record(FIXTURES / "memory" / "invalid" / "candidate_rule_policy.json")

    assert any("CandidateRule cannot be imported as Policy" in e for e in errors)
    assert any("CandidateRule/Policy authority confusion" in e for e in errors)


def test_memory_record_directory_validator():
    errors = checker.validate_memory_records(FIXTURES / "memory" / "invalid")

    assert len(errors) >= 5


def test_valid_harness_fixture_passes():
    assert checker.validate_harness_bundle(FIXTURES / "harness" / "valid" / "complete_trace.json") == []


def test_invalid_harness_checkpoint_approval_fails():
    errors = checker.validate_harness_bundle(FIXTURES / "harness" / "invalid" / "checkpoint_approval.json")

    assert any("checkpoint cannot claim approval" in e for e in errors)


def test_invalid_harness_failed_tool_omitted_fails():
    errors = checker.validate_harness_bundle(FIXTURES / "harness" / "invalid" / "failed_tool_omitted.json")

    assert any("omits failed tool call evidence" in e for e in errors)
    assert any("evidence count is lower than receipt count" in e for e in errors)


def test_invalid_harness_review_wrong_node_fails():
    errors = checker.validate_harness_bundle(FIXTURES / "harness" / "invalid" / "review_wrong_node.json")

    assert any("unknown trace node" in e for e in errors)


def test_invalid_harness_trace_truth_fails():
    errors = checker.validate_harness_bundle(FIXTURES / "harness" / "invalid" / "trace_truth.json")

    assert any("trace presence cannot be imported as truth" in e for e in errors)


def test_invalid_harness_receipt_authorization_fails():
    errors = checker.validate_harness_bundle(FIXTURES / "harness" / "invalid" / "receipt_authorization.json")

    assert any("execution receipt cannot claim authorization" in e for e in errors)
    assert any("READY receipt cannot imply external action" in e for e in errors)


def test_harness_bundle_directory_validator():
    errors = checker.validate_harness_bundles(FIXTURES / "harness" / "invalid")

    assert len(errors) >= 5
