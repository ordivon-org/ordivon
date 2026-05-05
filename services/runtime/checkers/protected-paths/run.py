"""Protected Paths Checker — detects unqualified references to protected file paths.

Scans CURRENT docs for references to sensitive paths (.env, secrets, etc.)
without explicit governance context. Excludes immutable evidence records
(docs/runtime/) and historical archives (docs/archive/).
"""

from __future__ import annotations
import re, sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PROTECTED = [
    r"\.env\b",
    r"\bsecrets?\b",
    r"private[_\s]?key",
    r"credentials?",
    r"pyproject\.toml",
    r"uv\.lock",
    r"(?:pnpm|package)-lock\.ya?ml",
    r"state/db/migrations/runner\.py",
]

SAFE = re.compile(
    r"NO-GO|not\s+allowed|protected|governed|forbidden|"
    r"FORBIDDEN|boundary|explicit\s+justification|explicitly\s+allowed",
    re.I,
)

# Directories excluded from scanning — immutable evidence records
SCAN_EXCLUDE_PREFIXES = (
    "docs/runtime/",     # immutable governance receipts
    "docs/archive/",     # historical records
    "docs/audits/",      # audit reports — document past findings
    "docs/plans/",       # planning docs — describe remediation, not violations
    "docs/ai/",          # AI agent templates — instruct on boundaries
    "docs/design/",      # design docs — reference paths in mockups/specs
    "docs/runbooks/",    # operational runbooks — document procedures
    "docs/architecture/",# architecture specs — define protection, don't violate it
    "docs/product/",     # product docs — describe what product checks for
    "docs/adr/",         # architecture decision records — historical design docs
)

# Files that define the protected paths policy itself
SAFE_FILES = {
    "packs/coding/policy.py",
    "docs/governance/document-governance-pack-contract.md",
    # Agentic pattern taxonomy — defines "Credential"/"secret" as pattern categories
    "docs/governance/agentic-pattern-taxonomy-adp-1.md",
    "docs/governance/agentic-pattern-source-ledger-adp-1.md",
    "docs/governance/capability-scaled-governance-gov-x.md",
    "docs/governance/document-authority-model-dg-1.md",
    "docs/governance/document-classification-index-dg-1.md",
    "docs/governance/authority-impact-gate-matrix-gov-x.md",
    "docs/governance/risk-ladder-gov-x.md",
    # Post-mortem — documents past incidents
    "docs/governance/vd-005-post-mortem-known-unknown-quadrant.md",
    # PGI docs that define boundaries
    "docs/governance/relationship-emotion-boundary-pgi-2.md",
    # AGENTS.md — documents CLOSED audit summary, not live secrets
    "AGENTS.md",
}


def _is_excluded(rel_path: str) -> bool:
    for prefix in SCAN_EXCLUDE_PREFIXES:
        if rel_path.startswith(prefix):
            return True
    return False


@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def run() -> CheckerResult:
    findings, stats = [], {"files": 0}
    scan_dirs = [ROOT / "docs", ROOT / "AGENTS.md"]

    for p in scan_dirs:
        if not p.exists():
            continue
        files = [p] if p.is_file() else list(p.rglob("*.md"))
        for f in files:
            if ".git/" in str(f) or "__pycache__" in str(f):
                continue
            try:
                rel = str(f.relative_to(ROOT))
            except ValueError:
                rel = str(f)
            if rel in SAFE_FILES or _is_excluded(rel):
                continue

            stats["files"] = stats.get("files", 0) + 1
            try:
                lines = f.read_text(encoding="utf-8", errors="replace").split("\n")
            except Exception:
                continue

            for i, line in enumerate(lines, 1):
                for pat in PROTECTED:
                    m = re.search(pat, line, re.I)
                    if not m:
                        continue
                    ctx_start = max(0, i - 3)
                    ctx_end = min(len(lines), i + 3)
                    ctx = "\n".join(lines[ctx_start:ctx_end])
                    if SAFE.search(ctx):
                        continue
                    findings.append(
                        f"{rel}:{i}: unprotected reference to '{m.group()}'"
                    )

    return CheckerResult(
        "fail" if findings else "pass",
        1 if findings else 0,
        findings,
        dict(stats),
    )


if __name__ == "__main__":
    r = run()
    print(f"Files: {r.stats.get('files', 0)} | Violations: {len(r.findings)}")
    for f in r.findings[:30]:
        print(f"  {f}")
    if len(r.findings) > 30:
        print(f"  ... +{len(r.findings) - 30} more")
    sys.exit(r.exit_code)
