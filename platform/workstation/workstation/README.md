# Workstation configuration authority

Operations owns machine desired-state declarations. Workstation E2E consumes realized consequences; it does not own package/configuration convergence.

## Linux user/tool state

Authority: Nix + Home Manager. Source: `workstation/nix/`. Build directly with Nix; activation remains an explicit operator/Operations action.

```sh
cd /root/projects/ordivon-operations-v2/workstation/nix
nix --extra-experimental-features 'nix-command flakes' build .#homeConfigurations.root.activationPackage --no-link
```

## Windows desired state

Authority: WinGet Configuration + DSC v3. Source: `workstation/windows/workstation.dsc.yaml`. Read-only evaluation uses DSC directly; no Workstation wrapper is required.

The source transfer does not itself activate a new Home Manager generation or apply DSC `set`.
