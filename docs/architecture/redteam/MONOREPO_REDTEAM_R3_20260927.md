# Ordivon Monorepo Red-Team R3

Date: 2026-09-27
Status: **CURRENT CANDIDATE FINDING LEDGER — provider-governance + authorization composition**

## Truth fence

- R3 candidate started from local integration main `eec3d13d61956a354ee9a93c9ecf47788096f8f0`.
- Fresh GitHub provider `main` readback during this cycle: `c309b467452beb56ae93ce9272461527f396ee23`.
- Live Gateway: `0.5.0`.
- Live Windows Runtime: node `windows-main-r6-candidate`, native Windows Runtime available.
- Live Host Social Work Fabric: PostgreSQL schema 9, integrity healthy.
- R1/R2 remain predecessor ledgers; this file does not rewrite their findings.

Local Git integration, GitHub provider governance, Gateway routing, Runtime execution, and Host collaboration are separate authorities. Each claim below names its truth source.

## R3 LEGO frontier

```text
ENTRY
  -> IDENTITY / AUTHENTICATION
  -> AUTHORIZATION / ADMISSION
  -> OWNER ROUTING
  -> EXECUTION OBJECT
  -> EFFECT / ARTIFACT
  -> EVIDENCE / ATTRIBUTION
  -> RELEASE SOURCE
  -> PROVIDER GOVERNANCE
```

R3 adds two provider-governance findings and one concrete consequence of the already-known AF-S2 authorization gap.

## RT-GOV-001 — Main rules do not enforce PR-only convergence

**Class:** `CONFIRMED_NEW`
**Priority:** HIGH
**Owner:** GitHub provider governance / repository mechanics

Provider-native effective rules for `refs/heads/main` contain only:

- required status check `root-verification`;
- merge queue;
- non-fast-forward protection.

The active ruleset has no `pull_request` rule. Classic branch protection does not add a required PR/review layer. GitHub defines **Require a pull request before merging** as the distinct rule requiring all changes to the target branch to be associated with a pull request; a merge queue does not itself encode that invariant.

No direct push to main was attempted. The falsifier is provider configuration readback, not an exploit claim.

**Impact:** the provider does not technically encode the repository's intended PR/merge-queue-only convergence law. Repository tooling can behave as though convergence is serialized while provider authority still lacks the corresponding entry gate.

**Acceptance:** enable the provider `pull_request` rule for `main`; choose review/code-owner requirements explicitly; verify effective rules by API; make repository governance verification fail if the rule disappears.

Evidence: `evidence/RT_GOV_001_MAIN_CONVERGENCE_RULES_R1.json`.

## RT-GOV-002 — Required `root-verification` check is not bound to its producer

**Class:** `CONFIRMED_NEW`
**Priority:** HIGH
**Owner:** GitHub provider governance / CI trust root

The main ruleset requires status context `root-verification`, but its required-check object has no `integration_id`. Current genuine `root-verification` check runs are produced by the GitHub Actions App (`app id 15368`), yet that producer identity is not enforced by the provider rule.

GitHub documents that write-capable people/integrations can set commit statuses and allows a required check to be restricted to an expected GitHub App. The current Ordivon provider rule uses the context name only.

A temporary branch was created to stage a source-binding canary. The actual synthetic status submission was blocked by the execution safety layer and was **not** bypassed; the temporary branch was deleted. R3 therefore does not claim that a forged status was live accepted. The confirmed defect is the absent source binding in provider configuration.

**Acceptance:** bind `root-verification` to the expected integration, or adopt a stronger provider-native required-workflow rule; read back the effective source binding; regression-test the live governance contract.

Evidence: `evidence/RT_GOV_002_REQUIRED_CHECK_SOURCE_R1.json`.

## RT-AUTHZ-001 — Gateway-to-Runtime composition collapses end-user identity

**Class:** `KNOWN_OPEN_CONSEQUENCE`
**Priority:** HIGH before multi-user/public execution promotion
**Owners:** Security authorization semantics + Gateway enforcement seam + Runtime object authorization

AF-S2 already records that authenticated Cloudflare ingress is not capability-scoped Security authorization. R3 does not double-count that gap. It establishes a more concrete consequence.

Gateway verifies a Cloudflare Access identity and derives a pseudonymous Principal, but the current execution routing path uses that Principal for audit only; `execution.submit/resolve/get/cancel/artifact.read` do not propagate an end-user Principal into owner calls.

Runtime itself has better primitives than the composition currently uses: execution admission accepts an `EffectivePrincipal`, idempotency is principal-scoped, credential authorities have Principal allowlists, and factorized Principal mode exists. However, live Windows Runtime `18997` is configured:

```text
ORDIVON_PRINCIPAL_MODE=static
ORDIVON_PRINCIPAL=principal:windows-main
```

The deployed MCP handlers bind `EffectivePrincipal` on `workspace.exec*`, but `job.get`, `job.observe`, `job.cancel`, `job.list`, and `artifact.read` do not consume `EffectivePrincipal`.

Therefore, when Gateway Runtime bearer routing is restored under this configuration, distinct authenticated Gateway users collapse to one Runtime service principal, and Job/Artifact lifecycle operations are not end-user-object-authorized. This also creates an evidence split: Gateway audit may name an end-user Principal while Runtime Job truth records only the service Principal.

Current Gateway Runtime capabilities were unavailable during the cycle, so no cross-user live cancel/read exploit is claimed.

**Acceptance:** factorize/delegate authenticated subject identity across Gateway -> Runtime or enforce an explicit Security subject/action/resource decision before every owner call; add object-level Job/Artifact authorization; separate service identity from delegated user identity; add two-principal negative tests.

Evidence: `evidence/RT_AUTHZ_001_PRINCIPAL_COLLAPSE_R1.json`.

## RT-SUPPLY-001 currentness recheck

R1's HIGH Runtime tag finding remains **OPEN** on provider `main@c309b467...`:

- only the branch ruleset was returned by provider ruleset inventory;
- no tag-target ruleset protects `runtime-v*`;
- the release workflow still accepts `runtime-v*` tag pushes after version + Runtime owner ancestry/tree checks;
- it still does not require the tagged repository revision to have been admitted through protected provider `main`, nor record that protected source ref in release identity.

This is a revalidation, not a second finding count.

Evidence: `evidence/RT_SUPPLY_001_REVALIDATION_R2.json`.

## Negative controls and rejected inflation

- Runtime replay identity remains a held negative control from R1.
- Runtime orphan recovery remains a held negative control from R2.
- Owner-boundary literal scanner incompleteness remains rejected as a standalone finding because its narrow scope is explicit.
- Undirected convergence closure remains CI-economics/precision pressure unless concrete under-verification is shown.
- Social Work ActorRef is explicitly not authenticated identity; R3 does not relabel that documented HOLD as a new bug.
- The blocked status-source canary was not bypassed and is not reported as an exploit success.

## External baseline mapping

- GitHub Rulesets: PR requirement and required-check expected-source binding are distinct provider controls.
- SLSA Source v1.2: consumable branch/tag references should be protected by technical controls, with provenance for how a revision reached a protected reference.
- OWASP API Security API1: object identifiers require object-level authorization, including read/update/destructive actions.
- NIST SSDF remains the broader protect/release/provenance baseline; R3 focuses on exact provider and owner seams rather than adding another scoring framework.

## Current frontier

1. Repair and independently re-read RT-GOV-001/002 at provider authority; do not infer closure from repository docs.
2. Close RT-SUPPLY-001 with provider-native tag rules plus protected-source ancestry admission.
3. Finish AF-S2 using existing Runtime factorized Principal primitives instead of creating a parallel identity system.
4. Add principal-bound Job/Artifact lifecycle semantics or move the enforcement seam to Security/Gateway with explicit subject/action/resource decisions.
5. Restore Gateway Runtime carrier liveness, then run two-principal negative live acceptance without conflating liveness with authorization safety.
6. Continue effect/recovery attacks only after principal boundaries are explicit, so evidence can attribute actions to the correct authority.
