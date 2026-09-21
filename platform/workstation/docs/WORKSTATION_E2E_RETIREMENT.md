# Workstation E2E retirement decision — superseded

Original decision date: 2026-09-12
Superseded: 2026-09-14

The earlier decision retired Workstation as an independent owner and placed generic machine operations under Operations v2. That split created an unnecessary owner seam: Operations already observed and maintained the same execution node while Agents still had to re-enter legacy Workstation for exact node-local software/materialization binding.

## Current decision

**Operations v2 is renamed/merged into Workstation v2.** The active implementation is the `platform/workstation` owner inside the canonical `/root/projects/ordivon` modular monorepo. Repository placement does not change Workstation authority boundaries. `/root/workstation-lab` is a historical Git carrier only; responsibilities that remained valid were migrated here or reassigned to their natural external owner.

Workstation v2 owns the execution-node layer: desired state, service lifecycle, generic observability, inventory, node-local software/device realization and exact caller-selected bindings, plus generic recovery substrate. It still does not own Runtime Job/Attempt truth, Network path semantics, Host continuity, Security policy meaning, or domain success.

The former standalone Workstation source carrier is retirement-only and must not become a second implementation. Current recovery, Edge provider realization, desired state, and owner verification bind the canonical monorepo Workstation owner.
