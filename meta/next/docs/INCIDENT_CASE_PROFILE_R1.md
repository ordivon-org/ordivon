# Incident Case Profile R1 — Cross-owner incident composition

Date: 2026-09-23
Status: **R1 EXTRACTED PROFILE / NO INCIDENT SERVICE**

## Decision

Ordivon already has multiple incident-adjacent owners:

- Social Fabric emits CloudEvents-shaped damage/attention signals.
- Runtime owns execution ambiguity, recovery, exact replay and terminal evidence.
- Harness has incident-analysis evidence with hypotheses, explicit unknowns and human-authority signals.
- Security derives verified consequence only from admitted effect + execution receipt + later authoritative observation.

The repeated structure is sufficient to name a composition profile. It is **not** sufficient to create a new incident database, incident daemon, global incident state machine, automatic containment controller, root-cause oracle, or repair authority.

## Core topology

```text
owner observation / damage signal
        |
        v
task-local incident admission
        |
        +---- exact affected-owner refs
        +---- exact evidence refs
        +---- impact / unknowns
        |
        v
investigation hypotheses
        |
        +---- supported
        +---- falsified
        +---- unresolved
        |
        +----> natural-owner containment actions
        |
        +----> natural-owner recovery actions
        |
        +----> authoritative consequence / recovery verification
        |
        v
regression obligation / owner closure
```

Each arrow is a relation between existing owner facts, not a new durable workflow.

## Separation laws

1. **Damage signal != incident admission.** A Social Fabric signal can attract attention but cannot mint an incident, grant authority or choose remediation.
2. **Incident case != owner truth registry.** Runtime, Security, Harness, Workstation and domain owners retain their own mutable facts.
3. **Detection != containment authority.** Observing a failure does not authorize stopping, restarting, revoking or mutating anything.
4. **Execution receipt != consequence truth.** Security's current consequence verifier already proves this distinction.
5. **Recovery action != verified recovery.** The relevant owner must observe the post-recovery state.
6. **Hypothesis != root cause.** Supported, falsified and unresolved hypotheses remain distinct; unknown root cause is a valid standing.
7. **Ambiguous external effects reconcile; they are not blindly retried.**
8. **Closure != evidence deletion.** Historical evidence and unresolved unknowns remain attributable after closure.
9. **Regression obligation != regression execution.** An incident may create a required future check without this profile owning CI or scheduling.
10. **Incident composition cannot widen its own authority.**

## Profile dimensions

R1 deliberately avoids one scalar incident state. A case may project independent dimensions:

- detection evidence;
- affected subjects/owners;
- impact;
- containment evidence;
- consequence standing;
- investigation hypotheses and unknowns;
- recovery evidence;
- regression obligations;
- natural-owner closure/acceptance.

A dimension may remain unknown without forcing the others to a fabricated terminal value.

## Evidence pressure

### Case A — WSL/VHD damage and coordination

Source:
`meta/next/evidence/acceptance/social-fabric-coordination-r2-vhd-cut-20260923.json`

The historical cut contains a CloudEvents damage signal for DiskPart RPC failure, competing VHD/WSLService candidates, exact evidence references, and storage pressure. Social Fabric correctly emits attention and shadow inhibition but does not select or execute remediation.

What it proves for R1: **anomaly/damage observation is useful input while remaining non-authoritative.**

### Case B — Runtime Windows recovery

Source:
`services/runtime/evidence/windows-native-rw5-recovery-20260810.json`

Runtime proves recovery with exact Job/Attempt identity, no duplicate dispatch, process-tree cleanup, power-request cleanup, reservation release and final acceptance. Exact replay never redispatches the interrupted effect.

What it proves for R1: **recovery and reconciliation remain with the execution owner and require exact evidence.**

### Case C — Harness engineering incident analysis

Source:
`services/harness/tests/fixtures/engineering_incident_browserless_20260909.json`

The fixture carries affected capabilities, observed/falsified signals, supported/falsified/unresolved hypotheses, explicit unknowns, impact and human-authority signals.

What it proves for R1: **investigation needs hypotheses and unknowns without pretending that the analysis layer owns provider truth.** The fixture is evidence of pressure, not a canonical global incident schema.

### Case D — Security consequence verification

Source:
`platform/security/docs/CONSEQUENCE-VERIFICATION-DIFFERENTIAL.md`

Security already distinguishes admitted, executed, unverified, consequence mismatch and verified consequence using later authoritative world observation.

What it proves for R1: **repair/execution cannot self-certify the resulting world state.**

## Canonical composition

R1 therefore reuses:

- CloudEvents 1.0 Social Fabric damage signals for optional detection input;
- owner-native evidence and identifiers;
- Runtime recovery/reconciliation;
- Security consequence verification where applicable;
- Verification Obligation / natural verifiers for regression checks where a consumer needs them;
- existing Human/domain authority for irreversible or domain-semantic decisions.

## Growth rule

A future Incident Contract/schema is admitted only if at least two natural owners require the **same machine-enforced missing relation** that this profile cannot express using exact references.

More incidents alone are not sufficient.

## Non-claims

R1 does not provide:

- a universal incident ID registry;
- severity ranking or universal risk score;
- incident scheduling/on-call dispatch;
- automatic containment;
- root-cause inference;
- automatic repair;
- automatic closure;
- a new source of truth;
- a second recovery engine;
- a replacement for Security, Runtime, Workstation, Harness or domain evidence.

The architectural rule is: **an incident coordinates evidence and obligations; natural owners still own effects and truth.**
