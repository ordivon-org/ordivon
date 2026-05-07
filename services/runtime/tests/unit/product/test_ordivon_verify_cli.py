"""Tests for Ordivon Verify CLI skeleton.

Covers: command dispatch, status mapping, JSON output, exit codes,
error handling, and checker integration (mocked).
"""

from __future__ import annotations

import json
import subprocess
import sys
from unittest.mock import MagicMock

from ordivon_verify import (
    run_check,
    determine_status,
    build_report,
    render_markdown,
    render_summary,
    discover_external_evidence,
    render_discovery_markdown,
    status_to_exit_code,
    parse_args,
    main,
)
from ordivon_verify.runner import CHECKER_SCRIPTS, _get_readonly_gate_ids


# ── Unit: status_to_exit_code ────────────────────────────────────────────


def test_status_ready_exit_0():
    assert status_to_exit_code("READY") == 0


def test_status_blocked_exit_1():
    assert status_to_exit_code("BLOCKED") == 1


def test_status_degraded_exit_2():
    assert status_to_exit_code("DEGRADED") == 2


def test_status_needs_review_exit_2():
    assert status_to_exit_code("NEEDS_REVIEW") == 2


def test_status_unknown_exit_1():
    assert status_to_exit_code("UNKNOWN") == 1


# ── Unit: determine_status ───────────────────────────────────────────────


def test_determine_status_all_pass():
    results = [
        {"id": "receipts", "status": "PASS", "exit_code": 0},
        {"id": "debt", "status": "PASS", "exit_code": 0},
    ]
    assert determine_status(results) == "READY"


def test_determine_status_one_fail():
    results = [
        {"id": "receipts", "status": "PASS", "exit_code": 0},
        {"id": "debt", "status": "FAIL", "exit_code": 1},
    ]
    assert determine_status(results) == "BLOCKED"


def test_determine_status_all_fail():
    results = [
        {"id": "receipts", "status": "FAIL", "exit_code": 1},
        {"id": "debt", "status": "FAIL", "exit_code": 1},
    ]
    assert determine_status(results) == "BLOCKED"


# ── Unit: build_report ───────────────────────────────────────────────────


def test_build_report_json_fields():
    results = [
        {
            "id": "receipts",
            "label": "Receipt Integrity",
            "status": "PASS",
            "exit_code": 0,
            "stdout": "All checks pass.",
            "stderr": "",
        },
    ]
    report = build_report(results, "all", "/root/test", None)
    assert report["tool"] == "ordivon-verify"
    assert report["schema_version"] == "0.1"
    assert report["status"] == "READY"
    assert report["mode"] == "all"
    assert report["root"] == "/root/test"
    assert len(report["checks"]) == 1
    assert report["checks"][0]["id"] == "receipts"
    assert report["checks"][0]["status"] == "PASS"
    assert "hard_failures" in report
    assert "warnings" in report
    assert "disclaimer" in report


def test_build_report_with_failures():
    results = [
        {
            "id": "receipts",
            "label": "Receipt Integrity",
            "status": "PASS",
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
        },
        {
            "id": "debt",
            "label": "Verification Debt",
            "status": "FAIL",
            "exit_code": 1,
            "stdout": "",
            "stderr": "overdue debt",
        },
    ]
    report = build_report(results, "all", "/root/test", None)
    assert report["status"] == "BLOCKED"
    assert len(report["hard_failures"]) == 1
    assert report["hard_failures"][0]["check"] == "debt"


# ── Unit: parse_args ─────────────────────────────────────────────────────


def test_parse_args_default_to_all():
    """Default (no command) should have command=None, handled by main as 'all'."""
    args = parse_args([])
    assert args.command is None


def test_parse_args_all():
    args = parse_args(["all"])
    assert args.command == "all"


def test_parse_args_suggest_config_flag():
    args = parse_args(["check", "/tmp/example", "--suggest-config"])
    assert args.command == "check"
    assert args.target == "/tmp/example"
    assert args.suggest_config is True


def test_parse_args_standard_pack_flag():
    args = parse_args(["check", "/tmp/example", "--suggest-config", "--standard-pack"])
    assert args.command == "check"
    assert args.suggest_config is True
    assert args.standard_pack is True


def test_parse_args_template_flag():
    args = parse_args(["check", "/tmp/example", "--suggest-config", "--template", "deep"])
    assert args.command == "check"
    assert args.suggest_config is True
    assert args.template == "deep"


def test_parse_args_profile_and_risk_stage_flags():
    args = parse_args(["check", "/tmp/example", "--profile", "coding", "--risk-stage", "merge", "--summary"])
    assert args.profile == "coding"
    assert args.risk_stage == "merge"
    assert args.summary is True


def test_discover_external_evidence_suggests_config(tmp_path):
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    (tmp_path / "SECURITY.md").write_text("# Security\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_smoke.py").write_text("def test_ok(): pass\n", encoding="utf-8")
    (tmp_path / "RELEASE_v1.md").write_text("- Shipped secure deployment path\n", encoding="utf-8")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "tests.yml").write_text("name: Tests\n", encoding="utf-8")
    (tmp_path / "skills" / "demo").mkdir(parents=True)
    (tmp_path / "skills" / "demo" / "SKILL.md").write_text(
        "---\nname: demo\n---\nUses shell. Set API key in env.\n",
        encoding="utf-8",
    )

    suggestion = discover_external_evidence(tmp_path)

    assert suggestion["mode"] == "suggest_config"
    assert suggestion["suggested_config"]["mode"] == "advisory"
    assert suggestion["suggested_config"]["pack"] == "coding"
    assert suggestion["suggested_config"]["profile"] == "ai_coding_trust_audit"
    assert "README.md" in suggestion["suggested_config"]["receipt_paths"]
    assert suggestion["inventory"]["tests"]["python_test_files"] == 1
    assert suggestion["inventory"]["skills"]["count"] == 1
    assert suggestion["inventory"]["skills"]["credential_language_mentions"] == ["skills/demo/SKILL.md"]
    assert suggestion["inventory"]["skills"]["items"][0]["status"] in ("WARN", "FAIL")
    assert suggestion["inventory"]["gate_manifest_candidates"]
    assert suggestion["inventory"]["release_claim_audit"]["missing_evidence_ref_count"] == 1
    assert suggestion["inventory"]["agent_native_risk_matrix"]


def test_discover_external_evidence_classifies_skills_per_file(tmp_path):
    clean = tmp_path / "skills" / "clean"
    clean.mkdir(parents=True)
    (clean / "SKILL.md").write_text(
        "---\nname: clean\n---\nRead-only review. Human review required. Run tests before use.\n",
        encoding="utf-8",
    )
    risky = tmp_path / "skills" / "risky"
    risky.mkdir(parents=True)
    (risky / "SKILL.md").write_text(
        "---\nname: risky\nallowed-tools: Bash\n---\nShell script asks for API key and says this authorizes deploy.\n",
        encoding="utf-8",
    )

    skills = discover_external_evidence(tmp_path)["inventory"]["skills"]

    by_path = {item["path"]: item for item in skills["items"]}
    assert by_path["skills/clean/SKILL.md"]["status"] == "PASS"
    assert by_path["skills/risky/SKILL.md"]["status"] == "FAIL"
    assert "authorization_language" in by_path["skills/risky/SKILL.md"]["findings"]


def test_discover_external_evidence_marks_deploy_workflow_not_canonical(tmp_path):
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "tests.yml").write_text(
        "on: [pull_request]\nname: Tests\njobs:\n  test:\n    steps:\n      - run: pytest\n",
        encoding="utf-8",
    )
    (wf_dir / "deploy.yml").write_text(
        "on: [workflow_dispatch]\npermissions:\n  contents: write\njobs:\n  deploy:\n    steps:\n      - run: gh release create v1\n",
        encoding="utf-8",
    )

    gates = discover_external_evidence(tmp_path)["inventory"]["gate_manifest_candidates"]
    by_id = {gate["gate_id"]: gate for gate in gates}

    assert by_id["tests"]["canonical_confidence"] == "high"
    assert by_id["deploy"]["canonical_confidence"] == "not_canonical"


def test_discover_external_evidence_maps_release_claims_to_signals(tmp_path):
    (tmp_path / "CHANGELOG.md").write_text(
        "\n".join(
            [
                "- Shipped secure production-ready deployment path.",
                "- Fixed parser with CI test evidence in #123.",
            ]
        ),
        encoding="utf-8",
    )

    audit = discover_external_evidence(tmp_path)["inventory"]["release_claim_audit"]
    by_claim = {item["claim_id"]: item for item in audit["items"]}

    assert by_claim["release-claim-001"]["trust_signal"] == "BLOCKED"
    assert by_claim["release-claim-002"]["evidence_status"] == "supported"


def test_discover_external_evidence_binds_agent_claims(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "agent_claims.jsonl").write_text(
        json.dumps(
            {
                "claim_id": "claim-clean",
                "claim": "Implemented feature and tests passed.",
                "work_artifacts": ["src/app.py"],
                "test_evidence": "pytest -q",
                "receipt": "receipt.md",
                "review_evidence": "review.md",
            }
        )
        + "\n"
        + json.dumps(
            {
                "claim_id": "claim-missing-test",
                "claim": "Tests passed for missing evidence.",
                "work_artifacts": ["src/app.py"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    bindings = discover_external_evidence(tmp_path)["inventory"]["agent_claim_bindings"]
    by_id = {item["claim_id"]: item for item in bindings["items"]}

    assert by_id["claim-clean"]["trust_signal"] == "READY_WITHOUT_AUTHORIZATION"
    assert by_id["claim-missing-test"]["trust_signal"] == "BLOCKED"


def test_discover_external_evidence_standard_pack_dry_run(tmp_path):
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_smoke.py").write_text("def test_ok(): pass\n", encoding="utf-8")

    suggestion = discover_external_evidence(tmp_path, include_standard_pack=True, risk_stage="merge")
    draft = suggestion["standard_pack_draft"]

    assert draft["writes_files"] is False
    assert draft["template_pack"] is True
    assert "ordivon.verify.json" in draft["files"]
    assert "governance/verification-gate-manifest.json" in draft["files"]
    assert draft["files"]["ordivon.verify.json"]["mode"] == "standard"
    assert draft["files"]["ordivon.verify.json"]["risk_stage"] == "merge"
    assert draft["files"]["ordivon.verify.json"]["project_name"] == "<project-name>"
    assert draft["files"]["ordivon.verify.json"]["gate_manifest"] == "governance/verification-gate-manifest.json"
    assert draft["files"]["governance/verification-gate-manifest.json"]["gates"][0]["gate_id"] == "<gate-id>"
    assert draft["files"]["governance/discovery-candidates.json"]["project_name"] == tmp_path.name
    assert draft["files"]["governance/document-registry.jsonl"][0]["type"] == "claim_or_receipt_candidate"


def test_discover_external_evidence_template_tiers_are_project_independent(tmp_path):
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")

    minimal = discover_external_evidence(tmp_path, include_standard_pack=True, template_tier="minimal")
    standard = discover_external_evidence(tmp_path, include_standard_pack=True, template_tier="standard")
    deep = discover_external_evidence(tmp_path, include_standard_pack=True, template_tier="deep")

    minimal_files = minimal["standard_pack_draft"]["files"]
    standard_files = standard["standard_pack_draft"]["files"]
    deep_files = deep["standard_pack_draft"]["files"]

    assert minimal["standard_pack_draft"]["template_tier"] == "minimal"
    assert standard["standard_pack_draft"]["template_tier"] == "standard"
    assert deep["standard_pack_draft"]["template_tier"] == "deep"
    assert "governance/verification-gate-manifest.json" not in minimal_files
    assert "governance/verification-gate-manifest.json" in standard_files
    assert "governance/tool-boundary-map.jsonl" in deep_files
    assert "governance/memory-source-ledger.jsonl" in deep_files
    template_only = {k: v for k, v in deep_files.items() if k != "governance/discovery-candidates.json"}
    serialized = json.dumps(template_only)
    assert str(tmp_path) not in serialized
    assert "/root/projects/hermes-agent" not in serialized


def test_render_discovery_markdown_contains_newcomer_sections(tmp_path):
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_smoke.py").write_text("def test_ok(): pass\n", encoding="utf-8")

    markdown = render_discovery_markdown(discover_external_evidence(tmp_path))

    assert "Ordivon Verify Discovery Report" in markdown
    assert "Suggested Config" in markdown
    assert "Gate Candidates" in markdown
    assert "Skill Safety Precheck" in markdown
    assert "Release Claim Evidence Map" in markdown
    assert "Agent Claim Bindings" in markdown
    assert "Agent-Native Risk Matrix" in markdown


def test_main_suggest_config_outputs_inventory(tmp_path, capsys):
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "tests.yml").write_text("name: Tests\n", encoding="utf-8")

    exit_code = main(["check", str(tmp_path), "--suggest-config"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["mode"] == "suggest_config"
    assert payload["root"] == str(tmp_path.resolve())
    assert payload["inventory"]["github_workflows"][0]["path"] == ".github/workflows/tests.yml"


def test_main_suggest_config_markdown_outputs_report(tmp_path, capsys):
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")

    exit_code = main(["check", str(tmp_path), "--suggest-config", "--markdown"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Ordivon Verify Discovery Report" in captured.out
    assert "Suggested Config" in captured.out


def test_main_suggest_config_standard_pack_markdown_outputs_draft(tmp_path, capsys):
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")

    exit_code = main(["check", str(tmp_path), "--suggest-config", "--standard-pack", "--markdown"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Template Pack Draft" in captured.out
    assert "ordivon.verify.json" in captured.out


def test_main_suggest_config_deep_template_markdown_outputs_deep_files(tmp_path, capsys):
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")

    exit_code = main(["check", str(tmp_path), "--suggest-config", "--template", "deep", "--markdown"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Template Pack Draft" in captured.out
    assert "Tier: `deep`" in captured.out
    assert "tool-boundary-map.jsonl" in captured.out
    assert "memory-source-ledger.jsonl" in captured.out


def test_main_emit_template_dir_writes_only_explicit_output_dir(tmp_path, capsys):
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    (target_repo / "README.md").write_text("# Target\n", encoding="utf-8")
    output_dir = tmp_path / "emitted-pack"
    before = sorted(p.relative_to(target_repo).as_posix() for p in target_repo.rglob("*") if p.is_file())

    exit_code = main(
        [
            "check",
            str(target_repo),
            "--suggest-config",
            "--template",
            "deep",
            "--emit-template-dir",
            str(output_dir),
            "--summary",
        ]
    )
    captured = capsys.readouterr()
    after = sorted(p.relative_to(target_repo).as_posix() for p in target_repo.rglob("*") if p.is_file())

    assert exit_code == 0
    assert before == after
    assert "Template Export" in captured.out
    assert (output_dir / "ordivon.verify.json").is_file()
    assert (output_dir / "PROJECT_AI_LOCALIZATION.md").is_file()
    assert (output_dir / "AI_TRUST_LEVELS.md").is_file()
    assert (output_dir / "governance" / "discovery-candidates.json").is_file()
    assert (output_dir / "governance" / "memory-source-ledger.jsonl").is_file()
    assert "<project-name>" in (output_dir / "ordivon.verify.json").read_text(encoding="utf-8")
    assert str(target_repo) not in (output_dir / "PROJECT_AI_LOCALIZATION.md").read_text(encoding="utf-8")


def test_emit_template_dir_requires_suggest_config(tmp_path, capsys):
    exit_code = main(["check", str(tmp_path), "--emit-template-dir", str(tmp_path / "out")])

    assert exit_code == 3
    assert "requires --suggest-config" in capsys.readouterr().err


def test_main_suggest_config_summary_outputs_compact_onboarding(tmp_path, capsys):
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "tests.yml").write_text("name: Tests\non: [pull_request]\n", encoding="utf-8")

    exit_code = main(["check", str(tmp_path), "--suggest-config", "--standard-pack", "--summary"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Ordivon Verify Onboarding Summary" in captured.out
    assert "Evidence Found" in captured.out
    assert "Template Pack Draft" in captured.out
    assert "Suggested Config" not in captured.out


def test_main_invalid_template_returns_3(tmp_path, capsys):
    exit_code = main(["check", str(tmp_path), "--suggest-config", "--template", "bespoke", "--json"])

    assert exit_code == 3
    assert "Invalid template" in capsys.readouterr().err


def test_main_unsupported_profile_returns_3(tmp_path, capsys):
    exit_code = main(["check", str(tmp_path), "--profile", "trade", "--json"])

    assert exit_code == 3
    assert "unsupported pack/profile" in capsys.readouterr().err


def test_main_invalid_risk_stage_returns_3(tmp_path, capsys):
    exit_code = main(["check", str(tmp_path), "--risk-stage", "chaos", "--json"])

    assert exit_code == 3
    assert "invalid risk_stage" in capsys.readouterr().err


def test_vibe_stage_missing_governance_is_degraded_not_blocked(tmp_path, capsys):
    exit_code = main(["check", str(tmp_path), "--profile", "coding", "--risk-stage", "vibe", "--json"])

    assert exit_code == 2
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "DEGRADED"


def test_receipt_paths_accept_markdown_files(tmp_path, capsys):
    receipt = tmp_path / "README.md"
    receipt.write_text(
        "# Receipt\n\nVerification passed locally.\nCommand: `python -m pytest tests/ -q`\n", encoding="utf-8"
    )
    config = tmp_path / "ordivon.verify.json"
    config.write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "mode": "advisory",
                "receipt_paths": ["README.md"],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(["check", str(tmp_path), "--config", str(config), "--json"])
    report = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    receipt_check = next(check for check in report["checks"] if check["id"] == "receipts")
    assert receipt_check["status"] == "PASS"
    assert receipt_check["summary"] == "1 receipt(s) scanned, 0 contradictions"


def test_configured_receipt_paths_that_scan_zero_are_missing_evidence(tmp_path, capsys):
    config = tmp_path / "ordivon.verify.json"
    config.write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "mode": "advisory",
                "receipt_paths": ["missing.md"],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(["check", str(tmp_path), "--config", str(config), "--json"])
    report = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    receipt_check = next(check for check in report["checks"] if check["id"] == "receipts")
    assert receipt_check["status"] == "WARN"
    assert any(item["check"] == "receipts" for item in report["missing_evidence"])
    assert report["profile"] == "ai_coding_trust_audit"
    assert report["risk_stage"] == "vibe"
    assert report["missing_evidence"]


def test_merge_stage_requires_agent_bindings_and_confirmed_gates(tmp_path, capsys):
    exit_code = main(["check", str(tmp_path), "--profile", "coding", "--risk-stage", "merge", "--json"])

    assert exit_code == 1
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "BLOCKED"
    assert report["risk_stage"] == "merge"
    assert any(item["check"] == "agent_claim_bindings" for item in report["missing_evidence"])
    assert any(item["check"] == "coding_profile_gate_manifest" for item in report["missing_evidence"])


def test_release_stage_blocks_unsafe_skill_and_release_claim(tmp_path, capsys):
    (tmp_path / "skills" / "danger").mkdir(parents=True)
    (tmp_path / "skills" / "danger" / "SKILL.md").write_text(
        "---\nname: danger\nallowed-tools: Bash\n---\nShell script asks for API key and says this authorizes deploy.\n",
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text("- Shipped secure production-ready deployment path.\n", encoding="utf-8")

    exit_code = main(["check", str(tmp_path), "--profile", "coding", "--risk-stage", "release", "--json"])

    assert exit_code == 1
    report = json.loads(capsys.readouterr().out)
    assert report["risk_stage"] == "release"
    assert any(f["check"] == "release_claim_audit" for f in report["hard_failures"])
    assert any(f["check"] == "skill_safety" for f in report["hard_failures"])


def test_release_stage_blocks_memory_authority_confusion(tmp_path, capsys):
    (tmp_path / "governance").mkdir()
    (tmp_path / "governance" / "memory-source-ledger.jsonl").write_text(
        json.dumps(
            {
                "memory_id": "mem-001",
                "source": "missing-receipt.md",
                "freshness": "2025-01-01",
                "scope": "OtherProject",
                "authority": "policy",
                "object_type": "CandidateRule",
                "evidence_status": "DEGRADED",
                "claim": "CandidateRule is active policy and degraded evidence is now truth.",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    exit_code = main(["check", str(tmp_path), "--profile", "coding", "--risk-stage", "release", "--json"])
    report = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert any(f["check"] == "memory_content_hygiene" for f in report["hard_failures"])
    memory = report["evidence_appendix"]["memory_content_hygiene"]
    assert memory["status_counts"]["BLOCKED"] == 1


def test_release_stage_blocks_harness_missing_failed_tool_and_checkpoint_approval(tmp_path, capsys):
    (tmp_path / "governance").mkdir()
    (tmp_path / "governance" / "harness-evidence.jsonl").write_text(
        json.dumps(
            {
                "bundle_id": "trace-001",
                "trace": {
                    "presence_claims_truth": True,
                    "nodes": [{"node_id": "review", "kind": "human_review"}],
                },
                "checkpoint": {"approval_claim": True, "authorizes_action": True},
                "tool_calls": [{"call_id": "call-pass", "status": "passed"}],
                "review_record": {
                    "human_reviewed": True,
                    "reviewed_node_id": "review",
                },
                "execution_receipt": {
                    "failed_tool_call_count": 1,
                    "authorization_claim": False,
                    "external_action_taken": False,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    exit_code = main(["check", str(tmp_path), "--profile", "coding", "--risk-stage", "release", "--json"])
    report = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert any(f["check"] == "harness_evidence_import" for f in report["hard_failures"])
    harness = report["evidence_appendix"]["harness_evidence_import"]
    assert harness["status_counts"]["BLOCKED"] == 1


def test_full_markdown_includes_memory_and_harness_appendix(tmp_path, capsys):
    (tmp_path / "governance").mkdir()
    (tmp_path / "governance" / "memory-source-ledger.jsonl").write_text(
        json.dumps(
            {
                "memory_id": "mem-ready",
                "source": "README.md",
                "freshness": "2026-05-08",
                "scope": "project",
                "authority": "supporting_evidence",
                "claim": "Local memory has source and freshness.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Receipt\n", encoding="utf-8")

    exit_code = main(["check", str(tmp_path), "--profile", "coding", "--risk-stage", "release", "--markdown", "--full"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Memory/content hygiene" in captured.out
    assert "Harness evidence import" in captured.out


def test_summary_output_is_compact(tmp_path, capsys):
    exit_code = main(["check", str(tmp_path), "--profile", "coding", "--risk-stage", "merge", "--summary"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Ordivon Verify Summary" in captured.out
    assert "Top Findings" in captured.out
    assert "Surfaces" not in captured.out


def test_full_markdown_includes_evidence_appendix(tmp_path, capsys):
    exit_code = main(["check", str(tmp_path), "--profile", "coding", "--risk-stage", "merge", "--markdown", "--full"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Evidence Appendix" in captured.out
    assert "Agent claim bindings" in captured.out


def test_parse_args_check_target():
    args = parse_args(["check", "."])
    assert args.command == "check"
    assert args.target == "."


def test_parse_args_receipts():
    args = parse_args(["receipts"])
    assert args.command == "receipts"


def test_parse_args_debt():
    args = parse_args(["debt"])
    assert args.command == "debt"


def test_parse_args_gates():
    args = parse_args(["gates"])
    assert args.command == "gates"


def test_parse_args_docs():
    args = parse_args(["docs"])
    assert args.command == "docs"


def test_parse_args_json_flag():
    args = parse_args(["all", "--json"])
    assert args.command == "all"
    assert args.json is True


def test_parse_args_markdown_flag():
    args = parse_args(["check", ".", "--markdown"])
    assert args.command == "check"
    assert args.target == "."
    assert args.markdown is True


def test_render_markdown_report_contains_pr_sections():
    results = [
        {
            "id": "receipts",
            "label": "Receipt Integrity",
            "status": "PASS",
            "exit_code": 0,
            "stdout": "1 receipt(s) scanned, 0 contradictions",
            "stderr": "",
        },
        {
            "id": "debt",
            "label": "Verification Debt",
            "status": "WARN",
            "exit_code": -1,
            "stdout": "",
            "stderr": "Not configured: debt_ledger",
            "missing_evidence": True,
            "next_action": "Add verification-debt-ledger.jsonl when moving from advisory to standard mode.",
        },
    ]
    markdown = render_markdown(build_report(results, "advisory", "/repo", None))
    assert "## Ordivon Verify Trust Report" in markdown
    assert "**Profile:** `ai_coding_trust_audit`" in markdown
    assert "| claims | PASS | receipts |" in markdown
    assert "### Missing Evidence" in markdown
    assert "READY means selected checks passed" in markdown
    assert "authorizes merge" not in markdown.lower()


def test_render_summary_report_contains_top_findings():
    report = build_report(
        [
            {
                "id": "agent_claim_bindings",
                "label": "Agent Claim Bindings",
                "status": "FAIL",
                "exit_code": 1,
                "stdout": "",
                "stderr": "No agent claim binding file found",
                "missing_evidence": True,
                "next_action": "Add agent_claims.jsonl.",
            }
        ],
        "advisory",
        "/repo",
        None,
        {"pack": "coding", "profile": "ai_coding_trust_audit", "risk_stage": "merge"},
    )

    summary = render_summary(report)

    assert "Ordivon Verify Summary" in summary
    assert "Risk stage:** `merge`" in summary
    assert "No agent claim binding file found" in summary


# ── Integration: run_check (mocked subprocess) ────────────────────────────


def test_run_check_pass(monkeypatch):
    """run_check returns PASS when subprocess exits 0."""
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = "All checks pass.\n"
    mock_run.stderr = ""

    def mock_subprocess_run(*args, **kwargs):
        return mock_run

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
    result = run_check("receipts")
    assert result["status"] == "PASS"
    assert result["exit_code"] == 0
    assert result["id"] == "receipts"


def test_run_check_fail(monkeypatch):
    """run_check returns FAIL when subprocess exits non-zero."""
    mock_run = MagicMock()
    mock_run.returncode = 1
    mock_run.stdout = "Violation found.\n"
    mock_run.stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_run)
    result = run_check("debt")
    assert result["status"] == "FAIL"
    assert result["exit_code"] == 1


def test_run_check_timeout(monkeypatch):
    """run_check handles subprocess timeout."""

    def mock_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="test", timeout=60)

    monkeypatch.setattr(subprocess, "run", mock_timeout)
    result = run_check("gates")
    assert result["status"] == "FAIL"
    assert result["exit_code"] == -1
    assert "timed out" in result["stderr"].lower()


def test_run_check_exception(monkeypatch):
    """run_check handles unexpected exceptions."""

    def mock_exception(*args, **kwargs):
        raise OSError("file not found")

    monkeypatch.setattr(subprocess, "run", mock_exception)
    result = run_check("docs")
    assert result["status"] == "FAIL"
    assert result["exit_code"] == -1
    assert "file not found" in result["stderr"]


# ── Integration: main() with mocked run_check ────────────────────────────


def _mock_run_pass(check_id: str) -> dict:
    return {
        "id": check_id,
        "label": check_id,
        "status": "PASS",
        "exit_code": 0,
        "stdout": "All good.",
        "stderr": "",
    }


def _mock_run_fail(check_id: str) -> dict:
    return {
        "id": check_id,
        "label": check_id,
        "status": "FAIL",
        "exit_code": 1,
        "stdout": "",
        "stderr": "Found issues.",
    }


def test_main_all_passes(monkeypatch, capsys):
    """main(['all']) with all checks passing -> exit 0, status READY."""
    monkeypatch.setattr("ordivon_verify.runner.run_check", _mock_run_pass)
    exit_code = main(["all"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "ORDIVON VERIFY" in captured.out
    assert "READY" in captured.out


def test_main_all_one_fail(monkeypatch, capsys):
    """main(['all']) with one check failing -> exit 1, status BLOCKED."""

    def mixed_run(check_id: str) -> dict:
        if check_id == "verification_debt":
            return _mock_run_fail(check_id)
        return _mock_run_pass(check_id)

    monkeypatch.setattr("ordivon_verify.runner.run_check", mixed_run)
    exit_code = main(["all"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "BLOCKED" in captured.out


def test_main_receipts_command(monkeypatch, capsys):
    """main(['receipts']) runs only receipts checker."""
    calls = []

    def track_run(check_id: str) -> dict:
        calls.append(check_id)
        return _mock_run_pass(check_id)

    monkeypatch.setattr("ordivon_verify.runner.run_check", track_run)
    exit_code = main(["receipts"])
    assert exit_code == 0
    assert calls == ["receipts"]


def test_main_debt_command(monkeypatch):
    """main(['debt']) runs only debt checker."""
    calls = []

    def track_run(check_id: str) -> dict:
        calls.append(check_id)
        return _mock_run_pass(check_id)

    monkeypatch.setattr("ordivon_verify.runner.run_check", track_run)
    exit_code = main(["debt"])
    assert exit_code == 0
    assert calls == ["debt"]


def test_main_gates_command(monkeypatch):
    """main(['gates']) runs only gates checker."""
    calls = []

    def track_run(check_id: str) -> dict:
        calls.append(check_id)
        return _mock_run_pass(check_id)

    monkeypatch.setattr("ordivon_verify.runner.run_check", track_run)
    exit_code = main(["gates"])
    assert exit_code == 0
    assert calls == ["gates"]


def test_main_docs_command(monkeypatch):
    """main(['docs']) runs only docs checker."""
    calls = []

    def track_run(check_id: str) -> dict:
        calls.append(check_id)
        return _mock_run_pass(check_id)

    monkeypatch.setattr("ordivon_verify.runner.run_check", track_run)
    exit_code = main(["docs"])
    assert exit_code == 0
    assert calls == ["docs"]


def test_main_default_maps_to_all(monkeypatch):
    """main([]) defaults to read-only Verify checks."""
    calls = []

    def track_run(check_id: str) -> dict:
        calls.append(check_id)
        return _mock_run_pass(check_id)

    monkeypatch.setattr("ordivon_verify.runner.run_check", track_run)
    exit_code = main([])
    assert exit_code == 0
    assert calls == _get_readonly_gate_ids()


def test_main_check_alias_maps_to_all(monkeypatch):
    """main(['check']) runs the read-only checker set."""
    calls = []

    def track_run(check_id: str) -> dict:
        calls.append(check_id)
        return _mock_run_pass(check_id)

    monkeypatch.setattr("ordivon_verify.runner.run_check", track_run)
    exit_code = main(["check"])
    assert exit_code == 0
    assert calls == _get_readonly_gate_ids()


def test_main_all_skips_side_effect_checkers(monkeypatch):
    """The public Verify entrypoint must not run state-updating checkers."""
    calls = []

    def track_run(check_id: str) -> dict:
        calls.append(check_id)
        return _mock_run_pass(check_id)

    monkeypatch.setattr("ordivon_verify.runner.run_check", track_run)
    exit_code = main(["all"])
    assert exit_code == 0
    assert "entropy_telemetry" not in calls
    assert "lesson_extraction" not in calls
    assert "policy_shadow" not in calls


def test_main_json_output_all_pass(monkeypatch, capsys):
    """main(['all', '--json']) emits valid JSON with required fields."""
    monkeypatch.setattr("ordivon_verify.runner.run_check", _mock_run_pass)
    exit_code = main(["all", "--json"])
    assert exit_code == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["tool"] == "ordivon-verify"
    assert report["status"] == "READY"
    assert report["trust_signal"] == "READY_WITHOUT_AUTHORIZATION"
    assert report["mode"] in ("all", "standard")  # auto-detects Ordivon-native
    assert len(report["checks"]) == len(_get_readonly_gate_ids())
    assert "surfaces" in report
    assert "claims" in report["surfaces"]
    assert report["hard_failures"] == []


def test_main_json_output_one_fail(monkeypatch, capsys):
    """main(['all', '--json']) with one failure -> status BLOCKED in JSON."""

    def mixed_run(check_id: str) -> dict:
        if check_id == "gate_manifest":
            return _mock_run_fail(check_id)
        return _mock_run_pass(check_id)

    monkeypatch.setattr("ordivon_verify.runner.run_check", mixed_run)
    exit_code = main(["all", "--json"])
    assert exit_code == 1
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["status"] == "BLOCKED"
    assert len(report["hard_failures"]) == 1


def test_main_unknown_command(monkeypatch):
    """main(['unknown']) -> exit code 3."""
    exit_code = main(["unknown"])
    assert exit_code == 3


def test_main_runtime_exception(monkeypatch):
    """main where build_report unexpectedly raises -> exit 4."""

    def mock_run(*args, **kwargs):
        return {
            "id": "receipts",
            "label": "Receipt Integrity",
            "status": "PASS",
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
        }

    monkeypatch.setattr("ordivon_verify.runner.run_check", mock_run)

    # Force an unexpected exception in build_report (called with --json)
    def boom_build(*args, **kwargs):
        raise RuntimeError("simulated crash in report builder")

    monkeypatch.setattr("ordivon_verify.cli.build_report", boom_build)
    exit_code = main(["all", "--json"])
    assert exit_code == 4


def test_main_no_shell_true(monkeypatch):
    """Verify that subprocess.run is called without shell=True."""
    calls = []

    def intercept(*args, **kwargs):
        calls.append(kwargs)
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = "ok"
        mock.stderr = ""
        return mock

    monkeypatch.setattr(subprocess, "run", intercept)
    main(["all"])
    for kw in calls:
        assert kw.get("shell", False) is False


# ── Verify no shell injection pattern ────────────────────────────────────


def test_run_check_uses_list_not_string(monkeypatch):
    """run_check passes a list (not a shell string) to subprocess.run."""
    calls = []

    def intercept(cmd, **kwargs):
        calls.append(cmd)
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = "ok"
        mock.stderr = ""
        return mock

    monkeypatch.setattr(subprocess, "run", intercept)
    run_check("receipts")
    assert len(calls) == 1
    # cmd should be a list (not a string)
    assert isinstance(calls[0], list)
    assert calls[0][0] == sys.executable


def test_main_invalid_explicit_config_returns_3(tmp_path, capsys):
    cfg = tmp_path / "ordivon.verify.json"
    cfg.write_text("{ invalid json")

    exit_code = main(["all", "--root", str(tmp_path), "--config", str(cfg)])

    assert exit_code == 3
    captured = capsys.readouterr()
    assert "Config parse error" in captured.err


def test_main_missing_explicit_config_returns_3(tmp_path, capsys):
    cfg = tmp_path / "missing.verify.json"

    exit_code = main(["all", "--root", str(tmp_path), "--config", str(cfg)])

    assert exit_code == 3
    captured = capsys.readouterr()
    assert "Config file not found" in captured.err


def test_main_invalid_auto_config_returns_3(tmp_path, capsys):
    cfg = tmp_path / "ordivon.verify.json"
    cfg.write_text("{ invalid json")

    exit_code = main(["all", "--root", str(tmp_path)])

    assert exit_code == 3
    captured = capsys.readouterr()
    assert "Config parse error" in captured.err


def test_standard_mode_without_receipt_paths_blocks(tmp_path, capsys):
    cfg = tmp_path / "ordivon.verify.json"
    cfg.write_text(json.dumps({"schema_version": "0.1", "mode": "standard"}))

    exit_code = main(["all", "--root", str(tmp_path), "--config", str(cfg), "--json"])

    assert exit_code == 1
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "BLOCKED"
    assert any(item["check"] == "receipts" for item in report["missing_evidence"])
    assert report["surfaces"]["receipts"]["status"] == "FAIL"


def test_native_checker_ids_map_to_public_trust_surfaces():
    report = build_report(
        [
            _mock_run_pass("receipt_integrity"),
            _mock_run_pass("verification_debt"),
            _mock_run_pass("gate_manifest"),
            _mock_run_pass("document_registry"),
        ],
        "standard",
        "/tmp/repo",
        None,
    )

    assert report["surfaces"]["claims"]["status"] == "PASS"
    assert report["surfaces"]["receipts"]["status"] == "PASS"
    assert report["surfaces"]["tests"]["status"] == "PASS"
    assert report["surfaces"]["diff"]["status"] == "PASS"
    assert report["surfaces"]["review"]["status"] == "PASS"
    assert report["surfaces"]["debt"]["status"] == "PASS"
    assert report["surfaces"]["gates"]["status"] == "PASS"
    assert report["surfaces"]["docs"]["status"] == "PASS"


# ── Verify CHECKER_SCRIPTS paths exist ────────────────────────────────────


def test_all_checker_scripts_exist():
    """All configured checker scripts should be real files."""
    for check_id, path in CHECKER_SCRIPTS.items():
        assert path.exists(), f"Checker script missing: {path}"
