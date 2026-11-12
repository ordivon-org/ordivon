# Artifact — Phase 0: source/consumer and verification baseline (2026-11-10)

> **Status: phase-0 source/consumer, locked-environment test, finite-formal and one Witness counterexample baseline executed; integration/provider/fault-injection and end-to-end performance baselines remain unverified.** This document is a source-cut observation, not current production deployment proof or acceptance of Phase 1–8 work.

## Source boundary

- Linux Stage-0 isolated Workspace: `ws-gpt6-artifact-stage0-20261110-r1`, checked-out commit `c7bbeed016be16f4860fec4ba069f3ee0cb11932` (detached, initially clean).
- Linux `origin/main` observed at `3ad65a19003545878192d45a057c10f5a9e57ea1`; `git diff HEAD..origin/main -- capabilities/artifact` was empty at observation time. This **does not** prove a live deployment is on either revision.
- Concurrent Artifact change: `ws-gpt6-artifact-first-batch-20261110-r1` at `eb23492d371fa00959f22e8b3b76c6d158132302` (commit subject: `fix(artifact): freeze self-contained native verification inputs`). Six Artifact files were changed there, including `artifact_verification/tool_identity.py`, binding JSON and snapshot tests. **Do not duplicate its implementation without reviewing/merging it.**
- Concurrent Windows Artifact consumer reform: `ws-gpt6-artifact-consumer-reform-20261110` at `2deb9733a3afc0b79dbee55764d3eb7023dcc273`; historical read-only audit Workspace at `ef17d6879d12faa61fff3bb762b0d500d73c9113`. Cross-OS workspaces represent different cuts.

## Static inventory and observed entrypoints

- Current source-tree count in `capabilities/artifact/`: **410 files, 191 Python files** (including filesystem items at this cut; not a permanent or deployment count).
- Major top-level source counts: `artifact-delivery/` 179; `tests/` 70; `scripts/` 42; `artifact_capabilities/` 22; `artifact_verifiers/` 21; `docs/` 19; `artifact_core/` 11; `artifact_verification/` 9; `artifact_operations/` 8; `artifact_trust/` 7; `artifact_evidence/` 3.
- Agent proposal/coverage entrypoint: `scripts/artifact_agent_surface.py` (390 lines); native profile verifier: `scripts/artifact_verify.py` (342 lines); independent v1 stage: `artifact_verification/stage.py` (378 lines).
- Durable orchestration: `scripts/artifact_temporal_workflow.py` and `artifact_operations/receipt.py`; direct local delivery: `scripts/artifact_deliver_html.py`; standard provider composition: `artifact_capabilities/dispatch.py`.
- Actual native consumers demonstrated by repository tests: `tests/test_artifact_consumer_acceptance.py` for WAVE/FLAC/PNG/Parquet; HTML browser/readback tests in `tests/test_artifact_deliver_html.py`; Temporal, receipt, native identity and claim-binding tests under `tests/`. These are **test consumers**, not evidence of live external adoption.
- Actual cross-owner source dependency: `capabilities/media/src/ordivon_studio/creative_index.py` imports `creative_index_artifact.py`; `creative_index_artifact.py` reads Artifact delivery data; Media tests `capabilities/media/tests/test_creative_index.py` reference the binding/acceptance data. Removing Shadow profiles or bindings requires consumer migration.
- Repository governance/documentation references exist in `tools/repo/dependency_contracts.toml`, `tools/repo/owners.toml`, `docs/architecture/`. Their references do not in themselves prove runtime deployment.

## Four-flow consumer graph (source-level)

1. **Control:** domain/agent intent → `scripts/artifact_agent_surface.py` → proposed Runtime execution / optional Temporal → `artifact_operations/` → native provider.
2. **Content:** file(s) / source commitment → `artifact_core/` admission and identity → `artifact_capabilities/` / native builder → native verifier → delivered file.
3. **Evidence:** Profile / capability binding → original native observation → Claim/Witness matching → verification stage/standing → optional Trust/OCI. The legacy `stage.py` and v2 `artifact_verify.py` remain separate evaluation backbones at this cut.
4. **Feedback:** actual readback / consumer rejection / effect uncertainty → corresponding domain, Runtime, Artifact or delivery owner → corrected input/contract/operation. Claim-level technical PASS does not establish consumer-domain acceptance.

## Environment probe and attempted tests

- System Python observed: **3.14.6**; repository requires **CPython ==3.15.1** in `pyproject.toml` and `.python-version`. Version 3.15.1 is installed under uv-managed Python.
- Executables found in PATH on this *Linux Stage-0 node*: `pytest`, `uv`, `git`, `ffmpeg`, `ffprobe`, `node`, `cosign`, `opa`, `docker`, `rg`. No PATH entry for `pandoc`, `oras`, `chromium`, `firefox`, `pnpm` in that probe. Other nodes/providers may have different capabilities.
- A selected pytest invocation across eight existing test modules was actually attempted using system Python. It stopped in collection with **7 import errors** from missing `jsonschema`; no correctness conclusion can be drawn.
- Retried with repository-standard `uv run --offline --locked python -m pytest …`; uv selected **Python 3.15.1**, created ignored `.venv`, but could not install **`temporalio==1.34.0`** because its locked wheel was absent from local cache and network was explicitly disabled. No tests were executed in this retry.
- **Environment recovered** with `uv sync --locked` (network permitted): Python 3.15.1 environment installed 25 locked packages including jsonschema and temporalio 1.34.0. The initial offline cache failure remains recorded as a diagnostic, not a product failure.
- **Initial performance microbaseline:** five fresh-interpreter imports of `artifact_core.profiles.ProfileRegistry` under warm OS file cache: 88.85, 97.19, 86.65, 72.48, 69.83 ms; median **86.65 ms**. No ProfileRegistry construction, native provider subprocess, end-to-end latency, I/O byte count or p95 workload distribution has been measured. Static counts are inventory only.

## Confirmed vs unresolved

| Topic | Status at this source cut | Immediate follow-up |
| --- | --- | --- |
| Separate v1 stage and v2 verification entrypoints | Confirmed distinct source paths and test consumers | Map common Claim/Standing semantics before migrating |
| Media consumption of Artifact Shadow/binding records | Confirmed import and test references | Record exact projected fields; migrate before deleting |
| Self-contained native snapshot repair in other workspace | Concurrent fix commit found; merge status not established | Compare `eb23492` against current main before A02 |
| Missing python dependencies on Stage-0 node | Observed with actual failing test commands | Restore locked environment and rerun |
| Claim/Witness unrelated-PASS counterexample | **Reproduced at `assess_required_evidence()` pure function boundary:** `colorProfile` native observation FAIL, claim PASS referencing `/imageDimensions` PASS, result `complete: true`, empty issues | Test upstream native adapters/reachability; preserve minimal negative fixture for Phase 2 |
| HTML publish/readback crash window | Source-design risk from prior audit; not fault-injected here | Run bounded failure-injection in disposable target |
| Receipt/remote external-effect Exactly-once | Not established by local ReceiptFence | Model effect/replay boundary; never imply proved exactly-once |
| Runtime/Temporal overlap | Two execution pathways present; required consumers not fully classified | Cross-check durable workflow consumers before removal |
| R2 Mailbox usage | Dedicated script present; exhaustive external provider call inventory not established | Check actual deployment and caller references |
| Timing/I/O/peak-RSS baseline | Not measured | Collect under the complete locked environment |

## Phase-0 completion gates

- [x] Fix exact local source cut, record concurrent Artifact work and mainline comparison.
- [x] Enumerate key source modules, primary entrypoints and Media cross-owner consumer.
- [x] Inventory current verification/consumer/receipt test cases.
- [x] Probe native executables and make a reproducible selected test attempt.
- [x] Recover pinned Python 3.15.1 environment, execute representative tests, existing CI queue subset and three formal checks.
- [ ] Finish all three negative mechanisms: Claim/Witness relatedness **reproduced at pure function boundary**; subject-swap and Receipt replay covered by existing tests, but separate fault-injection evidence and production reachability analysis remain.
- [ ] Capture cold/warm startup and selected native consumer p50/p95, bytes read and subprocess counts.
- [ ] Validate live execution/provider availability separately from source and tool PATH.

This file is a **Phase-0 partial evidence record**. Its unchecked gates must not be promoted to Phase-0 completion or treated as proof of Phase-1–8 implementation.
## Executed validation addendum (2026-11-10, same c7bbeed cut)

1. **Initial selected core suite:** 8 test files (input snapshot, binding authority, native identity, operation receipt, Claim Results, Standing Decision, Agent Surface, consumer acceptance), `-m "not integration"`: **62 tests passed**, exit 0. This is separate from, and overlaps with, the broad suite below.
2. **Repository CI queue-compatible non-integration pytest command:** `uv run --locked python -m pytest -m "not integration" --disable-warnings --maxfail=5` plus the exact six `--deselect` items and two `--ignore` paths listed under `mise.toml` `[tasks.queue]`. **519 passed, 3 skipped, 42 deselected, 1 warning, 115 subtests passed; exit 0; 77.75 seconds.** This covers existing tests but cannot establish workstations' external native provider acceptance.
3. **Finite formal checks using locked Python:** `artifact_verification/formal/verify_claim_coverage.py` → 289,008 abstract states, 0 counterexamples; `verify_native_identity.py` → 216 states, 0 counterexamples; `verify_profile_refinement.py` → 1,024 states, 0 counterexamples. All three exit 0. Their declared nonclaims remain applicable (not full arbitrary JSON equivalence, real native tool correctness, physical effect or domain acceptance).
4. **New stage-0 negative probe with no product source edits:**
   - `requiredEvidence`: `colorProfile` and `imageDimensions` both mandatory.
   - Raw native `colorProfile.status=FAIL` and `imageDimensions.status=PASS`.
   - Claim `colorProfile.status=PASS` points to `/imageDimensions` rather than color evidence.
   - `artifact_verification.claim_coverage.assess_required_evidence(...)` returned `complete=true` and empty issues. **The existing function checks pointer target status, not Claim/Witness semantic correspondence.** This is a confirmed *local function-boundary* behavior; no claim is made that all production adapters accept arbitrary forged native reports.
5. **Microbenchmark limitation:** the 5 repeated import times above use a warm filesystem cache and fresh Python subprocesses. They do **not** justify a performance optimization without a cold-start/workload baseline.

## Phase-1/2 handoff

- **A02 / subject continuity:** inspect and incorporate the already-existing `eb23492` input snapshot repair before creating another implementation; extend to sidecars only for demonstrated consumer dependency closures.
- **A04 / Witness relatedness (high-value confirmed reproducer):** constrain pointer validity by the existing native result schema or authoritative adapter-generated Claim/Witness mapping. Do not hardcode an all-format pointer dictionary or invent a second Evidence registry.
- **A05 / one Standing semantic owner:** keep v1/v2 behavior intact until their common semantic subset and separate consumer requirements are compared.
- **A06/A07 / recovery:** plan controlled crash experiments on disposable outputs; never infer external Exactly-once or successful delivery from a local Receipt alone.

## Supplementary baseline: lint and repeated native consumer readback

- `uv run --locked ruff check` over the directories and entrypoints listed by `mise.toml` `[tasks.queue]`: **exit 0, "All checks passed!"**.
- `tests/test_artifact_consumer_acceptance.py` executed 3 times with the locked Python and fresh pytest subprocesses: **8/8 passed on each run**. Measured process wall times: **1.946 s, 1.476 s, 1.298 s**, median **1.476 s**. These measurements include fixture creation and local native readback; they are not latency of a production consumer or an isolated native verifier.
- Coverage exclusions are preserved: Stage-0 Linux PATH did not expose Pandoc, ORAS, Chromium/Firefox, so the full offline HTML browser acceptance and OCI publication through actual external tools remain **unobserved here**, even though their unit and non-integration contracts are covered by the queue suite.
- The closest actionable confirmed Phase-2 source defect is still **Claim/Witness semantic mismatch at the pure function boundary**. Scope and upstream-reachability investigation must precede claims about exploitability.
