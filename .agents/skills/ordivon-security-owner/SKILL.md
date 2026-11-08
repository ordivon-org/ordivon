---
name: ordivon-security-owner
description: Audit, refactor, verify and operate the Ordivon Security Owner using its current public contracts, source-anchored evidence and native OPA/uv/mise verification. Use for Security authorization, threat-model, supply-chain-attestation, browser-witness or Security tree cleanup tasks. Distinguish verified ingress identity from Agent Grant and effect authority, and never infer deployment from local policy PASS.
compatibility: Requires access to the Ordivon monorepo. External scans are provider-dependent; pure source and OPA policy checks can run independently. Does not confer authorization or mutate credentials.
license: MIT
---

# Ordivon Security Owner

**Authority of this Skill:** guidance only; actual execution/authorization stays with installed Gateway, Runtime, identity and domain owners. Read `platform/security/docs/security-owner-guide.md` for current exact-directory map, Human workflow, Agent workflow and provider selection.

## Choose the real task

- Authorization: start with `platform/security/policies/`, `contracts/agent-admission-v1/`, `contracts/agent-request-verifier-v1/` and the **current** `services/gateway/src/ordivon_gateway/authzen_authorizer.py` + `capability_authz.py`. Existing Gateway-v1 evaluator is retired; do not resurrect it. Agent Step-up requires both matching `effectId` and `effectDigest`, with approval authenticity established by the real WebAuthn/store owner; a self-reported `verified=true` is never sufficient. Effect Admission accepts only input schemaVersion=2 and requires exact qualified `request.authorityDigest == authority.authorityDigest`; the Agent public evaluator and Lab adapter verify the returned binding. The old unversioned Range admission is retired rather than kept as a downgrade path. This is content/current-record binding, not authentication of caller-supplied authorities.
- Agent Grant resource scopes: current v1 inputs use canonical, Owner-derived absolute resource paths, not raw string prefixes. Scope authorization matches the exact path or slash-segment descendants and rejects dot segments, percent aliases, backslashes, duplicate slashes, query/fragment and control characters. Both Rego agent_admission.rego and the real TypeScript Lab GrantStore must agree. Run check_agent_scope_refinement.py through security:verify (bounded cross-language differential cases); do not infer that a generic URL, Windows path or untrusted user string is an Owner-qualified canonical resource. A new resource kind requires an explicit versioned contract.
- Source assurance: prefer external Gitleaks / Semgrep / OSV-Scanner / Trivy / Syft, SARIF, CycloneDX and OPA. Prove scanner execution, report subject, freshness and policy standing separately. The product gate requires complete, unique provider records with typed exit-code semantics and full SHA-256 references; an absent mechanicalSuccess is not a clean scan. Do not claim Python-scoped Semgrep p/python rules scan Rust/TypeScript code.
- Artifact provenance: prefer current build-owner native GitHub actions/attest and gh attestation verify for a signed SLSA/in-toto statement, or Cosign/Sigstore for the actual producer trust profile. Do not mint build-system facts in Security; its verify_build_provenance.py only binds unsigned statement content and returns authenticated=false. The old local Python 3.12 wheel builder has been retired. When issuing Security reference/VSA material, use emit_attestations.py: it rehashes exact local inputs, binds the provider receipt and reevaluates the claimed decision with current native OPA. Even a matching unsigned VSA is not cryptographically authenticated.
- Threats: reuse OWASP Threat Model Library, STRIDE, CWE/CAPEC; bind the model to exact architecture files.
- Browser evidence: compare versioned detector witnesses; changed challenge outcome alone is not a root cause.
- Consequence: a caller's `world-truth` string plus matching SHA-256 proves **content equality**, not an independent trusted observer. The current policy returns `CONTENT_MATCHED_UNVERIFIED` and never exports `verifiedConsequence` without a real trusted observation source. Never accept caller-provided `verified`, `signed`, or `issuer` fields as cryptographic verification.

## Native owner verification

From `platform/security/`, run `mise run verify` for the full owner task or `MISE_OFFLINE=1 MISE_AUTO_INSTALL=false mise exec -- opa test -v --fail-on-empty policies` for the focused policy suite. For the existing Lean 4.35 proof of the **abstract consequence source-authenticity invariant**, run `mise run verify-formal`; it reuses `tools/formal` and is distinct from owner implementation checks. A successful isolated test or model theorem does **not** mean all deployed Gateways consume that policy or that real-world effects were verified.

## Refactor and delete

Trace source -> contract -> tests/CI -> real consumer -> deployment. Never treat code that references itself as a real consumer, but check direct and configured external users before removing a public name. Preserve exact R2.1 pre/post/inv/effect assumptions when replacing an implementation; use the existing `recursive-lego-calculus` Skill for formal contract/refinement work, not a duplicate theory. Report retired source paths and unproven deployment explicitly.

## Human and Agent usage

Human: define the operation and business effect, verify ownership and source identity, inspect the authorization decision, compare independent readback, then approve the concrete change.

Agent: bind the exact current revision and targeted Owner first, choose the mature provider, execute only within its real configured authority, and report `observed/verified/UNKNOWN` separately. Never claim a successful Job, a local test PASS or an old planning note proves live Security enforcement.
