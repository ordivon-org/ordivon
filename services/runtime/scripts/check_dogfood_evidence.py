#!/usr/bin/env python3
"""Dogfood Evidence Checker — validates dogfood scripts and evidence reports.

Checks:
  1. Dogfood scripts are committed and syntactically valid.
  2. Run count consistency (declared vs actual runs in script).
  3. Governance verdict vocabulary (execute/reject/escalate only, no win/loss).
  4. Error handling patterns exist in dogfood scripts.
  5. Evidence report integrity (pass/fail count matches actual lines).
  6. No manual ALTER TABLE or DuckDB writes in dogfood code.

This is a CandidateRule (advisory) — it does NOT block CI by default.
Exit 0 = clean; Exit 1 = violations found.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ── Dogfood script paths ────────────────────────────────────────
DOGFOOD_SCRIPTS = [
    "scripts/h9_dogfood_runs.py",
    "scripts/h9c_verification.py",
    "scripts/h9f_31_dogfood.py",
]

# ── Evidence report paths (optional) ────────────────────────────
EVIDENCE_REPORTS = [
    "docs/runtime/h9-evidence-report-v2.txt",
    "docs/runtime/h9-evidence-report.md",
]

# ── Valid governance verdict vocabulary ─────────────────────────
VALID_VERDICTS = {"execute", "reject", "escalate"}

# ── Forbidden verdicts (that would indicate test pollution) ─────
FORBIDDEN_VERDICTS = {"win", "loss", "profit", "draw", "success", "failure"}


def find_all_violations() -> list[str]:
    violations: list[str] = []

    # Check 1: Scripts exist and are syntactically valid
    violations.extend(check_scripts_exist())

    # Check 2: Run count consistency
    violations.extend(check_run_counts())

    # Check 3: Verdict vocabulary
    violations.extend(check_verdict_vocabulary())

    # Check 4: Error handling
    violations.extend(check_error_handling())

    # Check 5: Evidence report integrity (if reports exist)
    violations.extend(check_evidence_reports())

    # Check 6: No DB contamination in dogfood code
    violations.extend(check_no_db_contamination())

    return violations


# ═══════════════════════════════════════════════════════════════════
# Check 1: Scripts exist
# ═══════════════════════════════════════════════════════════════════


def check_scripts_exist() -> list[str]:
    violations: list[str] = []
    for rel_path in DOGFOOD_SCRIPTS:
        full = ROOT / rel_path
        if not full.exists():
            violations.append(f"{rel_path}: not found — is the dogfood script committed?")
            continue
        try:
            with open(full) as f:
                source = f.read()
            ast.parse(source)
        except SyntaxError as e:
            violations.append(f"{rel_path}: syntax error — {e}")
    return violations


# ═══════════════════════════════════════════════════════════════════
# Check 2: Run count consistency
# ═══════════════════════════════════════════════════════════════════


def check_run_counts() -> list[str]:
    violations: list[str] = []

    for rel_path in DOGFOOD_SCRIPTS:
        full = ROOT / rel_path
        if not full.exists():
            continue
        text = full.read_text(encoding="utf-8")

        # For h9f_31_dogfood.py: check declared run count
        if "h9f_31" in rel_path:
            expected_match = re.search(r"(\d+)-Run Dogfood", text)
            if expected_match:
                expected = int(expected_match.group(1))
                # Count primary run record() calls (R1-R31 intake, excluding complete_review sub-records)
                primary_records = len([
                    m
                    for m in re.finditer(r"""record\s*\(\s*["']R\d+\b""", text)
                    if "complete_review" not in text[m.start() : m.start() + 40]
                ])
                if primary_records > 0 and primary_records != expected:
                    violations.append(
                        f"{rel_path}: declared {expected} runs but found {primary_records} primary record() calls"
                    )

        # For h9_dogfood_runs.py: check runs.append() calls
        if "h9_dogfood_runs" in rel_path and "h9f" not in rel_path:
            run_appends = len(re.findall(r"runs\.append\(", text))
            run_tags = len(re.findall(r'"tag"\s*:', text))
            if run_tags > 0 and run_appends > 0 and run_tags != run_appends:
                violations.append(f"{rel_path}: {run_tags} run tags but {run_appends} runs.append() — mismatch")

        # For h9c_verification.py: check check() call count
        if "h9c_verification" in rel_path:
            # count actual check() invocations (not the def line)
            check_calls = len(re.findall(r"^\s+check\s*\(", text, re.MULTILINE))
            if check_calls > 0:
                # verify the pass/fail increments exist inside the check function
                has_pass_inc = bool(re.search(r"def\s+check\b.*:.*pass_count\s*\+=\s*1", text, re.DOTALL))
                has_fail_inc = bool(re.search(r"def\s+check\b.*:.*fail_count\s*\+=\s*1", text, re.DOTALL))
                if not has_pass_inc:
                    violations.append(f"{rel_path}: {check_calls} check() calls but no pass_count increment in check()")
                if not has_fail_inc:
                    violations.append(f"{rel_path}: {check_calls} check() calls but no fail_count increment in check()")

    return violations


# ═══════════════════════════════════════════════════════════════════
# Check 3: Verdict vocabulary
# ═══════════════════════════════════════════════════════════════════


def check_verdict_vocabulary() -> list[str]:
    violations: list[str] = []

    for rel_path in DOGFOOD_SCRIPTS:
        full = ROOT / rel_path
        if not full.exists():
            continue
        text = full.read_text(encoding="utf-8")

        # Check for forbidden verdict strings in governance-related contexts
        for forbidden in FORBIDDEN_VERDICTS:
            # Search for the word used as a verdict value (not in comments/docstrings)
            pattern = rf"""["']{forbidden}["']"""
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Filter: only flag if it looks like a governance verdict assignment
                for m in matches:
                    # Check context — is it near "verdict", "decision", "governance"?
                    idx = text.find(m)
                    context = text[max(0, idx - 80) : idx + 80]
                    if any(kw in context.lower() for kw in ("verdict", "governance", "decision", "outcome_type")):
                        violations.append(f"{rel_path}: forbidden verdict '{m}' near governance context")
                        break  # one per file

        # Check that all expected verdicts are from the valid set
        # Look for governance_decision assignments
        gov_decisions = re.findall(r"""governance_decision["']\s*[=:]\s*["'](\w+)["']""", text)
        for dec in gov_decisions:
            if dec not in VALID_VERDICTS:
                violations.append(
                    f"{rel_path}: unexpected governance_decision '{dec}' "
                    f"(expected: {', '.join(sorted(VALID_VERDICTS))})"
                )

        # Also check verdict strings in outcome/complete_review calls
        verdict_vals = re.findall(r"""["']verdict["']\s*:\s*["'](\w+)["']""", text)
        for v in verdict_vals:
            if v in FORBIDDEN_VERDICTS:
                violations.append(f"{rel_path}: forbidden outcome verdict '{v}'")

    return violations


# ═══════════════════════════════════════════════════════════════════
# Check 4: Error handling
# ═══════════════════════════════════════════════════════════════════


def check_error_handling() -> list[str]:
    violations: list[str] = []

    for rel_path in DOGFOOD_SCRIPTS:
        full = ROOT / rel_path
        if not full.exists():
            continue
        text = full.read_text(encoding="utf-8")

        # Dogfood scripts that make API calls must handle HTTPError
        has_api_calls = bool(re.search(r"urllib\.request\.(urlopen|Request)", text))
        has_error_handler = bool(re.search(r"HTTPError|URLError|except\s+Exception", text))

        if has_api_calls and not has_error_handler:
            violations.append(f"{rel_path}: makes API calls but has no HTTPError/Exception handler")

    return violations


# ═══════════════════════════════════════════════════════════════════
# Check 5: Evidence report integrity
# ═══════════════════════════════════════════════════════════════════


def check_evidence_reports() -> list[str]:
    violations: list[str] = []

    for rel_path in EVIDENCE_REPORTS:
        full = ROOT / rel_path
        if not full.exists():
            continue  # evidence reports are optional — skip silently

        text = full.read_text(encoding="utf-8")

        # Count pass/fail markers
        pass_lines = len(re.findall(r"^\s*✅", text, re.MULTILINE))
        fail_lines = len(re.findall(r"^\s*❌", text, re.MULTILINE))

        # Parse summary line: "N pass, M fail"
        summary_match = re.search(r"(\d+)\s+pass\s*[,/]\s*(\d+)\s+fail", text, re.IGNORECASE)
        if summary_match:
            declared_pass = int(summary_match.group(1))
            declared_fail = int(summary_match.group(2))
            total_declared = declared_pass + declared_fail
            total_actual = pass_lines + fail_lines

            if total_actual > 0 and total_actual != total_declared:
                violations.append(
                    f"{rel_path}: summary says {total_declared} total checks "
                    f"but found {total_actual} result lines "
                    f"({pass_lines}✅ + {fail_lines}❌)"
                )

        # Check verdict patterns in embedded JSON (if any)
        # Look for "verdict": "win" or "verdict": "loss" patterns
        for forbidden in FORBIDDEN_VERDICTS:
            pattern = rf"""["']verdict["']\s*:\s*["']{forbidden}["']"""
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(f"{rel_path}: forbidden verdict '{forbidden}' in evidence report")

    return violations


# ═══════════════════════════════════════════════════════════════════
# Check 6: No DB contamination in dogfood code
# ═══════════════════════════════════════════════════════════════════


def check_no_db_contamination() -> list[str]:
    violations: list[str] = []

    for rel_path in DOGFOOD_SCRIPTS:
        full = ROOT / rel_path
        if not full.exists():
            continue
        text = full.read_text(encoding="utf-8")

        if re.search(r"ALTER\s+TABLE", text, re.IGNORECASE):
            violations.append(f"{rel_path}: contains ALTER TABLE")
        if re.search(r"import\s+duckdb", text):
            violations.append(f"{rel_path}: imports duckdb directly")
        if re.search(r"duckdb\.connect", text):
            violations.append(f"{rel_path}: calls duckdb.connect()")

    return violations


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════


def main() -> int:
    violations = find_all_violations()

    print("=== Dogfood Evidence Check ===")
    print()

    # Group by check type for display
    checks = {
        "Script existence & syntax": check_scripts_exist,
        "Run count consistency": check_run_counts,
        "Verdict vocabulary": check_verdict_vocabulary,
        "Error handling": check_error_handling,
        "Evidence report integrity": check_evidence_reports,
        "DB contamination in dogfood": check_no_db_contamination,
    }

    total_ok = 0
    for name, check_fn in checks.items():
        v = check_fn()
        if v:
            print(f"❌ {name}:")
            for item in v:
                print(f"  {item}")
        else:
            print(f"✅ {name}")
            total_ok += 1

    # Summary
    print()
    if violations:
        print(f"❌ {len(violations)} violation(s) — Dogfood evidence incomplete")
        return 1
    else:
        print("✅ Dogfood evidence consistent")
        return 0


if __name__ == "__main__":
    sys.exit(main())
