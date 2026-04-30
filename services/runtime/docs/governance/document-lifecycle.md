# Document Lifecycle

Status: **ACCEPTED** | Date: 2026-04-30 | Phase: DG-1
Tags: `governance`, `document`, `lifecycle`, `status`, `staleness`, `archive`

## 1. Purpose

Every document in Ordivon exists in exactly one lifecycle status. The status
determines whether the document can be treated as current truth, whether it can
be archived, and whether AI agents should trust its contents without verification.

This spec defines the statuses, transition rules, and staleness policies.

## 2. Status Definitions

### 2.1 draft

**Definition**: Work in progress. Not yet reviewed or accepted.

**Authority**: None. A draft document has no authority.

**Behavior**: AI agents may read drafts for context but must not treat them as
current truth. Drafts must be labeled `Status: DRAFT`.

**Permitted transitions**: `draft` → `proposed`

### 2.2 proposed

**Definition**: Formal proposal awaiting acceptance.

**Authority**: `proposal` — carries no enforcement weight.

**Behavior**: AI agents may reference proposed documents as "this is what is
proposed" but must not treat them as accepted governance.

**Permitted transitions**: `proposed` → `current`, `proposed` → `archived` (rejected)

### 2.3 current

**Definition**: Active, authoritative guidance.

**Authority**: Depends on type. `source_of_truth` or `current_status` typically.

**Behavior**: AI agents may treat as current truth for decisions within the
document's scope. Must verify freshness timestamp.

**Permitted transitions**: `current` → `implemented`, `current` → `superseded`,
`current` → `stale`, `current` → `closed`, `current` → `deferred`

### 2.4 implemented

**Definition**: The guidance has been implemented in code. The document remains
as reference but the truth is now in code behavior.

**Authority**: `current_status` (descriptive of what is implemented).

**Behavior**: AI agents should prefer runtime behavior over document claims.
If code and doc disagree, code is truth until doc is updated.

**Permitted transitions**: `implemented` → `superseded`, `implemented` → `archived`

### 2.5 closed

**Definition**: The phase, activity, or process this document describes is
permanently closed.

**Authority**: `historical_record` (what happened), except Stage Summit which
carries `current_status` for phase boundaries.

**Behavior**: Closed documents are evidence of closure. They are not current
authority for what is allowed.

**Permitted transitions**: `closed` → `archived` (after cooling period)

### 2.6 deferred

**Definition**: The work described is deferred to a future phase.

**Authority**: `current_status` (for the deferral decision).

**Behavior**: AI agents must treat deferred items as NOT ACTIVE. The deferral
itself is current truth.

**Permitted transitions**: `deferred` → `current` (when un-deferred),
`deferred` → `closed` (if permanently deferred)

### 2.7 superseded

**Definition**: Replaced by a newer document of the same type.

**Authority**: None. The superseding document holds authority.

**Behavior**: AI agents must reference the superseding document, not this one.
A superseded document should link to its replacement via `superseded_by`.

**Permitted transitions**: `superseded` → `archived`

### 2.8 archived

**Definition**: Retained for historical record. Not active guidance.

**Authority**: `archive` — historical interest only.

**Behavior**: AI agents must NOT treat archived documents as current truth.
Archived docs should carry warning headers.

**Permitted transitions**: Terminal state. No transitions out.

### 2.9 stale

**Definition**: The document's freshness has expired. Its contents have not been
verified recently.

**Authority**: None. Stale docs cannot be treated as current truth.

**Behavior**: AI agents must flag stale documents and request verification before
using their contents for decisions. A stale `phase_boundary` doc is a
governance incident.

**Permitted transitions**: `stale` → `current` (after reverification),
`stale` → `superseded`, `stale` → `archived`

## 3. Lifecycle Diagram

```
draft ──────→ proposed ──────→ current ──────→ implemented ──┐
  │                               │    │            │          │
  │                               │    │            │          │
  │                               │    ├─→ stale ───┤          │
  │                               │    │            │          │
  │                               │    ├─→ closed ──┤          │
  │                               │    │            │          │
  │                               │    └─→ deferred─┤          │
  │                               │                 │          │
  └───────────────────────────────┴─→ archived ←────┴──────────┘
                                                  ↑
                                  proposed ────────┘ (rejected)
                                  superseded ──────┘
```

## 4. Transition Rules

### 4.1 Progression

| From | To | Requires |
|------|----|----------|
| `draft` | `proposed` | Author declares ready for review |
| `proposed` | `current` | Stakeholder acceptance (human sign-off for governance packs) |
| `current` | `implemented` | Code implementation complete + tests pass |
| `current` | `closed` | Stage Summit published or explicit closure decision |
| `current` | `deferred` | Documented deferral with reason and gate criteria |
| `current` | `superseded` | New document published, `superseded_by` set |
| `current` | `stale` | Freshness timer expires without reverification |
| `implemented` | `superseded` | New implementation replaces old |
| `implemented` | `archived` | Cooling period elapsed |
| `closed` | `archived` | Cooling period elapsed (≥30 days after closure) |
| `deferred` | `current` | Gate criteria met, explicit un-defer decision |
| `deferred` | `closed` | Permanent deferral decision |
| `superseded` | `archived` | Cooling period elapsed |
| `stale` | `current` | Full reverification complete, freshness reset |

### 4.2 Forbidden Transitions

- `archived` → any other status (terminal)
- `closed` → `current` (cannot un-close without new phase/gate)
- `stale` → `current` without reverification
- `draft` → `current` (must pass through `proposed`)
- `receipt` type docs changing status (receipts are immutable)
- `ledger` type events changing status (ledger events are append-only immutable)

## 5. Staleness Policy

### 5.1 Freshness Windows

| Document Type | Max Staleness | Consequence of Staleness |
|--------------|---------------|--------------------------|
| `root_context` | 7 days | Governance incident — AI onboarding broken |
| `ai_onboarding` | 14 days | AI agents may have wrong boundaries |
| `phase_boundary` | 7 days | AI agents may violate NO-GO boundaries |
| `architecture` | 30 days | Possible structure drift |
| `design_spec` | 30 days | Possible UI drift |
| `runbook` | 60 days | May reference wrong commands |
| `receipt` | N/A | Receipts don't stale — they're historical |
| `stage_summit` | N/A | Superseded, not stale |
| `red_team` | 60 days | May miss new attack surface |
| `ledger` | N/A | Individual events don't stale |
| `tracker` | 30 days | May show wrong readiness state |
| `schema` | 30 days | Schema may be out of sync with code |
| `template` | 60 days | May follow old conventions |
| `adr` | N/A | ADRs don't stale — superseded if reversed |
| `archive_index` | 90 days | May miss recent archives |
| `product` | 30 days | May show wrong product direction |
| `runtime` | 30-60 days | Depends on subtype |
| `governance_pack` | 30 days | Governance rules may be out of date |

### 5.2 Staleness Detection

In future phases, a document checker will scan all documents for:
- `Status:` field presence
- `Date:` field presence
- Freshness window violation (current date - document date > max staleness)
- Missing `last_verified` field (if applicable)

For DG-1, staleness detection is manual.

### 5.3 Staleness Remediation

When a document is discovered as stale:
1. Flag it (add `⚠ STALE — last verified YYYY-MM-DD` banner)
2. Determine if contents are still correct
3. If correct: update `Date` or `last_verified` to current date, remove stale banner
4. If incorrect: update contents + date, or transition to `superseded`/`archived`

## 6. Archive Policy

### 6.1 What Gets Archived

- Documents superseded by newer versions
- Phase documents after cooling period (≥30 days)
- Consolidated receipts (11→1 pattern)
- Old templates replaced by new conventions
- Deferred items that are permanently deferred

### 6.2 What Never Gets Archived (Active Project)

- `root_context` documents (AGENTS.md, etc.) — updated in place
- `ai_onboarding` documents — updated in place
- `phase_boundary` documents — updated in place
- `stage_summit` documents — retained as evidence, linked from current boundaries
- `ledger` JSONL files — retained permanently

### 6.3 Archive Format

Archived documents should:
1. Move to an `archive/` directory within their domain (e.g., `docs/runtime/archive/`)
2. Carry an `archived` status header with archive date
3. Link to the superseding document if applicable
4. Include a brief note explaining why archived

### 6.4 Cooling Period

Documents transition through `closed` or `superseded` before reaching `archived`.
Minimum cooling period: 30 days in `closed`/`superseded` state before archive.
This prevents premature archival of documents that may contain useful evidence.

## 7. Special Cases

### 7.1 Receipts (Immutable)

Receipts are historical records. They do not transition through lifecycle
statuses. They are created in `closed` state and remain there permanently.
They may be consolidated (11→1 pattern from PT-001) but not deleted.

### 7.2 JSONL Ledger (Append-Only)

JSONL ledger events are immutable and append-only. New events are added.
Existing events are never modified or removed. The ledger itself carries
`current` status while active and `closed` status when the phase closes.

### 7.3 Stage Summit (Special Closure Authority)

A Stage Summit carries unique authority: it can close a phase AND define
post-phase boundaries. It transitions to `closed` status immediately on
publication. Its boundary definitions remain in effect until a new Stage
Summit supersedes them.

### 7.4 Templates (No Authority)

Templates have `example` authority and never transition to `current` status.
They are `proposed` (when drafted) or `example` (when published). A template
that becomes a real document should be copied, not promoted.
