# Workstation E2E retirement decision — superseded

Original decision date: 2026-09-12
Superseded: 2026-09-14

The earlier decision retired Workstation as an independent owner and placed generic machine operations under Operations v2. That split created an unnecessary owner seam: Operations already observed and maintained the same execution node while Agents still had to re-enter legacy Workstation for exact node-local software/materialization binding.

## Current decision

**Operations v2 is renamed/merged into Workstation v2.** The implementation rooted at the current `ordivon-operations-v2` repository is the active Workstation v2 implementation during physical path cutover. `/root/workstation-lab` is the legacy Workstation implementation whose remaining valid responsibilities are migrated here or reassigned to their natural external owner.

Workstation v2 owns the execution-node layer: desired state, service lifecycle, generic observability, inventory, node-local software/device realization and exact caller-selected bindings, plus generic recovery substrate. It still does not own Runtime Job/Attempt truth, Network path semantics, Host continuity, Security policy meaning, or domain success.

The former retired `/root/projects/ordivon-workstation-v2` repository remains archival until the physical repository-name cutover is performed; it must not become a second implementation.
