# Coverage Plane — From Validation-Aware to Coverage-Aware Governance

> Ordivon does not only verify claims. It verifies the coverage of the world
> those claims refer to.
>
> Ordivon 不只验证声明本身，还验证声明所指向的世界是否被完整覆盖。

## What Changed

VD-005 exposed a meta-governance gap: `check_document_registry.py` returned PASS
but only validated registered documents. Unregistered current-scope docs and
identity-bearing config surfaces were invisible to the checker.

PV-N2H closed this gap by adding a **coverage plane** — a new layer of governance
that asks not "are the registered items correct?" but "are all relevant items
registered?"

## Current Implementation

Two new functions in `check_document_registry.py`:

- `check_completeness()` — discovers all `.md` files under `docs/ai`, `docs/governance`,
  `docs/product`, `docs/architecture`, `docs/runtime` and verifies each is registered
  or excluded with reason.

- `check_identity_surfaces()` — validates `pyproject.toml`, `package.json`, `README.md`,
  and `tests/conftest.py` do not carry legacy PFIOS identity.

Supporting artifact: `document-registry-exclusions.json` (143 entries, each with
reason, classification, owner, reviewed_at).

## The Four-Quadrant Governance Model

| Quadrant | What It Is | Governance Action |
|----------|-----------|-------------------|
| **Known Known** | Registered, validated objects | Checker validates |
| **Known Unknown** | Known exclusions, deferred debt | Debt ledger + exclusions |
| **Unknown Known** | Human knowledge not machine-encoded | Docs, registry, onboarding |
| **Unknown Unknown** | Undiscovered objects | Discovery scan |

Governance maturity = migrating objects leftward and downward through this matrix.

## Core Invariants

1. **PASS is scoped.** Every PASS result must declare its coverage universe.
2. **Coverage precedes confidence.** A check is only trustworthy if its object
   discovery model is complete.
3. **Silent omission is not governance.** Every exclusion must be explicit
   and justified.
4. **Identity-bearing surfaces are governance-relevant.** Files that carry
   project identity (package metadata, README, config headers) are governance
   objects, not raw configuration.

## COV-1 Generalization

The coverage plane graduated from a DG-specific check to a cross-Ordivon
governance contract in COV-1:

- `docs/governance/coverage-governance-contract.md` — 6 invariants, checker
  responsibility model, known/unknown quadrant model
- `docs/governance/checker-coverage-manifest.json` — 10 checkers, each declaring
  universe, discovery method, exclusion policy, known gaps
- `scripts/check_coverage_governance.py` — validates the manifest; 12th hard gate
- 15 tests in `tests/unit/governance/test_coverage_governance.py`

Every checker must now declare:
- What universe it claims to cover
- How it discovers objects in that universe
- What its exclusion policy is
- What known gaps remain
- What its PASS scope statement is

## Core Candidate Principles

These have been promoted from DG-specific to Core governance principles:

1. **Coverage precedes confidence.**
2. **PASS is scoped.**
3. **Silent omission is not governance.**
4. **A checker is only as trustworthy as its discovery model.**
5. **Registry must reconcile with repository reality.**

## Future: Cross-Pack Coverage

The coverage plane is currently implemented inside the Document Governance checker.
It should eventually become a cross-cutting concern:

- **Finance Pack:** Are all broker actions, paper orders, and API writes registered?
- **Coding Pack:** Are all files in the diff declared? Are forbidden files detected?
- **Verify Pack:** Do receipt claims match discoverable changed files?
- **Knowledge Pack:** Are all high-impact docs indexed?

When coverage checks serve multiple packs, they graduate from DG extension
to Core governance plane.

## Product Direction

Ordivon Verify can evolve from "receipt checker" to "AI work coverage auditor":

> User: "I'm done."
> Ordivon: "You claim these files changed. Discovery scan found these additional
> files you didn't mention. The PASS is scoped to 8 of 11 changed files."

This transforms Ordivon Verify into a trust-quality tool for AI-generated work.

---

*Created: 2026-05-01, post VD-005 closure*
*Status: living document — evolves with coverage plane implementation*
