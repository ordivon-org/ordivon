# Finance retention / migration disposition

> **SUPERSEDED BY FINAL SOURCE-RETIREMENT CLOSEOUT — 2026-09-14.** This record remains the historical reason Finance was correctly held while current consumers, executor/recovery consequences, and owner-state responsibilities still depended on it. Those gates were subsequently revalidated and discharged for the **source repository**. Current disposition is `SOURCE_RETIRED / ARCHIVE_PRESERVED / LIVE_RECOVERY_RESIDUAL_SEPARATE`; see `finance-source-retirement-closeout-20260914.md`. The live recovery custody residual is not evidence that the Finance source repository remains a current project.

- Source: `/root/projects/ordivon-finance`
- Observed Finance revision: `f5f3c96a45d3ef2ea47311dc64ccc96d2877778d`
- Compared Market Capital Next revision: `33bd58f3ffd9a0425c41a54dd7d7cd336f90ee06`
- Assessed: 2026-09-14
- New-model disposition: **RETAIN ACTIVE / MIGRATE BY PROVEN CONSUMER CUTOVER / DO NOT ARCHIVE YET**

## Why Finance is not a retirement candidate yet

Finance still has current runtime and consumer consequences. The machine has an enabled/running `ordivon-finance-executor.service`, an enabled recovery-custody timer, and Harness still contains Finance current-state/recovery consumer paths. Finance also contains the current owner-specific state, observation, reconciliation, performance and execution-admission semantics used by those paths.

This is materially different from the retired broad owners whose remaining references were provenance only. Archiving Finance now would cut a current owner boundary before a successor has demonstrated parity.

## Current external-effect standing

The running executor is **disabled staging**, not an admitted live submission surface. Read-only observation on 2026-09-14 established:

- executor identity `executor:local-disabled-staging`;
- trust policy `disabled = true`;
- `realVenueReachable = false`;
- `readyForLocalSubmission = false`;
- `readyForHighAssuranceSubmission = false`;
- `readyForExternalSubmission = false`;
- no external financial write was attempted by the status check.

The fail-closed blockers included local submission disabled, real-venue reachability disabled, intentionally non-local human authority, and stale trade-credential/live-reconciliation readiness evidence. The service can therefore remain a bounded staging/recovery surface while migration proceeds; its mere running state must not be interpreted as live-trading authorization.

## Relationship to Market Capital Next

`ordivon-market-capital-next` is a clean-room mature-standard composition and explicitly does **not** import legacy Finance/Market-Capital code or schemas. It currently uses CFA/FIX/PFMI+ISO 20022/XBRL-oriented composition and bounded LEAN/Nautilus shadow paths, with production/live authorization still blocked.

Therefore Market Capital Next is a replacement **candidate and convergence target**, not a completed Finance successor. No semantic or operational equivalence is assumed from similar domain vocabulary.

## Required cutover rule

Finance may be retired only after each current consequence has a demonstrated destination and regression gate. At minimum:

1. owner/current capital-state and portfolio observation consumers have an admitted replacement;
2. effect identity, reservation/admission, ambiguous-outcome reconciliation and evidence retention are preserved by the selected mature/provider-native path;
3. Harness no longer has a current Finance owner dependency or its replacement is proven;
4. executor/recovery systemd units can be disabled without losing required recovery or reconciliation authority;
5. historical Finance research/state/evidence has a preservation path distinct from current operational truth;
6. Market Capital Next or another selected owner proves the exact needed real workload rather than claiming architecture-level parity.

## Migration direction

Continue externalizing Finance capability-by-capability into mature financial standards, provider-native APIs, Market Capital Next, Research v2, Runtime, Operations and ordinary data tooling. Retain custom Finance semantics only where an exact current consumer or safety/reconciliation invariant still fails substitution.

Do not create new broad Finance-native infrastructure merely to maintain historical architecture. Conversely, do not delete the current Finance owner while current consumers and the disabled staging executor still depend on it.
