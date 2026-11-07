---
name: ordivon-security-owner
description: Audit, refactor, verify and operate the Ordivon Security Owner using its current public contracts, source-anchored evidence and native OPA/uv/mise verification. Use for Security authorization, threat-model, supply-chain-attestation, browser-witness or Security tree cleanup tasks. Distinguish verified ingress identity from Agent Grant and effect authority, and never infer deployment from local policy PASS.
compatibility: Requires access to the Ordivon monorepo. External scans are provider-dependent; pure source and OPA policy checks can run independently. Does not confer authorization or mutate credentials.
license: MIT
---

# Ordivon Security Owner

**Authority of this Skill:** guidance only; actual execution/authorization stays with installed Gateway, Runtime, identity and domain owners. Read `platform/security/docs/security-owner-guide.md` for current exact-directory map, Human workflow, Agent workflow and provider selection.

## Choose the real task

- Authorization: start with `platform/security/policies/`, `contracts/agent-admission-v1/`, `contracts/agent-request-verifier-v1/` and the **current** `services/gateway/src/ordivon_gateway/authzen_authorizer.py` + `capability_authz.py`. Existing Gateway-v1 evaluator is retired; do not resurrect it.
- Source assurance: prefer external Gitleaks / Semgrep / OSV-Scanner / Trivy / Syft, SARIF, CycloneDX and OPA. Prove scanner execution, report subject, freshness and policy standing separately.
- Artifact provenance: use SLSA, in-toto and Sigstore/Cosign; require an exact artifact digest and builder/trust policy. Do not mint build-system facts at the Security verifier.
- Threats: reuse OWASP Threat Model Library, STRIDE, CWE/CAPEC; bind the model to exact architecture files.
- Browser evidence: compare versioned detector witnesses; changed challenge outcome alone is not a root cause.

## Native owner verification

From `platform/security/`, run `mise run verify` for the full owner task or `MISE_OFFLINE=1 MISE_AUTO_INSTALL=false mise exec -- opa test -v --fail-on-empty policies` for the focused policy suite. A successful isolated test does **not** mean all deployed Gateways consume that policy.

## Refactor and delete

Trace source -> contract -> tests/CI -> real consumer -> deployment. Never treat code that references itself as a real consumer, but check direct and configured external users before removing a public name. Preserve exact R2.1 pre/post/inv/effect assumptions when replacing an implementation; use the existing `recursive-lego-calculus` Skill for formal contract/refinement work, not a duplicate theory. Report retired source paths and unproven deployment explicitly.

## Human and Agent usage

Human: define the operation and business effect, verify ownership and source identity, inspect the authorization decision, compare independent readback, then approve the concrete change.

Agent: bind the exact current revision and targeted Owner first, choose the mature provider, execute only within its real configured authority, and report `observed/verified/UNKNOWN` separately. Never claim a successful Job, a local test PASS or an old planning note proves live Security enforcement.
