"""Trace / Harness Evidence Import Scanner Alpha.

Fixture-only, read-only scanner for runtime evidence surfaces:
trace, checkpoint, tool call, and review record.

Core invariants:
- trace present != truth
- checkpoint exists != approval
- tool call success != safe action
- trace completeness != factual correctness
- review record != authorization
- review timing matters
- failed tool call must not disappear
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
    "trace.json",
    "checkpoint.json",
    "review-record.json",
    "trace-events.jsonl",
    "harness-trace.jsonl",
    ".ordivon/traces/*.json",
    ".ordivon/traces/*.jsonl",
    ".ordivon/checkpoints/*.json",
    ".ordivon/reviews/*.json",
)

_TRUTH_CLAIM_MARKERS = (
    "proves truth",
    "confirms factual",
    "canonical truth",
    "is truth",
    "is fact",
    "is correct",
)

_APPROVAL_MARKERS = (
    "approve",
    "authorize",
    "release ready",
    "merge permission",
    "safe to deploy",
)

_SAFE_ACTION_MARKERS = (
    "safe action",
    "approved action",
    "production ready",
    "safe to execute",
    "safe to run",
)

_SOURCE_FIELDS = ("reviewer", "source", "actor", "timestamp", "scope")

_ARTIFACT_TYPE_MAP = {
    "trace": "runtime_trace",
    "checkpoint": "checkpoint",
    "review-record": "review_record",
}


def _parse_json(path: Path) -> dict | list | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        return data
    except (json.JSONDecodeError, OSError):
        return None


def _parse_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped:
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
        if key in filename.lower():
            return atype
    return "runtime_trace"


def _flatten_text(data) -> str:
    """Recursively extract all string values from JSON as lowercase text."""
    if isinstance(data, str):
        return data.lower()
    if isinstance(data, dict):
        return " ".join(_flatten_text(v) for v in data.values())
    if isinstance(data, list):
        return " ".join(_flatten_text(v) for v in data)
    return ""


def _classify_trace(path: Path, root: Path) -> tuple[list[MetabolicFinding], ArtifactRecord | None]:
    data = _parse_json(path)
    if data is None:
        return [], None

    rel = _rel(path, root)
    artifact_id = rel.replace("/", "-").replace(".", "-")[:120]
    content_hash = _compute_hash(path)
    filename = path.name.lower()
    text = _flatten_text(data)

    findings: list[MetabolicFinding] = []

    # Determine if it's a trace, checkpoint, or review based on filename + content
    is_review = "review" in filename or "review" in str(data)[:200].lower()
    is_checkpoint = "checkpoint" in filename
    is_trace = not is_review and not is_checkpoint

    # Rule 1: TRACE-FAILED-TOOL-CALL-MISSING
    if is_trace:
        has_success_claim = "complete" in text or "success" in text or "passed" in text
        has_failure_surface = "fail" in text or "error" in text or "retry" in text
        if has_success_claim and not has_failure_surface:
            pass  # No failure detected
        if has_failure_surface:
            findings.append(
                MetabolicFinding(
                    code="TRACE-FAILED-TOOL-CALL-MISSING",
                    status="BLOCKED",
                    message="Trace claims success but contains failure/error/retry indicators without resolution",
                    artifact_id=artifact_id,
                    repair_action="Include failed tool calls in trace summary. Do not hide errors.",
                )
            )

    # Rule 2: TRACE-AS-TRUTH
    has_truth_claim = any(m in text for m in _TRUTH_CLAIM_MARKERS)
    if has_truth_claim:
        findings.append(
            MetabolicFinding(
                code="TRACE-AS-TRUTH",
                status="BLOCKED",
                message="Trace claims to prove truth or factual correctness",
                artifact_id=artifact_id,
                repair_action="Trace is runtime evidence, not truth. Remove truth claims.",
            )
        )

    # Rule 3: CHECKPOINT-AS-APPROVAL
    has_approval = any(m in text for m in _APPROVAL_MARKERS)
    if is_checkpoint and has_approval:
        findings.append(
            MetabolicFinding(
                code="CHECKPOINT-AS-APPROVAL",
                status="BLOCKED",
                message="Checkpoint claims approval/authorization without external review reference",
                artifact_id=artifact_id,
                repair_action="Checkpoint records state, not approval. Add external review/owner reference.",
            )
        )

    # Rule 4: TOOL-SUCCESS-AS-SAFE-ACTION
    has_safe_action = any(m in text for m in _SAFE_ACTION_MARKERS)
    if has_safe_action:
        findings.append(
            MetabolicFinding(
                code="TOOL-SUCCESS-AS-SAFE-ACTION",
                status="BLOCKED",
                message="Tool call success described as safe/approved/production-ready",
                artifact_id=artifact_id,
                repair_action="Tool success is execution evidence, not safety or authorization.",
            )
        )

    # Rule 5: REVIEW-AFTER-DECISION-BOUNDARY
    if is_review:
        review_data = data if isinstance(data, dict) else {}
        review_ts = review_data.get("timestamp", review_data.get("reviewed_at", ""))
        decision_ts = review_data.get("decision_at", review_data.get("merged_at", review_data.get("deployed_at", "")))
        if review_ts and decision_ts and review_ts > decision_ts:
            findings.append(
                MetabolicFinding(
                    code="REVIEW-AFTER-DECISION-BOUNDARY",
                    status="BLOCKED",
                    message="Review timestamp occurs after decision/merge/deploy boundary",
                    artifact_id=artifact_id,
                    repair_action="Review must precede decision. Timestamps suggest review happened after action.",
                )
            )

    # Rule 6: TRACE-COMPLETENESS-MISSING
    if is_trace or is_checkpoint:
        missing = []
        for field in ("run_id", "started_at", "completed_at", "source", "actor"):
            if isinstance(data, dict) and field not in data:
                missing.append(field)
        if missing:
            findings.append(
                MetabolicFinding(
                    code="TRACE-COMPLETENESS-MISSING",
                    status="DEGRADED",
                    message=f"Trace/checkpoint missing fields: {', '.join(missing)}",
                    artifact_id=artifact_id,
                    repair_action=f"Add missing provenance fields: {', '.join(missing)}.",
                )
            )

    # Rule 7: REVIEW-RECORD-MISSING-SOURCE
    if is_review:
        if isinstance(data, dict):
            missing_source = not any(data.get(f) for f in _SOURCE_FIELDS)
            if missing_source:
                findings.append(
                    MetabolicFinding(
                        code="REVIEW-RECORD-MISSING-SOURCE",
                        status="DEGRADED",
                        message="Review record has no reviewer/source/timestamp/scope",
                        artifact_id=artifact_id,
                        repair_action="Add reviewer, timestamp, and scope to the review record.",
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
        scope=f"trace:{artifact_id}",
        content_hash=content_hash,
        created_in_phase=None,
        last_verified=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        review_date=None,
        supersedes=[],
        superseded_by=None,
        depends_on=[],
        new_ai_entry=False,
        current_truth_allowed=False,
        notes=f"Auto-discovered {atype}. Trace/checkpoint/review is evidence, not truth or authorization.",
    )

    return findings, record


def discover_trace_surfaces(
    root: Path, *, fixture_mode: bool = False
) -> tuple[list[MetabolicFinding], list[ArtifactRecord]]:
    all_findings: list[MetabolicFinding] = []
    all_records: list[ArtifactRecord] = []

    trace_files: list[Path] = []
    for pattern in _CONVENTION_PATHS:
        if "*" in pattern:
            trace_files.extend(sorted(root.glob(pattern)))
        else:
            candidate = root / pattern
            if candidate.is_file():
                trace_files.append(candidate)

    if not trace_files:
        return all_findings, all_records

    seen = set()
    unique: list[Path] = []
    for p in trace_files:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    trace_files = unique

    if not fixture_mode:
        _EXCLUDE_MARKERS = (
            "tests/fixtures/",
            "/unsafe/",
            "/unsafe-",
            "docs/archive/",
            ".tmp/",
        )
        trace_files = [p for p in trace_files if not any(m in str(p) for m in _EXCLUDE_MARKERS)]

    for p in trace_files[:300]:
        if not p.is_file():
            continue
        findings, record = _classify_trace(p, root)
        all_findings.extend(findings)
        if record:
            all_records.append(record)

    return all_findings, all_records
