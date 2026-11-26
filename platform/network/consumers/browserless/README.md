# Browserless Network consumer

Browserless is a bounded Network consumer, not the physical VPN owner or the generic Network graduation authority. Browser readiness belongs to its own application acceptance.

## Selected production path

- The single Surfshark WireGuard physical identity belongs to the Gluetun Quadlet under `providers/gluetun/`.
- The shared HTTP carrier `10.252.246.2:19680` is projected by `network-v2-gluetun-owned-adapter.service` into `nv2-browserless-prod`, which has no IPv4/IPv6 default routes.
- Finance, Supply Chain, Claude, Codex, Discord and Model Provider retain separate destination policies; none owns an additional physical WireGuard session.

The generic namespace, forwarding, target and carrier SourceCut now belong to `substrates/shared-egress/` with `task substrate:shared-egress:{validate,materialize,verify}`. The selector marker is `/etc/network-v2/gluetun/m4-owned-mode.selected`. The legacy `task consumer:browserless:provider-carrier:materialize` delegates shared installation to that native interface and only manages legacy-specific targets, without starting an additional physical VPN. `network-v2-browserless.target` owns only namespace and forwarding, while the explicit `network-v2-browserless-legacy-provider.target` is cold rollback gated by `ConditionPathExists=!/etc/network-v2/gluetun/m4-owned-mode.selected` and remains disabled in normal operation. `converge` observes the current adapter. `verify` checks exact installed readiness bytes and selected provider identity.

The provider witness checks service selection, no namespace default route, real HTTPS proxy CONNECT and allowed origin status for OpenAI, OCI Registry and Anthropic. OKX additionally requires CONNECT 200, origin HTTP 200 and valid time JSON. Process liveness alone is not sufficient.

While Gluetun is selected, the native Browserless materialization first
requires the legacy target and WireGuard/DNS/carrier Units to be inactive.
It then refreshes **only their inert systemd Unit files** and performs
`daemon-reload`; it never starts or enables the legacy provider, changes its
WireGuard profile, or restarts the selected Gluetun Provider. This keeps
cold-rollback ownership readback in sync without creating two VPN identities.

## Inactive legacy migration path

If the Gluetun marker is absent, the older Browserless WireGuard materialization and serial `production-cutover.sh` path are available for deliberate recovery. This cutover rejects before any effects while Gluetun is selected, and explicitly starts the legacy provider target; starting the compatibility target alone never starts a second VPN. On failure, rollback stops only the Browserless legacy provider target and its dedicated services; it does not disable or stop `network-v2-shared-egress.target` (the alias of `network-v2-browserless.target`) because other consumers share that substrate. `provider-switch.sh` refuses to operate while Gluetun owns the identity. Old `th-bkk` qualification is not an automatic best-server decision.

The legacy-only provider switch now starts
`network-v2-browserless-legacy-provider.target`, which is responsible
for its own dedicated WireGuard/DNS/carrier service stop propagation;
it no longer uses the shared Target as its provider-control handle.
The shared target retains canonical physical identity through its
`network-v2-shared-egress.target` alias.

## Natural Owner entrypoints

`task consumer:browserless:provider-carrier:validate`, `:materialize`, `:verify` and `:converge` reuse Taskfile and systemd. No separate controller or registry is introduced.
