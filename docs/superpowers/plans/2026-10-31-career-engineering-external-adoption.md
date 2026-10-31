# Career Engineering External Adoption Implementation Plan

> **Rule:** DELETE / REUSE / COMPOSE before EXTEND / CREATE. Provider popularity is discovery evidence only; behavioral admission requires a real consumer and reproducible provider-native evidence.

**Goal:** Rebase Career Engineering on maintained external providers without extending detached R2–R6 experiments into a new Career runtime/product stack.

**Source baseline:** `origin/main@277a62019b498614baf7b9666fb7a4c607c5172e`
**Observed through:** 2026-11-01

## Global constraints

- Stable release/package/commit is the executable identity; main is discovery.
- No second Runtime, scheduler, registry, application UI or canonical application DB.
- No durable Career SQLite state.
- Human approval before irreversible communication/application effects.
- Provider case state is not employer truth.
- Provider scores are diagnostics, not outcome probabilities.
- `UNKNOWN != FALSE` and `UNKNOWN != FAIL`.

### Task 1 — Refresh provider discovery evidence

- [x] Refresh GitHub global Top-100 snapshot.
- [x] Record Career donor stars, license, archived state, exact head, 30/90-day activity and release data.
- [x] Keep stars/activity explicitly bounded to discovery/currentness, not correctness or admission.

### Task 2 — Initial external-first decomposition

- [x] Preserve Career semantic chain: Career Record → Opportunity → Role/Competency → Evidence/Gap → Artifact Compiler → Application Lifecycle.
- [x] Delete custom Career runtime/scheduler/registry/UI/database ownership by default.
- [x] Inspect Career-Ops, Reactive Resume, Resume-Matcher, JobSync, JobSpy, AI-Job-Search, JSON Resume and RenderCV as external donors/candidates.

### Task 3 — Stable release/currentness probes

- [x] Career-Ops `1.38.0`: exact release init, doctor/fresh-state observation, release/main drift counterexample.
- [x] Reactive Resume: correct stale `v6.0.2` assumption to latest stable `v6.0.9@854459a...`.
- [x] Validate Reactive Resume native Agent Plugin + MCP schemas on the stable release itself.
- [x] Observe hosted MCP OAuth protection without credentials/user data.
- [x] Resume-Matcher v1.4.0: verify Python 3.13 runtime requirement and default SQLite boundary.
- [x] JobSpy 1.4.1: package/entrypoint smoke only.

### Task 4 — Historical slices

- [x] Capture one live Cloudflare opportunity from official Greenhouse API and run deterministic Career-Ops diagnostics on a synthetic candidate.
- [x] Run Resume-Matcher synthetic preservation experiment and demonstrate institution-identity rejection.
- [x] Keep both truth boundaries explicit.
- [x] Reclassify these slices after independent review: Cloudflare = historical live observation not replay-complete; Resume-Matcher = experiment only, not admission proof.

### Task 5 — Provider overlap/delete challenge

- [x] Reject parallel JobSync tracker/product ownership.
- [x] Reduce JobSync to reference-only because no verified consumer remains.
- [x] Reduce Resume-Matcher to experiment-only because its demonstrated preservation path is stateful and has no qualified PG/canonical-source consumer.
- [x] Reduce JobSpy to dormant fallback because package smoke does not establish board/MCP behavior.
- [x] Delete the Ordivon JobSpy Agent Plugin activation.
- [x] Keep Reactive Resume as interface-qualified/preferred external product surface, not behaviorally admitted.
- [x] Keep only Career-Ops' deterministic gap diagnostic as current behaviorally qualified external capability.

### Task 6 — Independent falsification

- [x] Send Space review handoffs (23952, 23961, 23962); no reply was treated as evidence.
- [x] Run a separate ephemeral Codex CLI review in read-only mode against exact head `baf7f557e0bf...`.
- [x] Record its **BLOCK** verdict and blockers C1/C2/C3.
- [x] Attempt a second Claude CLI review; exclude it because local Claude was not authenticated and produced no review.
- [x] Preserve independent-review evidence in `meta/next/evidence/career/independent-codex-review-baf7f557-20261101.json`.

### Task 7 — Close BLOCK C1: admission boundary mismatch

- [x] Demote Resume-Matcher from active artifact provider to experiment-only/no admitted consumer.
- [x] Remove its generic compiler/scoring/rendering/application roles from the active stack.
- [x] Keep PostgreSQL qualification mandatory before any future persisted provider-state admission.

### Task 8 — Close BLOCK C2/C3: behavioral replay and retained inputs

- [x] Correct Career-Ops boundary: top-level npm CLI is workspace init; diagnostic is an initialized stable-release script.
- [x] Commit exact synthetic JD/CV fixtures.
- [x] Add `meta/next/scripts/replay_career_provider_qualification.py`.
- [x] Replay exact `@santifer/career-ops@1.38.0` and verify release git head.
- [x] Verify deterministic result: resume-supported `TypeScript/Rust/Python/Go`; gaps `Spring/JavaScript/C++`.
- [x] Run provider built-in self-test: **115 passed, 0 failed**.
- [x] Run negative currentness probe: stable release rejects `keyword-match.mjs --url`.
- [x] Separate unit snapshot/composition checks from provider-native behavioral replay.
- [x] Record replay as current admission evidence; retain historical slices only as observations/experiments.

### Task 9 — Integration gate

- [x] Detect remote `main` advance to `277a62019b49...`; audit `ffd81854... → 277a620...` and observe zero exact Career remediation overlap / zero Career-provider related paths.
- [ ] Rebase the complete detached Career candidate chain onto `origin/main@277a62019b49...` before fresh rereview.
- [x] Encode last independent review as BLOCK, not as consensus.
- [x] Remove self-referential "current candidateHead" gate semantics; bind reviews to the exact head they actually reviewed.
- [ ] Commit the BLOCK remediation as a new detached technical candidate.
- [ ] Run a **fresh independent read-only rereview of that exact commit**, explicitly checking C1/C2/C3.
- [ ] If rereview still BLOCKs, repair and repeat.
- [ ] Do not merge/cut over while `mergeAdmitted=false`; production integration is separate from technical qualification.
