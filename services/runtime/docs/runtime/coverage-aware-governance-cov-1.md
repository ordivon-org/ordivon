# COV-1 — Coverage-Aware Governance Generalization

## Purpose

Generalize VD-005 and PV enumeration blind spots into a cross-Ordivon
coverage governance model. A checker that does not declare what universe
it covers is producing an untrustworthy signal.

## Incident Pattern Generalized

Three documented failures of the same class:

1. **VD-005 (document registry):** Checker returned PASS on 31 registered docs
   while 142+ unregistered docs existed. Fixed by adding completeness scan.

2. **pr-fast wave_files (PV-N7):** Ruff format gate returned PASS on 9 whitelisted
   files while new test files outside the list were unformatted.

3. **Build artifact inspection (PV-N8):** Wheel inspection detects 244 private core
   files because pyproject.toml scope is not wedge-only.

Root cause: checker scope defined by enumeration, not discovery. New objects
created outside the enumeration are invisible.

## First-Principles Analysis

A governance checker has four responsibilities:
- **Universe:** What objects does it claim to govern?
- **Discovery:** How does it find objects in that universe?
- **Validation:** What invariants does it check?
- **Reconciliation:** Does it cross-reference discovered objects against known objects?

A checker that only validates (step 3) without declaring universe (step 1),
discovering objects (step 2), or reconciling (step 4) can silently miss new objects.

## Four-Quadrant Model

| Quadrant | Governance Action | Example |
|----------|------------------|---------|
| Known Known | Validate with checker | Registered docs pass freshness |
| Known Unknown | Manage with debt + exclusions | Pending registration docs |
| Unknown Known | Encode in docs/registry | PFIOS→Ordivon identity in README |
| Unknown Unknown | Discover via reconciliation | Completeness scan finds new .md files |

## What Was Added

1. `coverage-governance-contract.md` — 6 core invariants, checker responsibility model
2. `checker-coverage-manifest.json` — 10 checkers, each declaring universe/discovery/exclusions
3. `check_coverage_governance.py` — validates manifest, 15 tests
4. Baseline integration: 12th hard gate (11→12)

## Checker Coverage Manifest Summary

```
10 checkers:
  Implemented: 7 (document_registry, verification_manifest, paper_dogfood,
                   public_wedge_audit, public_repo_dryrun, private_install_smoke,
                   build_artifact_smoke)
  Partial:     3 (verification_debt, receipt_integrity, pr_fast_baseline)
  Deferred:    0
```

## Baseline Integration

pr-fast: 11/11 → 12/12 PASS. New gate: `coverage_governance` (L4, hard).

## Artifact Integrity Incident

During COV-1, governance JSON artifacts were corrupted by formatter/tooling scope misuse:

- `checker-coverage-manifest.json` and `verification-gate-manifest.json` received
  invalid trailing commas when a formatter whose supported extensions (python,
  pyi, ipynb, markdown — not json) was applied to .json governance artifact files.
- `document-registry.jsonl` was temporarily zeroed by a repair script that
  discarded all entries when parsing failed after the JSON corruption.

Root cause classification: **JSON/JSONL governance artifacts were exposed to an
unsafe formatting/repair path.** The formatter's extension scope (Python +
Markdown) was overextended onto data artifact files. Whether the triggering
mechanism was Ruff wrapper, preview scope, editor integration, or script
misprocessing is secondary — the governance invariant is that JSON/JSONL
artifacts must never travel through a non-JSON formatting pipeline.

Governance conclusion: **Governance artifacts are executable data, not prose.**
Their authoritative validator is the parser + schema/checker, never a formatter.

Resolution:
- Restored `document-registry.jsonl` from git HEAD
- Rewrote JSON manifests via `json.dump()` and re-verified with `json.loads()`
- Added 3 COV-1 registry entries as single-line JSONL via `json.dumps(separators=(",", ":"))`
- Added `check_governance_artifacts()` to `check_coverage_governance.py`:
  validates all 3 governance JSON files, 2 JSONL ledgers, gate_count vs gates length
- Narrowed ruff commands to exclude .json and .jsonl files from formatter scope
- New principle: **Governance artifacts are executable data, not prose.**

This incident is COV-1's core case law — proving that coverage governance
must also cover governance artifacts themselves.

## What Remains Partial

- `verification_debt`: no automated discovery of unregistered debt
- `receipt_integrity`: universe bound by configured receipt_paths
- `pr_fast_baseline`: wave_files whitelist is hand-maintained (scope-drift risk)
- `build_artifact_smoke`: currently BLOCKED — 244 private paths in wheel

## What COV-1 Proves

1. Scope drift is a structural problem, not an accidental oversight.
2. Forcing checkers to declare universe/discovery/exclusions closes the discovery gap.
3. Partial status is acceptable when explicit.

## Boundary Confirmation

- Meta-governance only. No release. No publish. No license.
- Phase 8 DEFERRED. Coverage plane active.

---

## COV-1-S — Full Verification Accounting Addendum

The COV-1 core governance verification was sealed with 12/12 pr-fast + 67 governance
tests. This addendum provides the complete cross-Ordivon verification that the
original COV-1 prompt required, so coverage governance does not itself leave a
verification blind spot.

| Verification | Result |
|---|---|
| Product tests (206) | PASS |
| Finance regression (188) | PASS |
| Frontend tests (57) + build | PASS + static OK |
| Eval corpus (24 cases) | PASS |
| Architecture boundaries | PASS |
| Runtime evidence integrity | PASS |
| Public wedge audit | PASS (0 blocking) |
| Public repo dry-run | PASS (16 copied, 13 excluded) |
| Private install smoke | PASS (7/7) |
| Build artifact smoke | BLOCKED (honest — 244 private paths) |
| Coverage governance check | PASS |
| Document registry (34 entries) | PASS |
| Verification debt ledger | PASS |
| Receipt integrity | PASS |
| Verification gate manifest | PASS |
| Paper dogfood ledger | PASS |
| Ordivon Verify (3 entrypoints) | READY |
| pr-fast | 12/12 PASS |

Build artifact BLOCKED is a known PV-N8 gap — a productization blocker, not a
COV-1 governance gap. It is honestly reported in checker-coverage-manifest.json.

*Closed: 2026-05-01*
*COV-1-S addendum: 2026-05-01*
*Phase: COV-1*
