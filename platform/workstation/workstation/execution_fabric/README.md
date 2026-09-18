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
