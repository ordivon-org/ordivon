# Workstation Execution Fabric Workflows

These manifests are Workstation/Operations-owned machine workflow plans.

They are plan-only Execution Fabric R1 data. They do not execute commands, acquire authority,
dispatch Runtime Jobs, stop WSL, compact VHDs, or replace the current accepted R2 maintenance
scripts.

The Runtime repository owns the generic WorkflowPlan contract. Workstation owns these concrete
machine-substrate compositions.

Current forcing workflows:

- wsl-control-plane-recovery-r1.json
- d-drive-vhd-compact-r2.json

Promotion rule: a workflow realization may replace an accepted maintenance script only after it
reproduces the same gates, evidence, failure recovery, and destructive acceptance.

## EF6b dry-run binding

workflow_resolver.py resolves workflow steps only against explicitly advertised Resource/Node/Provider
descriptors. It never executes a shell fallback. Zero provider matches remain unresolved; multiple
matches remain ambiguous.

catalog/current-r1.json records only currently proven provider reality:

- the local Linux runner;
- the Windows native launcher attached to the Linux Runtime node;
- windows-local exists as a future control domain but does not yet claim a native control plane or
  machine-control providers.

provider-backlog-r1.json groups current unresolved workflow capabilities into six planned provider
families. A planned provider is not discoverable or routable until it is implemented, tested,
materialized, and added to the current catalog.

## EF6c accepted read providers

The current catalog now includes two live-read-accepted Linux-side providers:

- provider/linux-local/runtime-control-observer-v1 exposes runtime health and doctor;
- provider/linux-local/service-observer-v1 exposes exact allowlisted Runtime + Host service probe.

They are observation providers only. They do not advertise runtime drain/recover or service ensure,
because those mutating capabilities have not yet reached the same acceptance state.

## EF6d Windows WSL observer

provider/windows-local/windows-wsl-observer-v1 is live-read accepted for:

- capability/wsl/probe;
- capability/wsl/verify-offline.

Its implementation is content-addressed under C:\ProgramData\Ordivon\ExecutionFabric and was
accepted through Runtime executionTarget=windows_native. windows-local still advertises
nativeControlPlane=false: native process execution is proven, but an independent Windows Runtime
control plane is not yet claimed.

The mutating capability capability/wsl/terminate remains missing and is intentionally not
advertised by the current catalog until its separate actuator contract and destructive acceptance
are complete.

## EF6d authority validation

provider/windows-local/authority-validation-v1 is live accepted for
capability/authority/validate using the D-drive compact R2 receipt profile.

It was accepted in both directions through windows_native execution:

- a short-lived synthetic receipt satisfying the exact profile validated successfully;
- the deliberately non-authorizing R2 template returned authorized=false and a non-zero exit.

The provider does not issue, renew, or mutate authority. It only evaluates supplied evidence.
