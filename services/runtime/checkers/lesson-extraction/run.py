"""Lesson → CandidateRule Extraction — closes the learning loop.

Scans lesson-ledger.jsonl for rule_candidate lessons, extracts CandidateRule
drafts, and tracks idempotency (same lesson never creates duplicate).

Output: candidate-rule-drafts.jsonl with extracted rules for human review.
"""

from __future__ import annotations
import json, sys, hashlib
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
LESSON_LEDGER = ROOT / "docs" / "governance" / "lesson-ledger.jsonl"
DRAFT_OUTPUT = ROOT / "docs" / "governance" / "candidate-rule-drafts.jsonl"
EXTRACTION_LOG = ROOT / "docs" / "governance" / "lesson-extraction-log.jsonl"

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _hash_lesson_id(lesson_id: str) -> str:
    """Deterministic draft ID from lesson ID — ensures idempotency."""
    return f"CR-{hashlib.md5(lesson_id.encode()).hexdigest()[:12]}"

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

def load_lessons() -> list[dict]:
    if not LESSON_LEDGER.exists():
        return []
    entries = []
    with open(LESSON_LEDGER) as f:
        for line in f:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries

def load_existing_drafts() -> dict[str, dict]:
    """Load existing drafts keyed by lesson_id for idempotency."""
    if not DRAFT_OUTPUT.exists():
        return {}
    drafts = {}
    with open(DRAFT_OUTPUT) as f:
        for line in f:
            if line.strip():
                try:
                    d = json.loads(line)
                    lid = d.get("source_lesson_id", "")
                    if lid:
                        drafts[lid] = d
                except json.JSONDecodeError:
                    pass
    return drafts

def load_extraction_log() -> set[str]:
    """Load set of already-extracted lesson IDs."""
    if not EXTRACTION_LOG.exists():
        return set()
    extracted = set()
    with open(EXTRACTION_LOG) as f:
        for line in f:
            if line.strip():
                try:
                    e = json.loads(line)
                    extracted.add(e.get("lesson_id", ""))
                except json.JSONDecodeError:
                    pass
    return extracted

def extract_candidate_rules() -> tuple[list[dict], dict]:
    """Extract CandidateRule drafts from rule_candidate lessons.

    Returns (new_drafts, stats).
    """
    lessons = load_lessons()
    existing = load_existing_drafts()
    already_extracted = load_extraction_log()
    new_drafts: list[dict] = []
    stats = {
        "total_lessons": len(lessons),
        "rule_candidates": 0,
        "new_drafts": 0,
        "skipped_duplicate": 0,
        "skipped_not_candidate": 0,
    }

    for lesson in lessons:
        lesson_id = lesson.get("lesson_id", "")
        lesson_type = lesson.get("lesson_type", "review_learning")

        if lesson_type != "rule_candidate":
            stats["skipped_not_candidate"] += 1
            continue

        stats["rule_candidates"] += 1

        # Idempotency: already extracted?
        if lesson_id in already_extracted or lesson_id in existing:
            stats["skipped_duplicate"] += 1
            continue

        # Build CandidateRule draft
        draft = {
            "candidate_rule_id": _hash_lesson_id(lesson_id),
            "source_lesson_id": lesson_id,
            "status": "draft",
            "summary": lesson.get("body", "")[:500],
            "tags": lesson.get("tags", []),
            "source_checker": lesson.get("source_checker", ""),
            "source_phase": lesson.get("source_phase", ""),
            "evidence_count": lesson.get("evidence_count", 0),
            "severity": lesson.get("severity", "medium"),
            "source_refs": [
                f"lesson:{lesson_id}",
                f"checker:{lesson.get('source_checker', '')}",
                f"phase:{lesson.get('source_phase', '')}",
            ],
            "extracted_at": _now_iso(),
            "review_status": "pending_review",
        }
        new_drafts.append(draft)

    stats["new_drafts"] = len(new_drafts)
    return new_drafts, stats

def run() -> CheckerResult:
    drafts, stats = extract_candidate_rules()

    findings = []
    if drafts:
        # Append new drafts to output file
        mode = "a" if DRAFT_OUTPUT.exists() else "w"
        with open(DRAFT_OUTPUT, mode) as f:
            for d in drafts:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        # Log extraction
        mode = "a" if EXTRACTION_LOG.exists() else "w"
        with open(EXTRACTION_LOG, mode) as f:
            for d in drafts:
                f.write(json.dumps({
                    "lesson_id": d["source_lesson_id"],
                    "candidate_rule_id": d["candidate_rule_id"],
                    "extracted_at": d["extracted_at"],
                }, ensure_ascii=False) + "\n")

        findings.append(f"Extracted {len(drafts)} new CandidateRule draft(s)")
        for d in drafts:
            findings.append(f"  {d['candidate_rule_id']}: {d['summary'][:120]}...")

    if stats["rule_candidates"] > 0 and stats["new_drafts"] == 0:
        findings.append("All rule_candidate lessons already extracted (idempotent)")

    return CheckerResult(
        "pass",
        0,
        findings,
        dict(stats),
    )

if __name__ == "__main__":
    r = run()
    s = r.stats
    print(f"Lessons: {s.get('total_lessons',0)} total, {s.get('rule_candidates',0)} rule_candidates")
    print(f"Extracted: {s.get('new_drafts',0)} new, {s.get('skipped_duplicate',0)} skipped (duplicate)")
    for f in r.findings: print(f"  {f}")
    sys.exit(r.exit_code)
