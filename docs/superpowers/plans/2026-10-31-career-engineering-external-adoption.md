# Career Engineering External Adoption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebase Ordivon Career Engineering on current, highly maintained external providers and refresh GitHub star-discovery evidence without extending the detached Career R2–R6 experiment chain.

**Architecture:** Preserve current `main@cbdd02771c7bc7842c38374854ffee703fb666e4` as the source baseline and treat prior Career branches as evidence/security donors only. External projects remain provider authorities behind narrow Skill/MCP/CLI/API seams; Ordivon owns composition, evidence/currentness, durable Runtime/Host state, and explicit human/effect boundaries rather than copying product implementations.

**Tech Stack:** GitHub CLI/API, Markdown/JSON evidence, Agent Skills/MCP provider seams, existing Ordivon Runtime/Host/PostgreSQL.

**Spec:** `meta/next/docs/CAREER_ENGINEERING_STRATEGIC_REBASE_R1.md`

## Global Constraints

- DELETE / REUSE / COMPOSE before EXTEND / CREATE.
- High GitHub stars are a discovery/maturity signal, never correctness or adoption proof.
- Prefer active MIT/Apache projects with recent commits/releases and narrow reusable interfaces.
- Do not create a second Runtime, scheduler, global registry, or Career-owned execution engine.
- Do not make an external product database authoritative for employer/university/provider truth.
- Pin provider versions/commits for reproducible execution; separately observe latest stable versions for upgrade decisions.
- Human approval remains required before irreversible application/communication effects.
- No production/main mutation or provider-side application submission in this candidate.

---

### Task 1: Refresh GitHub global and Career-specific ranking evidence

**Files:**
- Create: `meta/next/evidence/career/github-career-provider-ranking-20261031.json`
- Create: `meta/next/knowledge/lessons/github-top100-capability-radar-r2.md`

**Interfaces:**
- Consumes: GitHub repository/search API via authenticated `gh api`.
- Produces: dated immutable discovery evidence and a human-readable R2 radar snapshot.

- [ ] **Step 1:** Query GitHub Search API for `stars:>100000`, sorted descending, exactly 100 rows.
- [ ] **Step 2:** Compare current repository identities with R1; preserve R1 as historical evidence rather than overwrite it.
- [ ] **Step 3:** Query Career donor repositories for stars, license, archived state, default-branch head, 30/90-day commit counts and latest release.
- [ ] **Step 4:** Record raw current observations with exact provider identity and observation date.
- [ ] **Step 5:** Validate row counts, uniqueness, descending star order and required fields with Python assertions.

### Task 2: Define strategic provider selection and authority boundaries

**Files:**
- Create: `meta/next/docs/CAREER_ENGINEERING_STRATEGIC_REBASE_R1.md`
- Create: `meta/next/planning/career-external-provider-stack-r1.json`

**Interfaces:**
- Consumes: Task 1 evidence plus current source interfaces inspected at exact upstream heads.
- Produces: selected donor stack and explicit ADOPT / COMPOSE / ABSORB / ON_DEMAND / REJECT decisions.

- [ ] **Step 1:** Select Career-Ops as primary Skill/workflow/validator donor, without adopting its file store as Ordivon canonical state.
- [ ] **Step 2:** Select Reactive Resume as primary product/UI/API/MCP donor for resumes, cover letters and application case tracking; keep external-employer truth separate.
- [ ] **Step 3:** Select Resume-Matcher as a narrow MCP/CLI artifact compiler/verification donor only where it adds functionality not already supplied by Reactive Resume.
- [ ] **Step 4:** Select JobSpy as a pinned MCP discovery fallback after official ATS APIs; encode scraping/currentness/ToS uncertainty.
- [ ] **Step 5:** Mark AI-Job-Search as workflow/adapter method donor, JobSync as targeted comparison, RenderCV on-demand, OpenResume stale/no-new-adoption, JSON Resume as interchange standard, ApplyPack as watchlist.
- [ ] **Step 6:** Encode Career core as Career Record → Opportunity Intake → Role/Competency → Evidence/Gap → Artifact Compiler → Application Lifecycle, all consuming existing Runtime/Host/PG rather than creating a Career runtime.

### Task 3: Prove direct external-provider consumption with a pinned JobSpy smoke test

**Files:**
- Create: `meta/next/evidence/career/jobspy-1.4.1-provider-smoke-20261031.json`

**Interfaces:**
- Consumes: published `python-jobspy==1.4.1` / `mcp-jobspy` package through `uvx`.
- Produces: execution receipt for package availability and exposed CLI/MCP entry points; no job-board write effects.

- [ ] **Step 1:** Run a pinned package command in an isolated temporary cache/environment, not a repository install.
- [ ] **Step 2:** Verify `jobspy` and/or `mcp-jobspy` entry point availability and version/package metadata.
- [ ] **Step 3:** Do not claim live board availability from a help/version smoke; record external network/provider truth as unverified unless separately queried.
- [ ] **Step 4:** Persist command, exit code, observed version, upstream commit/release and authority boundary.

### Task 4: Independent review request and verification

**Files:**
- Modify only if required by failed validation; otherwise no new implementation files.

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces: fresh verification evidence and a Space peer-review request.

- [ ] **Step 1:** Validate all new JSON with `python -m json.tool`.
- [ ] **Step 2:** Run source-policy/architecture checks relevant to `meta/next` documentation/evidence.
- [ ] **Step 3:** Inspect `git diff --check`, status, and exact diff.
- [ ] **Step 4:** Post a bounded peer-review request asking for counterexamples to provider selection, especially Reactive Resume vs JobSync duplication, Career-Ops persistence mismatch, Resume-Matcher overlap, and JobSpy scraping risk.
- [ ] **Step 5:** Do not call the candidate complete or merged; leave it detached until independent review/integration choice.
