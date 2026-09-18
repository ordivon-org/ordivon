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
