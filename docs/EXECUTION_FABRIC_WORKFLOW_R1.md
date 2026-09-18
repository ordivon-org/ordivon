# Execution Fabric Workflow R1

## Ownership

A WorkflowPlan is an execution-free composition contract above Runtime admission.

Runtime owns physical Job / Attempt truth after a concrete step is admitted.
Controllers own desired/observed reconciliation.
Workflow owners compose controller/capability intents across time.
Workstation/Operations owns machine substrate workflows such as WSL lifecycle and VHD maintenance.

A WorkflowPlan therefore cannot claim that execution has started and a WorkflowStep cannot claim that an effect was dispatched.

## Step model

Every step names:

- one resource;
- one requested capability;
- optional preferred provider;
- authority mode;
- conflict mode;
- dependency step IDs;
- optional evidence policy;
- a phase: observe, gate, act, verify, recover, or compensate.

The dependency graph must be acyclic. Dependencies and compensation targets must reference real steps.

## WSL control-plane recovery decomposition

1. observe WSL availability;
2. gate on exact Runtime + Host service state;
3. recover only the required control-plane services;
4. verify Runtime-owned health projection.

This replaces a monolithic recovery script conceptually, but R1 does not yet delete or activate any machine script.

## D-drive VHD compact R2 decomposition

The existing R2 safety contract maps to reusable workflow steps:

1. fence/drain Runtime admission and capacity;
2. verify Runtime Doctor and zero recovery-required state;
3. validate short-lived authorization bound to the exact controller/gate/VHD;
4. trim and sync the Linux filesystem;
5. terminate only the target WSL distribution;
6. gate on VHD exclusive-open availability;
7. compact the VHD;
8. recover Runtime + Host;
9. verify Runtime health and Runtime Doctor closure.

The current PowerShell/Bash implementation remains the execution truth until a Workstation-owned workflow realization has equivalent evidence and destructive acceptance.

## Non-goals

R1 is not a workflow executor, scheduler, Temporal replacement, retry engine, policy engine, authority issuer, or Runtime admission surface.
