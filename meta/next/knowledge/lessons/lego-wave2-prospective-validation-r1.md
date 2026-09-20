# LEGO Theory Wave 2 — Prospective Cross-Domain Validation R1

Date: 2026-09-18
Status: PROSPECTIVE VALIDATION COMPLETE / FOLLOW-UPS OPEN

## Purpose

Test whether Wave 2 mature-theory lenses improve real Ordivon decisions rather than merely adding vocabulary.

Wave 2 lenses:
- compositional contracts;
- causal intervention;
- FMEA / FTA;
- information flow.

Acceptance follows the Wave 1 rule. A lens earns retention when it produces at least one:
- corrected boundary;
- corrected edge/contract;
- falsifiable experiment;
- newly exposed hazard/failure path;
- justified no-change / not-identified decision.

No result from one case enters the common LEGO schema automatically.

---

## Case A — Harness replacement seam / Compositional Contracts

System:
- `/root/projects/ordivon-harness`
- examined source revision `8e291f2af2912af37572a09e8f0ed4daece733f6`
- project LEGO node `H05 HarnessProviderSPI`

### Before

The H05 acceptance condition was essentially:

> a second harness implementation can run behind the same caller-facing contract.

That is compatibility-by-execution, not substitutability.

A replacement can pass the same superficial API and still:
- require stronger hidden network/credential/environment assumptions;
- widen the admitted Tool surface;
- turn UNKNOWN into retry permission;
- collapse Provider transport success into semantic completion;
- move Runtime or caller Task authority into the adapter.

### Assume-guarantee result

The replacement seam must satisfy:

`existing environment assumptions discharge replacement assumptions`

and:

`replacement guarantees >= required Harness guarantees`

without strengthening caller authority requirements.

The Harness plan was corrected so H05/HS1 now requires:
- no stronger undeclared caller/environment authority assumptions;
- preservation of Tool authority;
- preservation of no-blind-redispatch / UNKNOWN semantics;
- preservation of completion boundaries;
- preservation of Runtime/Task ownership;
- negative substitutability/fault characterization, not only a happy-path second implementation.

Integrated Harness main commit:
- `e29def339995c20ed4f0022d502b557d13a4359d`

Result:
- **POSITIVE CONTRACT CORRECTION**

This is a concrete improvement over API-shape compatibility.

---

## Case B — Browser/provider security / Causal Intervention

Evidence:
- `knowledge/lessons/cloudflare-provider-security-boundary-r1.md`
- `knowledge/lessons/cloudflare-provider-security-exp-r5.md`

### Causal question split

R5 supports bounded intervention-style engineering attribution inside the neutral test environment:

1. host-direct -> container-direct changed fonts/canvas and browser-level GPU evidence while the Browserless control layer was absent;
2. container-direct -> Browserless changed command-line/target topology/window geometry while the image/runtime baseline was matched.

These comparisons narrow which system boundary produces measured local differences.

But the target provider outcome is a different causal estimand:

`effect of measured browser/runtime variable on provider challenge/admission`

R5 did not intervene on those variables while observing a protected-provider challenge, by design.

Therefore:

`local mechanism attribution != provider-challenge causal effect`

and the provider effect remains:

- **NOT IDENTIFIED from current neutral evidence**

The existing project already states this boundary and explicitly refuses to use the protected challenge as an optimization oracle.

Result:
- **CONFIRMATORY / JUSTIFIED NOT-IDENTIFIED DECISION**

No architecture change is justified.

The causal lens earned retention by preventing an invalid transport from a local controlled differential to a third-party provider policy claim.

---

## Case C — Agent Automation continuation / FMEA + FTA

System:
- `/root/projects/ordivon-harness`
- source revision `8e291f2af2912af37572a09e8f0ed4daece733f6`

Scope:
- Browserless continuation effect family;
- `turn_effects` ledger;
- Temporal continuation workflow.

### FMEA failure mode

Function:
- send exactly one continuation turn and retain enough evidence to recover/reconcile ambiguous outcomes.

Failure mode:
- process/transport failure after durable UNKNOWN effect fence and around/after SEND, before a conclusive COMPLETED write.

Current barriers:

`BEGIN IMMEDIATE -> INSERT UNKNOWN -> COMMIT -> send.click()`

This is a strong duplicate-effect barrier.

Observed behavior:
- any existing turn ledger row disables provider preflight/retry admission for that logical turn;
- UNKNOWN remains `safeToResend=false`;
- activity retry re-enters the same effect identity;
- no public/service turn-level reconcile/observe operation was found;
- only `playwright_browserless_turn_once.py` writes `turn_effects`.

Existing characterization test:
- `test_claimed_continuation_never_enters_retry_or_provider_preflight`
- rerun under this study: PASS.

Runtime evidence:
- `job-01a0b3da-84fa-7920-ae26-a971c1ed9e5c`

### Failure effect

Safety:
- PASS: blind duplicate SEND remains blocked.

Liveness:
- unresolved: an UNKNOWN continuation has no explicit owner that can re-observe the provider and converge the ledger to a stronger standing.

This is a classic safety/liveness trade:

`no duplicate effect`
does not imply
`ambiguous effect eventually converges`

### FTA top event

Top event:
- `continuation remains permanently non-convergent after ambiguous SEND`

Current credible path:

`effect fence committed UNKNOWN`
AND
`SEND outcome not conclusively written`
AND
`same logical turn cannot be resent`
AND
`no turn-level reconciliation owner exists`
-> `persistent UNKNOWN`

Candidate follow-up:
- define a read-only `TurnReconciler` only if provider evidence can safely identify the exact turn without creating another SEND.
- if exact reconciliation is not possible, document UNKNOWN as intentionally terminal and expose an explicit human/domain resolution policy instead of silently retrying.

Result:
- **POSITIVE RELIABILITY / CONVERGENCE GAP DISCOVERY**

No production repair is claimed yet because the correct reconciliation oracle must be established first.

---

## Case D — Agent Service R14 credentials / Information Flow

System:
- Agent Service R14 line based on `0721009237365ea61cd975bd187be5171f1dcd52`

Initial R14 wording called `CredentialReference` "secret-free" locator metadata.

### Information-flow model

Actual R10/R14 design separates:

`CredentialReference (durable opaque locator metadata)`
from
`CredentialHeaderMaterial (transient resolved credential material)`

R10 already contains an intentional test locator:

`vault://SECRET-PATH-THAT-MUST-NOT-BE-AUDITED`

and verifies that the locator is omitted from audit projection.

A bounded characterization in the Wave 2 study also showed that `CredentialReferenceStore.register()` accepts and persists arbitrary opaque locator bytes. A marker placed in the locator remained in the credential-reference table.

Runtime evidence:
- `job-01a0b3d6-603b-7ca1-b8bf-d8f9eb08d200`

This does not demonstrate leakage of a real token. It demonstrates that:

`reference-only != guaranteed non-sensitive`

### Corrected information-flow contract

The accurate boundary is:

- Agent Service does not persist resolved access-token/header material in the R14 transport-credential bridge;
- `CredentialReference.reference` is opaque provider locator metadata and may itself be sensitive;
- locator metadata must remain absent from public/model/audit projections unless the owning provider explicitly classifies it safe;
- information visibility and effect authority remain separate.

The R14 documentation/graph/acceptance were corrected without changing runtime behavior.

Validation:
- R10 + R14 relevant suites: **25 tests PASS**
- Runtime test job: `job-01a0b3db-e394-7a83-aeb6-32b137d1c683`

Correction commit:
- initial detached correction: `c393d9b7e7970f5dd68bdd49a219d5c7e713d60f`
- integrated active R14 workspace head: `3f3dbb9940e12755485d5149f843d1dbb13ec982`

Result:
- **POSITIVE INFORMATION-BOUNDARY / MODEL CORRECTION**

---

## Cross-domain lens verdicts

### Compositional Contracts — PROSPECTIVELY VALIDATED

It changed a real replacement acceptance condition from:

`same interface + successful run`

to:

`assumptions discharged + required guarantees preserved`.

Standing:
- **PROSPECTIVELY_VALIDATED_REPLACEMENT_LENS**

### Causal Intervention — PROSPECTIVELY VALIDATED AS A CLAIM-BOUNDARY LENS

It did not add a new mechanism. It prevented an invalid causal promotion from neutral browser differential to protected-provider policy causality.

Standing:
- **PROSPECTIVELY_VALIDATED_CAUSAL_BOUNDARY_LENS**

### FMEA / FTA — PROSPECTIVELY VALIDATED

It exposed a reliability property not captured by the existing no-resend safety claim:
- duplicate-effect safety is strong;
- convergence/liveness after UNKNOWN lacks an explicit turn-level owner.

Standing:
- **PROSPECTIVELY_VALIDATED_RELIABILITY_LENS**

### Information Flow — PROSPECTIVELY VALIDATED

It corrected the distinction among:
- resolved credential secret material;
- opaque locator metadata;
- audit/model/public projections;
- effect authority.

Standing:
- **PROSPECTIVELY_VALIDATED_INFORMATION_BOUNDARY_LENS**

---

## Core-promotion result

No new mandatory LEGO Core field is promoted.

Wave 2 findings fit existing mechanisms:
- substitutability belongs in acceptance/contract obligations;
- causal models remain derived evidence;
- failure trees/FMEA remain analysis evidence and follow-up slices;
- information-flow labels remain scoped to the system and observer model.

`schemas/project-lego-plan-r1.schema.json` remains unchanged.

## Meta-method update

Wave 2 strengthens the LEGO method with four distinct questions:

1. **Composition:** If every brick works, does the assembly work, and may this brick really replace that one?
2. **Causation:** If two states differ, what intervention actually caused the outcome?
3. **Failure:** If a component or step fails, where does failure propagate and can the system recover?
4. **Information:** What information can influence or be observed across each boundary?

These questions are orthogonal enough to remain separate lenses.

## Follow-ups

1. Harness H05: implement/falsify one alternate adapter against the strengthened assume-guarantee acceptance.
2. Agent Automation: decide whether exact read-only continuation reconciliation is possible; if not, make terminal UNKNOWN resolution policy explicit.
3. Agent Service R14: keep the information-flow correction attached to the R14 integration line.
4. Causal Browser Security: retain NOT IDENTIFIED for protected-provider causality until a legitimate experiment actually observes the relevant outcome under a valid intervention design.
