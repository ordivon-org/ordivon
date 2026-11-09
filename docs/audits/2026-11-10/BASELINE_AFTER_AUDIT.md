# BASELINE_AFTER_AUDIT — actual source-bound outcome

## Source identity and scope

- Frozen pre-change Git base: ef17d6879d12faa61fff3bb762b0d500d73c9113
- Initial tracked-file census: 5002 paths; 21 Owner roots; 1460 Python files parsed AST, no parse failure.
- Audit evidence: six Markdown files and one FILE_INVENTORY.csv. No new CI, test, Agent or execution service added.
- Repo source change: only services/harness/pyproject.toml stale Python 3.14 Trove classifier removed; requires-python ==3.15.1, Python major classifier and mise 3.15.1 retained.
- Concurrent PR #2009 separately retires Harness two broken historical runners; not duplicated or claimed as this branch's diff.

## Actual verification already observed

| Verification | Status | Evidence / scope |
|---|---|---|
| Git 5002 rows and 64-char hashes in CSV | PASS | local Python csv.DictReader; every semantic field left pending |
| Python AST syntax in frozen source | PASS | 1460 parsed, zero parse errors |
| check_owner_boundaries.py | PASS | reported 2320 active source files, 10 packages, 31 seams |
| test_owner_boundaries.py and test_affected_owners.py | PASS | native existing unittest/CLI; 45 tests shown across root invocation output |
| check_architecture_docs.py + test_architecture_docs.py | PASS | existing root documentation tests |
| check_structure_r2.py | PASS | existing structure source check |
| Harness pyproject and mise requirements alignment | PASS | exact requires-python ==3.15.1, no classifier 3.14 |
| Native Harness uv lock --check, Ruff, compileall, scripts/check_docs.py | PASS | existing owner checks |
| Harness wheel build and exact installed wheel metadata | PASS | uv build --offline; isolated wheel bytes Requires-Python ==3.15.1 and no Python 3.14 classifier |
| Harness existing check_wheel.py | PASS | official package check with disposable PostgreSQL 18, live Host-free Harness PG reopen/doctor |
| Harness existing non-node pytest | PASS | 1425 passed, 73 skipped, 2 deselected, 386 subtests passed; skipped are NOT PASS |
| Full repo:ci, all 21 Owner verify, installed systemd/Windows consumers | NOT RUN | outside narrow metadata change and no production effect in this audit |

## Original failure and corrected execution

The first package-wheel verification stopped with HARNESS_PG_TEST_DSN required (environment was missing, not a source assertion failure). It was rerun using disposable Docker postgres:18, a fresh temporary database/user/password and an automatically reclaimed container. The owner-native check_wheel then passed, including an independent Host-free PostgreSQL smoke and installed wheel interface. This verifies package behavior within the declared test scope; it does not claim Windows, production Host or persistent side effects.

## Before vs after

| Property | Before | Source-qualified after |
|---|---|---|
| Harness Python version constraint | ==3.15.1 | unchanged |
| Harness advertised Python minor classifier | 3.14 (false relative to exact constraint) | removed, no duplicate version authority |
| Public CLI and Python API | baseline | unchanged by this source diff; isolated wheel check PASS |
| Python runtime tests | existing suite | 1425 passed / 73 skipped / 2 deselected in current test invocation |
| Git changes | baseline | one-line metadata removal plus audit deliverables; no app feature |
| Other Owner semantic files | unreviewed/partially reviewed | still unreviewed/partially reviewed, explicitly not certified |

## Unfinished obligations and accepted risks

1. Full 5002-file dynamic semantic audit and all 21 Owner remodels remain incomplete. Every CSV row states SEMANTIC_REVIEW_PENDING; this report cannot substitute for that work.
2. Installation SourceCut and Windows Runtime PostgreSQL-native migration are not inferred from this Git metadata edit.
3. Concurrent PRs #2006/#2010/#2012/#2013/#2014 around the Owner programme must be reconciled by Repo owner; this audit deliberately does not edit the canonical programme.
4. Existing PG/SQLite state, original creative assets, service drop-ins and financial legacy replay are retained while real consumers remain; no production database or retention was mutated.
5. Any packaging consumer that relied on an inaccurate Python 3.14 marker might behave differently; direct counterexample must be presented against exact wheel metadata and package contract.

## Rollback and claim boundaries

Revert the exact Git commit that changes pyproject and this snapshot; no migrations or environment mutation are part of that commit. Disposable PostgreSQL was removed by shell trap. SOURCE-qualified does not automatically mean PR merged, wheel installed on every machine or domain outcomes consumed.

## Cross-agent handoff contract

Status: SOURCE_VERIFIED, PR/merge unknown until GitHub check.
Completed: 5002-file physical inventory, 21 module report, one stock-only metadata repair, root and Harness native validations.
Outstanding: complete per-file semantic consumer inspections under each Owner, reconcile concurrent PRs, sample dynamic import edges and install state.
Evidence: this audit folder; frozen Git SourceCut; original pyproject and wheel output; Host Space coordination message; GitHub PR HEAD once published.
Next: Owner-by-owner delete/merge only after actual source or runtime witnesses, and close remaining false currentness statements without creating a new audit framework.
