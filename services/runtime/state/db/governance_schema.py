"""Ordivon governance schema — SQLAlchemy ORM models.

These tables are the authoritative truth-state database for Ordivon.
JSONL files are export/compatibility only, NOT source of truth.

Table summary:
  document_registry     — document registry entries (DGP-2)
  current_truth_entries — current truth entry map (DGP-3)
  governance_events     — event log (E0-E9 classes, → NATS JetStream later)
  governance_debts      — debt ledger (verification, dependency, etc.)
  governance_findings   — checker findings
  governance_traces     — trace spans (→ OTel/OpenInference later)
  governable_objects    — core governable entities
  evidence_records      — evidence metadata (content → S3 later)
  receipts              — governance receipts
  claims                — assertions about governance state
  lessons               — extracted lessons from resolved debt
  policies              — active governance policies
  observations          — system observations
  phase_closures        — phase closure records
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)

from sqlalchemy.orm import relationship

from .base import Base


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Document Registry ──────────────────────────────────────────────────────


class DocumentRegistry(Base):
    """Document registry entry (DGP-2). Canonical source: document-registry.jsonl."""

    __tablename__ = "document_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(String(256), unique=True, nullable=False, index=True)
    path = Column(String(1024), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    doc_type = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="current")
    authority = Column(String(64), nullable=False)
    phase = Column(String(32), nullable=True)
    owner = Column(String(128), nullable=False)
    freshness = Column(String(32), nullable=True)
    ai_read_priority = Column(Integer, default=0)
    supersedes = Column(String(256), nullable=True)
    superseded_by = Column(String(256), nullable=True)
    related_docs = Column(JSON, nullable=True)
    related_ledgers = Column(JSON, nullable=True)
    related_receipts = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    last_verified = Column(String(32), nullable=True)
    stale_after_days = Column(Integer, nullable=True)
    doc_layer = Column(String(8), nullable=True)
    doc_authority = Column(String(64), nullable=True)
    authority_domain = Column(String(128), nullable=True)
    authority_role = Column(String(128), nullable=True)
    authority_scope = Column(String(256), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_doc_registry_status_doc_type", "status", "doc_type"),
        Index("ix_doc_registry_authority", "authority"),
    )


# ── Current Truth Entries ──────────────────────────────────────────────────


class CurrentTruthEntry(Base):
    """Current truth entry map (DGP-3). Canonical source: current-truth-entry-map.jsonl."""

    __tablename__ = "current_truth_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(256), unique=True, nullable=False, index=True)
    doc_id = Column(String(256), nullable=False, index=True)
    path = Column(String(1024), nullable=False)
    authority_type = Column(String(64), nullable=False)
    authority_tier = Column(String(32), nullable=False)
    current_truth_allowed = Column(Boolean, default=True)
    owner = Column(String(128), nullable=False)
    last_verified = Column(String(32), nullable=True)
    review_date = Column(String(32), nullable=True)
    source_registry = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_cte_authority_tier", "authority_tier"),
        Index("ix_cte_doc_id", "doc_id"),
    )


# ── Governance Events ──────────────────────────────────────────────────────


class GovernanceEvent(Base):
    """Governance event log. Event type and class per event-taxonomy.json.
    NATS JetStream will be the real-time transport; PG is the durable log."""

    __tablename__ = "governance_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    event_class = Column(String(32), nullable=False, index=True)
    producer = Column(String(64), nullable=False)
    producer_type = Column(String(32), nullable=False, default="unknown")
    source_context = Column(String(64), nullable=True)
    object_kind = Column(String(64), nullable=True)
    object_ref = Column(String(512), nullable=True)
    affected_surfaces = Column(JSON, nullable=True)
    authority_impact = Column(String(64), nullable=True)
    risk_class = Column(String(16), nullable=True)
    evidence_refs = Column(JSON, nullable=True)
    not_claimed = Column(JSON, nullable=True)
    payload = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_ge_event_class_ts", "event_class", "timestamp"),
        Index("ix_ge_producer_ts", "producer", "timestamp"),
    )


# ── Governance Debts ───────────────────────────────────────────────────────


class GovernanceDebt(Base):
    """Governance debt ledger. Tracks acknowledged gaps, blockers, and tech debt."""

    __tablename__ = "governance_debts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    debt_id = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(String(32), nullable=False, default="OPEN", index=True)
    severity = Column(String(16), nullable=False, default="medium")
    description = Column(Text, nullable=False)
    source_path = Column(String(1024), nullable=True)
    owner = Column(String(128), nullable=True)
    due_stage = Column(String(32), nullable=True)
    close_criteria = Column(Text, nullable=True)
    evidence_refs = Column(JSON, nullable=True)
    not_claimed = Column(JSON, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    closed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_gd_status_severity", "status", "severity"),
        Index("ix_gd_owner", "owner"),
    )


# ── Governance Findings ────────────────────────────────────────────────────


class GovernanceFinding(Base):
    """Checker findings — result of a governance check execution."""

    __tablename__ = "governance_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    finding_id = Column(String(64), unique=True, nullable=False, index=True)
    checker_name = Column(String(128), nullable=False, index=True)
    severity = Column(String(16), nullable=False, index=True)
    description = Column(Text, nullable=False)
    affected_surface = Column(String(256), nullable=True)
    evidence_ref = Column(String(64), nullable=True)
    run_id = Column(String(32), nullable=True, index=True)
    trace_id = Column(String(32), nullable=True)
    status = Column(String(32), nullable=False, default="PASS")
    raw_payload = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_gf_checker_severity", "checker_name", "severity"),
        Index("ix_gf_run_id", "run_id"),
    )


# ── Governance Traces ──────────────────────────────────────────────────────


class GovernanceTrace(Base):
    """Trace span records. OTel/OpenInference is the runtime tracer; PG stores structured trace data."""

    __tablename__ = "governance_traces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    span_id = Column(String(32), unique=True, nullable=False, index=True)
    trace_id = Column(String(32), nullable=False, index=True)
    parent_span_id = Column(String(32), nullable=True)
    tool = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False)
    input_refs = Column(JSON, nullable=True)
    output_refs = Column(JSON, nullable=True)
    evidence_refs = Column(JSON, nullable=True)
    duration_ms = Column(Integer, default=0)
    attributes = Column(JSON, nullable=True)

    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_gt_trace_id", "trace_id"),
        Index("ix_gt_status", "status"),
    )


# ── Governable Objects ─────────────────────────────────────────────────────


class GovernableObject(Base):
    """Core governable entity — the primary unit of Ordivon governance.

    Every document, artifact, checker, receipt, or policy that enters the
    governance system is tracked as a GovernableObject.
    """

    __tablename__ = "governable_objects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    object_id = Column(String(64), unique=True, nullable=False, index=True)
    object_type = Column(String(64), nullable=False, index=True)
    path = Column(String(1024), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="DECLARED")
    owner = Column(String(128), nullable=True)
    system = Column(String(128), nullable=True)  # Backstage-style catalog
    domain = Column(String(128), nullable=True)  # Backstage-style catalog
    lifecycle = Column(String(32), nullable=True)  # Backstage-style catalog
    extra = Column(JSON, nullable=True)  # Flexible governance payload
    relations = Column(JSON, nullable=True)  # Related object refs

    declared_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_go_type_status", "object_type", "status"),
        Index("ix_go_path", "path"),
    )


# ── Governable Transitions ─────────────────────────────────────────────────


class GovernableTransition(Base):
    """State transition of a governable object. Every status change is recorded."""

    __tablename__ = "governable_transitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transition_id = Column(String(64), unique=True, nullable=False, index=True)
    object_id = Column(String(64), ForeignKey("governable_objects.object_id"), nullable=False, index=True)
    from_status = Column(String(32), nullable=False)
    to_status = Column(String(32), nullable=False)
    triggered_by = Column(String(128), nullable=True)
    reason = Column(Text, nullable=True)
    evidence_refs = Column(JSON, nullable=True)
    authority_refs = Column(JSON, nullable=True)

    transitioned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    object = relationship("GovernableObject", backref="transitions")

    __table_args__ = (
        Index("ix_gtr_object_id_ts", "object_id", "transitioned_at"),
        Index("ix_gtr_to_status", "to_status"),
    )


# ── Claims ─────────────────────────────────────────────────────────────────


class Claim(Base):
    """Assertion about governance state. Must be backed by evidence."""

    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(String(64), unique=True, nullable=False, index=True)
    claim_type = Column(String(64), nullable=False, index=True)
    subject_object_id = Column(String(64), nullable=True, index=True)
    predicate = Column(String(256), nullable=False)
    asserted_by = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False, default="UNVERIFIED")  # UNVERIFIED, VERIFIED, REFUTED, EXPIRED
    evidence_refs = Column(JSON, nullable=True)
    extra = Column(JSON, nullable=True)

    asserted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    verified_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_claims_status", "status"),
        Index("ix_claims_subject", "subject_object_id"),
    )


# ── Evidence Records ───────────────────────────────────────────────────────


class EvidenceRecord(Base):
    """Evidence metadata. Content blobs go to S3-compatible object storage.
    PG stores index: object_key, hash, content_type, governance refs."""

    __tablename__ = "evidence_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evidence_id = Column(String(64), unique=True, nullable=False, index=True)
    object_key = Column(String(1024), nullable=True)  # S3 key
    local_path = Column(String(1024), nullable=True)  # Local path (transitional)
    sha256 = Column(String(64), nullable=True, index=True)
    content_type = Column(String(128), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    command = Column(Text, nullable=True)
    exit_code = Column(Integer, nullable=True)
    expected_failure = Column(Boolean, default=False)
    status = Column(String(32), nullable=False, default="collected")
    claim_refs = Column(JSON, nullable=True)
    extra = Column(JSON, nullable=True)

    collected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    duration_ms = Column(Integer, default=0)

    __table_args__ = (
        Index("ix_er_sha256", "sha256"),
        Index("ix_er_status", "status"),
    )


# ── Receipts ───────────────────────────────────────────────────────────────


class Receipt(Base):
    """Governance receipt — proof of governance work performed."""

    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    receipt_id = Column(String(64), unique=True, nullable=False, index=True)
    receipt_type = Column(String(64), nullable=False, index=True)
    phase = Column(String(32), nullable=True)
    status = Column(String(32), nullable=False, default="DRAFT")
    summary = Column(Text, nullable=True)
    claims = Column(JSON, nullable=True)  # List of claim refs
    evidence_refs = Column(JSON, nullable=True)
    author = Column(String(128), nullable=True)
    verified_by = Column(String(128), nullable=True)
    extra = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    verified_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_receipts_phase", "phase"),
        Index("ix_receipts_status", "status"),
    )


# ── Lessons ────────────────────────────────────────────────────────────────


class Lesson(Base):
    """Extracted lesson from resolved debt, finding, or incident."""

    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(String(64), unique=True, nullable=False, index=True)
    source_type = Column(String(64), nullable=False)  # debt, finding, incident, review
    source_ref = Column(String(256), nullable=True)
    category = Column(String(64), nullable=True)
    summary = Column(Text, nullable=False)
    severity = Column(String(16), nullable=False, default="medium")
    candidate_rule_ids = Column(JSON, nullable=True)
    related_lessons = Column(JSON, nullable=True)

    extracted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_lessons_category", "category"),
        Index("ix_lessons_severity", "severity"),
    )


# ── Policies ───────────────────────────────────────────────────────────────


class Policy(Base):
    """Active governance policy. CandidateRules graduate to Policy on activation."""

    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(256), nullable=False)
    policy_type = Column(String(64), nullable=False, index=True)  # admission, authority, lifecycle, etc.
    status = Column(String(32), nullable=False, default="DRAFT")
    rego_module = Column(String(256), nullable=True)  # OPA Rego module path
    rules = Column(JSON, nullable=True)  # Inline rules if not using Rego
    applies_to = Column(JSON, nullable=True)  # Object types this policy applies to
    activated_by = Column(String(128), nullable=True)
    supersedes = Column(String(256), nullable=True)
    extra = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    activated_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_policies_type_status", "policy_type", "status"),)


# ── Phase Closures ─────────────────────────────────────────────────────────


class PhaseClosure(Base):
    """Phase closure records from phase-closure-ledger.jsonl."""

    __tablename__ = "phase_closures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    closure_id = Column(String(64), unique=True, nullable=False, index=True)
    phase = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="CLOSED")
    summary = Column(Text, nullable=True)
    receipt_ref = Column(String(256), nullable=True)
    debt_count = Column(Integer, nullable=True)
    evidence_refs = Column(JSON, nullable=True)
    extra = Column(JSON, nullable=True)

    closed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (Index("ix_pc_phase", "phase"),)


# ── Observations ───────────────────────────────────────────────────────────


class Observation(Base):
    """System observation — what a checker or scanner observed at a point in time."""

    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    observation_id = Column(String(64), unique=True, nullable=False, index=True)
    observer = Column(String(128), nullable=False, index=True)
    observation_type = Column(String(64), nullable=False, index=True)
    subject_path = Column(String(1024), nullable=True)
    subject_object_id = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False, default="RECORDED")
    summary = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)

    observed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_obs_observer_ts", "observer", "observed_at"),
        Index("ix_obs_type", "observation_type"),
    )


# ── Owner Routing Rules ────────────────────────────────────────────────────


class OwnerRoutingRule(Base):
    """Owner routing rules from owner-routing-rules.jsonl."""

    __tablename__ = "owner_routing_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(String(64), unique=True, nullable=False, index=True)
    path_pattern = Column(String(1024), nullable=False)
    owner = Column(String(128), nullable=False)
    priority = Column(Integer, default=0)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (Index("ix_orr_path_pattern", "path_pattern"),)
