# Step 1 Foundation Report - 2026-04-18

## Scope

This report closes Step 1 of the current foundation plan:

- keep moving high-frequency truth modules out of `pfios/*`
- make root layers the default place for active code
- leave legacy paths as compatibility surfaces only

## What Was Completed

### Root ownership established

The following modules now have real root-layer implementations:

- `domains/research`: analysis
- `domains/strategy`: recommendation and outcome
- `domains/journal`: review, lesson, and issue
- `state/db`: database foundation
- `state/usage`: usage snapshots
- `governance/audit`: audit events and auditor
- `governance/risk_engine`: default governance checks
- `knowledge/wiki`: markdown wiki listing
- `tools/reports`: report rendering

### Active imports moved

Active code paths now prefer root layers for:

- analysis flows
- recommendation lifecycle access
- review creation and completion
- outcome-backed dashboard summary reads
- issue-backed validation summary and reporting
- lesson creation during review completion
- audit writing and audit listing
- usage snapshot creation and reporting

### Legacy paths downgraded

The following legacy families have been downgraded to compatibility re-exports:

- `pfios.domain.analysis.*`
- `pfios.domain.recommendation.*`
- `pfios.domain.review.*`
- `pfios.domain.outcome.*`
- `pfios.domain.lessons.*`
- `pfios.domain.issue.*`
- `pfios.domain.usage.*`
- `pfios.domain.audit.*`
- `pfios.audit.auditor`

## Current Truth Ownership

### Domains

- `domains/research`: analysis artifacts
- `domains/strategy`: recommendation lifecycle and outcome snapshots
- `domains/journal`: review, lessons, issues

### Governance

- `governance/risk_engine`: allow/block reasoning for analysis flows
- `governance/audit`: audit event persistence and JSONL logging

### State

- `state/db`: SQLAlchemy base/session/bootstrap/schema foundation
- `state/usage`: operational usage snapshots

## Verification

Step 1 was validated with targeted tests covering:

- root import availability
- legacy compatibility imports
- repository persistence behavior
- bootstrap metadata loading
- capability/runtime import sanity

Representative passing test groups include:

- recommendation migration tests
- review migration tests
- usage migration tests
- audit migration tests
- outcome/lesson/issue migration tests

## What This Means

The repository is no longer just "architecturally shaped" like the target system.
The main analysis -> recommendation -> review -> lesson -> audit path now runs through root-layer ownership for most of its core truth modules.

The remaining `pfios/*` surface is increasingly a compatibility shell rather than the real home of business truth.

## Remaining Gaps After Step 1

Step 1 does **not** complete the whole framework.

The largest remaining gaps are:

- capability contracts are still uneven
- orchestrator still needs stronger workflow/runtime structure
- intelligence still lacks active prompt/task/schema ownership
- knowledge layer still only has a first wiki slice
- execution layer still lacks a real umbrella implementation
- infrastructure and observability are still lightweight

## Ready For Step 2

The repository is now ready for Step 2:

**formalize Domain / State / Governance ownership and boundaries**

That work can proceed without fighting large unresolved truth-location ambiguity for the highest-frequency modules.
