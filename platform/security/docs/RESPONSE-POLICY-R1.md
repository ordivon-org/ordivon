# Response Policy R1

Date: 2026-10-01
Work: `work:security:dwc-r21:dw03-response-policy:20261001`
Status: DW03 CANDIDATE / POLICY PROJECTION / NO EFFECT AUTHORITY

## Decision

DW03 is a thin response-policy projection over exact DW01/DW02 facts plus organization-owned impact/policy inputs.

It does **not** introduce a universal cyber-risk score, a workflow engine, a vulnerability database, a new policy service, or effect authority. OPA/Rego remains the existing policy execution owner.

The output is:

- a bounded response action class: `defer`, `scheduled`, `out-of-cycle`, or `immediate`;
- an optional owner-supplied deadline budget;
- explicit policy/input uncertainty and ambiguity;
- `authorityGranted=false` in every case.

A deadline may inform orchestration priority. It never authorizes a patch, isolation action, exploit-validation action, restart, credential rotation, or any other effect.

## Upstream binding

DW03 consumes the exact DW02 fusion envelope:

- `kind = ordivon.security.threat-applicability-fusion`;
- exact DW01 `subject.subjectRef`;
- exact DW01 `subject.snapshotDigest = sha256:<64 hex>`;
- `vulnerabilityRef`;
- `claim = AFFECTED | NOT_AFFECTED | UNDER_INVESTIGATION`;
- DW02 currentness;
- current CISA KEV `threatSignals.knownExploited`;
- dated FIRST EPSS rows.

A malformed or missing exact DW01 subject snapshot binding is `INVALID_INPUT`. DW03 therefore cannot turn an unbound CVE/threat signal into a response obligation.

DW02 emits `knownExploited=true` only from current admitted CISA KEV evidence. DW03 may promote effective SSVC exploitation to `active` from that current signal. Absence of a current KEV signal does not prove non-exploitation and does not overwrite the separately supplied exploitation decision point.

## SSVC / external-first policy shape

The core vocabulary follows the CERT/CC SSVC deployer decision model:

- Exploitation: `ssvc:E:1.1.0`
- System Exposure: `ssvc:EXP:1.0.1`
- Automatable: `ssvc:A:2.0.0`
- Human Impact: `ssvc:HI:2.0.2`
- outcomes Defer / Scheduled / Out-of-Cycle / Immediate: `ssvc:DSOI:1.0.0`
- deployer decision table: `ssvc:DT_DP:1.0.0`

Ordivon does not turn these into a proprietary scalar score. The Rego module performs exact row matching against a decision table supplied by an identified policy owner.

The R1 test table contains only representative upstream-compatible rows for qualification. It is **not** the production organization policy and does not claim to reproduce the complete upstream table.

## Local decision facts

In addition to the exact DW02 envelope, the case supplies four separable policy facts:

- `exploitation = none | public-poc | active | UNKNOWN`;
- `systemExposure = small | controlled | open | UNKNOWN`;
- `automatable = no | yes | UNKNOWN`;
- `humanImpact = low | medium | high | very-high | UNKNOWN`.

Human/mission/business impact remains domain-owned input. DW03 does not infer it from CVSS, EPSS, asset names, model capability tiers, or market value.

`UNDER_INVESTIGATION` is treated as explicit applicability uncertainty. UNKNOWN facts are never silently coerced. A policy owner may deliberately provide `unknownActionClass`; that is a versioned policy choice, not an Ordivon default.

## EPSS semantics

FIRST EPSS remains a dated probabilistic signal. DW03 validates and preserves the DW02 EPSS rows but has **no built-in EPSS threshold**.

Changing EPSS from a low to a high probability alone does not change the action class in R1. If an organization wants EPSS to alter response outcomes, that behavior must be represented explicitly in a future versioned policy/table contract rather than hidden in code.

## Policy identity and deadline profile

`input.policy` must identify:

- `ownerRef`;
- `policyId`;
- `policyVersion`;
- `decisionTableRef`;
- `decisionTableRows`.

Optional `deadlineBudgets[actionClass]` entries carry:

- `budgetRef`;
- positive `maxSeconds`.

No production deadline is hardcoded. Missing budget => `ACTION_ONLY` / `deadlineStatus=UNSET`. A malformed supplied deadline profile makes the policy invalid.

## Standing

- `INVALID_POLICY`: policy identity/table/deadline profile is malformed.
- `INVALID_INPUT`: exact DW01/DW02 binding or a supplied fact is malformed.
- `NOT_APPLICABLE`: DW02 says `NOT_AFFECTED`.
- `UNKNOWN_INPUT`: applicability or another required decision fact is unknown and policy has no explicit unknown disposition.
- `POLICY_AMBIGUOUS`: more than one row matches.
- `POLICY_NO_MATCH`: no row matches a fully known affected case.
- `ACTION_ONLY`: action class resolved, but no valid owner deadline budget exists for it.
- `DECIDED`: action class plus owner-supplied deadline budget resolved.

None of these standings proves patch installation, mitigation, verified protection, absence of compromise, eradication, or recovery.

## Qualification / negative controls

R1 tests cover:

1. exact DW02 -> decision-table projection;
2. exact DW01 snapshot digest required;
3. policy owner/version required;
4. owner deadline projected rather than invented;
5. `UNDER_INVESTIGATION` preserved as uncertainty;
6. explicit owner routing for unknowns without granting authority;
7. current KEV signal promotion to active exploitation;
8. absent current KEV does not invent exploitation state;
9. exposure sensitivity;
10. EPSS 0.01 -> 0.99 alone does not create a hidden threshold;
11. malformed EPSS fails closed;
12. NOT_AFFECTED has no remediation action;
13. duplicate matching rows fail as ambiguity.

## Promotion boundary

R1 closes the response-policy **mechanics** gap, not organization policy ownership.

Production promotion still requires the legitimate policy owner to pin:

- the exact production decision-table artifact/version;
- the organization-specific unknown disposition;
- any explicit EPSS-derived policy behavior;
- numeric response budgets/SLEs and review cadence.

The later DWC stages remain separate:

`DW03 response obligation -> DW04/DW05 evidence/coverage -> DW06 COA -> DW07 effect admission/execution -> DW08 consequence verification`.

No earlier stage may bypass those authority and verification boundaries.
