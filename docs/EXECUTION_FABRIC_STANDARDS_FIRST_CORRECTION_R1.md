# Execution Fabric Standards-First Correction R1

Status: ACTIVE / supersedes the old E1-E7 implementation plan
Date: 2026-09-19

## Why this correction exists

The Workstation wave5 standards-first slice retired the generic Execution Fabric workflow resolver,
static routing catalog, binding files and workflow-derived provider backlog.

That newer result changes the implementation plan.

The old E1-E7 list remains useful only as a decomposition of physical effects. It must not be
implemented as another Workstation capability ontology.

Do not recreate:

- a Workstation workflow schema;
- a Workstation workflow resolver;
- a static provider-routing catalog;
- a planned-provider backlog merely to make an old workflow resolve;
- a generic Runtime drain/recover capability detached from the exact operation that owns its fence.

## Revised LEGO ownership

| Physical need | Mature / natural owner | Residual adapter |
|---|---|---|
| fence new Runtime admissions for one exact maintenance effect | Runtime admission.lock inside that effect owner | operation-specific adapter only |
| recover Runtime durable physical truth | Runtime startup, reconciliation and doctor semantics | observation adapter only |
| filesystem trim | Linux filesystem / fstrim | narrow Workstation provider only if a real operation consumes it |
| WSL terminate or shutdown | Microsoft wsl.exe lifecycle surface | narrow Windows WSL actuator with exact distro and postcondition evidence |
| VHD exclusive-open | Windows filesystem / VHD stack | narrow Windows storage actuator |
| VHD compact | native Windows VHD mechanism available on the host | narrow Windows storage actuator |
| VHD non-growth / identity verification | Windows filesystem observation | operation-scoped verifier |
| durable multi-stage orchestration | Temporal | activities bind narrow provider actions |
| process / decision interchange | BPMN / DMN when actually required | no Ordivon workflow language |
| compensation | effect or domain owner using Saga semantics | exact compensating action only |

## Revised composition

Owner operation
    |
    +-- systemd / SCM / provider-native controller
    |
    +-- Temporal, only when durable orchestration is required
            |
            v
       narrow provider action
            |
            v
       platform authority
            |
            v
          evidence
            |
            v
   Runtime Job / Attempt truth
            |
            v
   owner-scoped semantic verifier

Ownership after correction:

- systemd, SCM and provider-native controllers own ordinary lifecycle;
- Temporal owns durable retries, timers, signals, cancellation and recovery when needed;
- provider code owns one concrete machine action;
- the host platform owns the primitive;
- Runtime owns physical Job, Attempt and evidence truth;
- Workstation owns exact node-local realization and binding plus operation-relative evidence;
- Host owns semantic continuity;
- the domain owner owns the final semantic verdict.

A missing physical operation is reported unavailable at its natural provider boundary.
It is not a reason to create a local routing ontology.

## D-drive / WSL maintenance after resolver retirement

The old D-drive forcing workflow remains useful only as a problem decomposition:

operation-specific preflight
    -> Runtime-owned admission fence for this exact maintenance effect
    -> filesystem trim
    -> Windows-owned WSL terminate / offline proof
    -> Windows VHD exclusive-open
    -> native VHD compact
    -> byte / identity verification
    -> Runtime and Host service recovery
    -> operation-scoped postconditions

If this maintenance becomes long-running, retryable, externally signaled or resumable across
process failure, encode the orchestration in Temporal. Otherwise retain the smallest accepted
maintenance mechanism.

In neither case recreate the retired EF6 resolver.

## Immediate order

1. complete remaining R6c native Windows acceptance;
2. use Workstation wave5 provider-only model as the forward baseline;
3. do not implement the retired E1-E7 backlog;
4. retain only concrete D-drive / WSL provider actions that a real accepted operation still needs;
5. use Temporal only if durable workflow requirements justify it;
6. promote the exact accepted native Windows Runtime only after evidence closes;
7. delete the WSL-hosted Windows control-plane carrier after windows-main becomes primary;
8. delete remaining retired EF6 workflow and binding artifacts after claimant checks.

## Active custom-carrier retirement

The claimant audit on 2026-09-19 found no production or documentation consumer for the former
`planning/lego-plan-r1.json` planning ontology or the active
`RUNTIME_WINDOWS_EXECUTION_FABRIC_LEGO_R1.md` execution-plan carrier. Their current content was
already owned by this standards-first correction, `AUTHORITY_STANDARD_MIGRATION_R1.md`, and the
R6c acceptance evidence. Both active custom carriers were therefore deleted rather than revised
into another Ordivon-specific schema. Historical documents explicitly marked `RETIRED` remain only
as migration evidence and are not architecture authority.

## Ratchet

CUSTOM
  -> SHADOWED_BY_STANDARD
  -> STANDARD_ACCEPTED_SIDE_BY_SIDE
  -> STANDARD_PRIMARY
  -> CUSTOM_UNREACHABLE
  -> CUSTOM_DELETED

A deleted custom authority may not be reintroduced without a new irreducibility argument and
fresh acceptance evidence.
