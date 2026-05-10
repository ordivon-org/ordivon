"""Integration tests for Memory Hygiene in discovery/report output."""

from __future__ import annotations

import tempfile
from pathlib import Path

from ordivon_verify.discovery import (
    discover_external_evidence,
    render_discovery_summary,
    render_discovery_markdown,
)


def _setup_memory_repo() -> tuple[Path, tempfile.TemporaryDirectory]:
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    (root / "README.md").write_text("# Test Repo")

    # A memory ledger with BLOCKED issues
    (root / "memory-source-ledger.jsonl").write_text(
        '{"id":"mem-001","notes":"No source, no freshness.","current_truth_allowed":true}\n'
    )
    (root / "lesson-ledger.jsonl").write_text(
        '{"id":"lesson-001","source_ref":"receipts/old.md","observed_at":"2026-05-08","freshness":"fresh","current_truth_allowed":true,"notes":"This lesson is required policy."}\n'
    )
    return root, td


def test_discovery_includes_memory_hygiene_inventory():
    root, _td = _setup_memory_repo()
    report = discover_external_evidence(root, include_standard_pack=False)
    inv = report["inventory"]
    assert "memory_hygiene" in inv
    mh = inv["memory_hygiene"]
    assert mh["discovered_count"] >= 1
    assert "blocked_count" in mh
    assert "degraded_count" in mh


def test_summary_report_includes_memory_hygiene_scan():
    root, _td = _setup_memory_repo()
    report = discover_external_evidence(root, include_standard_pack=False)
    summary = render_discovery_summary(report)
    assert "Memory hygiene scan:" in summary


def test_markdown_report_includes_memory_hygiene_section():
    root, _td = _setup_memory_repo()
    report = discover_external_evidence(root, include_standard_pack=False)
    md = render_discovery_markdown(report)
    assert "Memory / Content Hygiene Findings" in md


def test_blocked_memory_finding_generates_next_action():
    root, _td = _setup_memory_repo()
    report = discover_external_evidence(root, include_standard_pack=False)
    next_actions = report.get("next_actions", [])
    mem_actions = [a for a in next_actions if "Memory hygiene" in a]
    assert len(mem_actions) >= 1


def test_no_memory_repo_reports_zero_surfaces():
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    (root / "README.md").write_text("# Empty Repo")
    report = discover_external_evidence(root, include_standard_pack=False)
    mh = report["inventory"]["memory_hygiene"]
    assert mh["discovered_count"] == 0
