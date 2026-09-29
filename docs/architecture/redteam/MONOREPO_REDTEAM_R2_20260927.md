# Ordivon Monorepo Red-Team R2

Date: 2026-09-27
Status: **CURRENT CANDIDATE FINDING LEDGER — successor to R1**

## Truth fence

- Current local `main` used for registration: `2bc46824d986c842375759ff39c731ee79195c5b`.
- Dynamic falsifiers were executed on immediately preceding current source `7661bdf90ce0878c39b8cdebf565ff2b01a686df`.
- The only intervening commit was Agent-Birth structured-Windows-context work; it did not touch the Runtime assurance, GitHub workflow, or SECURITY-policy paths under test.
- R1 remains immutable historical campaign evidence. R2 adds only findings proven after R1.

## LEGO standing

```text
SOURCE / PROVIDER TRUTH
  -> SECURITY CONTROL DISCOVERY
  -> ASSURANCE PREDICATE
  -> OBSERVATION SUBJECT BINDING
  -> REPORTING / RESPONSE AUTHORITY
  -> RECOVERY FALSIFIER
```

A file being present is not provider execution. A check returning PASS is not evidence unless its subject and provider truth are bound correctly.

## RT-ASSURANCE-001 — Runtime conformance treats inert nested workflow source as active CodeQL evidence

**Class:** `CONFIRMED_NEW`
**Priority:** MEDIUM
**Owners:** Runtime assurance + repository mechanics

The authoritative monorepo has only two root GitHub Actions workflow files: `.github/workflows/ci.yml` and `.github/workflows/runtime-release.yml`. Runtime still retains `services/runtime/.github/workflows/codeql.yml`. GitHub Actions discovers workflow files from the repository-root `.github/workflows` directory; a nested owner `.github/workflows` directory is not itself a live monorepo Actions entry point.

This alone would be migration residue, not a finding. The finding is that `services/runtime/scripts/check_runtime_standard_native_r3.py` uses `exists(".github/workflows/codeql.yml")` under `services/runtime` as evidence for `RT-Q-003`, `RT-SSDF-PO-002`, and `RT-SSDF-PW-001`. `services/runtime/SECURITY.md` also says the Runtime security process is enforced through CodeQL. Current root CI contains no CodeQL step and current `runtime:verify` contains no CodeQL step.

A fresh execution on source `7661bdf90...` emitted `RT-Q-003=PASS` and `RT-SSDF-PW-001=PASS` while using the nested workflow-file existence predicate. `RT-SSDF-PO-002` happened to remain OPEN because the nested standalone Dependabot file is absent.

**Impact:** assurance can report a provider-backed security control as present without proving that the provider executes that control. This is evidence/assurance corruption, not proof that CodeQL scanning is absent everywhere: GitHub provider-native default setup or another external configuration was not read back by this falsifier.

**Acceptance:** bind CodeQL assurance to an active root workflow or provider-native CodeQL configuration/readback; never infer provider execution from nested workflow-file existence; explicitly classify retained owner workflow templates as portable/non-live.

Evidence: `evidence/RT_ASSURANCE_001_NESTED_WORKFLOW_EVIDENCE_R1.json`.

## RT-EVIDENCE-001 — Runtime conformance generator emits fresh observations under a hard-coded historical subject

**Class:** `CONFIRMED_NEW`
**Priority:** MEDIUM
**Owner:** Runtime assurance/evidence

`check_runtime_standard_native_r3.py` hard-codes:

```text
date              = 2026-09-14
subject.repo       = ordivon-runtime
subject.revision   = 8355a4d24d2930d87969d769a73882396b806f48
```

The red-team executed that generator from current monorepo source `7661bdf90...`; the newly generated observation still claimed the historical standalone revision above. The measurement values changed relative to the checked-in historical report, proving this is not merely archival metadata: new measurements are being attached to an old subject.

**Impact:** exact evidence/currentness binding is broken. An Agent or human can consume a newly generated report and incorrectly attribute its measurements to a historical source revision.

**Acceptance:** derive exact current Git revision at generation time; represent owner subtree identity separately when useful; separate observation time from historical standard metadata; explicitly bind dirty source state or fail closed.

Evidence: `evidence/RT_EVIDENCE_001_SUBJECT_BINDING_R1.json`.

## RT-SECURITY-001 — Canonical monorepo lacks a repository-local recognized vulnerability-reporting authority

**Class:** `CONFIRMED_NEW`
**Priority:** MEDIUM
**Owners:** repository governance + Security

Canonical origin is `git@github.com:ordivon-org/ordivon.git`. The only tracked `SECURITY.md` files are owner-local `services/runtime/SECURITY.md` and `services/harness/SECURITY.md`; none exists at `.github/SECURITY.md`, repository-root `SECURITY.md`, or `docs/SECURITY.md`. Those owner policies still route private vulnerability reports to the pre-monorepo standalone repositories `zycxfyh/ordivon-runtime` and `zycxfyh/ordivon-harness`.

GitHub recognizes repository security-policy files in `.github`, repository root, or `docs`; nested owner locations are documentation, not the repository community-health policy location.

**Impact:** vulnerability reporters and GitHub repository UI may not reach the canonical monorepo reporting authority from repository-local policy, while owner documentation can direct reports to historical repositories. This does not claim that the `ordivon-org` organization lacks an organization-wide default policy; that provider fallback was not read back here.

**Acceptance:** establish a canonical repository-level policy or explicitly verify/bind an organization-level policy; route reports to the canonical provider authority; retain owner security boundaries as subordinate documentation; make repository governance test the location and reporting target.

Evidence: `evidence/RT_SECURITY_001_REPORTING_AUTHORITY_R1.json`.

## Negative control — Runtime orphan recovery held

Two harmless red-team executions initially projected `orphaned / LIVE_UNIT_WITHOUT_LAUNCH_TOKEN_EVIDENCE`. Both later converged to the identity-bound runner result without redispatch; one durable timeline explicitly recorded `RUNNER_RESULT_RECOVERED` followed by `JOB_RESOLUTION_CORRECTED`, final `succeeded`, exit code 0. This directly exercises the newly integrated orphan-recovery outcome-preservation work and did not yield a finding.

Evidence: `evidence/RUNTIME_ORPHAN_RECOVERY_NEGATIVE_CONTROL_R2.json`.

## R2 frontier

1. Repair assurance/evidence predicates before adding more scanners: provider execution truth first.
2. Add canonical monorepo vulnerability-reporting authority and remove stale standalone report routing.
3. Continue R1 RT-SUPPLY-001 and RT-CI-001 remediation independently; do not mix provider tag governance with evidence-generator fixes.
4. Re-run Runtime conformance after repair and require exact source binding plus honest CodeQL standing.
5. Keep Gateway AF-S2 as known-open until Runtime Gateway credentials are live enough to measure actual consequence; liveness failure is not authorization evidence.
6. Continue Social Work attacks only above its documented HOLD boundary; self-asserted ActorRef is explicitly not authenticated identity.
