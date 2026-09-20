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
| input-authority ingress stable carrier | `workstation/input_authority_ingress.py` + Workstation v2 Ansible | **migrated in R4; consumer config remains externally owned** |
| Agent Automation stable carrier | `workstation/agent_automation_carrier.py` + immutable `/opt/ordivon/agent-automation/current` | **carrier migrated in R4; semantic/release source -> Harness HOLD** |
| giant global Doctor | upstream facts + narrow owner verifiers | **RETIRE; no live external consumer found in R4 census** |
| legacy `workstation-semantic` | exact tool binding supersedes its current equipment-resolution role | **RETIRED live launcher in R5; zero current tracked consumers** |
| `engineering-python` legacy helper | historical design experiments only | **live launcher retired in R5; do not migrate** |
| giant global Doctor | decompose into upstream observation + operation-relative verifier | draining |
| Workstation recovery scheduler | Workstation v2 systemd substrate | migrated |
| recovery generation/restore semantics | minimal `recovery/` kernel + immutable generation | **migrated + activated in R3 (`aba2a689…`), verify-current PASS** |
| Windows Runtime launcher materialization | native Runtime + Windows SCM/Job Objects; Workstation WSL carrier is retired after native acceptance | **v2 provider source retired; live transition carrier remains only until cutover** |
| production transport/failover | Network v2 | do not migrate |
| domain suitability/completion | owning Domain E2E | do not migrate |
| Host task continuity | Host | do not migrate |

## R1 cut

R1 deliberately moves the software declaration/binding seam first because it removes the concrete double-hop exposed by Blender/REAPER/Godot consumers: an Agent no longer needs one owner for machine inventory and then legacy Workstation for the exact selected local executable. Workstation v2 owns both generic discovery and exact node-local binding, while Runtime and the consuming domain retain their separate authorities.

The old `workstation.equipment.resolve` / `workstation.software.affordance` compatibility surfaces in `/root/workstation-lab` are not deleted in this cut. Current consumers must be rebound to the Workstation v2 binding path first; then the legacy surface can be retired with evidence.
