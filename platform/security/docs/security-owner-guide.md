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
| `scripts/`, `profiles/product/`, `profiles/zap/` | Native provider runs/verification and provider-specific settings | KEEP the actual product scan and verification entrypoints; do not create a parallel scanner orchestrator. The current scan_product.sh Semgrep p/python profile is Python-scoped, not a TypeScript/Rust SAST acceptance claim |
| `scripts/smoke_external.sh`, `fixtures/smoke/` | Standalone scanner smoke wrapper and its only input fixture | RETIRED in source audit R2: no tracked caller beyond the wrapper itself. The product scanner remains under scripts/scan_product.sh; do not keep a parallel unconsumed smoke runner |
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

## Product evidence admission — native OPA contract and observed counterexample (2026-11-07)

The earlier product Rego gate counted only explicit `mechanicalSuccess == false` records. A real OPA evaluation with all five `mechanicalSuccess` fields missing still returned `allow=true` and `standing=CURRENT`: an observed representation-to-policy fail-open, not a hypothetical unit-test label. The consumer profile is `scripts/scan_product.sh` -> `scripts/assemble_gate_input.py` -> OPA `policies/admission.rego`.

The current source gate requires exactly one status and one valid native-format evidence reference for each of Gitleaks, Semgrep, Trivy, Syft and OSV-Scanner; an optional single `ordivon-runner` reference is allowed. Every status requires a nonnegative integral exit code, actual Boolean `mechanicalSuccess` and `blocking` fields and the exit-code classification used by the exact scanner profile (normal detection: 0 clean, 1 findings, higher error; Syft: 0 success, nonzero error). Every evidence reference must have a matching provider format, nonempty path, positive integer byte count and a **full 64-hex SHA-256 string**. The source and observed revisions must be full Git SHA-1/SHA-256 hexadecimal IDs and match before `CURRENT` can be produced. Duplicate/extra/malformed input is not admitted. Use the Owner's native `opa test -v --fail-on-empty policies` suite with malformed and positive real-profile tests; never turn an empty or skipped suite into PASS.

OPA itself checks **structure and claimed digests** but cannot read the actual referenced local files. The native `scripts/emit_attestations.py` issuance boundary now re-reads and hashes every bound evidence file, binds the single runner receipt to the gate's provider results/revision, and re-evaluates the current source policy with native OPA before emitting a reference/VSA. Reusing an earlier CURRENT decision after evidence or result changes is rejected. This is still an **unsigned attestation** and does not authenticate provider execution or an eventual signer; verified Cosign/Sigstore identity remains separate. No production trust standing is implied by a local policy PASS. Semgrep's current product rule profile is `p/python`; it must not be presented as all-language Python/Rust/TypeScript SAST coverage. Reuse OPA's `every`, `regex.match` and tests rather than adding a second schema/validator DSL. Mature references: https://www.openpolicyagent.org/docs/policy-reference/keywords/every ; https://www.openpolicyagent.org/docs/policy-testing ; https://baseline.openssf.org/ (current OSPS Baseline v2026.08.28; reference controls, not an Ordivon conformance claim).

The product scanner now reports `observedSubjectRevision=UNKNOWN` if its Git target is dirty or has untracked files at either the beginning or end of scanning, or if `HEAD` changes during collection. A Git commit cannot bind uncommitted bytes. This remains a bounded before/after witness, **not an immutable snapshot** or protection against a file changed and reverted during collection; a release owner should scan a content-addressed, immutable checkout for high-assurance claims.

Human: check the exact scan target/revision, clean checkout, required native provider outputs and trustworthy collection boundary; treat incomplete adapter status as incomplete evidence, not a clean result.

Agent: invoke the native policy with an exact subject and actual provider reports. Preserve `CURRENT`, `BLOCKED`, `PROVIDER_ERROR`, `STALE_EVIDENCE` and `INCOMPLETE_EVIDENCE` separately. Never invent a zero exit status, a missing Boolean, a digest, or an unseen scan.

## Formal contract and proof frontier — Product Admission (R2.1)

The Security Product Admission responsibility is modeled as a **stateless decision LEGO**, not a new verification engine or a file-by-file LEGO registry. Its eleven effective coordinates are grounded in the existing native artifacts:

| Coordinate | Effective value and evidence obligation |
| --- | --- |
| `I` | Typed `GateInput` with source/observed Git revisions, Gitleaks/Semgrep/Trivy/Syft/OSV-Scanner evidence references, native exit-code status and optional runner reference |
| `O` | `decision {allow, standing, evidenceComplete, resultsComplete, provider sets, revisions}`; local unsigned VSA is a separate downstream output |
| `S` | `Unit` for pure OPA evaluation; external provider/report snapshot state is **not** included |
| `pre` | Native scanner profile known; status and report references supplied by source-observing adapter; caller authority trust remains externally checked |
| `post` | `allow ⇔ authority="security-verification" ∧ evidenceComplete ∧ resultsComplete ∧ mechanicalSound ∧ revisionsCurrent ∧ noBlockingProviders` |
| `inv` | No `CURRENT` for missing/duplicate/malformed provider, incomplete hash, inconsistent native exit classification, or stale/unknown revision |
| `eff` | Empty for OPA decision; evidence emission writes files and belongs to a separate effectful boundary |
| `c` | `UNKNOWN(cost model not measured, Security admission scope)`; no invented complexity bound |
| `epsilon` | `UNKNOWN(implementation/spec conformance not machine-proved over all Rego inputs)`; do not claim a proven zero approximation |
| `prov` | Pinned source revision + `policies/admission.rego` digest + exact native OPA version/test receipt |
| `unfold` | `policies/admission.rego`, `scripts/scan_product.sh`, `scripts/assemble_gate_input.py`, `src/ordivon_security_v2/evidence.py` and signed/unsigned attestation provider semantics |

**Human-checkable set lemma:** let `P` be the five required providers, and `R` an array of records whose provider names are all in `P`. If `|R|=|P|` and `set(provider(R))=P`, every required provider occurs exactly once. Likewise, an evidence array `E` containing only `P ∪ {ordivon-runner}`, with `|E|=|set(provider(E))|`, `P ⊆ set(provider(E))`, and `5 ≤ |E| ≤ 6`, has exactly one evidence item per required provider and at most one runner. These are finite-set consequences, not yet a machine-checked proof that native OPA implements all intended predicates. The test suite provides source refinement/negative counterexample coverage, not universal proof.

The **first verified source counterexample** was a policy returning `CURRENT` when every `mechanicalSuccess` was missing. Treat that as a refinement falsification, not a reason to multiply tests indefinitely. Reuse a mature model/proof tool (Z3/Lean or bounded Rego enumeration) when its proof goal is precise; delete redundant example tests only after the property and implementation link have real evidence. `opa test` is regression/consumer verification, not an SMT theorem prover.

**Provider-semantics correction:** Gitleaks' default exit code 1 ambiguously means detected leaks *or* tool error. The native scanner therefore now uses its official `--exit-code 10` option, with 0 = clean, 10 = finding, all other exits = tool failure, and the OPA model enforces that exact mapping. OSV-Scanner version 2 reserves 1–126 for result-related statuses; treat only 1 as a defined finding in this specific profile and do not falsely claim all higher codes are clean or even necessarily infrastructure failure. Source: https://github.com/gitleaks/gitleaks ; https://google.github.io/osv-scanner/output/ .

**Proof/evidence grades:** source spec = DECLARED; bounded OPA checks = TESTED for those cases; Python emission integration = CODE_REFINED only for executed checks; installed producer authenticity = UNKNOWN until native signed attestation and independently trusted issuer evidence; complete domain effect = UNKNOWN until live consumer readback. Do not collapse these into a single PASS.

## IPinfo candidate — Network owns collection, Security may consume evidence

https://ipinfo.io is a mature IP metadata/intelligence data provider, **not a VPN or proxy service**. Its documented API tiers distinguish Lite country/continent/ASN data from richer paid tiers that may expose hosting, VPN, proxy, Tor, relay, residential-proxy and confidence information. Network should own egress-IP observation, any IPinfo client, caching, quotas, token materialization and source-time collection. Security may consume a digest-bound, timestamped observation for a narrowly defined risk or verification decision, but an IPinfo annotation **must not** become unconditional identity authority, authorization denial, or a substitute for actual VPN route/exit readback. API metadata may be unavailable or tier-limited: keep `UNKNOWN`, not `false`. No live consumer justifies installing another IPinfo client within Security in this audit. References: https://ipinfo.io/developers/ipinfo-api ; https://support.ipinfo.io/hc/en-us/articles/30792494886162-Do-You-Provide-VPN-or-Proxy-Services .

Human: compare the observed public egress address, dated ASN and privacy labels with the real intended network route; check the chosen API tier.

Agent: request a Network-owned exact IP observation, keep provider provenance, age, confidence and fields actually present, and never infer a successful VPN tunnel from a single third-party classification.

## Consequence authority / independent readback (2026-11-08)

A native OPA input with a caller-generated `observation.plane="world-truth"` and matching `stateDigest` previously returned `VERIFIED_CONSEQUENCE` and `observationAuthoritative=true`. This was a genuine **model-to-source counterexample**: the JSON plane was self-asserted; no independent observer, issuer proof or effect-to-observation authentication was supplied. A digest equality comparison proves content agreement only, not truth of the observed world.

The current `policies/consequence_verification.rego` therefore returns `CONTENT_MATCHED_UNVERIFIED` for matching content, `observationAuthoritative=false`, and `verifiedConsequence=null`, irrespective of caller-supplied `signed`/`verified` flags. It checks complete SHA-256 syntax rather than a prefix. The older local AF3 differential is qualified as **historical local-backend evidence**; the present differential runner expects a non-promoting outcome. No independently authenticated production observation issuer was identified in the tracked consumer search.

The **existing** Lean 4.35 provider and `formal/ConsequenceEvidence.lean` prove the pure semantic obligations: a content match does not imply an authenticated independent observation, and the stronger conclusion requires both authentication and observer independence. Run `mise run verify-formal` from this Owner for model proof, and `mise run verify` for native OPA + Python + shell checks. These checks are distinct and neither proves deployed source authenticity or complete implementation refinement. Reference: the Cedar verification-guided approach (Lean specification + differential implementation tests), https://github.com/cedar-policy/cedar-spec ; https://docs.kernel.org/security/landlock.html .

Before a future verified-consequence outcome is valid, the natural producing Owner must supply a source-authenticated observation with its own trusted identity, exact subject/effect and freshness binding, and real consumer readback. Reuse provider-native signed/verified receipts and the Artifact/Runtime identities rather than adding a Security-owned signing system or accepting a boolean from the same untrusted caller.

## Current observed integration gaps

- The retired Gateway v1 source-only evaluator was not compatible with the current Gateway's resource-bound response. Gateway's AuthZEN-v3 adapter exists in source; deployment, coverage and complete Principal/Agent-Grants path require separate runtime evidence.
- The Agent Admission lab uses SQLite for local experimental Grants and challenges. Its E2E and repository checks have concrete references; a PG production replacement must not be inferred from Runtime's PostgreSQL migration. The lab's `src/oauth-verifier.ts` largely duplicates the Security `contracts/agent-request-verifier-v1/src/index.ts` OAuth/DPoP verifier; this is a real refactoring candidate, but a source-file import alone would break separately installed pnpm package resolution. Reuse the real package only after the lab's pnpm workspace/lockfile and Keycloak E2E consumer are proven compatible; do not retain a second cryptographic protocol implementation as a permanent architecture.
- Scorecard's official provider acceptance is not automatically current Ordivon-repository admission. Falco, ZAP, ClusterFuzzLite and image-tool provider acceptance are individually scoped.
- The `agent-admission-input-v0` schema now permits an optional `approval.effectDigest` for compatibility; `agent_admission.rego` **requires exact `effectId` and `effectDigest`** for high-risk WebAuthn Step-up. `apps/web` and the lab's verified-approval projections supply the digest read through their actual pending/consumed approval queries. Older same-ID approvals lacking a digest now yield `STEP_UP`, not ALLOW. The historical v0 schema remains accepted for low-risk effects; full production consumer/currentness and WebAuthn cryptographic trust are separate obligations. The Security policy never authenticates a caller-supplied `verified` flag on its own. The new `formal/AgentApprovalBinding.lean` proves abstract content-binding and a concrete same-ID/changing-digest counterexample; public Python contract and native Web/Lab tests provide implementation-refinement evidence.
- The Effect Admission Rego decision currently reads the authority record's `authorityDigest` into the output but does **not** compare an independently supplied request digest to it. The historical `range-effect-request` input and `scripts/differential_effect_admission.py` omit that request coordinate, whereas the Agent Admission projection includes it. This is an observed cross-contract representation gap, not a proven exploit in Gateway/Runtime. Do not add a digest check to the existing unversioned policy until all actual producers, difference fixtures and PEP consumers are migrated to a versioned bound contract; the required refinement property is `admitted -> request.authorityDigest == registry.authorityDigest`, with trusted registry identity and exact request source assumptions. Verify with native OPA + consumer traversal, and keep old compatibility explicitly qualified.
- No evidence from this source-only audit establishes a globally complete Security authorization or independent consequence verification chain across every Owner.

## Naming and retirement policy

Prefer: `authorization`, `authentication`, `attestations`, `provenance`, `threat-model`, `security-observation`, `resource`, `principal`, `policy-decision`. Avoid `range-*` for generic effect decisions, unqualified `security-check` and a second custom `findings` model. Keep public versioned paths/names stable until their consumers are migrated; internal source semantics and provider-native formats take priority over cosmetic renames.
