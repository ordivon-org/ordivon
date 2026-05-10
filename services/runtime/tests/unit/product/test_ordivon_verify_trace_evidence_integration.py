"""Integration tests for Trace Evidence in discovery/report output."""

from __future__ import annotations

import tempfile
import json
from pathlib import Path

from ordivon_verify.discovery import (
    discover_external_evidence,
    render_discovery_summary,
    render_discovery_markdown,
)


def _setup_trace_repo() -> tuple[Path, tempfile.TemporaryDirectory]:
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    (root / "README.md").write_text("# Test Repo")
    (root / "trace.json").write_text(
        json.dumps({
            "run_id": "run-001",
            "actor": "agent-a",
            "started_at": "2026-05-08T10:00:00Z",
            "completed_at": "2026-05-08T10:05:00Z",
            "status": "completed",
            "summary": "This trace proves the truth of all operations.",
            "tool_calls": [{"name": "deploy", "status": "success", "note": "safe action, production ready"}],
        })
    )
    return root, td


def test_discovery_includes_trace_evidence_inventory():
    root, _td = _setup_trace_repo()
    report = discover_external_evidence(root, include_standard_pack=False)
    assert "trace_evidence" in report["inventory"]


def test_summary_report_includes_trace_evidence_scan():
    root, _td = _setup_trace_repo()
    report = discover_external_evidence(root, include_standard_pack=False)
    summary = render_discovery_summary(report)
    assert "Trace evidence scan:" in summary


def test_markdown_report_includes_trace_evidence_section():
    root, _td = _setup_trace_repo()
    report = discover_external_evidence(root, include_standard_pack=False)
    md = render_discovery_markdown(report)
    assert "Trace / Harness Evidence Findings" in md


def test_blocked_trace_finding_generates_next_action():
    root, _td = _setup_trace_repo()
    report = discover_external_evidence(root, include_standard_pack=False)
    next_actions = report.get("next_actions", [])
    trace_actions = [a for a in next_actions if "Trace evidence" in a]
    assert len(trace_actions) >= 1


def test_no_trace_repo_reports_zero_surfaces():
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    (root / "README.md").write_text("# Empty Repo")
    report = discover_external_evidence(root, include_standard_pack=False)
    te = report["inventory"]["trace_evidence"]
    assert te["discovered_count"] == 0
