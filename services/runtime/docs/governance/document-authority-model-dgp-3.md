# Document Authority Model — DGP-3

Status: **CURRENT** | Date: 2026-05-09 | Phase: DGP-3
Authority: current_status | Owner: Governance

## Purpose

Define which document types may claim authority in Ordivon, and what boundaries prevent authority laundering across generated views, receipts, proposals, lessons, and CandidateRules.

This doc defines the conceptual model. Enforcement lives in the Registry Control Plane reconciler (check: authority-boundary).

## Authority Types

### source_of_truth
Canonical truth for its scope. The highest authority tier a document can hold.
- Must have: owner, last_verified, review_date, lifecycle_state = active/stable.
- Must NOT be: generated_view, receipt, proposal, lesson, archived.
- Maps to: AuthorityTier.T0_SOURCE_OF_TRUTH.

### current_status
Current operational status. Describes what IS true now, not what was true historically.
- Must have: owner, last_verified.
- Maps to: AuthorityTier.T1_CURRENT_STATUS.

### supporting_evidence
Corroborating material. Supports truth claims but is not truth itself.
- Maps to: AuthorityTier.T2_SUPPORTING_EVIDENCE.
- Default for: receipts, runtime evidence, generated views, ledgers, test results.

### generated_view
Machine-produced artifact. Derived from source data. Cannot be source_of_truth.
- Maps to: AuthorityTier.T2_SUPPORTING_EVIDENCE.
- Must have: generated=True, current_truth_allowed=False.
- Examples: verification-gate-manifest.json, registry-index output.

### receipt
Phase closure evidence. Records what happened. Is not permanent truth.
- Authority: supporting_evidence (default).
- A receipt claiming source_of_truth requires explicit current-truth-entry-map registration.

### stage_summit
Compressed phase summary for human/AI onboarding. Is not permanent truth.
- Authority: proposal or supporting_evidence.
- A stage summit claiming source_of_truth requires explicit current-truth-entry-map registration.

### proposal
Speculative or planned work. Carries no enforcement weight.
- Authority: proposal (T3_CANDIDATE_PROPOSAL).
- Cannot be current_truth_allowed.

### lesson
Learned insight from checker findings or operational experience.
- Authority: supporting_evidence.
- Lesson is not policy. Lesson → CandidateRule → PolicyActivation → Policy is the only path.

### candidate_rule
Draft governance rule extracted from lessons.
- Authority: T3_CANDIDATE_PROPOSAL.
- CandidateRule is NOT Policy. Requires PolicyActivation to become active.

### policy_activation
The bridge between CandidateRule and active Policy. Cannot exist without candidate_rule target.
- Authority: T1_CURRENT_STATUS (when active).
- Must reference candidate_rule_id.

### archive_historical
Preserved historical record. Not current truth.
- Authority: T4_ARCHIVE_HISTORICAL.
- Must NOT be current_truth_allowed.

### tombstoned
Decommissioned document. Explicitly dead. Must have reason or successor.
- Authority: T5_DEPRECATED_TOMBSTONED.
- Must NOT be current_truth_allowed.

## Hard Invariants (enforced by reconciler authority-boundary check)

1. generated_view must not be current_truth_allowed → BLOCKED.
2. archive/tombstoned must not be current_truth_allowed → BLOCKED.
3. receipt must not self-declare source_of_truth without current-truth-entry-map entry → DEGRADED.
4. proposal must not be current_truth_allowed → BLOCKED.
5. CandidateRule without policy_activation must not act as policy → BLOCKED.
6. Lesson must not claim policy status → DEGRADED.

## Current Truth Entry Map

The `current-truth-entry-map.jsonl` is the machine-readable register of documents that are explicitly authorized to carry current truth status. A document not in this map defaults to its authority tier's standard truth boundary.

## Relationship to Existing Systems

- `current_truth_protocol` checker: DGP-3 does not weaken it. The protocol remains the gate for current truth claims.
- `registry-index`: authority model metadata appears in generated index summary.
- `document-registry`: authority field maps to authority_tier via RCP import adapters.
- DGP-2 lifecycle states: authority checks are lifecycle-aware (archive/tombstoned truth blocked).
