# Claude Private workstation profile

`claude-private` is the Workstation-owned local realization for running Claude Code with minimized ambient host/network identity. Network v2 owns the transport authority; this profile owns only process/environment and human OAuth-browser projection.

## CLI boundary

- Network namespace: `nv2-claude-client`.
- Proxy authority: `http://10.252.247.1:19482`.
- No direct IPv4/IPv6 default route exists in the client namespace.
- UTS hostname: `claude-workspace`.
- Accurate clock with timezone `UTC`; locale `C.UTF-8`.
- NSS is reduced to `files dns`; host systemd-resolved IPC is hidden.
- Resolver is intentionally unreachable locally; Claude resolves proxy destinations through the proxy.
- HOME: `/var/lib/claude-private/home`.
- Project projection: `/workspace`; host `/root`, `/home`, `/mnt`, system D-Bus and systemd-resolved sockets are hidden in the private mount namespace.
- `auth/*` commands use `/var/lib/claude-private/auth-workspace`, so Claude's account-control metadata probes cannot touch a project checkout.

Cloud connectors, Remote Control, Artifact, Claude.ai skill/plugin sync, background Agent View and Workflows are disabled during the privacy canary. They can be re-admitted individually after process-wrapper/network acceptance.

## OAuth browser

`claude-private auth login --claudeai` starts a temporary Chrome-for-Testing human browser in the same `nv2-claude-client` namespace. Chrome uses the same scoped HTTP proxy, UTC, a dedicated profile, fixed 1440x1000 Xvfb geometry, geolocation/camera/microphone/notification denial defaults, and `disable_non_proxied_udp` WebRTC policy. A loopback-only noVNC surface is exposed at `http://127.0.0.1:16090/` for the duration of login and is stopped when the auth command exits.

The OAuth browser does not use the Windows default browser or host browser profile. The Claude network allowlist remains authoritative; if an external SSO identity provider is required, login fails closed until that provider receives an explicit network authority.
