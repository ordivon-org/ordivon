# Exceptions and Reset Policy

Status:

- use together with `[[99 Rules/Machine Policy v2]]`
- exceptions must not override machine policy silently

## Why Exceptions Exist

Some tools are already installed in a way that does not match the ideal target model, but removing them immediately would break working workflows.

Current examples should be explicitly documented and time-bounded.

## Policy

- do not keep undocumented runtime exceptions alive by inertia
- do not treat app-private runtimes as the preferred model for general development
- migrate new development work to flakes-first project environments
- if an exception is necessary, document the reason, scope, owner, exit condition, and review date in the vault

## Reset Strategy

### Immediate

- clean shell startup
- document the rules
- stop adding new global runtimes

### Near-term

- standardize new repos on `flake.nix` + `.envrc`
- define language templates for Python, Node, and mixed projects
- reconnect projectized Hermes to the vault workflow and operating docs

### Later

- selectively retire legacy global runtimes when no workflow depends on them
- keep only OS tools, long-lived user CLI tools, and project-local environments

## Practical Standard

The target machine model is:

- stable OS base
- small Nix profile for evergreen tools
- project-local development stacks via flakes
- explicit exceptions documented here
- machine-level policies documented explicitly for systemd, DNS, VPN behavior, and PATH injection

## Post-Reset Standard

After the reset, new runtime introduction should follow this order:

1. project `flake.nix`
2. `.envrc` with `use flake`
3. `direnv allow`

No replacement runtime should be reintroduced through app-private directories or ad hoc user-local installs unless explicitly documented as an exception.

## Current Hermes Position

- Hermes is no longer a global installer-managed runtime
- the active runtime lives at `/home/dev/projects/hermes-runtime`
- persistent state lives at `/home/dev/state/hermes`
- optional extras such as Node/browser/WhatsApp support must not block the base CLI runtime
- retired historical Hermes home was preserved under `/home/dev/state/legacy/hermes-home-2026-04-11`
