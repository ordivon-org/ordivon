#!/usr/bin/env python3
"""Phase DG-4: Document Registry Consistency Checker with Freshness + Semantic Checks.

Reads docs/governance/document-registry.jsonl and verifies core document
governance invariants including freshness windows and semantic phrase checks.
Never calls Alpaca. Never requires API keys. Read-only evidence validation.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs" / "governance" / "document-registry.jsonl"
EXCLUSIONS_PATH = ROOT / "docs" / "governance" / "document-registry-exclusions.json"

# ── Discoverable paths for completeness check ─────────────────────────
DISCOVERABLE_DIRS = [
    "docs/ai",
    "docs/governance",
    "docs/product",
    "docs/architecture",
    "docs/runtime",
]

# ── Identity-bearing surfaces ─────────────────────────────────────────
IDENTITY_SURFACES = {
    "pyproject.toml": {"field": "project.name", "must_not_contain": ["pfios"]},
    "package.json": {"field": "name", "must_not_contain": ["pfios"]},
    "apps/web/package.json": {"field": "name", "must_not_contain": ["pfios"]},
    "apps/api/pyproject.toml": {"field": "project.name", "must_not_contain": ["pfios"]},
}

# ── Deterministic reference date for testing ──────────────────────────
# Set REFERENCE_DATE env var for deterministic staleness checks.
# Format: YYYY-MM-DD. Defaults to today if not set.
_REF_DATE = os.environ.get("REFERENCE_DATE", "")
REFERENCE_DATE = date.fromisoformat(_REF_DATE) if _REF_DATE else date.today()

# ── Valid values from governance docs ──────────────────────────────────

VALID_DOC_TYPES = {
    "root_context",
    "ai_onboarding",
    "phase_boundary",
    "architecture",
    "design_spec",
    "runbook",
    "receipt",
    "stage_summit",
    "red_team",
    "ledger",
    "tracker",
    "schema",
    "template",
    "adr",
    "archive_index",
    "product",
    "runtime",
    "governance_pack",
}

VALID_STATUSES = {
    "draft",
    "proposed",
    "current",
    "accepted",
    "implemented",
    "closed",
    "deferred",
    "superseded",
    "archived",
    "stale",
}

ACTIVE_STATUSES = {"current", "accepted", "implemented"}

VALID_AUTHORITIES = {
    "source_of_truth",
    "current_status",
    "supporting_evidence",
    "historical_record",
    "proposal",
    "example",
    "archive",
}

DECISION_AUTHORITIES = {"source_of_truth", "current_status"}

HIGH_PRIORITY_AI_READ = {0, 1}
LOW_PRIORITY_AI_READ = {4}

# Ordivon structural layers (from Core/Pack/Adapter ontology)
VALID_STRUCTURAL_LAYERS = {
    "core",
    "pack",
    "adapter",
    "surface",
    "checker",
    "ledger",
    "registry",
    "governance_plane",
    "knowledge_harness",
    "external_harness",
}

# Ordivon governance planes (from Core/Pack/Adapter ontology)
VALID_GOVERNANCE_PLANES = {
    "evidence_state",
    "authority_policy",
    "verification_safety",
    "orchestration_lifecycle",
    "knowledge_documentation",
    "risk_side_effect",
    "actor_trust",
    "surface_representation",
}

NEVER_STALE_TYPES = {"root_context", "phase_boundary", "ai_onboarding"}
NEVER_ARCHIVE_TYPES = {"root_context", "phase_boundary", "ai_onboarding"}

# Critical AI doc IDs that must have freshness metadata
CRITICAL_AI_DOCS = {"agents-md", "ai-readme", "phase-boundaries", "agent-output-contract", "ordivon-root-context"}

# Documents whose content will be scanned for semantic phrase checks
# Only current/accepted status docs are scanned (archived/closed docs exempt)
SEMANTIC_SCAN_STATUSES = {"current", "accepted"}

# ── Dangerous phrases that must never appear in current docs ──────────

# Format: (compiled_regex, error_template)
# Each regex will be checked against line-by-line content.
# Safe negations (NOT, NO-GO, DEFERRED, BLOCKED) are excluded.

DANGEROUS_PHRASES: list[tuple[re.Pattern, str]] = [
    (
        re.compile(
            r"(?:phase\s*8\s+(?:is\s+)?active|phase\s*8\s+(?:is\s+)?enabled"
            r"|Phase\s*8\s+ACTIVE)",
            re.IGNORECASE,
        ),
        "Phase 8 described as active/enabled",
    ),
    (
        re.compile(
            r"live\s+trading\s+(?:is\s+)?(?:\w+\s+)?(?:active|enabled)",
            re.IGNORECASE,
        ),
        "live trading described as active/enabled",
    ),
    (
        re.compile(
            r"CandidateRule\s+(?:is\s+)?Policy",
            re.IGNORECASE,
        ),
        "CandidateRule described as Policy",
    ),
    (
        re.compile(
            r"CandidateRule\s+(?:is\s+)?(?:active|enforced|activated)",
            re.IGNORECASE,
        ),
        "CandidateRule described as active/enforced",
    ),
    (
        re.compile(
            r"ledger\s+(?:authorizes|is\s+execution\s+authority|is\s+an\s+execution\s+authority)",
            re.IGNORECASE,
        ),
        "ledger described as execution authority",
    ),
    (
        re.compile(
            r"(?:Phase\s*6\s+(?:is\s+)?ACTIVE|Phase\s*6\s+ACTIVE)",
        ),
        "Phase 6 described as ACTIVE (should be COMPLETE)",
    ),
]

# ── Context-safe negations that override dangerous phrase matches ─────
SAFE_NEGATIONS: list[re.Pattern] = [
    re.compile(r"NOT\s+Policy", re.IGNORECASE),
    re.compile(r"advisory\s+only", re.IGNORECASE),
    re.compile(r"NO-GO", re.IGNORECASE),
    re.compile(r"DEFERRED", re.IGNORECASE),
    re.compile(r"BLOCKED", re.IGNORECASE),
    re.compile(r"not\s+execution\s+authority", re.IGNORECASE),
    re.compile(r"evidence,\s+not", re.IGNORECASE),
    re.compile(r"remain(?:s)?\s+deferred", re.IGNORECASE),
]


def load_registry(path: Path) -> list[dict]:
    """Load entries from JSONL."""
    entries = []
    with open(path) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"ERROR line {i}: invalid JSON: {e}")
                sys.exit(1)
    return entries


def load_exclusions(path: Path) -> dict:
    """Load exclusion entries. Returns dict with 'entries' key or empty list."""
    if not path.exists():
        return {"entries": []}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception) as e:
        print(f"WARNING: could not load exclusions: {e}")
        return {"entries": []}


def check_completeness(entries: list[dict], exclusions: dict) -> list[str]:
    """Discover .md files under DOCS_PATH, check each is registered or excluded."""
    errors: list[str] = []
    registered_paths = {e.get("path", "") for e in entries}
    registered_paths.discard("")
    excluded_entries = exclusions.get("entries", [])
    excluded_paths = {x.get("path", "") for x in excluded_entries}
    excluded_paths.discard("")

    discovered = 0
    registered_count = 0
    excluded_count = 0

    for d in DISCOVERABLE_DIRS:
        dir_path = ROOT / d
        if not dir_path.is_dir():
            continue
        for md_file in sorted(dir_path.rglob("*.md")):
            # Skip archive directory
            if "docs/archive" in str(md_file.relative_to(ROOT)):
                continue
            rel = str(md_file.relative_to(ROOT))
            discovered += 1

            if rel in registered_paths:
                registered_count += 1
                continue
            if rel in excluded_paths:
                # Verify exclusion has required fields
                excl = next(x for x in excluded_entries if x.get("path") == rel)
                if not excl.get("reason"):
                    errors.append(f"{rel}: excluded but missing 'reason'")
                if not excl.get("classification"):
                    errors.append(f"{rel}: excluded but missing 'classification'")
                excluded_count += 1
                continue

            errors.append(
                f"{rel}: unregistered current-scope doc — must be registered in "
                "document-registry.jsonl, moved to docs/archive/, or listed in "
                "document-registry-exclusions.json with a valid reason"
            )

    return errors


def check_identity_surfaces() -> list[str]:
    """Validate identity-bearing config files do not carry legacy PFIOS identity."""
    errors: list[str] = []

    # pyproject.toml
    ppt = ROOT / "pyproject.toml"
    if ppt.exists():
        try:
            content = ppt.read_text()
            if 'name = "pfios"' in content or "name = 'pfios'" in content:
                errors.append("pyproject.toml: project name is 'pfios' — must be 'ordivon'")
        except Exception:
            pass

    # package.json (root)
    pj = ROOT / "package.json"
    if pj.exists():
        try:
            data = json.loads(pj.read_text())
            name = data.get("name", "")
            if "pfios" in name.lower():
                errors.append(f"package.json: name '{name}' contains 'pfios' — must be 'ordivon'")
        except Exception:
            pass

    # README.md current identity
    readme = ROOT / "README.md"
    if readme.exists():
        try:
            first_lines = readme.read_text().split("\n")[:5]
            header = "\n".join(first_lines)
            if "# Financial AI OS" in header or "AegisOS / CAIOS" in header:
                errors.append(
                    "README.md: opening identifies as 'Financial AI OS' or 'AegisOS' — "
                    "current project identity is Ordivon"
                )
        except Exception:
            pass

    # tests/conftest.py — must not globally set PFIOS_DB_URL unconditionally
    conftest = ROOT / "tests" / "conftest.py"
    if conftest.exists():
        try:
            text = conftest.read_text()
            # Check for unconditional global PFIOS_DB_URL=duckdb
            if "PFIOS_DB_URL" in text:
                if 'os.environ["PFIOS_DB_URL"]' in text:
                    if "tests/contracts" not in text and "tests/integration" not in text:
                        errors.append(
                            "tests/conftest.py: globally sets PFIOS_DB_URL without scoping "
                            "to legacy test paths — must be scoped or removed"
                        )
        except Exception:
            pass

    return errors


def _line_is_safe(line: str) -> bool:
    """Check if a line contains a safe negation context."""
    for neg in SAFE_NEGATIONS:
        if neg.search(line):
            return True
    return False


def check_semantic_phrases(entries: list[dict]) -> list[str]:
    """Scan file contents of registered current docs for dangerous phrases."""
    errors: list[str] = []
    scanned_count = 0

    for e in entries:
        did = e.get("doc_id", "")
        status = e.get("status", "")
        path_str = e.get("path", "")

        if not path_str or status not in SEMANTIC_SCAN_STATUSES:
            continue

        full_path = ROOT / path_str
        if not full_path.exists() or full_path.suffix != ".md":
            continue

        try:
            content = full_path.read_text()
        except Exception:
            continue

        scanned_count += 1
        lines = content.split("\n")

        for pattern, desc in DANGEROUS_PHRASES:
            for i, line in enumerate(lines, 1):
                if pattern.search(line):
                    # Check for safe negation on same line or adjacent lines
                    ctx_start = max(0, i - 2)
                    ctx_end = min(len(lines), i + 2)
                    ctx_text = "\n".join(lines[ctx_start:ctx_end])
                    if _line_is_safe(ctx_text):
                        continue
                    errors.append(f"{did}:{i}: {desc} — '{line.strip()}'")

    return errors


def check_invariants(entries: list[dict]) -> list[str]:
    """Return list of invariant violations."""
    errors: list[str] = []
    ids: set[str] = set()

    REQUIRED_FIELDS = {
        "doc_id",
        "path",
        "title",
        "doc_type",
        "status",
        "authority",
        "phase",
        "owner",
        "freshness",
        "ai_read_priority",
        "supersedes",
        "superseded_by",
        "related_docs",
        "related_ledgers",
        "related_receipts",
        "notes",
    }

    for e in entries:
        did = e.get("doc_id", f"<missing doc_id at index {entries.index(e)}>")

        # --- Required fields ---
        missing = REQUIRED_FIELDS - set(e.keys())
        if missing:
            errors.append(f"{did}: missing required fields: {missing}")

        # --- Unique doc_id ---
        if did in ids:
            errors.append(f"{did}: duplicate doc_id")
        ids.add(did)

        # --- doc_type ---
        dt = e.get("doc_type", "")
        if dt not in VALID_DOC_TYPES:
            errors.append(f"{did}: invalid doc_type '{dt}'")
        if not dt:
            continue

        # --- status ---
        status = e.get("status", "")
        if status not in VALID_STATUSES:
            errors.append(f"{did}: invalid status '{status}'")

        # --- authority ---
        authority = e.get("authority", "")
        if authority not in VALID_AUTHORITIES:
            errors.append(f"{did}: invalid authority '{authority}'")

        # --- path must exist ---
        path_str = e.get("path", "")
        if path_str:
            full_path = ROOT / path_str
            if not full_path.exists():
                errors.append(f"{did}: registered path does not exist: {path_str}")

        # --- ai_read_priority ---
        priority = e.get("ai_read_priority")
        if priority is not None and (not isinstance(priority, int) or priority not in (0, 1, 2, 3, 4)):
            errors.append(f"{did}: invalid ai_read_priority '{priority}'")

        # --- Freshness metadata: high-priority AI docs must have last_verified ---
        if did in CRITICAL_AI_DOCS:
            lv = e.get("last_verified")
            if not lv:
                errors.append(f"{did}: critical AI doc missing last_verified field")
            else:
                # Staleness window check
                stale_days = e.get("stale_after_days")
                if stale_days is not None and isinstance(stale_days, (int, float)):
                    try:
                        verified_date = date.fromisoformat(lv)
                        age_days = (REFERENCE_DATE - verified_date).days
                        if age_days > stale_days:
                            errors.append(
                                f"{did}: stale — last_verified={lv} ({age_days}d ago), stale_after_days={stale_days}"
                            )
                    except (ValueError, TypeError):
                        errors.append(f"{did}: invalid last_verified date format '{lv}'")

        # --- source_of_truth docs cannot be stale/archived ---
        if authority == "source_of_truth" and status in ("stale", "archived"):
            errors.append(f"{did}: source_of_truth doc has status '{status}' — must be current")

        # --- root_context / phase_boundary cannot be stale ---
        if dt in NEVER_STALE_TYPES and status == "stale":
            errors.append(f"{did}: {dt} doc has status 'stale' — governance incident")

        # --- root_context / phase_boundary / ai_onboarding cannot be archived ---
        if dt in NEVER_ARCHIVE_TYPES and status == "archived":
            errors.append(f"{did}: {dt} doc has status 'archived' — never archived while project active")

        # --- Archived docs cannot be high-priority AI read ---
        if status == "archived" and priority in HIGH_PRIORITY_AI_READ:
            errors.append(f"{did}: archived doc has AI read priority {priority} — should be level 4")

        # --- Ledger docs must be supporting_evidence, not source_of_truth ---
        if dt == "ledger" and authority == "source_of_truth":
            errors.append(f"{did}: ledger doc has authority 'source_of_truth' — must be 'supporting_evidence'")

        # --- Paper dogfood ledger: evidence, NOT execution authority ---
        if "paper-dogfood-ledger" in did.lower() and dt == "ledger":
            notes = e.get("notes", "")
            if "execution authority" in notes.lower() and "not" not in notes.lower():
                errors.append(f"{did}: paper dogfood ledger described as execution authority")
            if "evidence" not in notes.lower():
                errors.append(f"{did}: paper dogfood ledger must be labeled as evidence")

        # --- CandidateRule docs must not be marked Policy / active authority ---
        if "candidate" in did.lower() or "candidate" in e.get("title", "").lower():
            if authority in DECISION_AUTHORITIES and dt != "root_context":
                errors.append(
                    f"{did}: CandidateRule doc has authority '{authority}' — "
                    "must be 'supporting_evidence' or 'proposal', NOT 'source_of_truth'/'current_status'"
                )
            notes = e.get("notes", "").lower()
            if "policy" in notes and "not policy" not in notes:
                errors.append(f"{did}: CandidateRule doc may describe itself as Policy")

        # --- Phase 8 docs must remain deferred ---
        if "phase-8" in did.lower() or "phase 8" in e.get("title", "").lower():
            if status not in ("deferred", "closed", "archived"):
                errors.append(f"{did}: Phase 8 doc has status '{status}' — must remain deferred")

        # --- Trackers referencing Phase 8 must be deferred ---
        if dt == "tracker" and "phase-8" in did.lower():
            if status != "deferred":
                errors.append(f"{did}: Phase 8 tracker must be deferred, got '{status}'")

    # --- Structural layers / governance planes validation ---
    for e in entries:
        did = e.get("doc_id", "")
        sl = e.get("structural_layers")
        gp = e.get("governance_planes")

        if sl is not None:
            if not isinstance(sl, list):
                errors.append(f"{did}: structural_layers must be a list, got {type(sl).__name__}")
            else:
                for v in sl:
                    if v not in VALID_STRUCTURAL_LAYERS:
                        errors.append(f"{did}: invalid structural_layer '{v}'")

        if gp is not None:
            if not isinstance(gp, list):
                errors.append(f"{did}: governance_planes must be a list, got {type(gp).__name__}")
            else:
                for v in gp:
                    if v not in VALID_GOVERNANCE_PLANES:
                        errors.append(f"{did}: invalid governance_plane '{v}'")

        # Architecture source_of_truth docs with ontology in path/title must have
        # structural_layers and governance_planes
        dt = e.get("doc_type", "")
        auth = e.get("authority", "")
        title = e.get("title", "").lower()
        path_s = e.get("path", "").lower()
        if dt == "architecture" and auth == "source_of_truth" and ("ontology" in title or "ontology" in path_s):
            if not sl:
                errors.append(f"{did}: ontology source_of_truth doc missing structural_layers")
            if not gp:
                errors.append(f"{did}: ontology source_of_truth doc missing governance_planes")

    # --- Supersedes / superseded_by references must resolve ---
    for e in entries:
        did = e.get("doc_id", "")
        for ref_field in ("supersedes", "superseded_by"):
            ref = e.get(ref_field)
            if ref and ref not in ids:
                errors.append(f"{did}: {ref_field} references unknown doc_id '{ref}'")

    # --- Critical AI onboarding docs must be high-priority ---
    for e in entries:
        did = e.get("doc_id", "")
        if did in CRITICAL_AI_DOCS:
            priority = e.get("ai_read_priority")
            if priority not in (0, 1):
                errors.append(f"{did}: critical AI onboarding doc has priority {priority}, expected 0 or 1")

    # --- current-phase-boundaries must be source_of_truth ---
    for e in entries:
        if e.get("doc_id") == "phase-boundaries":
            if e.get("authority") != "source_of_truth":
                errors.append("phase-boundaries: must have authority 'source_of_truth'")

    # --- Semantic phrase checks on file contents ---
    phrase_errors = check_semantic_phrases(entries)
    errors.extend(phrase_errors)

    return errors


def print_summary(
    entries: list[dict], completeness_errors: list[str] = None, identity_errors: list[str] = None
) -> None:
    """Print compact registry summary."""
    type_counter = Counter(e.get("doc_type", "unknown") for e in entries)
    authority_counter = Counter(e.get("authority", "unknown") for e in entries)
    status_counter = Counter(e.get("status", "unknown") for e in entries)

    source_of_truth_count = authority_counter.get("source_of_truth", 0)
    current_status_count = authority_counter.get("current_status", 0)
    supporting_evidence_count = authority_counter.get("supporting_evidence", 0)
    archive_count = authority_counter.get("archive", 0)
    stale_count = status_counter.get("stale", 0)
    superseded_count = status_counter.get("superseded", 0)
    high_priority_count = sum(1 for e in entries if e.get("ai_read_priority") in HIGH_PRIORITY_AI_READ)
    # Count entries with last_verified
    has_lv = sum(1 for e in entries if e.get("last_verified"))
    has_stale_days = sum(1 for e in entries if e.get("stale_after_days") is not None)

    # Count current docs scanned for semantics
    scannable = sum(
        1
        for e in entries
        if e.get("status") in SEMANTIC_SCAN_STATUSES
        and e.get("path", "").endswith(".md")
        and (ROOT / e.get("path", "")).exists()
    )

    print("=" * 60)
    print("DOCUMENT REGISTRY SUMMARY")
    print("=" * 60)
    print(f"  Total registered docs:     {len(entries)}")
    print(f"  source_of_truth:           {source_of_truth_count}")
    print(f"  current_status:            {current_status_count}")
    print(f"  supporting_evidence:       {supporting_evidence_count}")
    print(f"  archive:                   {archive_count}")
    print(f"  stale + superseded:        {stale_count + superseded_count}")
    print(f"  High-priority AI read:     {high_priority_count}")
    print(f"  With last_verified:        {has_lv}")
    print(f"  With stale_after_days:     {has_stale_days}")
    print(f"  Semantic scan targets:     {scannable} (current/accepted .md)")
    print(f"  Doc types:                 {len(type_counter)}")
    print(f"  Statuses:                  {len(status_counter)}")
    if completeness_errors is not None:
        print(f"  Completeness violations:   {len(completeness_errors)}")
    if identity_errors is not None:
        print(f"  Identity surface violations: {len(identity_errors)}")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else REGISTRY_PATH
    if not path.exists():
        print(f"ERROR: registry not found at {path}")
        return 1

    entries = load_registry(path)
    errors = check_invariants(entries)

    # Completeness check — only on real registry (not temp test files)
    completeness_errors: list[str] = []
    identity_errors: list[str] = []
    if path == REGISTRY_PATH:
        exclusions = load_exclusions(EXCLUSIONS_PATH)
        completeness_errors = check_completeness(entries, exclusions)
        identity_errors = check_identity_surfaces()
        errors.extend(completeness_errors)
        errors.extend(identity_errors)

    if errors:
        print(f"\n❌ {len(errors)} INVARIANT VIOLATION(S):\n")
        for err in errors:
            print(f"  - {err}")
        print()
        return 1

    print_summary(entries, completeness_errors, identity_errors)
    print("\n✅ All document registry invariants pass (freshness + semantics + completeness + identity).\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
