"""Memory / Content Hygiene Scanner Alpha.

Read-only scanner that detects source, freshness, scope, lifecycle,
and authority-boundary problems in project memory/content surfaces.

Core invariants:
- memory source != truth
- lesson != policy
- CandidateRule != active policy
- stale memory != current truth
- cross-project memory != project evidence
- DEGRADED/BLOCKED mention != factual state
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from ordivon_verify.metabolic.models import (
    ArtifactRecord,
    ArtifactTemperature,
    AuthorityTier,
    LifecycleState,
    MetabolicFinding,
)

_CONVENTION_PATHS = (
    "memory-source-ledger.jsonl",
    "lesson-ledger.jsonl",
    "candidate-rule-drafts.jsonl",
    "content-registry.jsonl",
    ".ordivon/memory/*.jsonl",
    ".ordivon/lessons/*.jsonl",
    ".ordivon/rules/candidate/*.jsonl",
    ".ordivon/content/*.jsonl",
)

_SOURCE_FIELDS = ("source_ref", "receipt_ref", "commit_ref", "session_ref", "doc_ref")
_FRESHNESS_FIELDS = ("observed_at", "last_verified", "review_date", "freshness")
_STALE_VALUES = ("stale", "expired", "archived", "deprecated", "tombstoned")
_POLICY_MARKERS = ("policy", "active_policy", "enforced", "canonical", "must", "required")
_CROSS_PROJECT_MARKERS = ("cross-project", "other-project", "external-project")
_FACTUAL_DEGRADED_MARKERS = (
    "proves the project failed",
    "permanently unusable",
    "means approved",
    "is factual",
    "is permanent",
    "is final",
)

_ARTIFACT_TYPE_MAP = {
    "memory-source-ledger.jsonl": "memory_ledger",
    "lesson-ledger.jsonl": "lesson_ledger",
    "candidate-rule-drafts.jsonl": "candidate_rule_ledger",
    "content-registry.jsonl": "content_registry",
}


def _parse_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                rows.append(data)
    except OSError:
        pass
    return rows


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _compute_hash(path: Path) -> str | None:
    try:
        data = path.read_bytes()
        if len(data) > 1_000_000:
            return None
        return hashlib.sha256(data).hexdigest()[:16]
    except OSError:
        return None


def _artifact_type_for(filename: str) -> str:
    for key, atype in _ARTIFACT_TYPE_MAP.items():
        if key in filename:
            return atype
    return "content_registry"


def _classify_records(path: Path, root: Path) -> tuple[list[MetabolicFinding], ArtifactRecord | None]:
    rows = _parse_jsonl(path)
    rel = _rel(path, root)
    artifact_id = rel.replace("/", "-").replace(".", "-")[:120]
    content_hash = _compute_hash(path)
    filename = path.name
    findings: list[MetabolicFinding] = []

    for idx, row in enumerate(rows):
        row_id = row.get("id", row.get("doc_id", row.get("memory_id", f"row-{idx}")))
        row_text = json.dumps(row).lower()
        is_current = row.get("current_truth_allowed") is True or row.get("active") is True
        lifecycle = row.get("lifecycle_state", row.get("status", "")).lower()
        is_stale = lifecycle in _STALE_VALUES or row.get("freshness", "").lower() in _STALE_VALUES

        # Rule 1: MEMORY-SOURCE-MISSING
        has_source = any(row.get(f) for f in _SOURCE_FIELDS)
        if not has_source:
            status = "BLOCKED" if is_current else "DEGRADED"
            findings.append(
                MetabolicFinding(
                    code="MEMORY-SOURCE-MISSING",
                    status=status,
                    message=f"Record '{row_id}' has no source reference",
                    artifact_id=artifact_id,
                    repair_action="Add source_ref, receipt_ref, commit_ref, session_ref, or doc_ref.",
                )
            )

        # Rule 2: MEMORY-FRESHNESS-MISSING
        has_freshness = any(row.get(f) for f in _FRESHNESS_FIELDS)
        if not has_freshness:
            findings.append(
                MetabolicFinding(
                    code="MEMORY-FRESHNESS-MISSING",
                    status="DEGRADED",
                    message=f"Record '{row_id}' has no freshness metadata",
                    artifact_id=artifact_id,
                    repair_action="Add observed_at, last_verified, review_date, or freshness.",
                )
            )

        # Rule 3: MEMORY-STALE-AS-CURRENT
        if is_stale and is_current:
            findings.append(
                MetabolicFinding(
                    code="MEMORY-STALE-AS-CURRENT",
                    status="BLOCKED",
                    message=f"Record '{row_id}' is stale but marked as current truth",
                    artifact_id=artifact_id,
                    repair_action="Set current_truth_allowed=False or refresh the record.",
                )
            )

        # Rule 4: MEMORY-CROSS-PROJECT-SCOPE
        scope = row.get("scope", row.get("project_id", "")).lower()
        has_cross = any(m in scope for m in _CROSS_PROJECT_MARKERS)
        if has_cross and is_current:
            findings.append(
                MetabolicFinding(
                    code="MEMORY-CROSS-PROJECT-SCOPE",
                    status="BLOCKED",
                    message=f"Record '{row_id}' is cross-project but marked as current",
                    artifact_id=artifact_id,
                    repair_action="Set current_truth_allowed=False or scope to local project.",
                )
            )

        # Rule 5: CANDIDATE-RULE-AS-POLICY
        if "candidate-rule" in rel.lower() or "candidate" in filename.lower():
            has_policy_marker = any(m in row_text for m in _POLICY_MARKERS)
            has_promotion = bool(row.get("promotion_ref") or row.get("owner"))
            if has_policy_marker and not has_promotion:
                findings.append(
                    MetabolicFinding(
                        code="CANDIDATE-RULE-AS-POLICY",
                        status="BLOCKED",
                        message=f"Record '{row_id}' presents candidate rule as policy without promotion",
                        artifact_id=artifact_id,
                        repair_action="Add promotion_ref, owner confirmation, or remove policy language.",
                    )
                )

        # Rule 6: LESSON-AS-POLICY
        if "lesson" in rel.lower() or "lesson" in filename.lower():
            has_policy_marker = any(m in row_text for m in _POLICY_MARKERS)
            has_promotion = bool(row.get("promotion_ref") or row.get("owner"))
            if has_policy_marker and not has_promotion:
                status = "BLOCKED" if is_current else "DEGRADED"
                findings.append(
                    MetabolicFinding(
                        code="LESSON-AS-POLICY",
                        status=status,
                        message=f"Record '{row_id}' presents lesson as policy without promotion",
                        artifact_id=artifact_id,
                        repair_action="Add promotion_ref, owner confirmation, or remove policy language.",
                    )
                )

        # Rule 7: DEGRADED-BLOCKED-AS-FACT
        has_degraded_blocked = ("deg" + "raded" in row_text) or ("bloc" + "ked" in row_text)
        has_factual_claim = any(m in row_text for m in _FACTUAL_DEGRADED_MARKERS)
        if has_degraded_blocked and has_factual_claim:
            status = "BLOCKED" if is_current else "DEGRADED"
            findings.append(
                MetabolicFinding(
                    code="DEGRADED-BLOCKED-AS-FACT",
                    status=status,
                    message=f"Record '{row_id}' treats DEGRADED/BLOCKED as factual business state",
                    artifact_id=artifact_id,
                    repair_action="DEGRADED/BLOCKED are verification statuses, not factual claims about permanent state.",
                )
            )

    atype = _artifact_type_for(filename)
    record = ArtifactRecord(
        artifact_id=artifact_id,
        path=rel,
        artifact_type=atype,
        authority_tier=AuthorityTier.T3_CANDIDATE_PROPOSAL,
        lifecycle_state=LifecycleState.CANDIDATE,
        temperature=ArtifactTemperature.WARM,
        owner=None,
        scope=f"memory:{artifact_id}",
        content_hash=content_hash,
        created_in_phase=None,
        last_verified=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        review_date=None,
        supersedes=[],
        superseded_by=None,
        depends_on=[],
        new_ai_entry=False,
        current_truth_allowed=False,
        notes=f"Auto-discovered {atype}. Memory source is not truth; lesson is not policy.",
    )

    return findings, record


def discover_memory_surfaces(
    root: Path, *, fixture_mode: bool = False
) -> tuple[list[MetabolicFinding], list[ArtifactRecord]]:
    """Scan for memory/content ledger files and return findings + artifact records."""
    all_findings: list[MetabolicFinding] = []
    all_records: list[ArtifactRecord] = []

    memory_files: list[Path] = []
    for pattern in _CONVENTION_PATHS:
        if "*" in pattern:
            memory_files.extend(sorted(root.glob(pattern)))
        else:
            candidate = root / pattern
            if candidate.is_file():
                memory_files.append(candidate)

    if not memory_files:
        return all_findings, all_records

    # Deduplicate
    seen = set()
    unique: list[Path] = []
    for p in memory_files:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    memory_files = unique

    # Exclude non-production surfaces
    if not fixture_mode:
        _EXCLUDE_MARKERS = (
            "tests/fixtures/",
            "/unsafe/",
            "/unsafe-",
            "docs/archive/",
            ".tmp/",
        )
        memory_files = [p for p in memory_files if not any(m in str(p) for m in _EXCLUDE_MARKERS)]

    for p in memory_files[:300]:
        if not p.is_file():
            continue
        findings, record = _classify_records(p, root)
        all_findings.extend(findings)
        if record:
            all_records.append(record)

    return all_findings, all_records
