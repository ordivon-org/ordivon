# GitHub Tooling Landscape

Status: **DOCUMENTED**
Date: 2026-04-28
Phase: 3.12
Tags: `tooling`, `github`, `landscape`, `evaluation`, `build-vs-buy`

## 1. Purpose

Map the GitHub / AI coding / security / CI ecosystem against Ordivon's
current capabilities. Identify which tools Ordivon should adopt, which
to defer, and where Ordivon's own governance semantics provide unique
value that no external tool can replicate.

## 2. Current Ordivon Capabilities (Phase 3.11)

| Capability | Implemented | Tool |
|-----------|------------|------|
| Governance classification (execute/escalate/reject) | ✅ | `packs/coding/policy.py` + `RiskEngine` |
| CLI governance adapter | ✅ | `scripts/repo_governance_cli.py` |
| GitHub PR governance adapter | ✅ | `scripts/repo_governance_github_adapter.py` |
| GitHub workflow integration | ✅ | `.github/workflows/ci.yml` `repo-governance-pr` |
| JSON schema contract | ✅ | `tests/contracts/repo_governance_output.schema.json` |
| Evidence artifacts | ✅ | `scripts/render_repo_governance_report.py` |
| Eval corpus (24 cases) | ✅ | `evals/run_evals.py` |
| Architecture boundary checker | ✅ | `scripts/check_architecture.py` |
| Runtime evidence checker (static) | ✅ | `scripts/check_runtime_evidence.py` |
| DB-backed evidence audit | ✅ | `scripts/audit_runtime_evidence_db.py` |
| Verification baseline (unified) | ✅ | `scripts/run_verification_baseline.py` |
| CandidateRule → PolicyProposal lifecycle | ✅ | `domains/candidate_rules/` |
| Ruff format/lint CI | ✅ | `backend-static` job |
| Unit / integration / contract CI | ✅ | Multiple jobs in `ci.yml` |
| PG regression CI | ✅ | `backend-unit-pg`, `backend-integration-pg` |
| Security scan (Bandit, pip-audit) | ✅ | `security.yml` |
| Gitleaks secret scan | ✅ | `secret-scan` job |

## 3. Tool Categories

### 3.1 AI Coding / Agent Execution

| Tool | What It Solves | What It Doesn't | Ordivon Risk | Timing |
|------|---------------|-----------------|-------------|--------|
| Claude Code CLI | AI-driven code changes | No pre-execution governance | High — no structured intake | Evaluate later |
| GitHub Copilot | Inline code suggestions | No governance classification | Low — editor-level, not CI | Adopt now (already used) |
| Codex CLI | Agentic code tasks | No governance pipeline | High — no classification | Evaluate later |
| Aider | AI pair programming | No intake/review loop | High — unstructured | Evaluate later |

**Ordivon position**: These tools produce code. Ordivon classifies the intent
before execution. Ordivon should integrate with these tools via the Adapter
Platform — CLI adapter and GitHub adapter are the first two adapters.

### 3.2 PR Review / Annotation / Comment

| Tool | What It Solves | What It Doesn't | Ordivon Risk | Timing |
|------|---------------|-----------------|-------------|--------|
| GitHub Checks API | Rich CI annotations | No governance semantics | Low — read-plus-annotate | Evaluate later |
| Reviewdog | Multi-linter reviewer | No governance classification | Low | Evaluate later |
| Danger JS | PR automation rules | No structured evidence chain | Medium | Avoid for now |
| CodeRabbit | AI PR review | No governance classification | High — external AI | Avoid for now |

**Ordivon position**: Ordivon's `::warning::` annotation + artifact upload
already provides governance visibility without write permissions. PR comments
and Checks API are deferred to Phase 4.x.

### 3.3 Security / Supply-Chain

| Tool | What It Solves | What It Doesn't | Ordivon Risk | Timing |
|------|---------------|-----------------|-------------|--------|
| Gitleaks | Secret detection | No governance classification | Low — already adopted | ✅ Adopt now |
| CodeQL | Code analysis | No governance pipeline | Low | Adopt soon |
| Bandit | Python security lint | AST-level only | Low — already adopted | ✅ Adopt now |
| pip-audit | Dependency vulns | Point-in-time scan | Low — already adopted | ✅ Adopt now |
| Trivy | Container + SBOM scanning | No governance | Low | Evaluate later |
| OpenSSF Scorecard | Repo security posture | Aggregate score | Low | Evaluate later |
| Dependabot | Dependency updates | Auto-PR without governance | Medium | Adopt soon |

**Ordivon position**: Security tools complement governance — they detect
vulnerabilities; Ordivon classifies whether changes are acceptable. Both
layers are needed.

### 3.4 Policy-as-Code / Config Governance

| Tool | What It Solves | What It Doesn't | Ordivon Risk | Timing |
|------|---------------|-----------------|-------------|--------|
| OPA / Conftest | Rego-based policy evaluation | No learning loop | High — different paradigm | Evaluate later |
| Semgrep | Custom pattern rules | No classification/receipt | Medium | Evaluate later |
| Kustomize | Config management | Not governance | Low | Avoid for now |

**Ordivon position**: Ordivon's `CodingDisciplinePolicy` with severity protocol
already implements the policy-as-code concept with richer semantics (reject/
escalate/execute + evidence chain). OPA/Conftest overlap on rule enforcement
but lack the learning loop.

### 3.5 Eval / Red-Team

| Tool | What It Solves | What It Doesn't | Ordivon Risk | Timing |
|------|---------------|-----------------|-------------|--------|
| lm-eval-harness | LLM benchmark | No governance classification | Low | Evaluate later |
| Garak | LLM vulnerability scanner | No governance pipeline | Low | Evaluate later |
| Ordivon Eval Corpus | Governance regression | Domain-specific only | N/A — we built it | ✅ Build ourselves |

**Ordivon position**: Ordivon's eval corpus tests governance classification
correctness. General LLM eval tools serve a different purpose (model quality)
and are complementary.

### 3.6 CI / Merge Automation

| Tool | What It Solves | What It Doesn't | Ordivon Risk | Timing |
|------|---------------|-----------------|-------------|--------|
| GitHub Actions | CI/CD pipeline | No governance semantics | Low — already adopted | ✅ Adopt now |
| Merge Queue | Automated merging | No governance check before merge | Medium | Evaluate later |
| Mergify | Merge automation rules | No governance classification | Medium | Avoid for now |
| ArgoCD | Kubernetes GitOps | Not repo governance | Low | Avoid for now |

**Ordivon position**: Ordivon's `repo-governance-pr` job runs as a GitHub
Actions job within the existing CI pipeline. Merge automation should require
the governance check to pass (execute) before merging.

## 4. Tool Adoption Matrix

### Adopt Now (already integrated)

| Tool | Category | Ordivon Integration |
|------|----------|-------------------|
| GitHub Actions | CI/CD | `.github/workflows/ci.yml` |
| Ruff | Static analysis | `backend-static` + `verification-fast` |
| Bandit | Security | `security.yml` |
| pip-audit | Supply-chain | `security.yml` |
| Gitleaks | Secret scan | `secret-scan` job |
| GitHub Copilot | AI coding | Editor-level (developer choice) |

### Adopt Soon (next 2-4 phases)

| Tool | Category | Rationale |
|------|----------|-----------|
| CodeQL | Security | Code analysis without runtime; low integration cost |
| Dependabot | Supply-chain | Auto-PR for dep updates; needs governance gate before merge |
| OpenSSF Scorecard | Security posture | Visibility into repo health; read-only |

### Evaluate Later (deferred to Phase 4+)

| Tool | Category | Rationale |
|------|----------|-----------|
| GitHub Checks API | PR review | Rich annotations; requires write token + stable semantics |
| Reviewdog | PR review | Multi-linter review; may overlap with Ordivon warnings |
| Semgrep | Policy-as-code | Custom rules; evaluate after CandidateRule→Policy path matures |
| OPA / Conftest | Policy-as-code | Different paradigm; Ordivon semantics may be sufficient |
| Trivy | Security | Container scanning; not needed for current repo scope |
| Merge Queue | CI automation | Governance gate must be proven before merge automation |
| lm-eval-harness | Eval | LLM quality; complementary to Ordivon governance evals |
| Garak | Security | LLM vuln scanning; complementary |

### Avoid for Now (explicitly deferred)

| Tool | Category | Rationale |
|------|----------|-----------|
| PR comments / write bots | PR review | Breaks read-only invariant; deferred to Phase 4.x |
| IDE adapters | AI coding | Premature before CLI + GitHub proven |
| MCP adapters | AI coding | Premature before CLI + GitHub proven |
| Mergify | Merge automation | Overlaps with native GitHub merge queue |
| CodeRabbit | AI PR review | External AI without governance; risk too high |
| Claude Code / Codex CLI integration | AI coding | No structured intake from these tools yet |

### Build Ourselves (Ordivon unique value)

| Capability | Why Build | Maturity |
|-----------|-----------|----------|
| Governance classification (execute/escalate/reject) | 3-tier semantics no external tool provides | ✅ Stable |
| Severity protocol (ADR-006) | Universal reason format across packs | ✅ Stable |
| Evidence chain (Intake→Receipt→Outcome→Review→Lesson) | Full traceability | ✅ Stable |
| Eval corpus | Domain-specific governance regression | ✅ Stable |
| CandidateRule→PolicyProposal lifecycle | Learning loop | ✅ Draft path |
| Verification baseline | Unified gate orchestration | ✅ Stable |
| Repo governance JSON contract | Adapter output standardization | ✅ Stable |
| Failure semantics | Decision→CI behavior mapping | ✅ Stable |

## 5. Key Principles

1. **Classify before execute** — governance runs in CI, not editor
2. **Adapter output is evidence, not truth** — read-only by default
3. **Build where Ordivon semantics are unique** — severity protocol, evidence chain, learning loop
4. **Adopt standard tools for standard problems** — linting, security scanning, testing
5. **Defer write-capable integrations** — PR comments, Checks API, merge automation require proven correctness first

## 6. Related Documents

| Document | Relationship |
|----------|-------------|
| `docs/adr/ADR-008-tooling-adoption-strategy.md` | Formal ADR for build/buy decisions |
| `docs/architecture/ordivon-platform-map.md` | Adapter Platform position |
| `docs/architecture/verification-platform.md` | Gate classification |
| `docs/runtime/verification-ci-gate-plan.md` | CI gate roadmap |
