# Workstation v2 configuration authority

Workstation v2 owns execution-node desired-state declarations and the node-local realization/binding consequences that remain after mature upstream tools are used directly. This directory is part of the active Workstation v2 owner; it is not a handoff from a separate Operations owner.

## Linux user/tool state

Authority: Nix + Home Manager. Source: `workstation/nix/`. Build directly with Nix; activation remains an explicit Workstation v2 operation.

```sh
cd /root/projects/ordivon-operations-v2/workstation/nix
nix --extra-experimental-features 'nix-command flakes' build .#homeConfigurations.root.activationPackage --no-link
```

The repository path above is a temporary physical path retained during the Operations -> Workstation v2 rename. Semantic ownership is already Workstation v2.

## Windows desired state

Authority: WinGet Configuration + DSC v3. Source: `workstation/windows/workstation.dsc.yaml`. Read-only evaluation uses DSC directly; no private configuration controller is required.

## Caller-selected software bindings

`workstation/software.toml` is the migrated bounded declaration set for professional and exact managed software that had proven current consumers in legacy `/root/workstation-lab`. `workstation/tool_binding.py` resolves only a caller-selected declared launcher into current path/version evidence and exact executable SHA-256. It does not select tools, grant Runtime execution authority, or decide domain suitability.

## Windows Runtime provider realization

`workstation/windows/runtime_provider.py` and `runtime-provider.toml` now own the node-side materialization contract for Runtime's Windows launcher, including exact source/compiler binding, the AF_VSOCK systemd drop-in, Runtime operator environment, and materialization receipt. Runtime continues to own Job/Attempt semantics and activation/restart. After deployment, the stable local entry is `/root/tools/bin/workstation-windows-runtime-provider status|apply`; `apply` stages provider bytes/configuration but deliberately does not restart Runtime.

## Stable node carriers

Workstation v2 versions and materializes only the thin node-local carriers that must remain stable across consuming-owner releases. `input_authority_ingress.py` performs digest-fenced physical admission into operator-configured Runtime input-authority roots; the consuming owner still owns the authority/configuration meaning. `agent_automation_carrier.py` owns only the stable `/root/tools/bin/agent-automation` entry and its release-admission read fence; Agent Automation implementation/release-source semantics remain outside Workstation v2 and currently require a separate Harness-owner migration.
