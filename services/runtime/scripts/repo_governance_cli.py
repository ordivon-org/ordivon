#!/usr/bin/env python3
"""Repo Governance CLI — classifies AI coding intents before execution.

Produces a JSON governance decision (execute / escalate / reject + reasons).
Does NOT execute code, modify files, call shell/MCP/IDE, or create
ExecutionRequest/ExecutionReceipt.

This is an Adapter-layer component: its output is evidence, not truth.

Usage:
  uv run python scripts/repo_governance_cli.py \
    --task-description "Fix unit test naming" \
    --file-path tests/unit/test_example.py \
    --estimated-impact low \
    --reasoning "Small test-only cleanup" \
    --test-plan "uv run pytest tests/unit/test_example.py" \
    --json

Exit codes:
  0 — execute
  2 — escalate
  3 — reject
  1 — internal error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Project root path resolution — works when run from project root
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-governance-cli",
        description="Classify an AI coding intent before execution.",
    )
    parser.add_argument(
        "--task-description",
        required=True,
        help="What the AI coding agent intends to do.",
    )
    parser.add_argument(
        "--file-path",
        action="append",
        dest="file_paths",
        default=[],
        help="File path(s) the agent intends to modify. Repeat for multiple files.",
    )
    parser.add_argument(
        "--estimated-impact",
        choices=["low", "medium", "high"],
        required=True,
        help="Estimated risk/impact of the change.",
    )
    parser.add_argument(
        "--reasoning",
        required=True,
        help="Why the agent thinks this change is necessary.",
    )
    parser.add_argument(
        "--test-plan",
        default=None,
        help="How the change will be tested (optional but recommended).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=True,
        help="Output JSON (default: true).",
    )
    return parser


def validate_args(args: argparse.Namespace) -> list[str]:
    """Pre-validate CLI arguments before constructing payload. Returns error list."""
    errors: list[str] = []
    if not args.task_description.strip():
        errors.append("task_description must not be empty.")
    if not args.file_paths:
        errors.append("At least one --file-path is required.")
    if not args.reasoning.strip():
        errors.append("reasoning must not be empty.")
    return errors


def classify_repo_intent(
    *,
    task_description: str,
    file_paths: list[str],
    estimated_impact: str,
    reasoning: str,
    test_plan: str | None = None,
    source: str = "repo_governance_cli",
) -> dict:
    """Classify a repo governance intent. Shared between CLI and GitHub adapter.

    Returns a result dict with decision, reasons, pack, underlying_policy,
    source, and side_effects.  Does NOT write files, call shell/MCP/IDE, or
    create ExecutionRequest/ExecutionReceipt.
    """
    from packs.coding.models import CodingDecisionPayload
    from domains.decision_intake.models import DecisionIntake
    from governance.risk_engine.engine import RiskEngine
    from packs.coding.policy import CodingDisciplinePolicy

    payload = CodingDecisionPayload(
        task_description=task_description.strip(),
        file_paths=tuple(file_paths),
        estimated_impact=estimated_impact,
        reasoning=reasoning.strip(),
        test_plan=test_plan.strip() if test_plan else None,
    )

    intake = DecisionIntake(
        pack_id="coding",
        intake_type="code_change",
        payload={
            "task_description": payload.task_description,
            "file_paths": list(payload.file_paths),
            "estimated_impact": payload.estimated_impact,
            "reasoning": payload.reasoning,
            "test_plan": payload.test_plan,
        },
        status="validated",
    )

    engine = RiskEngine()
    policy = CodingDisciplinePolicy()
    decision = engine.validate_intake(intake, pack_policy=policy)

    return {
        "decision": decision.decision,
        "reasons": decision.reasons,
        "pack": "repo_governance",
        "underlying_policy": "coding",
        "source": source,
        "side_effects": {
            "file_writes": False,
            "shell": False,
            "mcp": False,
            "ide": False,
            "execution_receipt": False,
            "execution_request": False,
        },
    }


def make_intake(args: argparse.Namespace):
    """Construct a DecisionIntake from CLI arguments."""
    from packs.coding.models import CodingDecisionPayload
    from domains.decision_intake.models import DecisionIntake

    payload = CodingDecisionPayload(
        task_description=args.task_description.strip(),
        file_paths=tuple(args.file_paths),
        estimated_impact=args.estimated_impact,
        reasoning=args.reasoning.strip(),
        test_plan=args.test_plan.strip() if args.test_plan else None,
    )

    intake = DecisionIntake(
        pack_id="coding",
        intake_type="code_change",
        payload={
            "task_description": payload.task_description,
            "file_paths": list(payload.file_paths),
            "estimated_impact": payload.estimated_impact,
            "reasoning": payload.reasoning,
            "test_plan": payload.test_plan,
        },
        status="validated",
    )
    return intake


def classify(args: argparse.Namespace) -> dict:
    """Run governance classification from CLI args. Delegates to classify_repo_intent."""
    return classify_repo_intent(
        task_description=args.task_description,
        file_paths=args.file_paths,
        estimated_impact=args.estimated_impact,
        reasoning=args.reasoning,
        test_plan=args.test_plan,
        source="repo_governance_cli",
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Pre-validate
    errors = validate_args(args)
    if errors:
        result = {
            "decision": "reject",
            "reasons": errors,
            "pack": "repo_governance",
            "underlying_policy": "coding",
            "source": "repo_governance_cli",
            "side_effects": {
                "file_writes": False,
                "shell": False,
                "mcp": False,
                "ide": False,
                "execution_receipt": False,
                "execution_request": False,
            },
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 3  # reject

    try:
        result = classify(args)
    except Exception as exc:
        error_result = {
            "decision": "reject",
            "reasons": [f"Internal error: {exc}"],
            "pack": "repo_governance",
            "underlying_policy": "coding",
            "source": "repo_governance_cli",
            "side_effects": {
                "file_writes": False,
                "shell": False,
                "mcp": False,
                "ide": False,
                "execution_receipt": False,
                "execution_request": False,
            },
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))

    decision = result["decision"]
    if decision == "execute":
        return 0
    elif decision == "escalate":
        return 2
    elif decision == "reject":
        return 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
