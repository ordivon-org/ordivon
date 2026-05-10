"""Generated artifact registry builder.

Converts discovered ArtifactRecords into a GeneratedRegistry with dry-run
metabolic findings. Never physically deletes files.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ordivon_verify.metabolic.models import (
    ArtifactRecord,
    AuthorityTier,
    GeneratedRegistry,
    LifecycleState,
    MetabolicFinding,
)


def _check_record(record: ArtifactRecord) -> list[MetabolicFinding]:
    findings: list[MetabolicFinding] = []

    # T3 candidate must not be current truth
    if record.authority_tier == AuthorityTier.T3_CANDIDATE_PROPOSAL and record.current_truth_allowed:
        findings.append(
            MetabolicFinding(
                code="ENTROPY-CANDIDATE-AS-TRUTH",
                status="BLOCKED",
                message=f"T3 candidate artifact '{record.artifact_id}' has current_truth_allowed=True",
                artifact_id=record.artifact_id,
                repair_action="Set current_truth_allowed=False for candidate artifacts.",
            )
        )

    # T4 archive must not be current truth
    if record.authority_tier == AuthorityTier.T4_HISTORICAL_ARCHIVE and record.current_truth_allowed:
        findings.append(
            MetabolicFinding(
                code="ENTROPY-ARCHIVE-AS-TRUTH",
                status="BLOCKED",
                message=f"T4 archive artifact '{record.artifact_id}' has current_truth_allowed=True",
                artifact_id=record.artifact_id,
                repair_action="Set current_truth_allowed=False for archived artifacts.",
            )
        )

    # Active artifacts (lifeycle = ACTIVE/STABLE, authority T1+) need owner
    if record.lifecycle_state in (LifecycleState.ACTIVE, LifecycleState.STABLE):
        if record.authority_tier in (AuthorityTier.T0_CURRENT_TRUTH, AuthorityTier.T1_ACTIVE_SPEC):
            if not record.owner:
                findings.append(
                    MetabolicFinding(
                        code="ENTROPY-MISSING-OWNER",
                        status="DEGRADED",
                        message=f"Active spec artifact '{record.artifact_id}' has no owner",
                        artifact_id=record.artifact_id,
                        repair_action="Assign an owner to this artifact.",
                    )
                )

    # Active artifacts need last_verified
    if record.lifecycle_state == LifecycleState.ACTIVE:
        if record.authority_tier in (AuthorityTier.T0_CURRENT_TRUTH, AuthorityTier.T1_ACTIVE_SPEC):
            if not record.last_verified:
                findings.append(
                    MetabolicFinding(
                        code="ENTROPY-MISSING-VERIFIED",
                        status="DEGRADED",
                        message=f"Active artifact '{record.artifact_id}' has no last_verified date",
                        artifact_id=record.artifact_id,
                        repair_action="Set last_verified date for this artifact.",
                    )
                )

    # T5 deprecated/tombstoned needs superseded_by or reason in notes
    if record.authority_tier == AuthorityTier.T5_DEPRECATED_TOMBSTONED:
        if not record.superseded_by and not record.notes:
            findings.append(
                MetabolicFinding(
                    code="ENTROPY-TOMBSTONE-NO-REASON",
                    status="DEGRADED",
                    message=f"T5 deprecated artifact '{record.artifact_id}' has no superseded_by or notes",
                    artifact_id=record.artifact_id,
                    repair_action="Add superseded_by reference or notes explaining deprecation.",
                )
            )

    return findings


def build_registry(records: list[ArtifactRecord], repo_root: str) -> GeneratedRegistry:
    findings: list[MetabolicFinding] = []
    for record in records:
        findings.extend(_check_record(record))

    return GeneratedRegistry(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        repo_root=repo_root,
        records=records,
        findings=findings,
    )


def plan_metabolic_actions(registry: GeneratedRegistry) -> list[MetabolicFinding]:
    """Dry-run metabolic analysis. Returns findings only — no physical deletion."""
    return registry.findings
