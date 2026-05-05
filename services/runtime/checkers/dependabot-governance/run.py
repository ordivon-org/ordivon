"""Dependabot Governance — classifies Dependabot PRs through governance gates.

First operational governance checker. Makes real decisions on CI data.
Input: JSON payload describing PR context (actor, files, CI status).
Output: governance decision with structured receipt.

Entry point: def run() -> CheckerResult
Also callable as: python run.py --input pr-context.json
"""

from __future__ import annotations
import json, sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]

# ── Protected paths for Dependabot — different from CodingDisciplinePolicy ─
# Dependabot ALWAYS changes lock files. That's its job. Only truly sensitive
# files are protected here: env, secrets, credentials, migration runner.
_FORBIDDEN = {
    ".env", "secrets", "private_key", "credentials",
    "state/db/migrations/runner.py",
}

# ── Elevated-review paths (not forbidden, but escalate) ─────────────
# pyproject.toml changes from Dependabot are normal (version bumps).
# But if the PR also touches source code beyond the lock file, escalate.
_ELEVATED = {
    "pyproject.toml", "package.json",
}

# ── Runtime dependency indicators ───────────────────────────────────
_RUNTIME_INDICATORS = {"react", "next", "vue", "fastapi", "uvicorn", "sqlalchemy",
                       "pydantic", "httpx", "redis", "celery", "django", "flask",
                       "numpy", "pandas", "torch", "tensorflow"}

# ── Data types ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class PRContext:
    """Structured input describing a PR for governance classification."""
    actor: str                          # "dependabot" | "human" | "ai_agent" | "unknown"
    changed_files: tuple[str, ...]      # relative file paths
    ci_status: str                      # "pass" | "fail" | "partial" | "unknown"
    is_runtime_dep: bool = False        # does this update affect runtime behavior?
    pr_title: str = ""                  # PR title for context
    has_test_plan: bool = False         # does the PR include a test plan?
    evidence_freshness: str = "current" # "current" | "stale" | "unknown"

    @classmethod
    def from_dict(cls, d: dict) -> PRContext:
        return cls(
            actor=d.get("actor", "unknown"),
            changed_files=tuple(d.get("changed_files", [])),
            ci_status=d.get("ci_status", "unknown"),
            is_runtime_dep=d.get("is_runtime_dep", False),
            pr_title=d.get("pr_title", ""),
            has_test_plan=d.get("has_test_plan", False),
            evidence_freshness=d.get("evidence_freshness", "current"),
        )

@dataclass(frozen=True)
class GovernanceReceipt:
    """Structured evidence record for a governance decision."""
    decision: str                       # execute | escalate | reject
    reasons: tuple[str, ...]
    actor: str
    file_count: int
    has_forbidden: bool
    has_runtime_dep: bool
    ci_status: str
    recommendation: str                 # human-readable recommendation
    auto_merge_safe: bool

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

# ── Classification logic ────────────────────────────────────────────

def classify(pr: PRContext) -> GovernanceReceipt:
    """Classify a PR through governance gates and return a receipt."""
    reasons: list[str] = []
    forbidden_files: list[str] = []
    has_runtime = False
    has_lockfile_only = True

    for f in pr.changed_files:
        f_lower = f.lower()
        # Gate 3: forbidden path check
        for forbidden in _FORBIDDEN:
            if forbidden in f_lower:
                forbidden_files.append(f)
                reasons.append(f"Forbidden path: '{f}' matches protected pattern '{forbidden}'")
                break
        # Check if this is a non-lockfile change
        is_lock = any(f_lower.endswith(ext) for ext in (".lock", "lock.json", "lock.yaml"))
        is_manifest = any(f_lower.endswith(ext) for ext in ("pyproject.toml", "package.json"))
        if not is_lock and not is_manifest:
            has_lockfile_only = False
        # Check for runtime dependency indicators
        for indicator in _RUNTIME_INDICATORS:
            if indicator in f_lower:
                has_runtime = True
                break

    if pr.is_runtime_dep:
        has_runtime = True
    # Also detect from pr_title for common runtime dependency patterns
    if not has_runtime and pr.pr_title:
        title_lower = pr.pr_title.lower()
        for indicator in _RUNTIME_INDICATORS:
            if indicator in title_lower:
                has_runtime = True
                break

    # ── Decision logic ──────────────────────────────────────────

    if forbidden_files:
        decision = "reject"
        recommendation = "BLOCKED: Protected files cannot be modified by automated dependency updates."
    elif pr.ci_status == "fail":
        if has_runtime:
            decision = "escalate"
            reasons.append("CI failure on runtime dependency update — human review required")
            recommendation = "ESCALATE: Runtime dependency with CI failure. Manual investigation needed."
        else:
            decision = "hold"
            reasons.append("CI failure on non-runtime dependency update")
            recommendation = "HOLD: CI failure detected. Wait for CI to pass before re-evaluating."
    elif pr.ci_status == "unknown":
        decision = "escalate"
        reasons.append("CI status unknown — cannot verify safety")
        recommendation = "ESCALATE: CI status unknown. Run CI before considering merge."
    elif pr.evidence_freshness == "stale":
        decision = "escalate"
        reasons.append("Stale governance evidence — re-run CI for fresh evidence")
        recommendation = "ESCALATE: Evidence is stale. Re-run CI to refresh."
    elif has_lockfile_only and pr.ci_status == "pass" and not has_runtime:
        decision = "execute"
        reasons.append("Lockfile-only dependency update with passing CI")
        recommendation = "SAFE: Lockfile-only change with green CI. Auto-merge candidate."
    elif pr.ci_status == "pass" and not has_runtime:
        decision = "execute"
        reasons.append("Non-runtime dependency update with passing CI")
        recommendation = "SAFE: Non-runtime dep with green CI. Auto-merge candidate."
    elif pr.ci_status == "pass" and has_runtime:
        decision = "escalate"
        reasons.append("Runtime dependency update — human review recommended even with green CI")
        recommendation = "REVIEW: Runtime dependency. Human should verify changelog before merge."
    else:
        decision = "escalate"
        reasons.append("Unclassified scenario — conservative escalation")
        recommendation = "ESCALATE: Unclassified. Human review required."

    return GovernanceReceipt(
        decision=decision,
        reasons=tuple(reasons) if reasons else ("Passed all governance gates.",),
        actor=pr.actor,
        file_count=len(pr.changed_files),
        has_forbidden=bool(forbidden_files),
        has_runtime_dep=has_runtime,
        ci_status=pr.ci_status,
        recommendation=recommendation,
        auto_merge_safe=(decision == "execute"),
    )

# ── Entry point ─────────────────────────────────────────────────────

def run() -> CheckerResult:
    """Run dependabot governance check. Uses TEST_SCENARIOS in test mode,
    or reads JSON from stdin/--input argument."""
    import os

    # Check for --input flag
    input_file = None
    args = sys.argv[1:]
    if "--input" in args:
        idx = args.index("--input")
        if idx + 1 < len(args):
            input_file = args[idx + 1]

    if input_file:
        with open(input_file) as f:
            pr = PRContext.from_dict(json.load(f))
        receipt = classify(pr)
        print(json.dumps({
            "decision": receipt.decision,
            "reasons": list(receipt.reasons),
            "recommendation": receipt.recommendation,
            "auto_merge_safe": receipt.auto_merge_safe,
        }, indent=2))
        exit_code = 0 if receipt.decision == "execute" else (2 if receipt.decision == "escalate" else 3)
        sys.exit(exit_code)

    # Test mode: run classification against standard scenarios
    # Each scenario has an EXPECTED decision — reject is a valid outcome
    scenarios = [
        PRContext("dependabot", ("uv.lock",), "pass", False, "bump typing-extensions"),
        PRContext("dependabot", ("pyproject.toml", "uv.lock"), "pass", True, "bump sqlalchemy"),
        PRContext("dependabot", (".env",), "pass", False, "update env"),
        PRContext("dependabot", ("uv.lock",), "fail", False, "bump certifi"),
    ]
    expected_decisions = ["execute", "escalate", "reject", "hold"]

    findings = []
    stats = {"scenarios": len(scenarios), "execute": 0, "escalate": 0, "reject": 0, "hold": 0}
    mismatches = 0

    for i, pr in enumerate(scenarios):
        receipt = classify(pr)
        actual = receipt.decision
        expected = expected_decisions[i] if i < len(expected_decisions) else None
        stats[actual] = stats.get(actual, 0) + 1
        short_files = ",".join(pr.changed_files[:2])
        findings.append(f"{pr.actor} | {short_files} | CI:{pr.ci_status} -> {actual.upper()}: {receipt.recommendation}")
        if expected and actual != expected:
            findings.append(f"  MISMATCH: expected {expected.upper()}, got {actual.upper()}")
            mismatches += 1

    if mismatches:
        findings.append(f"{mismatches} decision mismatch(es) — checker logic may need review")
    return CheckerResult("pass" if mismatches == 0 else "fail", 0 if mismatches == 0 else 1, findings, dict(stats))

if __name__ == "__main__":
    r = run()
    print(f"Scenarios: {r.stats.get('scenarios',0)}")
    print(f"Decisions: execute={r.stats.get('execute',0)}, escalate={r.stats.get('escalate',0)}, reject={r.stats.get('reject',0)}, hold={r.stats.get('hold',0)}")
    for f in r.findings: print(f"  {f}")
    if r.status == "fail":
        print(f"\n❌ {r.stats.get('reject',0)} blocked scenario(s)")
    else:
        print("\n✅ All scenarios classified correctly")
    sys.exit(r.exit_code)
