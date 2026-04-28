#!/usr/bin/env python3
"""GitHub Actions Repo Governance Adapter — classifies PR intents before merge.

This is a read-only Adapter-layer component. It reads PR metadata (title, body,
labels, changed files), calls the shared classify_repo_intent() function from
the Repo Governance CLI, and outputs a JSON governance decision.

Does NOT: write files, comment on PRs, push commits, create
ExecutionRequest/ExecutionReceipt, call shell/MCP/IDE.

Two modes:
  A. CLI/local test mode:
     --task-description, --file-path, --estimated-impact, --reasoning, --test-plan
  B. GitHub event mode:
     --github-event-path "$GITHUB_EVENT_PATH"
     --changed-files-file changed_files.txt

Usage (GitHub event mode):
  uv run python scripts/repo_governance_github_adapter.py \
    --github-event-path "$GITHUB_EVENT_PATH" \
    --changed-files-file changed_files.txt \
    --json

Usage (CLI/local mode — for testing):
  uv run python scripts/repo_governance_github_adapter.py \
    --task-description "Fix unit test naming" \
    --file-path tests/unit/test_example.py \
    --estimated-impact low \
    --reasoning "Small test-only cleanup" \
    --test-plan "uv run pytest" \
    --json

Exit codes:
  0 — execute
  2 — escalate (blocks CI → forces human review)
  3 — reject
  1 — internal error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Project root path resolution
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _parse_github_event(event_path: str) -> dict:
    """Parse a GitHub webhook event JSON file."""
    with open(event_path, encoding="utf-8") as f:
        return json.load(f)


def _read_changed_files(file_path: str) -> list[str]:
    """Read changed files list (one per line)."""
    with open(file_path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


DEPENDABOT_SYNTHETIC_TEST_PLAN = (
    "Dependabot update. Validation is full CI, security checks, "
    "Repo Governance evidence artifact, and human review before merge."
)

# Files that Dependabot is expected to modify. These are excluded from
# RiskEngine forbidden-file checks for Dependabot PRs only, because the
# CodingDisciplinePolicy treats them as AI-agent-forbidden but Dependabot
# legitimately modifies them as part of dependency updates.
DEPENDABOT_EXPECTED_FILES = frozenset(
    {
        "pyproject.toml",
        "uv.lock",
        "package.json",
        "pnpm-lock.yaml",
        # Also common in Dependabot grouped updates
        "apps/web/package.json",
        ".github/dependabot.yml",
    }
)


def _is_dependabot_pr(event: dict, pr: dict, pr_title: str, pr_labels: list[str]) -> bool:
    """Detect whether a PR is from Dependabot.

    Checks multiple signals in priority order:
      1. PR user login is 'dependabot[bot]' or 'dependabot'
      2. Event sender login is 'dependabot[bot]'
      3. PR title matches Dependabot pattern (starts with 'deps:' or 'bump ')
      4. PR has 'dependencies' label (weakest — only as confirmation)

    Returns True if the PR is from Dependabot.
    """
    # Signal 1: PR user login
    pr_user = (pr.get("user") or {}).get("login", "")
    if pr_user and ("dependabot" in pr_user.lower()):
        return True

    # Signal 2: Event sender login
    sender = (event.get("sender") or {}).get("login", "")
    if sender and ("dependabot" in sender.lower()):
        return True

    # Signal 3: Title pattern (Dependabot prefixes: 'deps:' or 'bump ')
    if pr_title:
        title_lower = pr_title.lower().strip()
        if title_lower.startswith("deps:") or title_lower.startswith("bump "):
            return True

    return False


def _extract_test_plan(pr_body: str) -> str | None:
    """Attempt to extract a test plan from PR body.

    Looks for sections like:
      ## Test Plan
      ## Testing
      ### How to test
    """
    if not pr_body:
        return None

    # Try to find a test plan section
    patterns = [
        r"(?i)#{1,4}\s*(?:test plan|testing|how to test|verification)\s*\n+(.*?)(?=\n#{1,4}\s|\Z)",
        r"(?i)test plan\s*[:：]\s*(.+?)(?:\n|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, pr_body, re.DOTALL)
        if match:
            text = match.group(1).strip()
            # Take first meaningful line
            lines = [l.strip() for l in text.split("\n") if l.strip() and not l.strip().startswith("#")]
            if lines:
                return lines[0][:200]  # Cap length

    return None


def _infer_impact(changed_files: list[str], labels: list[str]) -> str:
    """Infer estimated_impact from PR labels and changed file count.

    Priority: labels > file count heuristics.
    """
    # Check labels for impact hints
    for label in labels:
        label_lower = label.lower()
        if "impact/high" in label_lower or label_lower == "high":
            return "high"
        if "impact/medium" in label_lower or label_lower == "medium":
            return "medium"
        if "impact/low" in label_lower or label_lower == "low":
            return "low"

    # Fallback: heuristics based on changed file count
    if len(changed_files) > 10:
        return "high"
    if len(changed_files) > 3:
        return "medium"
    return "low"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-governance-github-adapter",
        description="Classify a GitHub PR intent before merge.",
    )

    # CLI/local mode args
    parser.add_argument("--task-description", default=None, help="PR title / task description.")
    parser.add_argument(
        "--file-path",
        action="append",
        dest="file_paths",
        default=[],
        help="Changed file path(s). Repeat for multiple.",
    )
    parser.add_argument(
        "--estimated-impact",
        choices=["low", "medium", "high"],
        default=None,
        help="Estimated risk/impact.",
    )
    parser.add_argument("--reasoning", default=None, help="PR body / reasoning.")
    parser.add_argument("--test-plan", default=None, help="Test plan (optional).")

    # GitHub event mode args
    parser.add_argument(
        "--github-event-path",
        default=None,
        help="Path to GitHub event JSON file ($GITHUB_EVENT_PATH).",
    )
    parser.add_argument(
        "--changed-files-file",
        default=None,
        help="Path to changed files list (one per line).",
    )
    parser.add_argument("--json", action="store_true", default=True, help="Output JSON.")
    return parser


def classify_from_github_event(event_path: str, changed_files_path: str) -> dict:
    """Parse GitHub event + changed files, then classify."""
    event = _parse_github_event(event_path)
    changed_files = _read_changed_files(changed_files_path)

    # Extract PR metadata
    pr = event.get("pull_request", {})
    pr_title = pr.get("title", event.get("head_commit", {}).get("message", "No PR title"))
    pr_body = pr.get("body", "") or ""
    pr_labels = [label.get("name", "") for label in pr.get("labels", [])]

    # Detect Dependabot PR
    is_dependabot = _is_dependabot_pr(event, pr, pr_title, pr_labels)

    # Infer classification inputs
    task_description = pr_title
    reasoning = pr_body[:500] if pr_body else "No PR body provided."

    # For Dependabot PRs without a human test plan, use synthetic test plan
    test_plan = _extract_test_plan(pr_body)
    if test_plan is None and is_dependabot:
        test_plan = DEPENDABOT_SYNTHETIC_TEST_PLAN

    estimated_impact = _infer_impact(changed_files, pr_labels)

    # For Dependabot PRs: filter out expected dependency files from the
    # RiskEngine check. These files (pyproject.toml, uv.lock, package.json,
    # pnpm-lock.yaml) are in CodingDisciplinePolicy's forbidden list to prevent
    # AI agents from modifying them, but Dependabot legitimately updates them.
    # Non-dependency files (e.g., .env, source code) still pass through the
    # full forbidden-file check.
    governance_files = list(changed_files)
    if is_dependabot:
        governance_files = [f for f in changed_files if f not in DEPENDABOT_EXPECTED_FILES]
        # If ALL files are Dependabot-expected dependency files,
        # use a synthetic "governance pass" path to avoid empty file list
        if not governance_files:
            result = {
                "decision": "execute",
                "reasons": ["Dependabot dependency update — all changed files are expected lockfile/manifest files."],
                "pack": "repo_governance",
                "underlying_policy": "coding",
                "source": "github_actions_adapter",
                "side_effects": {
                    "file_writes": False,
                    "shell": False,
                    "mcp": False,
                    "ide": False,
                    "execution_receipt": False,
                    "execution_request": False,
                    "pr_comments": False,
                    "push": False,
                },
            }
            result["changed_files_count"] = len(changed_files)
            result["dependabot_pr"] = True
            result["dependabot_test_plan"] = "synthetic"
            return result

    from scripts.repo_governance_cli import classify_repo_intent

    result = classify_repo_intent(
        task_description=task_description,
        file_paths=governance_files if governance_files else ["(no non-dependency files changed)"],
        estimated_impact=estimated_impact,
        reasoning=reasoning,
        test_plan=test_plan,
        source="github_actions_adapter",
    )

    # Add adapter-specific metadata
    result["changed_files_count"] = len(changed_files)
    result["side_effects"].update(
        {
            "pr_comments": False,
            "push": False,
        }
    )

    # Tag Dependabot PRs in the result for downstream consumption
    if is_dependabot:
        result["dependabot_pr"] = True
        if test_plan == DEPENDABOT_SYNTHETIC_TEST_PLAN:
            result["dependabot_test_plan"] = "synthetic"

    return result


def classify_from_cli(args: argparse.Namespace) -> dict:
    """Classify from CLI arguments (local test mode)."""
    from scripts.repo_governance_cli import classify_repo_intent

    # Pre-validate
    errors: list[str] = []
    if not (args.task_description or "").strip():
        errors.append("task_description must not be empty.")
    if not args.file_paths:
        errors.append("At least one --file-path is required.")
    if not (args.reasoning or "").strip():
        errors.append("reasoning must not be empty.")
    if errors:
        return {
            "decision": "reject",
            "reasons": errors,
            "pack": "repo_governance",
            "underlying_policy": "coding",
            "source": "github_actions_adapter",
            "side_effects": {
                "file_writes": False,
                "shell": False,
                "mcp": False,
                "ide": False,
                "execution_receipt": False,
                "execution_request": False,
                "pr_comments": False,
                "push": False,
            },
        }

    result = classify_repo_intent(
        task_description=args.task_description,
        file_paths=args.file_paths,
        estimated_impact=args.estimated_impact,
        reasoning=args.reasoning,
        test_plan=args.test_plan,
        source="github_actions_adapter",
    )
    result["changed_files_count"] = len(args.file_paths)
    result["side_effects"].update(
        {
            "pr_comments": False,
            "push": False,
        }
    )
    return result


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Determine mode
    if args.github_event_path and args.changed_files_file:
        # GitHub event mode
        try:
            result = classify_from_github_event(args.github_event_path, args.changed_files_file)
        except Exception as exc:
            result = {
                "decision": "reject",
                "reasons": [f"Adapter error: {exc}"],
                "pack": "repo_governance",
                "underlying_policy": "coding",
                "source": "github_actions_adapter",
                "side_effects": {
                    "file_writes": False,
                    "shell": False,
                    "mcp": False,
                    "ide": False,
                    "execution_receipt": False,
                    "execution_request": False,
                    "pr_comments": False,
                    "push": False,
                },
            }
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 1
    else:
        # CLI/local mode
        result = classify_from_cli(args)

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
