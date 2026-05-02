# Document Authority Model (DG-1)

Status: **current** | Date: 2026-05-02 | Phase: DG-1
Tags: `dg-1`, `authority`, `truth`, `evidence`, `lifecycle`
Authority: `source_of_truth` | AI Read Priority: 1

## Core Principle

**Document authority defines what a document CAN claim, not what it CAN authorize.**

No document in the Ordivon governance system can authorize:
- Live financial action
- Broker write operations
- Auto-trading
- Credential access
- External tool execution
- Binding policy activation (CandidateRule remains advisory)
- Package publication
- Public repo creation
- License activation

Authority is about truth, not execution permission.

## Authority Types

### source_of_truth

**Can**: Define current project truth, normative semantics, structural invariants.
**Cannot**: Authorize live action, broker writes, credential access, execution.
**Examples**: AGENTS.md, root-context.md, phase-boundaries.md, ontology docs, schemas.
**Freshness requirement**: Must have `last_verified` and `stale_after_days`.
**Supersession**: Can be superseded by newer source_of_truth docs.

### current_status

**Can**: Report current phase status, active boundaries, open debt, next steps.
**Cannot**: Define policy alone; cannot override source_of_truth.
**Examples**: README.md, agent-working-rules.md, runbooks.
**Freshness requirement**: Must have `last_verified`; `stale_after_days` strongly recommended.
**Supersession**: Can be superseded.

### supporting_evidence

**Can**: Provide evidence for review, record what happened, support closure decisions.
**Cannot**: Define current truth, authorize action, override phase boundaries.
**Examples**: Closure receipts, runtime evidence docs, paper dogfood ledgers.
**Freshness requirement**: Dated at creation; archival after phase closure.
**Supersession**: May be superseded by updated evidence docs.

### historical_record

**Can**: Preserve traceability of past decisions and processes.
**Cannot**: Be used as current guidance or action authorization.
**Examples**: Closed phase receipts from completed historical phases.
**Freshness requirement**: Stated creation date; does not expire.
**Supersession**: Can be superseded; superseded historical records enter archive.

### proposal

**Can**: Propose new rules, designs, or governance structures.
**Cannot**: Be treated as adopted policy unless a later phase explicitly accepts it.
**Examples**: Product briefs, design proposals, contract drafts.
**Freshness requirement**: Dated; stale after proposing phase closes if not adopted.

### example

**Can**: Illustrate patterns, templates, or conventions.
**Cannot**: Define policy, authorize action, or override normative docs.
**Examples**: Task prompt templates, fixture examples, use case docs.

### archive

**Can**: Preserve historical record with no current authority.
**Cannot**: Be referenced as current guidance in L0/L1 AI read path.
**Examples**: Archived receipts, superseded docs moved to archive.
**Freshness requirement**: Stated archive date; does not expire.

## Authority Invariants

1. **Receipts are evidence, not action authorization.**
   A closure receipt records what was done and verified. It does not authorize future action.

2. **Stage Summits close phase truth, not live-action permission.**
   A Stage Summit marks a phase CLOSED. It does not authorize the next phase's actions.

3. **Document registry records truth metadata; it does not create action authority.**
   Registry PASS means metadata is consistent. It does not prove content correctness.

4. **Detector PASS is not authorization.**
   ADP-3 detector findings are review evidence. They do not approve or authorize anything.

5. **Absence of findings is not proof of safety.**
   A clean detector scan means no patterns matched. It does not mean the system is safe.

6. **Wiki generation PASS is not proof of freshness.**
   The wiki is derived from the registry. A correctly generated wiki may contain stale content.

7. **Public wedge is not public release.**
   Ordivon Verify is a public wedge product. It is not the full private core, and no release has occurred.

## Authority Transitions

| From | To | Condition |
|------|-----|-----------|
| `current` → `superseded` | New doc supersedes it | superseded_by field set |
| `accepted` → `current` | Acceptance sealed | Status updated |
| `current` → `archived` | Phase closed, no longer active | Moved to archive |
| `source_of_truth` → `historical_record` | Superseded by new source_of_truth | Authority downgraded |
| `proposal` → `accepted` | Phase explicitly accepts | Dogfood or Stage Gate |

## Detector Implications

ADP-3 detector rules (ADP3-DG-STALENESS, ADP3-DG-DEGRADED-LIFECYCLE, ADP3-DG-RECEIPT-AUTH)
depend on correct authority metadata. A document with wrong authority can cause false
positives or false negatives in detector output.
