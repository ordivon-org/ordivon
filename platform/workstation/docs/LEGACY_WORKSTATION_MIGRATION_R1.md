# Legacy Workstation -> Workstation v2 migration R1

Date: 2026-09-14

## Decision

The former Operations v2 owner is now Workstation v2. `/root/workstation-lab` becomes the legacy source to drain. Migration is by responsibility, not by repository copying.

## Responsibility disposition

| Legacy workstation-lab responsibility | Workstation v2 disposition | Status |
| --- | --- | --- |
| generic software/package census | native osquery/pacman/WinGet/uninstall-registry federation | already migrated |
| Linux user/tool desired state | Nix + Home Manager under `workstation/nix/` | already migrated |
| Windows desired state | WinGet Configuration + DSC under `workstation/windows/` | already migrated |
| systemd/service/timer lifecycle | Ansible + systemd/Podman/Quadlet | already migrated |
| professional/managed software declarations | `workstation/software.toml` | **migrated in R1** |
| exact caller-selected software binding | `workstation/tool_binding.py` + stable compatibility entry | **migrated/deploying in R2** |
| global software census/classification database | do not migrate; native sources remain authority | retired |
| giant global Doctor | decompose into upstream observation + operation-relative verifier | draining |
| Workstation recovery scheduler | Workstation v2 systemd substrate | migrated |
| recovery generation/restore semantics | migrate only surviving node-owner semantics | pending |
| Windows Runtime launcher materialization | `workstation/windows/runtime_provider.py`; Runtime keeps Job/Attempt semantics | **source/config migrated in R2** |
| production transport/failover | Network v2 | do not migrate |
| domain suitability/completion | owning Domain E2E | do not migrate |
| Host task continuity | Host | do not migrate |

## R1 cut

R1 deliberately moves the software declaration/binding seam first because it removes the concrete double-hop exposed by Blender/REAPER/Godot consumers: an Agent no longer needs one owner for machine inventory and then legacy Workstation for the exact selected local executable. Workstation v2 owns both generic discovery and exact node-local binding, while Runtime and the consuming domain retain their separate authorities.

The old `workstation.equipment.resolve` / `workstation.software.affordance` compatibility surfaces in `/root/workstation-lab` are not deleted in this cut. Current consumers must be rebound to the Workstation v2 binding path first; then the legacy surface can be retired with evidence.
