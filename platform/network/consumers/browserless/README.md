# Browserless Network consumer

Browserless is a bounded Network consumer, not the physical VPN owner or the generic Network graduation authority. Browser readiness belongs to its own application acceptance.

## Selected production path

- The single Surfshark WireGuard physical identity belongs to the Gluetun Quadlet under `providers/gluetun/`.
- The shared HTTP carrier `10.252.246.2:19680` is projected by `network-v2-gluetun-owned-adapter.service` into `nv2-browserless-prod`, which has no IPv4/IPv6 default routes.
- Finance, Supply Chain, Claude, Codex, Discord and Model Provider retain separate destination policies; none owns an additional physical WireGuard session.

The selector marker is `/etc/network-v2/gluetun/m4-owned-mode.selected`. In this mode, `task consumer:browserless:provider-carrier:materialize` synchronizes ONLY the shared readiness script. It never installs legacy systemd units or restarts/reselects the physical VPN. `converge` observes the current adapter. `verify` checks exact installed readiness bytes and selected provider identity.

The provider witness checks service selection, no namespace default route, real HTTPS proxy CONNECT and allowed origin status for OpenAI, OCI Registry and Anthropic. OKX additionally requires CONNECT 200, origin HTTP 200 and valid time JSON. Process liveness alone is not sufficient.

## Inactive legacy migration path

If the Gluetun marker is absent, the older Browserless WireGuard materialization and serial `production-cutover.sh` path are available for deliberate recovery. `provider-switch.sh` refuses to operate while Gluetun owns the identity. Old `th-bkk` qualification is not an automatic best-server decision.

## Natural Owner entrypoints

`task consumer:browserless:provider-carrier:validate`, `:materialize`, `:verify` and `:converge` reuse Taskfile and systemd. No separate controller or registry is introduced.
