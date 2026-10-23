# Codex CLI — pnpm materialization

The package version in package.json is the release authority consumed by
Nix home.nix. This directory is a normal pnpm 12 project: check in its
pnpm-lock.yaml and do not create a second npm lock.

From platform/workstation, run 'mise run codex:materialize' to materialize
a versioned /root/tools/share/codex-pnpm-VERSION release using owner pnpm.
It verifies the real Codex version before declaring release readiness.
Activate the Home Manager symlink only after that consumer check succeeds.
The old codex-npm-VERSION directory remains a rollback candidate; this
workflow never deletes or silently replaces it.

For isolated verification, set ORDIVON_CODEX_PREFIX_ROOT to a temporary
directory before running the same task. CI validates the frozen pnpm install
and executes the installed Codex CLI.
