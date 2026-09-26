# Claude Private workstation profile

`claude-private` is the Workstation-owned local realization for running Claude Code with minimized ambient host/network identity. Network v2 owns the transport authority; this profile owns only process/environment projection.

## Boundary

- Network namespace: `nv2-claude-client` (owned by `platform/network/consumers/claude`).
- Proxy authority: `http://10.252.247.1:19482`.
- No direct IPv4/IPv6 route exists in the client namespace.
- UTS namespace hostname: `claude-workspace`.
- Timezone: UTC with accurate host clock.
- Locale: `C.UTF-8`.
- NSS: `hosts: files dns`; systemd-resolved IPC is not consulted.
- Resolver: intentionally unreachable loopback resolver; Claude Code resolves proxy destinations through the proxy (`CLAUDE_CODE_PROXY_RESOLVES_HOSTS=1`).
- HOME: `/var/lib/claude-private/home`.
- Current project is projected at `/workspace` before host home/mount roots are hidden.
- `/root`, `/home`, `/mnt`, system D-Bus and systemd-resolved runtime sockets are hidden inside the private mount namespace.

The profile intentionally disables cloud connectors, Remote Control, Artifact, Claude.ai skill/plugin sync, background Agent View and Workflows during the privacy canary. These surfaces may be re-admitted individually after they have their own namespace/process-wrapper acceptance.

OAuth is intentionally not completed by deployment. `BROWSER=echo` prevents a normal host browser from being opened implicitly. A later OAuth-browser carrier must use the same VPN authority before subscription sign-in is accepted as privacy-complete.
