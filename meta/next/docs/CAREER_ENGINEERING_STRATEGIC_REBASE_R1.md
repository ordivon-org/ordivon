# Career Engineering Strategic Rebase R1

Status: **DETACHED CANDIDATE / EXTERNAL-FIRST / NO PRODUCTION CUTOVER**
Source baseline: `origin/main@ffd81854b424b4fb136715a8ea022ca3b28fc2e7`\nOriginal audit baseline: `cbdd02771c7bc7842c38374854ffee703fb666e4`; rebased 2026-11-01 after verifying no intervening Career/provider path overlap.
Observed through: **2026-11-01**

## Decision

Do not extend the detached Career R2–R6 chain as if it were current architecture. Retain it only as a donor for proven evidence/currentness/security boundaries. Career Engineering is rebuilt from current main around maintained external providers and Ordivon's existing Runtime / Host / PostgreSQL substrate.

The semantic composition is:

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

A resume is a materialized artifact. An AI job-search project is a replaceable provider/operator. Neither becomes Career Core.

## Stable release is the executable contract

Provider selection now separates three different facts:

```text
upstream main          = discovery of possible future capability
stable release/package = executable provider contract
live hosted service    = independently currentness-observed external service
```

This distinction was falsified in practice. Career-Ops `main` documents `keyword-match --url/--jd-text`, while the actually published `1.38.0` release does not; executing `--url` against the release returned `Unknown option: --url`. Therefore no Career capability may be admitted merely because it exists on upstream main.

Durable executions pin exact release/package/commit identities. Floating `latest` is a discovery signal, not a durable execution contract.

## Selected external stack and actual adoption evidence

| Provider | Role | Executable boundary | Current standing |
|---|---|---|---|
| Career-Ops | workflow / rubric / deterministic Career validators | upstream Agent Plugin + Skill + `@santifer/career-ops@1.38.0` | **release init verified** |
| Reactive Resume | primary resume / cover-letter / application product surface | upstream native Agent Plugin + hosted/self-hosted MCP/REST | **native plugin schema + hosted OAuth boundary verified** |
| Resume-Matcher | narrow artifact compiler / preservation / ATS diagnostics | stable v1.4.0 CLI/MCP under Python 3.13 | **stable CLI + preservation tests verified** |
| JobSync | ATS opportunity-discovery method donor | Greenhouse / Lever / Ashby discovery patterns | **absorb methods; no parallel product** |
| JobSpy | discovery fallback | pinned `python-jobspy[mcp]==1.4.1` | **package/plugin smoke verified** |
| AI-Job-Search | workflow and source-adapter method donor | Skills / deterministic guards | **absorb methods, not whole product** |
| JSON Resume | resume interchange | schema ecosystem | **adopt interchange** |
| RenderCV | optional renderer | CLI/library | **on demand only** |

The dated star/maintenance census remains discovery evidence, not acceptance proof.

## Delete-by-default decisions

Because mature providers now cover these surfaces, Career should not build or retain a custom:

- resume editor/template product;
- application board/calendar/CRM UI;
- generic job-board scraper when an official ATS or selected provider exists;
- workflow engine, scheduler, queue or Career runtime;
- global registry parallel to Ordivon's existing module/catalog machinery;
- second canonical application database.

Reactive Resume is the primary product surface. JobSync remains valuable for its ATS discovery methods, not as a second tracker product. Resume-Matcher application CRUD is explicitly excluded from the initial adoption surface.

## Career-Ops: upstream Skill/CLI donor, not database authority

The exact `1.38.0` npm release was installed into an ephemeral directory. Its Agent Skill was present, `doctor --json` correctly reported an unconfigured fresh workspace, and `verify-pipeline` correctly reported that no application ledger existed yet. No user facts were invented to make the smoke pass.

Career-Ops is therefore adopted at the upstream Skill/workflow/validator boundary. Its file-first tracker remains provider-local implementation and does not become Ordivon durable truth.

## Reactive Resume: reuse its native plugin, do not wrap it

Current upstream already ships an Agent Plugins 1.0 plugin and a streamable-HTTP MCP configuration. Those current plugin schemas validate against Ordivon's Agent Plugins 1.0 fixtures. An unauthenticated probe of the hosted MCP returned HTTP 401 plus the OAuth protected-resource challenge, proving the endpoint is reachable and guarded without exposing user data.

Therefore Ordivon should consume the upstream plugin/service directly. A private Reactive Resume wrapper would be redundant. Self-hosted deployment must pin a stable release/image; hosted service currentness is observed independently.

Reactive Resume application state remains **user-side product case state**, not employer truth.

## Resume-Matcher: narrow compiler/verifier with a hard runtime boundary

Stable v1.4.0 is pinned to commit `dcd0962656e3e1ac2b4490689159362f9d48cd32`.

A negative probe on the current host Python 3.15 failed dependency resolution because the tested `onnxruntime` wheel set did not provide `cp315`. The exact same stable provider succeeded under `uvx --python 3.13`. That runtime version is therefore part of the provider contract, not an incidental local detail.

The provider also reports SQLite as its default backend. That is **not admitted as Ordivon Career durable state**. Initial production-facing adoption is biased toward stateless/read-only validation tools; any persistent Resume-Matcher deployment requires explicit PostgreSQL configuration and a real consumer.

Initial admitted tools:

```text
get_status
get_resume_schema
validate_tailored_resume
parse_check_file
score_resume
```

Stateful compilation/rendering tools remain conditional. `create_application / update_application / list_applications` are excluded initially to prevent a second application-state authority.

## First real vertical slices

### Official ATS -> deterministic gap diagnostic

A live Cloudflare `Software Engineer Intern (2027)` posting was captured from the official Greenhouse Job Board API, not through scraping. Career-Ops release `1.38.0` then deterministically extracted:

`Spring, TypeScript, JavaScript, Rust, C++, Python, Go`.

Against a synthetic CV, its keyword diagnostic reported 4/7 coverage (57%). That number is evidence that the deterministic function ran; it is **not** eligibility, offer probability or employer judgment.

Evidence: `meta/next/evidence/career/cloudflare-8245211-career-ops-vertical-slice-20261031.json`.

### Canonical master -> preservation -> scoring

Stable Resume-Matcher v1.4.0 created a synthetic master in an ephemeral provider-local directory. The test then read the master back through `get_resume` before deriving drafts, preserving provider-generated `sectionMeta`.

- changing only summary/bullet text: **accepted**;
- changing the institution from `Synthetic University` to `Invented University`: **rejected** with `education.identity`;
- no application CRUD was invoked;
- a draft ATS diagnostic was returned, but is explicitly typed as a provider diagnostic rather than hiring probability.

Evidence: `meta/next/evidence/career/resume-matcher-1.4.0-artifact-compiler-slice-20261101.json`.

This test also caught a useful composition rule: **read provider-canonical state back before deriving a mutation**. Guessing the provider's generated structure caused the first positive attempt to fail closed.

## Opportunity acquisition order

```text
official ATS API / company structured feed
  -> Schema.org JobPosting / provider-native structured page
  -> official company career page
  -> provider-native ATS discovery (e.g. selected JobSync methods)
  -> JobSpy fallback
  -> generic browser/scrape only when justified
```

JobSpy never displaces first-party sources when they exist.

## Career semantic core

### CE1 Career Record
Private, source-locatable facts, achievements, projects, education, credentials, claims and evidence. External standards/interchange may describe it; external products do not become its truth authority.

### CE2 Opportunity Intake
Captures provider identity, source time, observation time and currentness. A captured listing does not prove future availability.

### CE3 Role / Competency Model
Separates hard eligibility, responsibilities, competencies, skills and preferences. Exact employer criteria outrank generic taxonomies.

### CE4 Evidence & Gap
Maps target requirements to claims/evidence. Missing keyword != missing ability. UNKNOWN != FAIL.

### CE5 Artifact Compiler
Materializes resume/cover-letter/answers/interview packets from approved facts. Provider preservation checks guard source identity; provider match scores remain diagnostics.

### CE6 Application Lifecycle
Durable case state composes existing Runtime/Host and the selected product surface. Irreversible external effects require human approval and external receipt/reconciliation.

## Formal / type-driven invariants

```text
StableProviderCapability => observed in pinned release/package/commit
MainOnlyCapability       => not executable contract
SubmittedApplication     => observed submission effect OR explicitly UNVERIFIED_USER_CLAIM
ExternalOutcome          => provider/external observation OR remains UNVERIFIED
ArtifactClaim            => supported by Career Record evidence OR marked unsupported
IrreversibleEffect       => HumanApproval
UNKNOWN                  != FAIL
Drafted                  != Submitted
ProductCaseState         != EmployerTruth
ProviderObservation      != FutureAvailability
ProviderScore            != HiringProbability
DurableCareerState       => PostgreSQL / existing Ordivon authority, not provider-default SQLite
```

## R2–R6 donor retention / deletion

Retain: SourceCut/currentness fencing, three-valued qualification, private-input negative tests, claim/evidence/external-truth separation, drafted-vs-submitted separation, exact provider identity and linked-source falsification.

Demote to specimens: HKUST-specific IELTS route and rust-analyzer issue experiments.

Delete from future Career ownership unless a real consumer proves otherwise: generic Agent capability registry ownership, Career execution runtime/scheduler, premature employer onboarding subsystem, duplicate resume/application UI and duplicate provider databases.

## Current standing

This remains a detached candidate. It is not merged into main and no production cutover or job application submission has occurred. What is now stronger than the initial candidate is that provider decisions are backed by executable release smokes and two end-to-end synthetic slices rather than repository popularity alone.
