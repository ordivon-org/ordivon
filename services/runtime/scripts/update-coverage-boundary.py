#!/usr/bin/env python3
"""Generate coverage boundary — classify every tracked file's governance status (PM-5).

Usage:
    python scripts/update-coverage-boundary.py
"""

from __future__ import annotations

import json, subprocess, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs/governance/generated"
SCHEMA_DIR = ROOT / "docs/governance/schemas"


def git_ls_files() -> list[str]:
    result = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=str(ROOT), timeout=15)
    return [l for l in result.stdout.strip().split("\n") if l]


def load_path_map() -> dict:
    pm = json.loads((OUTPUT_DIR / "path-map.json").read_text())
    return {n["path"]: n for n in pm.get("nodes", [])}


def load_registry() -> dict:
    entries = {}
    reg_path = ROOT / "docs/governance/document-registry.jsonl"
    if reg_path.exists():
        with open(reg_path) as f:
            for line in f:
                if line.strip():
                    e = json.loads(line)
                    entries[e["path"]] = e
    return entries


def load_exclusions() -> dict:
    excl_path = SCHEMA_DIR / "governed-exclusions.json"
    return json.loads(excl_path.read_text()).get("entries", {}) if excl_path.exists() else {}


def load_batch_receipts() -> dict[str, str]:
    """Load applied batch receipts — status overrides from PM-7."""
    receipts = {}
    receipt_dir = ROOT / "docs/governance/receipts/coverage-batches"
    if receipt_dir.exists():
        for rf in receipt_dir.glob("*.json"):
            r = json.loads(rf.read_text())
            target = r.get("target_status", "")
            if target:
                for fp in r.get("affected_paths", []):
                    receipts[fp] = target
    return receipts


def load_debts() -> dict[str, dict]:
    global _debt_patterns
    _debt_patterns = []
    debts = {}
    debt_path = ROOT / "docs/governance/dependency-audit-debts.jsonl"
    if debt_path.exists():
        with open(debt_path) as f:
            for line in f:
                if line.strip():
                    d = json.loads(line)
                    p = d.get("path", "")
                    if p and ("*" in p or "**" in p):
                        _debt_patterns.append(d)
                    elif p:
                        debts[p] = d
                    debts[d.get("debt_id", "")] = d
    return debts


def load_coverage_rules() -> dict:
    return json.loads((SCHEMA_DIR / "coverage-boundary.json").read_text())


def is_protected(filepath: str, protected_paths: list[str]) -> bool:
    import fnmatch

    return any(fnmatch.fnmatch(filepath, p) for p in protected_paths)


def classify(
    filepath: str, pm_nodes: dict, registry: dict, exclusions: dict, debts: dict, rules: dict, batch_receipts: dict
) -> dict:
    protected_paths = rules.get("protected_paths", [])
    node = pm_nodes.get(filepath)
    reg = registry.get(filepath)
    excl = filepath in exclusions

    # Coverage by rule precedence
    
    # 1. Has registry entry
    if reg and node and node.get("classification_status") == "governed":
        return {
            "path": filepath,
            "coverage_status": "governed",
            "source": "registry + path-map",
            "metadata": {
                "route": node.get("route", ""),
                "doc_type": reg.get("doc_type", ""),
                "authority_domain": reg.get("authority_domain", ""),
            },
        }

    # 2. Generated
    if node and node.get("kind") == "generated_view":
        return {
            "path": filepath,
            "coverage_status": "generated",
            "source": "path-map classification",
            "metadata": {"must_not_be_source_of_truth": node.get("must_not_be_source_of_truth", False)},
        }

    # 3. Explicit exclusion
    if excl or filepath in exclusions or (node and node.get("kind") == "explicit_exclusion"):
        reason = exclusions.get(filepath, node.get("reason", "")) if node else ""
        return {
            "path": filepath,
            "coverage_status": "excluded",
            "source": "governed-exclusions.json",
            "metadata": {"reason": str(reason)[:100]},
        }

    # 4. Source code
    if node and node.get("route") == "source-code":
        return {
            "path": filepath,
            "coverage_status": "governed",
            "source": "path-map route",
            "metadata": {"route": "source-code"},
        }

    # 5. Checker nodes
    if node and node.get("kind") == "checker":
        return {
            "path": filepath,
            "coverage_status": "governed",
            "source": "checker discovery",
            "metadata": {"route": node.get("route", "")},
        }

    # 6. CI workflows
    if filepath.startswith(".github/workflows/"):
        return {"path": filepath, "coverage_status": "governed", "source": "CI discovery"}

    # 7. Knowledge assets
    if node and node.get("kind") == "knowledge_asset":
        return {"path": filepath, "coverage_status": "governed", "source": "ledger discovery"}

    # 8. Test fixtures
    if "tests/fixtures/" in filepath:
        return {
            "path": filepath,
            "coverage_status": "fixture",
            "source": "path pattern",
            "metadata": {"need_owning_test": True},
        }

    # 9. Legacy / archive
    if "/legacy/" in filepath or "/archive/" in filepath:
        return {"path": filepath, "coverage_status": "legacy", "source": "path pattern"}

    # 10. Vendor
    if "/vendor/" in filepath or "/vendored/" in filepath:
        return {"path": filepath, "coverage_status": "vendored", "source": "path pattern"}

    # 11. Debt-parked: exact + pattern match
    import fnmatch

    debt_entry = debts.get(filepath)
    if not debt_entry:
        for pd in _debt_patterns:
            if pd.get("status") == "OPEN" and fnmatch.fnmatch(filepath, pd.get("path", "")):
                debt_entry = pd
                break
    if debt_entry and debt_entry.get("status") == "OPEN":
        return {
            "path": filepath,
            "coverage_status": "debt_parked",
            "source": "debt ledger",
            "metadata": {"debt_id": debt_entry.get("debt_id", "")},
        }

    # 12. Applied batch receipt (PM-7): status override from resolution batches
    if filepath in batch_receipts:
        target = batch_receipts[filepath]
        return {"path": filepath, "coverage_status": target, "source": "batch receipt (GOS-PM-7)"}

    # 13. Governance scripts (scripts/ files that are governance tools)
    gov_prefixes = [
        "scripts/check_",
        "scripts/run_",
        "scripts/generate-",
        "scripts/update-",
        "scripts/verify-",
        "scripts/reconcile",
        "scripts/hash_ledger",
        "scripts/review_lessons",
        "scripts/detect_overclaim",
        "scripts/detect_agentic",
        "scripts/triage",
        "scripts/explain",
        "scripts/collect-stage",
        "scripts/verify-stage",
    ]
    if any(filepath.startswith(p) for p in gov_prefixes):
        return {"path": filepath, "coverage_status": "governed", "source": "governance script"}

    # 13. Schema files in governed dirs (excluded from doc governance)
    if filepath.startswith("docs/governance/schemas/") and filepath.endswith(".json"):
        return {
            "path": filepath,
            "coverage_status": "excluded",
            "source": "schema file in governed dir — excluded from doc governance",
            "metadata": {"reason": exclusions.get(filepath, "Meta-schema, not governed doc")},
        }

    # 14. Protected path → blocked
    if is_protected(filepath, protected_paths):
        return {
            "path": filepath,
            "coverage_status": "blocked",
            "source": "protected path",
            "finding": "CB-1 UNKNOWN_PROTECTED_FILE",
        }

    # 13. Non-protected → requires debt or exclusion
    return {"path": filepath, "coverage_status": "debt_or_exclusion_required", "source": "non-protected unclassified"}


def main() -> int:
    files = git_ls_files()
    pm = load_path_map()
    reg = load_registry()
    excl = load_exclusions()
    debts = load_debts()
    rules = load_coverage_rules()
    batch_receipts = load_batch_receipts()

    classified = []
    counts = Counter()
    blocked = []

    for fp in sorted(files):
        c = classify(fp, pm, reg, excl, debts, rules, batch_receipts)
        classified.append(c)
        counts[c["coverage_status"]] += 1
        if c["coverage_status"] == "blocked":
            blocked.append(c)

    stats = {"total": len(files), "by_status": dict(counts), "blocked": len(blocked), "protected_unknown": len(blocked)}

    output = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authority": "generated_view",
        "source_refs": [
            "git ls-files",
            "path-map.json",
            "document-registry.jsonl",
            "governed-exclusions.json",
            "debt ledger (pattern match)",
        ],
        "stats": stats,
        "files": classified,
        "blocked_findings": blocked,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "coverage-boundary.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")

    # Generate markdown
    lines = [
        "# Coverage Boundary",
        "",
        "> **GENERATED VIEW — DO NOT EDIT**",
        "> Full Closure: NOT CLAIMED",
        "",
        "## Summary",
        "",
        "| Status | Count |",
        "|---|---|",
    ]
    for status in rules["coverage_statuses"]:
        c = counts.get(status, 0)
        if c > 0:
            lines.append(f"| {status} | {c} |")
    lines.extend([
        "",
        f"**Total files**: {len(files)}",
        f"**Blocked**: {len(blocked)}",
        "",
        "## Blocked Files",
        "",
    ])
    if blocked:
        for b in blocked:
            lines.append(f"- `{b['path']}`: {b.get('finding', 'CB-1')}")
    else:
        lines.append("None.")
    lines.extend(["", "---", "```text", "READY means selected checks passed.", "```"])
    (OUTPUT_DIR / "_coverage-boundary.md").write_text("\n".join(lines) + "\n")

    print(f"Coverage Boundary: {len(files)} files")
    for status, c in counts.most_common():
        print(f"  {status}: {c}")
    print(f"Blocked: {len(blocked)}")
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
