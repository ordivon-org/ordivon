# Agent Birth Provider Boundary R1

Date: 2026-09-18
Standing: **IMPLEMENTED + TESTED IN HARNESS MAIN / PRODUCTION RELEASE CUTOVER NOT YET CLAIMED**

## One-sentence result

Agent Birth now has an explicit Provider Boundary diagnosis LEGO between read-only provider preflight and carrier routing. A healthy Browserless substrate combined with `CHALLENGE_GATED` is represented as `SUBSTRATE_HEALTHY_PROVIDER_NOT_ADMISSIBLE`, not as browser/carrier failure; the selected carrier is preserved, automatic Browserless/Profile/Launcher/Network repair is prohibited, and the existing bounded human-verification path remains available.

## Why this node exists

Before this change, the implementation already had an important partial separation:

- transport/carrier failures could fail over;
- challenge/auth/rate-limit/UI states did not rotate carriers.

But that separation lived mainly as a standing set and tests. A provider-policy blocker still flowed into the general materialization path without an explicit machine-readable diagnosis explaining **why infrastructure repair must not follow from it**.

R1-R9 Browser Security research made the missing abstraction visible.

The correct composition is:

```text
AB16 CarrierLease
        |
        v
AB17 ProviderPreflightObserver
        |
        | read-only observation
        v
AB37 ProviderBoundaryDiagnosis
        |
        +--> AB15 CarrierCandidateRouter
        |      carrier/transport failure -> narrow failover
        |      provider boundary         -> preserve selected carrier
        |
        +--> AB35 AutomationDoctor
               expose repair/routing policy
```

AB37 is deliberately not durable truth. It is a pure policy/classification LEGO.

## Runtime state

For:

```text
substrateHealth.healthy = true
provider standing       = CHALLENGE_GATED
```

AB37 produces:

```text
state                  = SUBSTRATE_HEALTHY_PROVIDER_NOT_ADMISSIBLE
substrateStanding      = HEALTHY
providerAdmission      = NOT_ADMISSIBLE
carrierRouting         = PRESERVE_SELECTED_CARRIER
humanVerificationEligible = true
reentry                = HUMAN_VERIFICATION_OR_EXPLICIT_AFTER_CONDITION_CHANGE
providerRootCauseEstablished = false
```

Automatic infrastructure mutation remains false.

## Repair non-conflation law

A provider-boundary observation by itself does **not** authorize:

```text
rotate-carrier
restart-carrier
clear-profile
mutate-launcher-flags
mutate-network-authority
```

This is stronger than “we currently choose not to do those things.” It is now an explicit policy output that downstream automation can inspect.

The only automatic carrier failover class remains the narrow pre-SEND transport/carrier set:

```text
SUBSTRATE_UNAVAILABLE
CARRIER_BUSY
PROVIDER_UNAVAILABLE
CONNECT_FAILED
```

## Human verification is preserved

The new diagnosis layer does not bypass or remove the existing human verification contract.

`CHALLENGE_GATED` and `AUTH_REQUIRED` remain human-verification eligible. The materialization layer can still create the existing private bounded handoff receipt and hold before SEND.

Therefore:

```text
provider boundary != infrastructure repair
provider boundary != automatic bypass
provider boundary -> explicit hold / bounded human verification / later re-entry
```

## Browser Security R9 relationship

The diagnosis carries:

```text
neutralAttributionReference:
  reference = browser-security-r9
  standing  = REFERENCE_ONLY_NOT_LIVE_ASSERTION
```

This distinction is intentional.

ProviderPreflight does not re-run R1-R9 experiments. It may prove current substrate health and current provider standing; it must not pretend that the entire neutral presentation stack was freshly re-measured.

R9 constrains **repair policy**, not current provider causality:

```text
R1-R9:
  measured neutral surfaces mechanistically localized

therefore:
  provider challenge alone is not evidence to randomly repair substrate nodes

but:
  provider-authoritative challenge cause remains UNKNOWN
```

## Current source implementation

Harness main:

```text
3f10f7bb7cb732e3b873fcc2aacb6ae7e9cf52f4
agent-birth: classify provider boundary holds
```

Primary implementation LEGO:

```text
scripts/provider_boundary_diagnosis.py
```

Consumers:

```text
ProviderPreflight / CF07 projection
Temporal Birth carrier routing
Browserless effect adapter
AutomationDoctor policy projection
release manifest
```

The implementation preserves CF07's content-minimal persisted event schema. The richer diagnosis is attached to the in-memory/provider-preflight result; sensitive `pageRef`, detail, token-like substrate fields, cookies, and provider content are not added to CF07 durable telemetry.

## Verification

Relevant Harness main gates passed:

```text
provider-boundary unit tests       6
Browserless automation tests      51 (3 skipped)
Temporal contract tests            7
Temporal deploy tests              3
release tests                     28
------------------------------------
relevant tests                    95
Ruff                              PASS
py_compile                        PASS
git diff --check                  PASS
```

## Remaining boundary

This change improves diagnosis and routing. It does not establish provider causality and does not make Agent Birth fully unattended through a provider challenge.

Current unresolved state remains:

```text
Browser substrate healthy
+
neutral measured mechanisms localized
+
provider not admissible
+
provider-authoritative cause unknown
```

That state is now represented explicitly rather than being collapsed into “browser automation failed.”
