#!/usr/bin/env python3
"""Ordivon Verify — Public Wedge Secret/Private-Reference Audit (PV-N6).

Scans the future public-wedge candidate surfaces for secrets, private paths,
legacy identity leakage, broker/finance references, unsafe maturity claims,
and license/release overclaims.

Audit dry run. Not a legal/security guarantee. Does not mutate files.
Does not publish, upload, or activate anything.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ── Audit scope: public-wedge candidate include set ────────────────────

INCLUDE_PATHS = [
    "src/ordivon_verify",
    "scripts/ordivon_verify.py",
    "scripts/smoke_ordivon_verify_private_install.py",
    "examples/ordivon-verify",
    "skills/ordivon-verify",
    "docs/product/ordivon-verify-public-readme-draft.md",
    "docs/product/ordivon-verify-landing-copy-v0.md",
    "docs/product/ordivon-verify-public-quickstart-v0.md",
    "docs/product/ordivon-verify-quickstart.md",
    "docs/product/ordivon-verify-ci-example.md",
    "docs/product/ordivon-verify-pr-comment-example.md",
    "docs/product/ordivon-verify-adoption-guide.md",
    "docs/product/ordivon-verify-package-structure-proposal.md",
    "docs/product/ordivon-verify-schema-extraction-plan.md",
    "docs/product/ordivon-verify-release-readiness-checklist.md",
    "docs/runtime/ordivon-verify-public-quickstart-dogfood-pv-n3.md",
    "docs/runtime/ordivon-verify-private-package-install-smoke-pv-n4.md",
]

# ── Category definitions ───────────────────────────────────────────────

CATEGORIES = {
    "secret_markers": {
        "patterns": [
            r"API_KEY",
            r"SECRET[_\s]*(?:KEY)?",
            r"TOKEN",
            r"PASSWORD",
            r"PRIVATE_KEY",
            r"ACCESS_KEY",
            r"BEARER",
            r"AUTHORIZATION",
        ],
        "blocking": True,
    },
    "broker_trading": {
        "patterns": [
            r"Alpaca",
            r"broker",
            r"live.trading",
            r"paper.trading",
            r"order.submit",
            r"account.id",
            r"trading.key",
        ],
        "blocking": True,
    },
    "private_paths": {
        "patterns": [r"/root/projects", r"/mnt/", r"C:\\", r"/home/\w+/projects"],
        "blocking": True,
    },
    "legacy_identity": {
        "patterns": [r"PFIOS", r"pfios", r"AegisOS", r"CAIOS"],
        "blocking": True,
    },
    "unsafe_maturity": {
        "patterns": [
            r"production-ready",
            r"stable.release",
            r"public.alpha",
            r"published\b(?!.*not\b)",
            r"open.source.now",
            r"enterprise-ready",
            r"customer.validated",
            r"auto.merge(?!.*no\b)",
            r"authorizes.execution",
            r"approved.by.Verify",
        ],
        "blocking": True,
    },
    "license_release": {
        "patterns": [
            r"Apache-2.0.activated",
            r"MIT.activated",
            r"LICENSE.final",
            r"package.published",
            r"PyPI.published",
            r"npm.published",
        ],
        "blocking": True,
    },
}

# ── Safe context patterns (negate blocking) ────────────────────────────

SAFE_CONTEXTS = [
    r"not\s+(?:a\s+)?(?:public\s+)?(?:release|published|package)",
    r"no\s+(?:broker|API|live|trading|auto.merge|authorization)",
    r"does\s+not\s+(?:authorize|publish|activate|auto.merge)",
    r"(?:legacy|historical)\s+(?:PFIOS|AegisOS|identity)",
    r"(?:blocked|deferred|not\s+yet)",
    r"recommendation only",
    r"proposal",
    r"private\s+(?:beta|package|prototype)",
    r"not\s+(?:public|production|stable)",
    r"evidence,\s*not",
    r"before\s+public\s+alpha",
    r"no\s+internal\s+paths",
    r"no\s+.*paths",
    r"not\s+.*authorization",
    r"not\s+.*auto.merge",
    r"check.*before\b",
    r"must\s+be\s+checked",
    r"is\s+evidence,\s*not",
    r"separate\s+from.*package",
    r"should\s+not\s+define",
    r"not\s+granted",
    r"no\s+\w+\s+authorization",
    r"forbidden\s*=",
    r"\[ \]",  # checklist item
    r"should\s+be\s+published",  # proposal, not claim
    r"separate\s+from",
    r"-\s+Finance\s+pack",
    r"-\s+Broker\s+API",
    r"context_tokens",  # LLM context window size — not a secret token
    r"max_context_tokens",  # HAP schema field — not a secret token
    r"READY_WITHOUT_AUTHORIZATION",
    r"no_action_authorization_statement",
    r"authorization_laundering",
    r"AUTHORIZATION_LAUNDERING_PATTERN",
    r"must\s+not\s+.*authorization",
    r"without\s+authorization",
    r"action\s+authorization",
]


def _is_safe_context(line: str) -> bool:
    """Check if a line contains a safe negation context."""
    for pattern in SAFE_CONTEXTS:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False


# ── File collection ────────────────────────────────────────────────────


def collect_files() -> list[Path]:
    """Collect all files in the public-wedge include set."""
    files: list[Path] = []
    for p in INCLUDE_PATHS:
        full = ROOT / p
        if not full.exists():
            continue
        if full.is_file():
            if full.suffix in (".py", ".md", ".json", ".jsonl", ".yaml", ".yml", ".toml"):
                files.append(full)
        elif full.is_dir():
            for f in sorted(full.rglob("*")):
                if f.is_file() and f.suffix in (".py", ".md", ".json", ".jsonl", ".yaml", ".yml", ".toml"):
                    files.append(f)
    return files


# ── Scan ────────────────────────────────────────────────────────────────


def scan_file(path: Path, rel: str) -> list[dict]:
    """Scan one file. Return list of findings."""
    findings: list[dict] = []
    try:
        content = path.read_text()
    except Exception:
        return findings

    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        for cat_name, cat_def in CATEGORIES.items():
            for pattern in cat_def["patterns"]:
                m = re.search(pattern, line, re.IGNORECASE)
                if not m:
                    continue

                matched = m.group(0)
                classification = "blocking" if cat_def["blocking"] else "review_needed"

                # Check safe context
                ctx_start = max(0, i - 2)
                ctx_end = min(len(lines), i + 2)
                ctx_text = "\n".join(lines[ctx_start:ctx_end])
                if _is_safe_context(ctx_text):
                    classification = "allowed_context"

                findings.append({
                    "file": rel,
                    "line": i,
                    "match": matched,
                    "category": cat_name,
                    "classification": classification,
                    "context": line.strip()[:120],
                })

    return findings


# ── Main ────────────────────────────────────────────────────────────────


def main(json_output: bool = False) -> int:
    files = collect_files()
    all_findings: list[dict] = []

    for f in files:
        rel = str(f.relative_to(ROOT))
        all_findings.extend(scan_file(f, rel))

    blocking = [f for f in all_findings if f["classification"] == "blocking"]
    allowed = [f for f in all_findings if f["classification"] == "allowed_context"]
    review = [f for f in all_findings if f["classification"] == "review_needed"]

    if json_output:
        print(
            json.dumps(
                {
                    "audit": "ordivon-verify-public-wedge-secret",
                    "phase": "PV-N6",
                    "dry_run": True,
                    "scanned_files": len(files),
                    "findings_total": len(all_findings),
                    "blocking_findings": len(blocking),
                    "allowed_context_findings": len(allowed),
                    "review_needed_findings": len(review),
                    "categories_checked": list(CATEGORIES.keys()),
                    "blocking": blocking,
                    "allowed_context": allowed,
                    "review_needed": review,
                    "disclaimer": "Audit dry run. Not a legal/security guarantee.",
                },
                indent=2,
            )
        )
    else:
        print("=" * 60)
        print("ORDIVON VERIFY — PUBLIC WEDGE SECRET/PRIVATE AUDIT")
        print("=" * 60)
        print(f"  Scanned files:            {len(files)}")
        print(f"  Findings total:           {len(all_findings)}")
        print(f"  Blocking findings:        {len(blocking)}")
        print(f"  Allowed context:          {len(allowed)}")
        print(f"  Review needed:            {len(review)}")
        print(f"  Categories checked:       {len(CATEGORIES)}")
        print()

        if blocking:
            print(f"❌ BLOCKING FINDINGS ({len(blocking)}):")
            for f in blocking:
                print(f"  {f['file']}:{f['line']} [{f['category']}] {f['match']}")
                print(f"    → {f['context']}")
            print()

        if review:
            print(f"⚠️  REVIEW NEEDED ({len(review)}):")
            for f in review:
                print(f"  {f['file']}:{f['line']} [{f['category']}] {f['match']}")
            print()

        if not blocking:
            print("✅ No blocking findings — public wedge candidate surfaces are clean.")
            print()
            print("   Audit dry run. Not a legal/security guarantee.")
            print("   Final pre-release audit required on any extracted repo.")

    return 1 if blocking else 0


if __name__ == "__main__":
    json_mode = "--json" in sys.argv
    sys.exit(main(json_output=json_mode))
