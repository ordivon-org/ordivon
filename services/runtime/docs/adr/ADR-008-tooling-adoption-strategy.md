# ADR-008: Tooling Adoption Strategy

Status: **proposed** (updated Phase 4.8)
Date: 2026-04-28 (updated 2026-04-29)
Phase: 3.12 → 4.8

## Context

Ordivon has reached the platformization threshold:
- Repo Governance CLI + GitHub adapter are operational
- Verification Platform has 10-layer gate classification
- Evidence chain produces JSON/Markdown artifacts
- CI has 14 jobs including `repo-governance-pr`
- Eval corpus has 24 cases across 3 packs

The GitHub ecosystem offers many tools for linting, security scanning, PR
review, policy-as-code, and AI coding. Ordivon must decide which to adopt,
which to defer, and where to invest in building its own capabilities.

## Decision

Adopt a **dual-layer tooling strategy**:

**Layer 1 — Standard tools for standard problems**: Use community tools for
linting, secret scanning, dependency auditing, and static analysis. These
are commodity capabilities where Ordivon adds no unique value.

**Layer 2 — Ordivon-built for Ordivon-unique semantics**: Build governance
classification, severity protocol, evidence chains, eval corpus, and learning
lifecycle internally. No external tool provides 3-tier execute/escalate/reject
with traceable evidence.

## Tooling Adoption Principles

1. **Prefer read-only first**: All integrations start read-only. Write
   capabilities (PR comments, Checks API annotations, merge automation)
   require proven correctness over months of CI data.

2. **One tool per problem**: Avoid overlapping capabilities. If Ruff handles
   linting, don't add another linter. If Gitleaks handles secret scanning,
   don't add another secret scanner.

3. **Integration cost matters**: A tool's value must exceed its CI runtime
   cost + maintenance burden + false positive rate.

4. **Ordivon governance wraps tools**: Security tools detect issues; Ordivon
   classifies whether the PR is acceptable given those issues.

5. **Build where semantics are unique**: If no external tool implements
   severity protocol, evidence chains, or CandidateRule learning — Ordivon
   builds it.

6. **Ecosystem key ≠ tool recommendation**: GitHub platform keys (Dependabot
   `package-ecosystem`, Actions `setup-*`) are upstream adapter identifiers.
   The project toolchain (uv, pnpm, bun) is the execution truth. Never let
   a platform naming convention redirect the project toolchain. See
   `docs/runtime/dependabot-strategy.md` §3 for full rationale.

## Build vs Buy Criteria

| Criterion | Buy (Adopt) | Build |
|-----------|------------|-------|
| Problem scope | Standard (linting, scanning) | Domain-specific (governance classification) |
| External tool quality | Mature, widely adopted | No equivalent exists |
| Integration effort | Low (single CI step) | High (new code, tests, docs) |
| False positive rate | Low | N/A (we control semantics) |
| Maintenance burden | Low (upstream updates) | Medium (we own the code) |
| Unique Ordivon value | None | High (severity protocol, evidence chain) |

## First Adoption Candidates (Adopt Soon)

| Tool | Rationale | Effort | Phase | Status |
|------|-----------|--------|-------|--------|
| CodeQL | Code analysis, low integration cost, GitHub-native | 1 CI job | 4.1-4.3 | ✅ Hard Gate |
| Dependabot | Auto-PR for dep updates, needs governance gate | Configure `.github/dependabot.yml` | 4.4-4.12 | ⏳ github-actions enabled; uv/npm strategy refined (4.8) |
| OpenSSF Scorecard | Read-only security posture report | 1 CI job | 4.x | 📋 Plan |

## Deferred Candidates (Evaluate Later)

| Tool | Rationale for Deferral | Evaluation Criteria |
|------|----------------------|-------------------|
| GitHub Checks API | Requires write token; annotations should not replace artifacts | Prove artifact stability over 6+ months of real PRs |
| Semgrep | Custom rules overlap with CandidateRule→Policy path | Evaluate after Policy activation (Phase 4.x) |
| OPA / Conftest | Different paradigm (Rego); Ordivon severity protocol may suffice | Evaluate when config governance use case emerges |
| Trivy | Container scanning; repo has no container deployment yet | Evaluate when Dockerized deployment exists |
| Merge Queue | Governance gate must be proven before merge automation | After 6+ months of correct repo-governance-pr data |
| lm-eval-harness | LLM quality evaluation; complementary to governance evals | Evaluate when LLM-based intelligence is used in governance |
| Reviewdog | Multi-linter review; may overlap with `::warning::` annotations | Evaluate if annotation format becomes insufficient |

## Rejected-for-Now Candidates

| Tool | Reason for Rejection |
|------|---------------------|
| PR comment bots (any) | Break read-only invariant; require write scope; no proven correctness data |
| IDE adapters (MCP, agent) | Premature before CLI + GitHub proven; IDE execution carries higher risk |
| Merge automation (Mergify) | Overlaps with native GitHub Merge Queue; governance gate not proven |
| CodeRabbit / external AI review | External AI without Ordivon governance; classification not traceable |
| Claude Code / Codex CLI integration | No structured intake from these tools; adapter pattern not yet extended |

## Consequences

### Positive

- Clear criteria for future tooling decisions
- Prevents scope creep (no "let's try every tool")
- Protects Ordivon's unique value (severity protocol, evidence chain)
- Read-only-first reduces security surface
- Tool identity vs ecosystem key distinction prevents supply-chain confusion

### Negative

- Defers some developer-experience improvements (PR comments, IDE integration)
- Requires discipline to say "no" to tempting tools
- May miss rapid ecosystem shifts (re-evaluate quarterly)

## Follow-up Phases

| Phase | Action | Status |
|-------|--------|--------|
| 4.1 | Adopt CodeQL (1 CI job, read-only) | ✅ Complete |
| 4.2 | CodeQL findings triage | ✅ Complete (zero alerts) |
| 4.3 | CodeQL workflow-health hard gate | ✅ Complete |
| 4.4 | Dependabot supply-chain strategy plan | ✅ Complete |
| 4.5 | Create + enable dependabot.yml (github-actions) | ✅ Complete |
| 4.6 | Observe first Dependabot PRs | ✅ Complete |
| 4.7 | Tune Dependabot grouping + validate evidence artifacts | ✅ Complete |
| 4.8 | Dependabot uv/pnpm strategy refinement | ▶️ Current |
| 4.9 | Enable Python/uv Dependabot (minimal config) | 📋 Plan |
| 4.10 | Observe first Python/uv Dependabot PR | 📋 Plan |
| 4.11 | Enable Node/pnpm Dependabot (minimal config) | 📋 Plan |
| 4.12 | Observe first Node/pnpm Dependabot PR | 📋 Plan |
| 4.x | OpenSSF Scorecard | 📋 Plan |
| 4.x | Re-evaluate Checks API based on artifact data | 📋 Plan |
| 4.x | Evaluate Semgrep after CandidateRule→Policy matures | 📋 Plan |
