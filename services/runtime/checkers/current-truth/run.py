"""Current Truth Protocol Checker — cross-document numerical consistency.

Validates that hard numbers in AI-facing docs match canonical ground truth.
With --auto-fix: patches stale numbers in-place. Documents become generated
artifacts, not hand-maintained ones. The registry/filesystem is the source
of truth; docs just reflect it.

Usage:
    python checkers/current-truth/run.py              # detect drift
    python checkers/current-truth/run.py --auto-fix   # detect AND fix
"""

from __future__ import annotations
import json, re, sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CHECKERS_DIR = ROOT / "checkers"
DG_REGISTRY = ROOT / "docs" / "governance" / "document-registry.jsonl"
GATE_MANIFEST = ROOT / "docs" / "governance" / "verification-gate-manifest.json"

DOCUMENTS_TO_CHECK = {
    "AGENTS.md": ROOT / "AGENTS.md",
    "systems-reference.md": ROOT / "docs" / "ai" / "systems-reference.md",
    "new-ai-collaborator-guide.md": ROOT / "docs" / "ai" / "new-ai-collaborator-guide.md",
    "current-phase-boundaries.md": ROOT / "docs" / "ai" / "current-phase-boundaries.md",
}

_HISTORICAL_PHASE_PATTERNS = [
    re.compile(r'\|\s+\*\*(DG|PV|PGI|CPR|ADP|EG|COV|OGAP|HAP|GOV|OSS)-[\dA-Za-z-]+\*\*'),
    re.compile(r'DG-[2-6][A-Za-z]?\s.*entries'),
    re.compile(r'Phase\s+[2-7][A-Za-z]?\b'),
]


@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)


@dataclass
class DriftFix:
    """A single drift that can be auto-fixed."""
    file: str
    line: int
    old_line: str    # the full original line
    new_line: str    # the corrected line
    description: str


# ── Ground truth collectors ─────────────────────────────────────────

def _collect_checker_truth() -> dict:
    hard = 0; escalation = 0; pr_fast = 0; total = 0
    if not CHECKERS_DIR.exists():
        return {"total": 0, "hard": 0, "escalation": 0, "pr_fast": 0}
    for entry in sorted(CHECKERS_DIR.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        total += 1
        md = entry / "CHECKER.md"
        if not md.exists():
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        in_frontmatter = False
        for line in text.splitlines():
            line = line.strip()
            if line == "---":
                if not in_frontmatter: in_frontmatter = True; continue
                else: break
            if not in_frontmatter: continue
            if ":" not in line: continue
            key, _, val = line.partition(":")
            key = key.strip(); val = val.strip().strip("'\"")
            if key == "hardness":
                if val == "hard": hard += 1
                elif val == "escalation": escalation += 1
            if key == "profiles" and "pr-fast" in val:
                pr_fast += 1
    return {"total": total, "hard": hard, "escalation": escalation, "pr_fast": pr_fast}


def _collect_dg_truth() -> int:
    if not DG_REGISTRY.exists(): return 0
    with open(DG_REGISTRY) as f: return sum(1 for _ in f)


def _collect_manifest_truth() -> dict:
    if not GATE_MANIFEST.exists():
        return {"gates": 0, "hard": 0, "escalation": 0, "discovered": 0}
    with open(GATE_MANIFEST) as f: m = json.load(f)
    gates = m.get("gates", [])
    return {
        "gates": len(gates),
        "hard": sum(1 for g in gates if g.get("hardness") == "hard"),
        "escalation": sum(1 for g in gates if g.get("hardness") == "escalation"),
        "discovered": m.get("checkers_discovered_total", 0),
    }


def _is_historical_phase_line(line: str) -> bool:
    for pat in _HISTORICAL_PHASE_PATTERNS:
        if pat.search(line): return True
    return False


# ── Scanner with fix support ────────────────────────────────────────

def _scan_doc_with_fixes(path: Path) -> tuple[list[str], list[DriftFix]]:
    """Scan a doc and return (findings, fixable_drifts)."""
    if not path.exists():
        return [f"{path.relative_to(ROOT)}: (file not found)"], []

    truth = _collect_checker_truth()
    dg_truth = _collect_dg_truth()
    manifest = _collect_manifest_truth()

    findings: list[str] = []
    fixes: list[DriftFix] = []
    content = path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()
    rel = str(path.relative_to(ROOT))

    for i, line in enumerate(lines):
        stripped = line.strip()
        if _is_historical_phase_line(stripped):
            continue

        # ── DG entry count ──────────────────────────────────────
        if re.search(r'document.*registry|document-registry|registered\s+doc', stripped, re.IGNORECASE):
            m = re.search(r'\b(\d+)\s+(?:registered\s+)?(?:entries|docs)\b', stripped, re.IGNORECASE)
            if m:
                claimed = int(m.group(1))
                if claimed != dg_truth:
                    old = m.group(0)
                    new = old.replace(str(claimed), str(dg_truth), 1)
                    new_line = line.replace(old, new, 1)
                    findings.append(f"{rel}:{i+1} — DG entries: claims {claimed}, actual {dg_truth}")
                    fixes.append(DriftFix(rel, i, line, new_line,
                                          f"DG entries: {claimed} → {dg_truth}"))

        # ── Total checker count ─────────────────────────────────
        m = re.search(r'\b(\d+)\s+checkers\b', stripped, re.IGNORECASE)
        if m:
            claimed = int(m.group(1))
            if claimed > 20 and claimed != truth["total"] and "pr-fast" not in stripped.lower():
                old = m.group(0)
                new = old.replace(str(claimed), str(truth["total"]), 1)
                new_line = line.replace(old, new, 1)
                findings.append(f"{rel}:{i+1} — checker total: claims {claimed}, actual {truth['total']}")
                fixes.append(DriftFix(rel, i, line, new_line,
                                      f"Checker total: {claimed} → {truth['total']}"))

        # ── Hard/escalation breakdown ───────────────────────────
        m = re.search(r'\(?(\d+)\s+hard\s*[+,]\s*(\d+)\s+escalation\)?', stripped, re.IGNORECASE)
        if m:
            claimed_hard = int(m.group(1)); claimed_esc = int(m.group(2))
            if claimed_hard != truth["hard"] or claimed_esc != truth["escalation"]:
                old = m.group(0)
                new = old.replace(str(claimed_hard), str(truth["hard"]), 1)
                new = new.replace(str(claimed_esc), str(truth["escalation"]), 1)
                new_line = line.replace(old, new, 1)
                findings.append(f"{rel}:{i+1} — hard/escalation: claims {claimed_hard}/{claimed_esc}, actual {truth['hard']}/{truth['escalation']}")
                fixes.append(DriftFix(rel, i, line, new_line,
                                      f"Hard/escalation: {claimed_hard}/{claimed_esc} → {truth['hard']}/{truth['escalation']}"))

        # ── pr-fast gate count ──────────────────────────────────
        m = re.search(r'pr-fast[:\s]+(\d+)/(\d+)', stripped, re.IGNORECASE)
        if m:
            claimed = int(m.group(1))
            if claimed != truth["pr_fast"]:
                old = m.group(0)
                new = old.replace(f"{claimed}/", f"{truth['pr_fast']}/", 1)
                new_line = line.replace(old, new, 1)
                findings.append(f"{rel}:{i+1} — pr-fast: claims {claimed}/{m.group(2)}, actual {truth['pr_fast']}")
                fixes.append(DriftFix(rel, i, line, new_line,
                                      f"pr-fast: {claimed} → {truth['pr_fast']}"))

        # ── Full baseline count ─────────────────────────────────
        m = re.search(r'full[:\s]+(\d+)/(\d+)', stripped, re.IGNORECASE)
        if m:
            claimed = int(m.group(1))
            if claimed != truth["total"]:
                old = m.group(0)
                new = old.replace(f"{claimed}/", f"{truth['total']}/", 1)
                new_line = line.replace(old, new, 1)
                findings.append(f"{rel}:{i+1} — full baseline: claims {claimed}/{m.group(2)}, actual {truth['total']}")
                fixes.append(DriftFix(rel, i, line, new_line,
                                      f"Full baseline: {claimed} → {truth['total']}"))

    return findings, fixes


def _auto_fix(fixes: list[DriftFix]) -> int:
    """Apply all fixes in-place. Returns number of files modified."""
    from collections import defaultdict
    by_file = defaultdict(list)
    for f in fixes:
        by_file[f.file].append(f)

    modified = 0
    for rel, file_fixes in by_file.items():
        path = ROOT / rel
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        # Sort by line number descending to avoid offset issues
        for fix in sorted(file_fixes, key=lambda x: x.line, reverse=True):
            lines[fix.line] = fix.new_line
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        modified += 1

    return modified


# ── Main ────────────────────────────────────────────────────────────

def run(auto_fix: bool = False) -> CheckerResult:
    findings: list[str] = []
    all_fixes: list[DriftFix] = []
    stats = {"docs_checked": 0, "drifts_found": 0, "drifts_fixed": 0,
             "checkers_total": 0, "dg_entries": 0}

    truth = _collect_checker_truth()
    stats["checkers_total"] = truth["total"]
    stats["dg_entries"] = _collect_dg_truth()

    for name, path in DOCUMENTS_TO_CHECK.items():
        stats["docs_checked"] += 1
        doc_findings, doc_fixes = _scan_doc_with_fixes(path)
        findings.extend(doc_findings)
        stats["drifts_found"] += len(doc_findings)
        all_fixes.extend(doc_fixes)

    if auto_fix and all_fixes:
        modified = _auto_fix(all_fixes)
        stats["drifts_fixed"] = len(all_fixes)
        findings.append(f"Auto-fixed {len(all_fixes)} drift(s) across {modified} file(s). "
                        f"Re-run without --auto-fix to verify.")

    if findings and not auto_fix:
        findings.insert(0, f"Cross-doc consistency: {stats['drifts_found']} drift(s) "
                        f"across {stats['docs_checked']} docs. "
                        f"Run with --auto-fix to patch automatically.")

    return CheckerResult(
        "fail" if (findings and not auto_fix) else "pass",
        1 if (findings and not auto_fix) else 0,
        findings,
        dict(stats),
    )


if __name__ == "__main__":
    auto = "--auto-fix" in sys.argv
    r = run(auto_fix=auto)
    label = "Current Truth Protocol"
    if auto and r.stats.get("drifts_fixed", 0) > 0:
        label += " (auto-fix)"
    print(f"{label}: {'PASS' if not r.findings or auto else 'FAIL'}")
    for f in r.findings:
        print(f"  {f}")
    sys.exit(r.exit_code)
