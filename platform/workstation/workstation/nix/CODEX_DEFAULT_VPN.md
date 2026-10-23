# Codex default VPN — Workstation PATH cutover (2026-10-23)

## Desired behavior

A plain `codex`, including absolute `/root/tools/bin/codex` in a Runtime Job,
uses the **existing** `/usr/local/bin/codex-vpn` launcher. No new proxy, VPN
session, default route, or CLI wrapper is created. Network v2 remains the sole
owner of the scoped `127.0.0.1:19982` Codex egress (shared Surfshark provider).

The upstream `@openai/codex` release remains a single locked pnpm package
managed by Workstation/Home Manager, exposed as `/root/tools/bin/codex-raw`.
Only explicit maintenance or diagnosis may invoke `codex-raw` directly.

## Required host carrier invariant

The pre-existing `/usr/local/bin/codex-vpn` must resolve its upstream executable
from `ORDIVON_CODEX_BIN` if explicitly set, otherwise
`/root/tools/bin/codex-raw`. It must **not** fall back to
`/root/tools/bin/codex` or it will recurse after the Home Manager cutover.
The installed launcher already invokes
`/usr/local/libexec/network-v2/codex-ready`, which enforces
`network-v2-codex.target` readiness and the real allowed-TLS,
unknown-destination-denied proxy contract before starting Codex. Failure is
fail-closed; do not silently use direct access.

Launcher environment policy: force upper- and lower-case HTTP(S)/ALL_PROXY
to `http://127.0.0.1:19982` and never allow a user-provided NO_PROXY=*
to bypass public egress. The existing Codex `--disable plugins` policy
remains active. Explicit Gateway MCP OAuth remains separate and is not
conferred by the VPN.

## Guarded deployment (not a second service)

1. Check source `main` and current Workstation/Home Manager baseline; verify
   `/usr/local/bin/codex-vpn` and readiness helper exist and are executable.
   Check for active Codex Jobs because replacing the first-PATH symlink while
   watched by Runtime can cause EXECUTABLE_RUNTIME_DRIFT. Do not interrupt them.
2. Install/confirm `/root/tools/bin/codex-raw` points to the versioned pnpm
   CLI and resolves; stage the existing launcher default CODEX_BIN change
   before switching `codex`. Keep original launcher and generation for rollback.
3. Build and activate the exact source-bound Home Manager generation. Preserve
   the existing `codex-vpn` script rather than adding a second wrapper.
4. Run source tests, `codex --version`, `codex login status`, native
   `codex-vpn --version`, and a bounded read-only `codex exec` model canary
   with **no manually supplied HTTP_PROXY**. Confirm the proxy readiness/TLS
   contract via the existing Network v2 `codex-ready` entry point.
5. On failure, rollback to the previous Home Manager generation and original
   launcher, then re-read physical paths and validate the old model route.
   Never modify the shared host's default route or generic production transport.

## Safety boundary

VPN is Codex's local transport default, **not** a production dependency for
unrelated Ordivon services. Invalid or absent VPN makes Codex fail closed.
This configuration alone does not prove safe environment merging inside
Runtime: any step-specific proxy overrides require their own CDC tests.
