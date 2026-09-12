# Provider: Ordivon Runtime

- Source: `/root/projects/ordivon-runtime`
- Observed revision: `e2c25e03dde1`
- Role: exact physical/local execution provider
- Migration mode: metadata only; Runtime remains external and replaceable

## Capabilities

- workspace-scoped execution;
- durable Job/Attempt/Artifact evidence;
- immutable/digest-bound inputs where configured;
- bounded Linux/Windows execution surfaces;
- exact execution/result projection and recovery-oriented inspection.

## Boundary

Runtime execution success is physical execution evidence only. It does not establish domain semantic completion or external-provider acceptance.

## Activation

Use only when a task requires this specific local execution/evidence boundary. Other mature execution providers may replace it without changing Ordivon Core.
