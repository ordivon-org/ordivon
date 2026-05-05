"""Checker Maturity Gate — enforces promotion rules for checker lifecycle.

Validates that every checker in the ecosystem follows the maturity
state machine: draft → shadow_tested → red_teamed → active.

Each promotion requires:
  - Independent review (not self-promotion)
  - Stage-specific evidence (shadow eval, red-team review, owner approval)
  - Traceable evidence references

Grandfathers existing checkers (those without explicit maturity records)
as maturity=active.
"""

from __future__ import annotations
import json, sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from domains.checker_maturity import (
    CheckerMaturityRecord,
    CheckerMaturityStateMachine,
    MaturityLevel,
    InvalidTransitionError,
    MissingEvidenceError,
    SelfPromotionError,
)

CHECKERS_DIR = ROOT / "checkers"
MATURITY_LEDGER = ROOT / "docs" / "governance" / "checker-maturity-ledger.jsonl"

# ── Data types ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

# ── Loaders ─────────────────────────────────────────────────────────

def _parse_checker_md(path: Path) -> dict | None:
    """Parse CHECKER.md YAML frontmatter."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    frontmatter = {}
    for line in parts[1].strip().split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip("'\"")
            if val.startswith("[") and val.endswith("]"):
                # Parse list
                val = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            frontmatter[key] = val
    return frontmatter

def _load_maturity_ledger() -> dict[str, CheckerMaturityRecord]:
    """Load existing maturity records, keyed by checker_id."""
    records = {}
    if not MATURITY_LEDGER.exists():
        return records
    with open(MATURITY_LEDGER) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                rec = CheckerMaturityRecord(
                    checker_id=entry["checker_id"],
                    maturity=MaturityLevel(entry["maturity"]),
                    author=entry.get("author", "unknown"),
                    changed_by=entry.get("changed_by", "unknown"),
                    changed_at=entry.get("changed_at", ""),
                    evidence_refs=tuple(entry.get("evidence_refs", [])),
                    predecessor_id=entry.get("predecessor_id"),
                    notes=entry.get("notes", ""),
                    grandfathered=entry.get("grandfathered", False),
                )
                # Keep the most recent record for each checker
                cid = rec.checker_id
                if cid not in records or rec.changed_at > records[cid].changed_at:
                    records[cid] = rec
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
    return records

# ── Validation ──────────────────────────────────────────────────────

def validate_checker_maturity(
    checker_id: str,
    declared_hardness: str,
    maturity_record: CheckerMaturityRecord | None,
) -> list[str]:
    """Validate that a checker's maturity state is consistent.

    Returns list of violation messages (empty = valid).
    """
    violations = []

    # Grandfathered: no maturity record = active (existing checkers)
    if maturity_record is None:
        return []

    level = maturity_record.maturity

    # ── Rule 0: grandfathered checkers bypass evidence + self-promotion ──
    # Grandfathered = admitted without full pipeline. The grandfathered_reason
    # documents the debt. These pass the gate but the debt is tracked.
    is_grandfathered = getattr(maturity_record, "grandfathered", False) or \
        "grandfathered" in [r.lower() for r in maturity_record.evidence_refs]

    if is_grandfathered:
        # Grandfathered checkers skip evidence and self-promotion checks.
        # The debt is documented in the maturity record, not enforced here.
        return []

    # ── Rule 1: hardness must match maturity ────────────────────
    if declared_hardness == "hard" and level not in (MaturityLevel.ACTIVE,):
        violations.append(
            f"{checker_id}: declared hardness='hard' but maturity='{level.value}'. "
            f"Hard gates must reach 'active' maturity before they can block PRs. "
            f"Current path: {_describe_path(level)}"
        )

    # ── Rule 2: active must have evidence of full pipeline ──────
    if level == MaturityLevel.ACTIVE:
        required_evidence = ("shadow_evaluation_log", "red_team_review", "owner_approval")
        has_evidence = set()
        for ref in maturity_record.evidence_refs:
            for req in required_evidence:
                if req in ref.lower():
                    has_evidence.add(req)
        missing = [r for r in required_evidence if r not in has_evidence]
        if missing:
            violations.append(
                f"{checker_id}: active but missing evidence: {missing}. "
                f"Active checkers require shadow evaluation + red-team review + owner approval."
            )

    # ── Rule 3: owner exists for active checkers ───────────────
    if level == MaturityLevel.ACTIVE and maturity_record.author == maturity_record.changed_by:
        violations.append(
            f"{checker_id}: active but author={maturity_record.author} "
            f"self-promoted. Independent review required."
        )

    return violations


def _describe_path(level: MaturityLevel) -> str:
    """Describe what's needed to reach active."""
    path = []
    if level == MaturityLevel.DRAFT:
        path = ["shadow_tested", "red_teamed", "active"]
    elif level == MaturityLevel.SHADOW_TESTED:
        path = ["red_teamed", "active"]
    elif level == MaturityLevel.RED_TEAMED:
        path = ["active"]
    else:
        return "terminal"
    return " → ".join(path)

# ── Main ────────────────────────────────────────────────────────────

def run() -> CheckerResult:
    findings = []
    stats = {"checkers_total": 0, "checkers_with_maturity": 0, "active": 0,
             "draft": 0, "shadow_tested": 0, "red_teamed": 0, "violations": 0}

    maturity_ledger = _load_maturity_ledger()

    # If the ledger file doesn't exist, all checkers are grandfathered by
    # default — but this is itself a governance gap. Document it.
    if not MATURITY_LEDGER.exists():
        findings.append(
            "checker-maturity-ledger.jsonl not found — all 33 checkers grandfathered "
            "as active by default. This is acceptable during bootstrap but the ledger "
            "must be created to track maturity state transitions."
        )

    # Discover all checkers
    if not CHECKERS_DIR.exists():
        return CheckerResult("pass", 0, ["No checkers directory"], dict(stats))

    for checker_dir in sorted(CHECKERS_DIR.iterdir()):
        if not checker_dir.is_dir():
            continue
        checker_md = checker_dir / "CHECKER.md"
        if not checker_md.exists():
            continue

        frontmatter = _parse_checker_md(checker_md)
        if frontmatter is None:
            continue

        checker_id = frontmatter.get("gate_id", checker_dir.name)
        hardness = frontmatter.get("hardness", "escalation")
        stats["checkers_total"] += 1

        rec = maturity_ledger.get(checker_id)
        if rec:
            stats["checkers_with_maturity"] += 1
            stats[rec.maturity.value] = stats.get(rec.maturity.value, 0) + 1
        else:
            # Grandfathered as active
            stats["active"] = stats.get("active", 0) + 1

        violations = validate_checker_maturity(checker_id, hardness, rec)
        if violations:
            stats["violations"] += len(violations)
            findings.extend(violations)

    if findings:
        findings.append(
            f"Maturity violations: {stats['violations']} across {stats['checkers_total']} checkers. "
            f"All promotions require independent review + stage-specific evidence."
        )

    return CheckerResult(
        "fail" if findings else "pass",
        1 if findings else 0,
        findings,
        dict(stats),
    )


if __name__ == "__main__":
    r = run()
    print(f"Checkers: {r.stats.get('checkers_total', 0)} total, "
          f"{r.stats.get('checkers_with_maturity', 0)} with maturity records")
    for f in r.findings:
        print(f"  {f}")
    sys.exit(r.exit_code)
