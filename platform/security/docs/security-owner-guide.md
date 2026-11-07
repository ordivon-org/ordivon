# Security Owner — operating model and consumer guide

Status: source-audited on 2026-11-07 against monorepo revision `f52091fb1c8f920b7114c813142d1e7795ae8664`. This is a repository/source inventory, not a production deployment attestation. Keep it current by replaying the cited consumer and owner tests, not by copying historical PASS labels.

## Responsibility and boundaries

Security is the owner of **authorization semantics, security evidence binding, software assurance verification, and security observation interpretation**. It is not the issuer of identity tokens, the system's central Job executor, a vulnerability database, a credential store, a generic workflow engine, or a clone of provider-native scanners.

The stable decision chain is:

`verified identity (provider/ingress) -> qualified subject/action/resource/context -> policy decision (Security/OPA or external AuthZEN PDP) -> owner PEP -> natural owner effect -> independent consequence observation`.

The first arrow must not be inferred from caller-authored JSON. A policy ALLOW is not an execution result; a Runtime Job success is not an independent world-state proof. For cross-owner use, depend on published contracts, not `src/`, `labs/`, or raw internal Rego paths.

## Directory-by-directory ownership and action

| Directory | Responsibility | Source audit decision |
|---|---|---|
| `src/ordivon_security_v2/` | Evidence, attestations, provenance, VEX, remediation, Scorecard, threat-model binding, browser witness/comparison | KEEP: distinct cohesive Python modules already exist; do not split only for directory aesthetics |
| `policies/` | OPA/Rego security/product/Agent/effect/consequence decisions and tests | KEEP: native policy engine; correct stale public decision names only with consumer search and tests |
| `contracts/agent-admission-v1/` | Normalized verified Grant and Effect policy contract | KEEP: `apps/web` uses the contract; this evaluator does not authenticate callers |
| `contracts/agent-request-verifier-v1/` | JWT/DPoP protocol verifier | KEEP: `apps/web` imports this package; preserve pinned provider interoperability behavior |
| `contracts/gateway-capability-authz-v1/` | Historical v1 Security Gateway evaluator | RETIRED in this change: old source contract lacked Gateway's required resource binding; no tracked direct non-Security code reference discovered. Current Gateway uses a resource-bound v2/v3 PEP contract and an AuthZEN v3 adapter. This does not assert live deployment qualification |
| `labs/agent-admission-rs/` | Isolated Keycloak/DPoP/WebAuthn test Resource Server with lab-local SQLite stores | KEEP as lab: `apps/web/agent-native-e2e.sh` and repository checks reference its exact paths; never confuse lab SQLite with production PG truth |
| `schemas/`, `threat-models/` | Input and source-bound threat-model formats | KEEP: version-tagged schema names are compatibility coordinates, not arbitrary directory clutter |
| `scripts/`, `profiles/product/`, `profiles/zap/` | Native provider runs/verification and provider-specific settings | KEEP when addressed by owner tasks and tests; do not create a parallel scanner orchestrator |
| `profiles/migration/old-security-gitleaks.toml` | Legacy unused migration copy | RETIRED: zero tracked textual consumers and current product profile under `profiles/product/` |
| `providers/packer/` | VM-image provider configuration | KEEP as integration evidence; VM lifecycle belongs to external libvirt/QEMU and Workstation/Runtime |
| `fuzz/`, `.clusterfuzzlite/` | Focused replay-binding fuzz harness and upstream fuzzing runner | KEEP while the target primitive is maintained; verify provider availability separately |
| `fixtures/`, `tests/` | Contract/negative/fixture evidence | KEEP tests that protect current semantics; remove self-referential tests for retired unconsumed implementations |
| `docs/` | Standards, observed acceptance, historic technology choices | KEEP dated evidence as history, mark superseded claims; never use an old planning note as current deployment truth |
| `planning/` | LEGO candidate/source projection | KEEP as non-authoritative planning only; clean dead paths and mark open consumer seams |
| `artifacts/` | Generated output target | KEEP the tracked `.gitkeep`; ignored local outputs are disposable only after their consumers have been checked |
| Root `pyproject.toml`, `uv.lock`, `mise.toml`, `.python-version` | Package/reproducible environment and native tasks | KEEP release identity until a published-package consumer cutover is accepted; do not rename versioned distribution identifiers just because they look dated |

No tracked system file, secret store, OS configuration, or production database is a cleanup target for this audit.

## Mature capability-provider map

| Capability / method (candidate, not automatically a formal R2.1 LEGO) | Native provider/standard | Ordivon-owned remainder and acceptance |
|---|---|---|
| Fine-grained authorization | OpenID AuthZEN Authorization API 1.0; OPA/Rego for local policies | Verified principal + server-derived resource/action binding; PEP enforces the same decision on the same request |
| Delegated Agent identity and proof-of-possession | Keycloak/OIDC, OAuth 2.0, DPoP via oauth4webapi, WebAuthn via SimpleWebAuthn | Grant scope, effect identity, replay guard ownership; no agent self-asserted identity |
| Source and dependency scanning | Gitleaks, Semgrep, Trivy, OSV-Scanner; SARIF | Exact revision, provider completeness, mechanical failure distinct from blocking finding |
| SBOM and vulnerability status | Syft, CycloneDX 1.7, VEX | Exact component references, evidence provenance and current applicability |
| Repository posture and fuzzing | OpenSSF Scorecard, ClusterFuzzLite | Named checks/testcase evidence rather than unqualified aggregate score or success |
| Threat modeling | OWASP Threat Model Library/Threat Dragon, STRIDE, CAPEC/CWE | Exact architecture/source binding; stale source invalidates current model claim |
| Build provenance/verification | SLSA v1.2, in-toto, Sigstore/Cosign | Exact artifact/source/builder/verification policy and trusted key identity; build execution belongs to builder |
| Web/runtime detection | OWASP ZAP (authorized targets), Falco where supported | Controlled target scope and independent findings; runtime authority remains with owner |
| Formal reasoning | OPA test/rego policy checks, JSON Schema; R2.1 assume-guarantee and refinement references | Prove specified obligations with their actual assumptions; UNKNOWN is not FALSE; no proprietary proof engine |

External references: https://openid.net/specs/authorization-api-1_0.html ; https://www.openpolicyagent.org/docs/policy-testing ; https://github.com/ossf/scorecard ; https://slsa.dev/spec/v1.2/ ; https://cyclonedx.org/ ; https://owasp.org/www-project-threat-dragon/ ; https://github.com/sigstore/cosign .

## Human operator guide

1. Select an exact subject (Git revision/artifact digest), affected Owner and the real intended outcome; decide whether the job is **authorization**, **assurance**, **modeling**, or **observation**.
2. For authorization, inspect who verified the identity, who constructs action/resource and who is the enforcing PEP. For external Gateway calls use the current Gateway AuthZEN-v3 adapter and resource-bound middleware sources, not the retired Security Gateway-v1 reference.
3. For assurance, select only necessary native provider scans, collect provider-native reports, then check revision binding, freshness, required coverage, and the actual standing. Do not interpret failed tooling as clean results.
4. For a risky effect, distinguish authorized request, Runtime receipt, independent readback and domain outcome. An Agent may have admin authority when the deployment provides it; an approval cannot invent platform capabilities.
5. Run `cd platform/security && mise run verify` for native acceptance. This executes locked Python checks, source-bound threat-model validation, OPA policies and shellcheck where configured. Consult separate provider acceptance when a particular external scanner/VM/runtime is involved.
6. For cleanup, inspect `git grep`, tests, scripts, CI, external callers and deployed consumer manifests. Delete only the proven redundant source slice. Do not delete database or credential files merely by filename search.

## Agent invocation and thinking guide

An Agent working in Security should first read root `AGENTS.md`, the existing `recursive-lego-calculus` Skill (only if architecture decisions matter), this owner guide, and then the **specific** public contract or `mise` task relevant to its request.

For every consequential decision report: `subject/revision`, `consumer`, `natural owner`, `identity authority`, `resource/action binding`, `native provider`, `evidence digest`, `outcome`, `not proven`. This is a reporting vocabulary, not a new persisted schema.

Choose **DELETE -> REUSE -> COMPOSE -> BUILD**. Prefer improving an existing OPA, AuthZEN, SLSA, CycloneDX, Sigstore or scanner integration over adding wrappers. Compare before/after on the same actual consumer input. Preserve `UNKNOWN` when live deployment or authoritative readback is missing. Do not treat `labs/` examples as authorization to alter production credentials, databases or control planes.

Use `git ls-files platform/security`, `git grep`, `mise run verify`, and focused owner tests. Do not install or copy remote code into live services merely because a GitHub project looks popular. Record actual tool version and acceptance evidence for any newly selected provider.

## Supply-chain producer retirement and modern provider choice (2026-11-07)

The unconsumed custom Security wheel provenance builder and its static local build-type document were retired. The builder's hardcoded Python 3.12 and standalone git-archive assumptions are incompatible with this monorepo's Python 3.15.1 source. The historic September 2026 acceptance remains available as dated evidence only.

Prefer GitHub Actions actions/attest to issue signed SLSA provenance from the actual producing workflow. Use gh attestation verify on the exact artifact to authenticate signer identity and predicate before Security evaluates its claimed content. The older slsa-framework/slsa-github-generator project explicitly states it is no longer actively maintained and recommends GitHub native artifact attestations. The local Security verify_build_provenance.py checker requires independent expected builder/build type and yields PROVENANCE_CONTENT_BOUND, authenticated=false; it is NOT proof that the statement was signed. References: https://github.com/actions/attest ; https://cli.github.com/manual/gh_attestation_verify ; https://slsa.dev/spec/v1.2/build-provenance .

Human: verify an artifact's signed attestation from the release workflow before accepting its provenance.

Agent: use the real provider-issued attestation and cryptographic verification; never invent build history from logs or promote parsed unsigned JSON into trusted builder identity.

## Current observed integration gaps

- The retired Gateway v1 source-only evaluator was not compatible with the current Gateway's resource-bound response. Gateway's AuthZEN-v3 adapter exists in source; deployment, coverage and complete Principal/Agent-Grants path require separate runtime evidence.
- The Agent Admission lab uses SQLite for local experimental Grants and challenges. Its E2E and repository checks have concrete references; a PG production replacement must not be inferred from Runtime's PostgreSQL migration.
- Scorecard's official provider acceptance is not automatically current Ordivon-repository admission. Falco, ZAP, ClusterFuzzLite and image-tool provider acceptance are individually scoped.
- No evidence from this source-only audit establishes a globally complete Security authorization or independent consequence verification chain across every Owner.

## Naming and retirement policy

Prefer: `authorization`, `authentication`, `attestations`, `provenance`, `threat-model`, `security-observation`, `resource`, `principal`, `policy-decision`. Avoid `range-*` for generic effect decisions, unqualified `security-check` and a second custom `findings` model. Keep public versioned paths/names stable until their consumers are migrated; internal source semantics and provider-native formats take priority over cosmetic renames.
