# Ordivon 2026 Governance Execution Plan

Status: **CURRENT** | Date: 2026-05-05 | Phase: GWOS-2026
Tags: `strategy`, `governed-work`, `alpha`, `egb`, `pgi`, `verify`
Authority: `source_of_truth` | AI Read Priority: 1

## Thesis

Ordivon's 2026 execution direction is a governed work operating system:

```text
Claim -> Evidence -> Review -> Decision Boundary -> Receipt
      -> Lesson -> CandidateRule -> Maturity
```

The system should make high-consequence work more trustworthy before a person
or team relies on it. It should not become an agent runner, CI replacement,
GitHub bot, auto-fixer, broker, public standard, compliance claim, or action
authorization system.

## First Principles

| Lens | Governance question | Ordivon consequence |
|---|---|---|
| Epistemology | Why should we believe the claim? | Evidence must be inspectable and reproducible. |
| Logic | Does the conclusion follow from evidence? | Receipts cannot overclaim beyond observed checks. |
| Cybernetics | Did the action re-enter a feedback loop? | Every meaningful outcome should produce review or no-rule rationale. |
| Organization governance | Who reviewed, who approved, who owns? | reviewer, approver, and owner stay separate. |
| SRE | How much risk is the stage carrying? | Trust budget is diagnostic input, not permission. |
| Security engineering | What can be abused before runtime? | Threat model, supply-chain evidence, and authority boundaries come first. |
| Product strategy | What earns external trust? | Casebook first, schema later, adapters after evidence. |

## Six Execution Phases

### Phase 1 - Foundation Completeness Round

Goal: make the current core stable against stale numbers, deprecated entry
points, registry drift, and ambiguous application boundaries.

Deliverables:

- Foundation completeness receipt.
- Checker ecosystem audit.
- Application boundary classification report.
- Current-truth guidance: live counts must be marked `observed_at_closure` or
  sourced from checker output.
- Registry drift remains zero before closure.

Exit evidence:

- read-only baseline READY.
- document and artifact registries pass.
- application boundary has no ambiguous "is this governed?" language.

### Phase 2 - Alpha-1 Trust Casebook Hardening

Goal: prove that Ordivon Verify catches trust laundering beyond the first four
fixtures.

Required cases:

- malformed config fail-closed.
- standard mode missing receipt evidence.
- READY/review authorization laundering.
- CandidateRule/Policy confusion.
- missing test command.
- stale current-truth citation.
- missing diff evidence.
- incomplete review.
- DEGRADED treated as pass.
- hidden debt.
- external benchmark overclaim.
- false clean working tree claim.
- safe DEGRADED boundary.

Exit evidence:

- `uv run python scripts/run_alpha_casebook.py` reports at least 12 cases.
- each case reports surface, expected signal, actual signal, and missing
  evidence.
- `READY` remains `READY_WITHOUT_AUTHORIZATION` in trust output.

### Phase 3 - EGB-3 Operating Governance

Goal: move engineering governance from reference plan to daily operating
discipline without prematurely hard-gating shadow surfaces.

Deliverables:

- OEP lifecycle: `draft -> shadow_tested -> red_teamed -> owner_reviewed ->
  active_or_closed`.
- Ownership manifest extends toward application/pack/adapter boundaries.
- Freeze protocol becomes a warning gate, not a hard gate yet.
- Trust-budget reports distinguish historical samples from current blockers.
- Red-team fixture for reviewer/approver/owner confusion.

Exit evidence:

- EGB checkers remain shadow-first.
- any promotion requires red-team evidence and owner review.

### Phase 4 - Agent-Native Evidence Surfaces

Goal: import evidence from skills, memory, content, traces, checkpoints, and
MCP-like manifests without becoming a runtime.

Deliverables:

- Skill safety review for `SKILL.md`, frontmatter, scripts, allowed tools,
  credential language, and authorization overclaim.
- Memory/content hygiene for source receipt, freshness, project scope, and
  authority confusion.
- Harness evidence import for failed tool calls, checkpoints, review nodes, and
  retained traces.
- MCP boundary checker for token/resource/audience language.

Exit evidence:

- all imports are read-only.
- no SDK, API server, MCP server, public platform, token refresh, or tool
  invocation claim is introduced.

### Phase 5 - Supply Chain + Public Verify Wedge

Goal: prepare `ordivon-verify` as a bounded public wedge without claiming a
standard, release, compliance, or production readiness.

Deliverables:

- package audit for private path leakage and public overclaim.
- SLSA/OpenSSF-inspired evidence track without SLSA level or compliance claim.
- three-layer install smoke: source import, wheel install, external trust
  fixture.
- quickstart converges on `ordivon-verify check .`.

Exit evidence:

- package smoke passes.
- public docs remain honest and bounded.
- no publication action is authorized by the receipt.

### Phase 6 - Companion Governance Packs

Goal: connect Ordivon's root meaning to creator companion governance while
preventing over-control.

Minimal packs:

- Body/Energy.
- Finance.
- Learning.
- Builder.
- Emotion.
- Relationship.
- Values/Constitution.

Each pack records one loop:

```text
decision/action -> evidence -> outcome -> review -> rule update or no-rule rationale
```

Anti-overforce boundary:

- body, emotion, and relationship packs cannot become hard productivity gates.
- Finance remains read-only and never grants trading permission.
- Builder pack is the bridge to Alpha, PGI, EGB, and receipts.

## Benchmark Mapping

External sources are benchmark inputs only. Kubernetes OWNERS/KEP, Rust RFC,
Python PEP, Apache PMC, GitHub review/CODEOWNERS, Google SRE, DORA, Microsoft
SDL, SLSA, OpenSSF, OpenAI traces, LangGraph checkpoints, Claude Skills, and
MCP authorization inform internal design. They do not create compliance,
certification, endorsement, partnership, equivalence, public-standard,
production-readiness, or action authorization claims.

## Operating Rule

When a future change is unclear, default to this order:

```text
case evidence -> red-team fixture -> blue-team repair -> receipt
              -> maturity record -> only then schema or adapter discussion
```

This plan is strategy and evidence direction. It does not authorize merge,
release, deployment, publication, trading, policy activation, token refresh, or
external action.
