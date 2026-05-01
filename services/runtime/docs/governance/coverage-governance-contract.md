# Coverage Governance Contract

> Coverage precedes confidence. PASS is scoped. Silent omission is not governance.

## Purpose

Define the contract by which Ordivon governance checkers declare their scope,
discovery method, exclusions, and pass semantics. A checker that does not
declare what universe it covers is producing an untrustworthy signal.

## Why Enumeration Is Necessary But Insufficient

Registry/manifest/allowlist governance is necessary — you must name what you
govern. But it is insufficient because:

1. A checker that only validates registered objects will never detect
   unregistered objects.
2. A checker whose input set is hand-maintained will rot as the repo grows.
3. PASS on a partial universe creates false confidence.
4. New objects created outside the enumeration are invisible.

This was proven twice:
- **VD-005:** `check_document_registry.py` returned PASS on 31 registered docs
  while 142+ unregistered docs existed.
- **pr-fast wave_files:** Ruff format gate returned PASS on 9 whitelisted files
  while new test files outside the list were unformatted.

The fix is not to eliminate enumerations — it is to pair every enumeration with
discovery, reconciliation, and explicit exclusion.

## Core Invariants

1. **Coverage precedes confidence.** A PASS is only trustworthy if the checker
   can describe what universe it covers and how it was discovered.

2. **PASS is scoped.** Every PASS result must declare its coverage universe.
   A checker must state what it checked and what it excluded.

3. **Silent omission is not governance.** Every exclusion must be explicit
   and carry reason, classification, owner, and reviewed_at.

4. **Out-of-scope requires reason.** "Not in scope" is valid only when
   accompanied by a classification and a reason. Blanket exclusion without
   justification is a coverage gap.

5. **Registry must reconcile with repository reality.** A registry is not
   complete until it has been checked against discoverable reality.

6. **A checker is only as trustworthy as its discovery model.** If a checker
   cannot describe how it found its input objects, its PASS cannot be trusted.

## Known/Unknown Model

| Quadrant | Governance Action |
|----------|------------------|
| Known Known | Validate with checker |
| Known Unknown | Manage with debt ledger + exclusions |
| Unknown Known | Encode in docs, registry, onboarding |
| Unknown Unknown | Discover through reconciliation scan |

Governance maturity = migrating objects leftward and downward.
Every checker must declare which quadrant it operates in and what
mechanism it uses for discovery.

## Checker Responsibility Model

Every governed checker must declare:

| Field | Required | Description |
|-------|----------|-------------|
| `claimed_universe` | Yes | What objects this checker governs |
| `discovery_method` | Yes | How objects are found (filesystem glob, registry load, manifest parse) |
| `registry_or_manifest` | Yes | What file defines the known universe |
| `exclusion_policy` | Yes | How exclusions are recorded and justified |
| `reconciliation_required` | Yes | Whether the checker must cross-reference discovery against registry |
| `coverage_summary_required` | Yes | Whether the checker output must include coverage counts |
| `unknown_object_test_required` | Yes | Whether tests exist proving unregistered objects are detected |
| `pass_scope_statement_required` | Yes | Whether PASS output must declare what universe was covered |

## Allowed Checker Coverage Statuses

| Status | Meaning |
|--------|---------|
| `implemented` | All coverage invariants satisfied, discovery + reconciliation active |
| `partial` | Some invariants satisfied, known gaps documented |
| `deferred_with_reason` | Coverage not yet implemented, explicit reason and follow-up required |
| `not_applicable` | This checker does not govern an object universe (e.g., pure invariant check) |

## Required PASS Semantics

A checker that returns PASS must:
- State what universe it covered.
- State how many objects were discovered.
- State how many were registered.
- State how many were excluded.
- State exclusion reasons if any.

A PASS without a scope statement is an untrustworthy signal.

## Required Exclusion Semantics

Every exclusion must carry:
- `path` — what is excluded
- `reason` — why it is excluded
- `classification` — archive_historical, pending_registration, intentionally_unregistered, etc.
- `owner` — who or what phase is responsible
- `reviewed_at` — ISO date of last review

## Relationship to DG

Document registry coverage is one instance of this contract. The document
governance pack's completeness and identity surface checks are an implementation
of the reconciliation principle.

## Relationship to PV

Public wedge audit, dry-run, and build artifact smoke are all coverage-governed:
- Audit scope: candidate public wedge include/exclude set
- Dry-run manifest: file-level include/exclude with reason
- Build artifact inspection: expected vs forbidden paths

## Relationship to Future Packs

Coding, Finance, MCP, Knowledge, Release, and CI packs must not rely on
silent enumeration. Every Pack-level checker must declare its coverage
model according to this contract.

## Non-Goals

- Does not require checking every file for every checker.
- Does not force all config/runtime files into DG.
- Does not publish or release anything.
- Does not make all checkers perfect — partial is allowed if explicit.

---

*Accepted: 2026-05-01*
*Phase: COV-1*
