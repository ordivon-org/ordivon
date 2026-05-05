"""Document Registry Checker — validates document-registry.jsonl invariants."""

from __future__ import annotations
import json, re, sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "docs" / "governance" / "document-registry.jsonl"

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

VALID_DOC_TYPES = {"root_context", "ai_onboarding", "phase_boundary", "architecture",
    "design_spec", "runbook", "receipt", "stage_summit", "red_team",
    "ledger", "tracker", "schema", "governance_pack", "runtime",
    "product", "template", "tooling"}
VALID_AUTHORITIES = {"source_of_truth", "current_status", "supporting_evidence",
    "historical_record", "proposal", "example", "archive", "derived_from_registry"}
REQUIRED_FIELDS = {"doc_id", "path", "doc_type", "status", "authority"}
DANGEROUS = [
    (re.compile(r"active policy", re.I), "claims 'active policy' — policy activation NO-GO"),
    (re.compile(r"live trading", re.I), "claims 'live trading' — Phase 8 DEFERRED"),
]

def run():
    errors, stats = [], {"total_entries": 0, "missing_files": 0, "stale_entries": 0}
    if not REGISTRY_PATH.exists():
        return CheckerResult("fail", 1, [f"Missing: {REGISTRY_PATH}"], stats)
    entries = []
    with open(REGISTRY_PATH) as f:
        for i, line in enumerate(f, 1):
            if not (line := line.strip()): continue
            try: entries.append(json.loads(line))
            except json.JSONDecodeError as e: errors.append(f"Line {i}: invalid JSON: {e}")
    stats["total_entries"] = len(entries)
    ids = set()
    for e in entries:
        did = e.get("doc_id", "?")
        if m := REQUIRED_FIELDS - set(e.keys()): errors.append(f"{did}: missing {m}")
        if did in ids: errors.append(f"{did}: duplicate")
        ids.add(did)
        if e.get("doc_type","") not in VALID_DOC_TYPES: errors.append(f"{did}: bad doc_type")
        if e.get("authority","") not in VALID_AUTHORITIES: errors.append(f"{did}: bad authority")
        if e.get("status") == "stale": stats["stale_entries"] += 1
        if (p := e.get("path","")) and not (ROOT / p).exists(): stats["missing_files"] += 1; errors.append(f"{did}: missing file {p}")
        for pr, desc in DANGEROUS:
            for fld in ("title","notes"):
                if pr.search(str(e.get(fld,""))): errors.append(f"{did}: {desc}")
    return CheckerResult("fail" if errors else "pass", 1 if errors else 0, errors, dict(stats))

if __name__ == "__main__":
    r = run()
    print(f"  Entries: {r.stats.get('total_entries',0)} | Violations: {len(r.findings)}")
    for f in r.findings: print(f"    {f}")
    sys.exit(r.exit_code)
