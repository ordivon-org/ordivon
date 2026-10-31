# Career Engineering Strategic Rebase R1

Status: **DETACHED CANDIDATE / EXTERNAL-FIRST / NO PRODUCTION CUTOVER**
Source baseline: `main@cbdd02771c7bc7842c38374854ffee703fb666e4`
Observation date: 2026-10-31

## Decision

Do not extend the detached Career R2–R6 chain as if it were the current architecture. Treat it as a donor set for proven boundaries and negative tests. Rebuild Career Engineering from current main around maintained external providers, standards and existing Ordivon Runtime/Host/PostgreSQL ownership.

The product goal is not "an AI job bot." It is an evidence-driven career engineering composition:

```text
Career Record
  -> Opportunity Intake
  -> Role / Competency Model
  -> Evidence & Gap
  -> Artifact Compiler
  -> Application Lifecycle
  -> External Outcome observations
  -> updated Career Record / decisions
```

Resume and cover-letter documents are materialized artifacts. AI job-search systems are replaceable provider/operator modules. Neither becomes the semantic core.

## Provider selection rule

GitHub stars are used as a discovery/community signal. Adoption requires all of:

1. current maintenance or a deliberately stable interface;
2. an exact reusable Skill/MCP/CLI/API/library seam;
3. compatible licensing for the intended mode;
4. a real Ordivon consumer;
5. no duplicate natural authority;
6. an explicit truth/effect boundary.

The dated evidence is `meta/next/evidence/career/github-career-provider-ranking-20261031.json`.

## Selected external stack

| Provider | Observed stars | Maintenance signal | Selected role | Decision |
|---|---:|---|---|---|
| Career-Ops | ~78.9k | 1166 commits/30d; current 2026-10 activity | Career workflow, rubrics, provenance/validation scripts | **ADOPT donor via Skill/CLI** |
| AI-Job-Search | ~68.1k | 133 commits/30d; v1.7.3 current | Source adapters, staged rank/apply methods, input guards | **ABSORB / COMPOSE methods** |
| Reactive Resume | ~45.1k | 267 commits/30d; pushed 2026-10-31 | Primary resume/cover-letter/application product surface; MCP/REST/OpenAPI | **ADOPT product/API/MCP donor** |
| Resume-Matcher | ~29.0k | 542 commits/30d; v1.4.0 | Narrow tailor/verify/score/export artifact compiler | **ADOPT narrow MCP/CLI donor** |
| RenderCV | ~17.9k | 0 main commits/90d | Optional deterministic renderer | **ON_DEMAND** |
| OpenResume | ~9.0k | main last committed 2024-10 | Historical reference only | **NO NEW ADOPTION** |
| JobSpy | ~4.6k | 32 commits/30d; v1.4.1 current | Multi-board discovery fallback through packaged CLI/MCP | **ADOPT pinned external provider** |
| JobSync | ~1.5k | 63 commits/30d; v1.2.0 | Compare ATS discovery/tracker semantics | **TARGETED COMPARE; do not deploy in parallel by default** |
| JSON Resume current monorepo | lower current repo stars; active | 161 commits/30d | Resume interchange schema/ecosystem | **ADOPT standard/interchange** |
| ApplyPack | low stars; very high commit velocity | 689 commits/30d | Local-first watchlist | **WATCH, not primary** |

Star counts are volatile. Exact observations and source heads live in the dated JSON evidence rather than this narrative.

## Why Reactive Resume displaces a custom Career UI

Current Reactive Resume v6 already owns a large coherent product surface that Ordivon should not rebuild:

- structured resumes and cover letters;
- PDF/DOCX/Markdown/JSON export;
- resume checks and keyword matching;
- application List / Board / Calendar / Insights;
- application stages `saved -> applied -> screening -> interview -> offer` plus closed reasons;
- contacts, notes, follow-ups, interviews and sent documents;
- PostgreSQL storage;
- REST/OpenAPI and MCP surfaces.

Therefore a custom Ordivon application board, resume editor, template engine or second tracking UI is DELETE-by-default. Ordivon should compose with the external provider and retain only missing semantic/evidence guarantees.

Reactive Resume application state remains a **user-side case record**. `applied`, `interview` or `offer` must not be promoted to provider-verified external truth unless an independent employer/ATS/email/provider observation supports it.

## Why Career-Ops is a donor, not a new Ordivon database

Career-Ops has the strongest current star/maintenance signal in the Career-specific set and already supports Codex, Claude Code, OpenCode and other agent CLIs. Its useful reusable material includes:

- source-grounded career profile extraction;
- skill/JD gap methods;
- provenance and CV-fact guards;
- ATS/PDF validators;
- staged evaluation and human review;
- outcome/pattern analysis;
- explicit application preparation.

Its file-first tracker and batch state are product-local implementation choices. Ordivon already owns durable execution/state through Runtime, Host and PostgreSQL. Importing Career-Ops storage/scheduler semantics into Core would create duplicate authority. Adopt Skill/CLI/validator behavior, not its storage topology.

## Resume-Matcher composition boundary

Resume-Matcher exposes the same operations through both MCP and a JSON shell CLI. That is a strong external-provider seam. Candidate operations include master-resume creation, score, tailor-and-verify, resume validation, PDF export and application operations.

Ordivon should initially permit only artifact/compiler operations that provide unique value beyond Reactive Resume. It must **not** establish a second application source of truth merely because Resume-Matcher happens to expose application CRUD.

## Opportunity acquisition order

Use the least brittle authoritative source first:

```text
official ATS API / company structured feed
    -> Schema.org JobPosting / provider-native structured page
    -> official company career page
    -> selected maintained adapter
    -> JobSpy fallback
    -> generic browser/scrape only when justified
```

JobSpy is deliberately a fallback provider. It can observe supported boards, but scraping success, Terms of Service, anti-bot behavior and vacancy freshness remain source-specific external facts.

## Career semantic core after rebase

### CE1 Career Record

References identity, education, experience, projects, credentials, claims and evidence. Prefer external vocabularies/interchange such as Trusted Career Profile, JSON Resume, Open Badges/ELM, ESCO/O*NET identifiers where useful. Personal raw records stay private.

### CE2 Opportunity Intake

Normalizes one externally observed opportunity without claiming completeness or current availability. Provider identity, source time, capture time and currentness are explicit.

### CE3 Role / Competency Model

Separates hard eligibility from tasks, competencies, skills and preferences. O*NET/ESCO are reference vocabularies, never a substitute for the exact job description or employer criteria.

### CE4 Evidence & Gap

Maps claims and evidence to the target role. Missing resume keywords are not automatically missing ability. Output must distinguish verified evidence, user assertions, derived mappings and unknowns.

### CE5 Artifact Compiler

Materializes resume, cover letter, portfolio snippets, application answers and interview packets from approved facts/evidence. External providers may implement compilation/validation. No artifact compiler owns application state.

### CE6 Application Lifecycle

Durable case state belongs to the selected product surface plus Ordivon composition/evidence. State changes with reputational or external effects require explicit human approval. Existing Runtime/Host provide durable execution primitives; Career must not create its own scheduler/runtime.

## Formal / type-driven constraints

Minimum invariants:

```text
SubmittedApplication => observed submission effect or explicitly UNVERIFIED_USER_CLAIM
ExternalOutcome       => provider/external observation OR status remains UNVERIFIED
ArtifactClaim         => references Career Record claim/evidence or is marked unsupported
IrreversibleEffect    => HumanApproval
UNKNOWN               != FAIL
Drafted               != Submitted
ProductCaseState      != EmployerTruth
ProviderObservation   != FutureAvailability
```

The useful formalization target is these state/authority boundaries, not proving a model-generated fit score.

## R2–R6 donor retention / deletion

Retain as donors:
- exact SourceCut/currentness fencing patterns;
- three-valued qualification;
- private-input negative tests;
- claim vs evidence vs external truth separation;
- drafted vs submitted separation;
- provider identity checks and linked-source falsification.

Demote to specimens:
- HKUST-specific IELTS route;
- rust-analyzer #23553 and linked PR logic.

Delete from future Career ownership unless a real consumer proves otherwise:
- generic Agent capability registry/reference ownership;
- a Career-owned execution runtime or scheduler;
- employer onboarding subsystem before an actual employer-authorized consumer;
- duplicate resume/application UI and duplicate provider databases.

## First vertical slice

The first real slice is intentionally read-mostly:

```text
official/selected job source
 -> normalized Opportunity
 -> hard eligibility + role/competency extraction
 -> Career Record evidence binding
 -> gap report
 -> evidence-linked resume variant
 -> deterministic artifact checks
 -> human approval
```

Do not auto-submit in this slice. A later submission path must have an actual provider-effect consumer and receipt/reconciliation contract.

## Current standing

This document records a strategic candidate. It does not claim that Reactive Resume, Career-Ops, Resume-Matcher or JobSpy is installed in production, that any job board is currently reachable, or that any application effect occurred. The JobSpy pinned package smoke is recorded separately after execution.
