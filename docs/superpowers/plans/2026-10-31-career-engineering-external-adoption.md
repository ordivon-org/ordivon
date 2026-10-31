# Career Engineering External Adoption Implementation Plan

> **For agentic workers:** Use execution + independent verification; provider popularity is discovery evidence only.

**Goal:** Rebase Career Engineering on maintained external providers without extending the detached Career R2–R6 experiment chain or creating duplicate Ordivon infrastructure.

**Source baseline:** `origin/main@ffd81854b424b4fb136715a8ea022ca3b28fc2e7`\n**Original audit baseline:** `cbdd02771c7bc7842c38374854ffee703fb666e4`; candidate rebased on 2026-11-01 after verifying the intervening main changes did not touch Career/provider-owned paths.

## Global constraints

- DELETE / REUSE / COMPOSE before EXTEND / CREATE.
- Stable release/package/commit is the executable provider contract; main is candidate future capability.
- Do not create a second Runtime, scheduler, registry, application UI or canonical application DB.
- No durable SQLite Career state.
- Human approval before irreversible application/communication effects.
- Provider scores are diagnostics, never hiring probabilities.

### Task 1 — Refresh GitHub global and Career ranking evidence

- [x] Query GitHub Top-100 by current stars and preserve R1 history.
- [x] Record Career donor stars, license, archived state, exact head, 30/90-day commits and latest release.
- [x] Validate exact 100-row Top-100, uniqueness and descending order.
- [x] Create dated Career ranking evidence and global R2 radar.

### Task 2 — Select providers and delete duplicate ownership

- [x] Career-Ops = workflow/Skill/validator donor, not canonical database.
- [x] Reactive Resume = primary product/UI/API/MCP donor; delete custom resume/application UI by default.
- [x] Resume-Matcher = narrow artifact compiler/verifier, not application-state authority.
- [x] JobSpy = pinned fallback after authoritative/structured sources.
- [x] AI-Job-Search = method/adaptor donor; JSON Resume = interchange; RenderCV = on-demand.
- [x] JobSync = absorb Greenhouse/Lever/Ashby discovery methods; do not deploy a parallel tracker product.
- [x] Keep Career Core at Career Record → Opportunity → Role/Competency → Evidence/Gap → Artifact Compiler → Application Lifecycle.

### Task 3 — Prove direct JobSpy external consumption

- [x] Pin `python-jobspy[mcp]==1.4.1`.
- [x] Verify distribution and `jobspy` / `mcp-jobspy` entry points.
- [x] Materialize Agent Plugins 1.0 candidate without copying scraper source.
- [x] Keep live-board/ToS/currentness outside the package smoke truth boundary.

### Task 4 — Stable-provider currentness and native-interface qualification

- [x] Career-Ops `1.38.0`: npm executable + full ephemeral init + doctor + fresh-state verification.
- [x] Detect Career-Ops release/main drift: released `keyword-match` lacks main-only `--url/--jd-text`.
- [x] Reactive Resume: verify upstream-native Agent Plugin/MCP schema on observed main.
- [x] Reactive hosted MCP: observe reachable OAuth-protected boundary without credentials.
- [x] Resume-Matcher stable `1.4.0`: negative default-Python probe and positive Python 3.13 CLI/get_status.
- [x] Record Resume-Matcher default SQLite as non-admitted durable Career state.

### Task 5 — Real vertical slices without external effects

- [x] Capture a live opportunity from official Cloudflare Greenhouse API.
- [x] Run Career-Ops release skill extraction and keyword coverage on synthetic CV.
- [x] Bind diagnostic output to truth boundary; do not infer eligibility/hiring probability.
- [x] Create/read-back synthetic Resume-Matcher master from provider canonical state.
- [x] Positive preservation test: summary/bullet rewrite accepted.
- [x] Negative preservation test: institution identity mutation rejected.
- [x] Run draft score without application CRUD; type score as provider diagnostic.
- [x] Keep all provider-local SQLite use ephemeral; no Ordivon durable SQLite introduced.

### Task 6 — Verification and independent falsification

- [x] Validate JSON evidence and provider contract tests for first candidate.
- [x] Validate JobSpy Agent Plugin schema/materialization.
- [x] Run architecture documentation drift and `git diff --check`.
- [x] Post independent peer-review request to Career Space (sequence 23952); sent request is not consensus.
- [x] Re-run expanded contract tests after the stable-provider/slice updates (7/7 PASS plus plugin/schema/architecture/semantic checks).
- [x] Commit the stable-provider/slice update as a second detached candidate commit.
- [ ] Post exact second commit + new counterexamples to Space and inspect any reply.
- [ ] Do not merge/cut over until integration selection and independent review are explicitly observed.
