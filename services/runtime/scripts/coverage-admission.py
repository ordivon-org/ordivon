#!/usr/bin/env python3
"""Coverage Admission Gate — evaluate coverage mutations before merge (PM-9).

Pattern: OPA admission control. Checks git diff against coverage policy.
Admission before mutation. ALLOW/BLOCK/SHADOW/A4_REQUIRED/REVIEW_REQUIRED.

Usage:
    python scripts/coverage-admission.py
    python scripts/coverage-admission.py --base HEAD~1 --head HEAD --json
"""

from __future__ import annotations

import fnmatch, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs/governance/generated"
SCHEMA_DIR = ROOT / "docs/governance/schemas"
POLICY = SCHEMA_DIR / "coverage-admission-policy.json"
COVERAGE = OUTPUT_DIR / "coverage-boundary.json"


def git_diff_files(base: str = "HEAD~1", head: str = "HEAD") -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", base, head],
        capture_output=True, text=True, cwd=str(ROOT), timeout=15
    )
    return [l for l in result.stdout.strip().split("\n") if l]


def load_policy() -> dict:
    return json.loads(POLICY.read_text())


def load_coverage() -> dict:
    return json.loads(COVERAGE.read_text()) if COVERAGE.exists() else {"files": []}


def is_protected(filepath: str) -> bool:
    protected = [
        "docs/governance/**", "docs/ai/**", "docs/architecture/**", "docs/product/**",
        "checkers/**", "scripts/check_*", "scripts/generate-*", "scripts/update-*",
        "scripts/verify-*", "scripts/reconcile*", "scripts/hash_ledger*", "scripts/review_lessons*",
        "scripts/detect_*", "scripts/triage*", "scripts/explain*", "scripts/collect-*",
        "scripts/verify-*", ".github/workflows/**"
    ]
    return any(fnmatch.fnmatch(filepath, p) for p in protected)


def evaluate(filepath: str, is_new: bool, coverage: dict) -> list[dict]:
    """Evaluate a changed file against admission policy."""
    findings = []
    cov_entry = next((f for f in coverage.get("files", []) if f["path"] == filepath), None)
    status = cov_entry.get("coverage_status", "unknown") if cov_entry else "unknown"
    meta = cov_entry.get("metadata", {}) if cov_entry else {}

    # CA-1: new protected unknown file
    if is_new and is_protected(filepath) and status not in ("governed", "generated", "excluded", "debt_parked", "fixture", "legacy"):
        findings.append({"code": "CA-1", "decision": "BLOCK", "path": filepath, "message": "New protected file without classification"})

    # CA-2: generated without source_refs
    if status == "generated" and not meta.get("source_refs"):
        findings.append({"code": "CA-2", "decision": "BLOCK", "path": filepath, "message": "Generated file without source_refs"})

    # CA-4: exclusion without required fields
    if status == "excluded" and (not meta.get("reason") or len(str(meta.get("reason", ""))) < 3):
        findings.append({"code": "CA-4", "decision": "BLOCK", "path": filepath, "message": "Exclusion missing reason"})

    # CA-5: debt_parked without debt_id
    if status == "debt_parked" and not meta.get("debt_id"):
        findings.append({"code": "CA-5", "decision": "BLOCK", "path": filepath, "message": "Debt-parked without debt_id"})

    # Default: allow
    if not findings:
        findings.append({"code": "ALLOW", "decision": "ALLOW", "path": filepath, "message": "Coverage admission passed"})

    return findings


def main() -> int:
    args = sys.argv[1:]
    base = "HEAD~1"
    head = "HEAD"
    as_json = "--json" in args

    files = git_diff_files(base, head)
    policy = load_policy()
    coverage = load_coverage()
    enforcement = policy.get("enforcement_mode", "SHADOW")

    all_findings = []
    for fp in files:
        is_new = not (ROOT / fp).exists()  # actually: check if it's in the diff as added
        # More accurate: use git diff --diff-filter
        result = subprocess.run(
            ["git", "diff", "--diff-filter=A", "--name-only", base, head],
            capture_output=True, text=True, cwd=str(ROOT), timeout=10
        )
        new_files = set(result.stdout.strip().split("\n"))
        is_new = fp in new_files
        all_findings.extend(evaluate(fp, is_new, coverage))

    blocked = [f for f in all_findings if f["decision"] == "BLOCK"]
    shadow = [f for f in all_findings if f["decision"] == "SHADOW"]
    allowed = [f for f in all_findings if f["decision"] == "ALLOW"]

    report = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authority": "generated_view",
        "base": base, "head": head,
        "enforcement_mode": enforcement,
        "files_evaluated": len(files),
        "summary": {"BLOCK": len(blocked), "SHADOW": len(shadow), "ALLOW": len(allowed)},
        "blocked": [{"path": f["path"], "code": f["code"], "message": f["message"]} for f in blocked],
        "not_claimed": ["full closure", "external governance", "admission pass = approval"],
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "coverage-admission-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    if as_json:
        print(json.dumps(report, indent=2))
        return 1 if blocked and enforcement != "SHADOW" else 0

    print(f"Coverage Admission ({enforcement}): {len(files)} files evaluated")
    print(f"  ALLOW: {len(allowed)} · BLOCK: {len(blocked)} · SHADOW: {len(shadow)}")
    if blocked:
        print(f"\nBLOCKED:")
        for f in blocked:
            print(f"  [{f['code']}] {f['path']}: {f['message']}")
    return 1 if blocked and enforcement != "SHADOW" else 0


if __name__ == "__main__":
    sys.exit(main())
