"""Integration tests for Skill Boundary in discovery/report output."""

from __future__ import annotations

import tempfile
from pathlib import Path

from ordivon_verify.discovery import (
    discover_external_evidence,
    render_discovery_summary,
    render_discovery_markdown,
)


def _setup_skill_repo() -> tuple[Path, tempfile.TemporaryDirectory]:
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    (root / "README.md").write_text("# Test Repo")
    skills_dir = root / "skills" / "test-skill"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text(
        "---\nname: test-skill\ndescription: A test skill with credential request.\nallowed-tools: Bash, Read\n---\n\n"
        "# Test Skill\n\n"
        "Set your API key before using. The token is needed.\n"
    )
    return root, td


def test_summary_report_includes_skill_boundary_scan():
    root, _td = _setup_skill_repo()
    report = discover_external_evidence(root, include_standard_pack=False)
    summary = render_discovery_summary(report)
    assert "Skill boundary scan:" in summary


def test_markdown_report_includes_skill_boundary_findings():
    root, _td = _setup_skill_repo()
    report = discover_external_evidence(root, include_standard_pack=False)
    md = render_discovery_markdown(report)
    assert "Skill / Tool Boundary Findings" in md


def test_json_inventory_contains_skill_boundary():
    root, _td = _setup_skill_repo()
    report = discover_external_evidence(root, include_standard_pack=False)
    inv = report["inventory"]
    assert "skill_boundary" in inv
    sb = inv["skill_boundary"]
    assert sb["discovered_count"] >= 1
    assert "blocked_count" in sb
    assert "degraded_count" in sb


def test_blocked_skill_finding_generates_next_action():
    root, _td = _setup_skill_repo()
    report = discover_external_evidence(root, include_standard_pack=False)
    next_actions = report.get("next_actions", [])
    skill_actions = [a for a in next_actions if "Skill boundary" in a]
    assert len(skill_actions) >= 1


def test_no_skill_repo_reports_zero_skill_surfaces():
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    (root / "README.md").write_text("# Empty Repo")
    report = discover_external_evidence(root, include_standard_pack=False)
    sb = report["inventory"]["skill_boundary"]
    assert sb["discovered_count"] == 0


def test_skill_boundary_blocked_visible_in_markdown():
    root, _td = _setup_skill_repo()
    report = discover_external_evidence(root, include_standard_pack=False)
    md = render_discovery_markdown(report)
    assert "Blocked" in md or "BLOCKED" in md
