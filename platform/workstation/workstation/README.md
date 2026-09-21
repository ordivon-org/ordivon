# Workstation v2 configuration authority

Workstation v2 owns execution-node desired-state declarations and the node-local realization/binding consequences that remain after mature upstream tools are used directly. This directory is part of the active Workstation v2 owner; it is not a handoff from a separate Operations owner.

## Linux user/tool state

Authority: Nix + Home Manager. Source: `workstation/nix/`. Build directly with Nix; activation remains an explicit Workstation v2 operation.

```sh
cd /root/projects/ordivon/platform/workstation/workstation/nix
nix --extra-experimental-features 'nix-command flakes' build .#homeConfigurations.root.activationPackage --no-link
```

The path above is the canonical modular-monorepo Workstation owner. Repository placement does not merge Workstation authority with other monorepo owners.

## Windows desired state

Authority: WinGet Configuration + DSC v3. Base source: `workstation/windows/workstation.dsc.yaml`. Conditional provider realizations remain separate when they have external-secret preconditions; the native Windows Runtime Cloudflare ingress is declared in `workstation/windows/cloudflared-runtime.dsc.yaml` and is applied only after its node-local Tunnel token file is materialized. Read-only evaluation uses DSC directly; no private configuration controller is required.

## Caller-selected software bindings

`workstation/software.toml` is the migrated bounded declaration set for professional and exact managed software that had proven current consumers in legacy `/root/workstation-lab`. `workstation/tool_binding.py` resolves only a caller-selected declared launcher into current path/version evidence and exact executable SHA-256. It does not select tools, grant Runtime execution authority, or decide domain suitability.

`playwright_cli_binding.py` is a narrower node-local compatibility binding for the installed Microsoft `@playwright/cli`. It combines the exact CLI entrypoint with the already-bound Playwright Chromium executable and materializes an upstream-native JSON config (`browserName=chromium`, exact `executablePath`, headless mode, and the root/WSL `chromiumSandbox=false` launch fact). It does **not** proxy or rename Playwright commands; callers invoke Microsoft `playwright-cli` directly using the returned command prefix/config/environment.

## Native Windows Runtime boundary

Workstation no longer materializes a Windows launcher into the Linux Runtime. Native Windows Runtime installation, SCM identity, launcher bytes, authority profile, Job Objects and acceptance are owned directly by Runtime plus Windows platform mechanisms. The former WSL-hosted provider is a live transition carrier only until native cutover; `ansible/retire-wsl-windows-runtime-provider.yml` is an idempotent post-acceptance cleanup using ordinary Ansible `state: absent` operations. It must not run before the native Windows post-cutover gates pass.

## Stable node carriers

Workstation v2 versions and materializes only the thin node-local carriers that must remain stable across consuming-owner releases. `input_authority_ingress.py` performs digest-fenced physical admission into operator-configured Runtime input-authority roots; the consuming owner still owns the authority/configuration meaning. `agent_automation_carrier.py` owns only the stable `/root/tools/bin/agent-automation` entry and its release-admission read fence; Agent Automation implementation/release-source semantics remain outside Workstation v2 and currently require a separate Harness-owner migration.
