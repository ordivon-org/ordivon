"""Finance Boundary Checker — enforces Phase 8 DEFERRED / live trading NO-GO.

Scans CURRENT docs for dangerous live trading language. Excludes immutable
evidence records (docs/runtime/) and historical archives (docs/archive/)
which document past state, not current claims.
"""

from __future__ import annotations
import re, sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DANGEROUS = [
    (re.compile(r"live\s+trad(?:e|ing)", re.I), "live trading reference"),
    (re.compile(r"live\s+order", re.I), "live order reference"),
    (re.compile(r"place_live_order", re.I), "place_live_order capability"),
    (re.compile(r"live\s+broker", re.I), "live broker reference"),
    (re.compile(r"live\s+execution", re.I), "live execution reference"),
    (re.compile(r"phase\s*8\s*(?:ready|active|start)", re.I), "Phase 8 readiness claim"),
    (re.compile(r"broker\s*write", re.I), "broker write reference"),
    (re.compile(r"can_place_live_order\s*:\s*True", re.I), "live order capability enabled"),
]

SAFE = re.compile(
    r"NO-GO|DEFERRED|BLOCKED|not\s+live|paper.?only|not\s+supported|"
    r"Phase\s*8\s+DEFERRED|never\s+live|no\s+live|not\s+auth",
    re.I,
)

# Directories excluded from scanning — immutable evidence records
SCAN_EXCLUDE_PREFIXES = (
    "docs/runtime/",     # immutable governance receipts
    "docs/archive/",     # historical records
    "docs/ai/",          # AI agent templates — instruct on boundaries, don't violate them
    "docs/audits/",      # audit reports — document past findings
    "docs/product/",     # product docs — describe what product checks for
    "docs/design/",      # design docs — reference live trading in mockups/specs
)

# Files that define the boundary (normative)
SAFE_FILES = {
    "docs/governance/finance-boundary-design.md",
    "docs/architecture/finance-pack-architecture.md",
    # Governance docs that define the finance boundary
    "docs/governance/document-authority-model-dg-1.md",
    "docs/governance/document-classification-index-dg-1.md",
    "docs/governance/document-staleness-audit-dg-3.md",
    "docs/governance/philosophical-governance-layer.md",
    "docs/governance/philosophical-surface-map-pgi-1.md",
    "docs/governance/ai-onboarding-doc-policy.md",
    "docs/governance/finance-pack-philosophical-hardening-pgi-2.md",
    # Architecture specs that define the boundary
    "docs/architecture/execution-request-receipt-spec.md",
    # Product docs — stage summits and scoping documents
    "docs/product/alpaca-paper-dogfood-stage-summit-phase-7p.md",
    "docs/product/ordivon-verify-product-brief.md",
    "docs/product/ordivon-verify-public-wedge-audit-scope.md",
    "docs/product/philosophical-governance-implementation-roadmap.md",
    "docs/product/policy-platform-stage-summit-phase-5.md",
}

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def _is_excluded(rel_path: str) -> bool:
    for prefix in SCAN_EXCLUDE_PREFIXES:
        if rel_path.startswith(prefix):
            return True
    return False


def run() -> CheckerResult:
    findings, stats = [], {"files": 0}
    for p in (ROOT / "docs",):
        if not p.is_dir():
            continue
        for f in p.rglob("*.md"):
            if ".git/" in str(f) or "paper-trades/PT-0" in str(f):
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
                for pat, desc in DANGEROUS:
                    m = pat.search(line)
                    if not m:
                        continue
                    ctx_start = max(0, i - 3)
                    ctx_end = min(len(lines), i + 3)
                    ctx = "\n".join(lines[ctx_start:ctx_end])
                    if SAFE.search(ctx):
                        continue
                    findings.append(f"{rel}:{i}: {desc} — '{m.group()}'")

    # Also check AGENTS.md
    agents = ROOT / "AGENTS.md"
    if agents.exists():
        lines = agents.read_text().split("\n")
        for i, line in enumerate(lines, 1):
            for pat, desc in DANGEROUS:
                m = pat.search(line)
                if not m:
                    continue
                ctx_start = max(0, i - 3)
                ctx_end = min(len(lines), i + 3)
                ctx = "\n".join(lines[ctx_start:ctx_end])
                if SAFE.search(ctx):
                    continue
                findings.append(f"AGENTS.md:{i}: {desc} — '{m.group()}'")

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
