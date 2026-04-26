# Step 2 Boundary Prep - 2026-04-18

## Goal

Prepare Step 2: make Domain / State / Governance ownership explicit and stable enough that new features stop drifting across layers.

## Recommended Ownership Decisions

### Domain-owned

These represent business semantics, not raw system state plumbing:

- `domains/research`
  - analysis request/result objects
  - analysis business semantics
- `domains/strategy`
  - recommendation lifecycle
  - outcome snapshots tied to recommendation meaning
- `domains/journal`
  - reviews
  - lessons
  - issues raised from validation or operational review

### State-owned

These represent "what is true now" and operational fact persistence:

- `state/db`
  - DB base/session/bootstrap/schema
- `state/usage`
  - usage snapshots and similar operational counters

Future likely state-owned areas:

- task state
- report metadata
- user preferences
- execution state snapshots

### Governance-owned

These represent system boundary enforcement and traceability:

- `governance/risk_engine`
  - allow/block logic
- `governance/audit`
  - audit persistence
  - audit log writing
  - audit retrieval

Future likely governance-owned areas:

- guards
- permissions
- policies
- approval gates

## Step 2 Concrete Tasks

1. Add short ownership notes to root packages where ambiguity remains.
2. Normalize imports so new code defaults to root owners only.
3. Decide where `issue` ends and governance incident handling begins.
4. Decide whether `outcome` should stay fully inside `domains/strategy` or split part of its operational snapshot behavior into `state`.
5. Add minimal contracts or schemas for the top capabilities.

## Risks To Watch

- `shared/` becoming a dumping ground for business types
- capability modules re-accumulating direct persistence details
- orchestrator taking back business truth ownership
- governance logic leaking into route handlers or domain repositories

## Completion Signal For Step 2

Step 2 is complete when:

- ownership questions have default answers
- package boundaries are documented in code or docs
- adding a new feature no longer requires guessing where core objects should live
