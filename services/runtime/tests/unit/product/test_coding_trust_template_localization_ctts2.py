"""CTTS-2 localization dogfood tests.

These tests exercise project-independent Coding Trust templates after a target
project AI has localized them into fake project evidence.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from ordivon_verify import discover_external_evidence, main, render_discovery_markdown, render_summary
from ordivon_verify.report import build_report, render_markdown
from ordivon_verify.runner import run_external_checker


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures" / "coding_trust_localization"
FORBIDDEN_TEMPLATE_TEXT = (
    "/root/projects/hermes-agent",
    "/root/projects/Ordivon",
    "approved to deploy",
    "release authorized",
    "safe to merge",
    "CandidateRule is policy",
)


def _copy_fixture(tmp_path: Path, name: str) -> Path:
    target = tmp_path / name
    shutil.copytree(FIXTURES / name, target)
    return target


def _run_json(repo: Path, *args: str, capsys):
    exit_code = main(["check", str(repo), *args, "--json"])
    payload = json.loads(capsys.readouterr().out)
    return exit_code, payload


def test_minimal_localized_fixture_binds_claim_to_l2_evidence_and_summary_is_compact(tmp_path, capsys):
    repo = _copy_fixture(tmp_path, "minimal_localization")

    suggestion = discover_external_evidence(repo)
    bindings = suggestion["inventory"]["agent_claim_bindings"]
    by_id = {item["claim_id"]: item for item in bindings["items"]}
    summary_exit = main(["check", str(repo), "--profile", "coding", "--risk-stage", "vibe", "--summary"])
    summary = capsys.readouterr().out

    assert by_id["claim-001"]["trust_signal"] == "READY_WITHOUT_AUTHORIZATION"
    assert by_id["claim-002"]["trust_signal"] == "BLOCKED"
    assert "test_evidence" in by_id["claim-002"]["missing_evidence"]
    assert summary_exit == 2
    assert "Ordivon Verify Summary" in summary
    assert "Surfaces" not in summary
    assert "does not authorize execution" in summary


def test_standard_localized_fixture_ready_requires_claim_review_and_owner_confirmed_gate(tmp_path, capsys):
    repo = _copy_fixture(tmp_path, "standard_localization")

    exit_code, report = _run_json(repo, "--profile", "coding", "--risk-stage", "merge", capsys=capsys)

    assert exit_code == 0
    assert report["status"] == "READY"
    assert report["trust_signal"] == "READY_WITHOUT_AUTHORIZATION"
    assert report["surfaces"]["review"]["status"] == "PASS"
    assert report["surfaces"]["gates"]["status"] == "PASS"


def test_standard_missing_claim_binding_at_merge_stage_is_blocked(tmp_path, capsys):
    repo = _copy_fixture(tmp_path, "standard_localization")
    (repo / "governance" / "agent-claim-bindings.jsonl").unlink()

    exit_code, report = _run_json(repo, "--profile", "coding", "--risk-stage", "merge", capsys=capsys)

    assert exit_code == 1
    assert report["status"] == "BLOCKED"
    assert any(item["check"] == "agent_claim_bindings" for item in report["missing_evidence"])


def test_workflow_candidate_is_not_canonical_gate_without_owner_confirmation(tmp_path):
    repo = _copy_fixture(tmp_path, "standard_localization")
    gate_manifest = repo / "governance" / "verification-gate-manifest.json"
    data = json.loads(gate_manifest.read_text(encoding="utf-8"))
    data["gates"][0]["owner_confirmed"] = False
    gate_manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")

    result = run_external_checker(
        "gates", repo, "standard", {"gate_manifest": "governance/verification-gate-manifest.json"}
    )

    assert result["status"] == "FAIL"
    assert "owner_confirmed must be true" in result["stderr"]


def test_evidence_without_review_is_not_reviewed_or_gate_checked(tmp_path, capsys):
    repo = _copy_fixture(tmp_path, "standard_localization")
    binding = {
        "claim_id": "claim-no-review",
        "claim": "Implemented merge-stage fixture with tests.",
        "work_artifacts": ["receipts/external-audit-receipt.md"],
        "test_evidence": "python -m pytest tests/ -q -> 1 passed",
        "receipt": "receipts/external-audit-receipt.md",
        "trust_signal": "DEGRADED",
        "boundary": "Missing review evidence should downgrade trust.",
    }
    (repo / "governance" / "agent-claim-bindings.jsonl").write_text(json.dumps(binding) + "\n", encoding="utf-8")

    exit_code, report = _run_json(repo, "--profile", "coding", "--risk-stage", "merge", capsys=capsys)

    assert exit_code == 1
    assert report["status"] == "BLOCKED"
    assert report["surfaces"]["review"]["status"] == "FAIL"


def test_deep_localized_fixture_blocks_release_skill_tool_and_debt_gaps(tmp_path, capsys):
    repo = _copy_fixture(tmp_path, "deep_localization")

    exit_code, report = _run_json(repo, "--profile", "coding", "--risk-stage", "release", capsys=capsys)

    assert exit_code == 1
    assert report["status"] == "BLOCKED"
    assert any(item["check"] == "release_claim_audit" for item in report["hard_failures"])
    assert any(item["check"] == "skill_safety" for item in report["hard_failures"])


def test_candidate_rule_draft_is_not_active_policy_and_allowed_tools_is_not_permission():
    repo = FIXTURES / "deep_localization"
    candidate = json.loads((repo / "governance" / "candidate-rule-drafts.jsonl").read_text(encoding="utf-8"))
    skill = json.loads((repo / "governance" / "skill-safety-report.json").read_text(encoding="utf-8"))
    tool = json.loads((repo / "governance" / "tool-boundary-map.jsonl").read_text(encoding="utf-8"))

    assert candidate["status"] == "draft"
    assert "advisory" in candidate["boundary"].lower()
    assert "permission" in skill["items"][0]["boundary"].lower()
    assert "permission" in tool["permission_boundary"].lower()
    assert "not authorization" in skill["items"][0]["boundary"].lower()


def test_reports_distinguish_candidates_from_canonical_gates_and_evidence_from_approval(tmp_path):
    repo = _copy_fixture(tmp_path, "standard_localization")
    suggestion = discover_external_evidence(repo, include_standard_pack=True, template_tier="standard")
    markdown = render_discovery_markdown(suggestion)

    assert "candidate evidence hints, not authority" in markdown
    assert "owner confirmation still required" not in markdown or "owner confirmation" in markdown
    assert "Template files are project-independent placeholders" in markdown
    assert "approval" not in markdown.lower() or "not approval" in markdown.lower()


def test_ready_output_has_no_positive_authorization_wording():
    report = build_report(
        [
            {
                "id": "receipts",
                "label": "Receipt Integrity",
                "status": "PASS",
                "exit_code": 0,
                "stdout": "ok",
                "stderr": "",
            }
        ],
        "advisory",
        "/fixture",
        None,
    )
    text = render_markdown(report) + render_summary(report)
    lower = text.lower()

    assert "READY_WITHOUT_AUTHORIZATION" in text
    for phrase in (
        "approved to",
        "authorizes",
        "safe to merge",
        "safe to deploy",
        "safe to release",
        "production ready",
        "certified",
        "compliant",
    ):
        assert phrase not in lower


def test_degraded_output_is_not_pass_wording():
    report = build_report(
        [
            {
                "id": "debt",
                "label": "Verification Debt",
                "status": "WARN",
                "exit_code": -1,
                "stdout": "",
                "stderr": "Not configured: debt_ledger",
                "missing_evidence": True,
            }
        ],
        "advisory",
        "/fixture",
        None,
    )
    text = render_markdown(report)

    assert "**Status:** DEGRADED" in text
    assert "DEGRADED is PASS" not in text
    assert "DEGRADED means PASS" not in text


def test_template_bodies_are_project_independent_and_candidates_are_separated(tmp_path):
    repo = _copy_fixture(tmp_path, "minimal_localization")
    suggestion = discover_external_evidence(repo, include_standard_pack=True, template_tier="deep")
    files = suggestion["standard_pack_draft"]["files"]
    template_only = {name: value for name, value in files.items() if name != "governance/discovery-candidates.json"}
    serialized_templates = json.dumps(template_only)
    serialized_candidates = json.dumps(files["governance/discovery-candidates.json"])

    for forbidden in FORBIDDEN_TEMPLATE_TEXT:
        assert forbidden not in serialized_templates
    assert str(repo) not in serialized_templates
    assert "minimal_localization" in serialized_candidates


def test_cli_template_regressions_and_no_target_writes(tmp_path, capsys):
    repo = _copy_fixture(tmp_path, "minimal_localization")
    before = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*") if p.is_file())

    assert main(["check", str(repo), "--suggest-config", "--template", "minimal", "--summary"]) == 0
    assert "Template Pack Draft" in capsys.readouterr().out
    assert main(["check", str(repo), "--suggest-config", "--template", "standard", "--markdown"]) == 0
    assert "Tier: `standard`" in capsys.readouterr().out
    assert main(["check", str(repo), "--suggest-config", "--template", "deep", "--full"]) == 0
    deep_json = json.loads(capsys.readouterr().out)
    assert deep_json["standard_pack_draft"]["template_tier"] == "deep"
    assert main(["check", str(repo), "--suggest-config", "--template", "invalid"]) == 3
    assert "Invalid template" in capsys.readouterr().err

    after = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*") if p.is_file())
    assert before == after


def test_new_ai_context_check_is_discoverable_from_onboarding_docs():
    docs = "\n".join(
        [
            (Path("AGENTS.md")).read_text(encoding="utf-8"),
            (Path("docs/ai/README.md")).read_text(encoding="utf-8"),
            (Path("docs/ai/current-phase-boundaries.md")).read_text(encoding="utf-8"),
            (Path("docs/ai/new-ai-collaborator-guide.md")).read_text(encoding="utf-8"),
            (Path("docs/product/coding-trust-profile-template-system.md")).read_text(encoding="utf-8"),
            (Path("docs/product/coding-trust-localization-casebook-ctts-2.md")).read_text(encoding="utf-8"),
        ]
    )

    docs_lower = docs.lower()
    required = [
        "ctts",
        "discovery-candidates.json",
        "minimal",
        "standard",
        "deep",
        "ready_without_authorization",
        "candidaterule",
        "skill/tool/workflow existence",
        "project ai localizes evidence",
        "owner/reviewer",
    ]
    for phrase in required:
        assert phrase in docs_lower
