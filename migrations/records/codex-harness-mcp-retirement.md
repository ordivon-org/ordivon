# Codex Harness MCP retirement

- Source: `/root/projects/codex-harness-mcp`
- Archive commit: `4717d2a7d512c90b5d4b9ea8d2ef9329e21708ec`
- Assessed: 2026-09-14
- Disposition: **LOCAL_RUNTIME_RETIRED / REMOTE_CLOUDFLARE_CLEANUP_HOLD**

## Local decision

The self-built Codex exec-server MCP adapter is no longer a current Ordivon capability. Runtime remains the durable physical execution substrate; the native Codex CLI remains available independently. No current Ordivon repository consumed the MCP adapter at retirement time.

Immediately before retirement both `codex-harness-mcp.service` and `codex-exec-server.service` were inactive and disabled. Port 8898 is now used by current Host v2, so accidental exec-server reactivation would also conflict with current local service allocation. Both unit files were preserved with digests under `/var/lib/ordivon/retired/codex-harness-mcp/`, removed from `/etc/systemd/system`, and systemd reloaded. Both now report `LoadState=not-found`.

`codex-cli 0.146.0` remains installed; retirement of this custom adapter does not retire Codex itself.

## Remote Cloudflare residual

A read-only Cloudflare census still found a hostname-specific residual for `codex-mcp.ordivon.com`:

- one proxied DNS CNAME to the shared `ordivon-wsl` tunnel;
- one self-hosted Access application named `Codex Exec Harness MCP`;
- one `ordivon-wsl` ingress rule targeting the former local MCP origin on port 8899.

The endpoint returned Cloudflare Access HTTP 401, proving the edge resources still existed. A narrowly scoped automated removal attempt was blocked by the execution safety layer before any remote mutation occurred. Therefore remote exposure retirement remains **HOLD**, and must not be represented as complete.

Only those hostname-specific resources should be removed through an admitted Cloudflare control-plane path; unrelated `ordivon-wsl` ingress/DNS/Access resources must remain unchanged.

## Reopen rule

Do not reactivate the adapter merely because Codex is installed. Reopen only if a concrete workload proves that Runtime plus native Codex interfaces cannot supply a required capability at lower total complexity.
