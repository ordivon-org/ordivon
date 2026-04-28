#!/usr/bin/env python3
"""Repo Governance Evidence Report Renderer — generates human + machine readable reports.

Reads the JSON output from repo_governance_cli.py or repo_governance_github_adapter.py
and produces two files:
  - repo-governance-report.json  (machine-readable evidence)
  - repo-governance-report.md    (human-readable evidence)

Both are evidence artifacts. They do NOT execute code, modify repo state,
create ExecutionRequest/ExecutionReceipt, or call shell/MCP/IDE.

Usage:
  uv run python scripts/render_repo_governance_report.py \
    --input repo_gov_result.json \
    --output-dir /tmp/repo-gov-report
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Project root path resolution
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ARTIFACT_VERSION = "v1"


def build_json_report(gov_result: dict) -> dict:
    """Build a JSON evidence report from the governance result."""
    decision = gov_result.get("decision", "unknown")

    if decision == "execute":
        ci_behavior = "pass"
    elif decision == "escalate":
        ci_behavior = "warning"
    elif decision == "reject":
        ci_behavior = "fail"
    else:
        ci_behavior = "fail"

    return {
        "artifact_version": ARTIFACT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "reasons": gov_result.get("reasons", []),
        "pack": gov_result.get("pack", "repo_governance"),
        "underlying_policy": gov_result.get("underlying_policy", "coding"),
        "source": gov_result.get("source", "unknown"),
        "changed_files_count": gov_result.get("changed_files_count", 0),
        "ci_behavior": ci_behavior,
        "side_effects": gov_result.get("side_effects", {}),
        "evidence_note": (
            "This report is evidence only. It does not execute code, "
            "modify repo state, create ExecutionRequest/ExecutionReceipt, "
            "or call shell/MCP/IDE."
        ),
    }


def build_markdown_report(json_report: dict) -> str:
    """Build a Markdown evidence report."""
    decision = json_report["decision"]
    emoji = {"execute": "✅", "escalate": "⚠️", "reject": "❌"}.get(decision, "❓")

    reasons_md = "\n".join(f"- {r}" for r in json_report.get("reasons", []))
    if not reasons_md:
        reasons_md = "_No reasons provided._"

    se = json_report.get("side_effects", {})

    return f"""# Repo Governance Evidence Report

**Decision:** {emoji} {decision.upper()}

**CI Behavior:** {json_report["ci_behavior"]}

**Source:** {json_report["source"]}

**Changed Files:** {json_report.get("changed_files_count", 0)}

**Artifact Version:** {json_report["artifact_version"]}

**Generated:** {json_report["generated_at"]}

---

## Reasons

{reasons_md}

---

## Side-Effect Guarantees

| Side Effect | Guarantee |
|-------------|-----------|
| File writes | {se.get("file_writes", "?")} |
| Shell | {se.get("shell", "?")} |
| MCP | {se.get("mcp", "?")} |
| IDE | {se.get("ide", "?")} |
| Execution Request | {se.get("execution_request", "?")} |
| Execution Receipt | {se.get("execution_receipt", "?")} |
| PR Comments | {se.get("pr_comments", "N/A")} |
| Push | {se.get("push", "N/A")} |

---

> ⚠️ This report is evidence only. It does not execute code or modify repo state.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render repo governance evidence report.")
    parser.add_argument("--input", required=True, help="Path to governance JSON result file.")
    parser.add_argument("--output-dir", required=True, help="Directory to write reports to.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read governance result
    gov_result = json.loads(input_path.read_text(encoding="utf-8"))

    # Build reports
    json_report = build_json_report(gov_result)
    md_report = build_markdown_report(json_report)

    # Write
    json_path = output_dir / "repo-governance-report.json"
    md_path = output_dir / "repo-governance-report.md"

    json_path.write_text(json.dumps(json_report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(md_report, encoding="utf-8")

    print(f"Reports written to {output_dir}:")
    print(f"  {json_path}")
    print(f"  {md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
