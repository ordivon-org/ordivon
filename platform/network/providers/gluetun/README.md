# Gluetun owned provider cold-start reconciliation

This is a native systemd timer and oneshot service, not a custom polling loop.
When the selected mode and enabled Provider target authorize recovery, it
starts the actual Gluetun container service and the compatibility adapter.
Starting an already-active target alone would not recover a failed child
service; starting the actual healthy services is an idempotent no-op.

It fixes the observed failure mode where an early Podman storage error
prevented the generated provider-network unit from starting during WSL boot.
Podman later recovered, but systemd did not re-attempt the failed target.
Periodic attempts use a two-minute calendar plus a boot-relative attempt.

The existing provider-identity-exclusive check refuses competing WireGuard
identity realization. A missing selector or disabled Gluetun target disables
recovery, allowing owned provider mode changes and operator maintenance.
No Windows-wide proxy, Surfshark GUI, host default route or extra WireGuard
identity is created. Service start success is not a proof of provider Internet
health; downstream consumer readiness must be separately verified.

Install this timer only after source tests and live owner preflight; disabling
the timer stops periodic recovery without changing a currently working provider.

## Source and installed closure

Quadlet configuration lives under quadlet/, the physical identity guard is
identity-exclusive.sh and the systemd recovery units live under systemd/.
Credentials stay outside Git. The native Gluetun healthchecker handles
in-tunnel reconnects; Network systemd reconciliation handles cold-start units.
Use task provider:gluetun:verify to inspect installed source and consumer result.

## Optional IPinfo witness

`task provider:gluetun:observe-exit` performs a single explicitly proxied
HTTPS request to IPinfo and reports IP, country and ASN organization. It
requires proxy CONNECT=200 and origin HTTP=200 but is not a VPN lifecycle
health check or a server-ranking algorithm. This avoids creating another
background poller and preserves Gluetun-native health recovery.

## Native Surfshark mode — selected physical provider

The production Quadlet now uses Gluetun native `VPN_SERVICE_PROVIDER=surfshark`
with WireGuard, rather than a pinned Custom WireGuard peer endpoint. Its
server selector is constrained to `SERVER_REGIONS=Asia Pacific` and
`SERVER_COUNTRIES=Singapore,Japan`. The installed Gluetun image exposes 20
WireGuard location records in those two countries; this bounded set meets
the current shared-consumer network acceptance, including Claude. The entire
Asia Pacific region contains 50 records but includes outlets which did not
pass every consumer acceptance. A reachable VPN endpoint alone is insufficient.

Native Gluetun owns its own healthchecks, VPN reconnect and server selection.
The official server catalog updates at `UPDATER_PERIOD=480h`; the systemd
oneshot only restarts physically stopped services. No Ordivon candidate loop
or competing WireGuard session is created.

The physical identity is imported from the already-owned WireGuard profile
by `task provider:gluetun:native:prepare`, which writes a root-only native
environment file and stores the private key in Podman Secret
`network-v2-gluetun-surfshark-wgkey`. The container receives only the
`WIREGUARD_PRIVATE_KEY_SECRETFILE` path. Never place the key in Git,
plain environment variables, CLI arguments or log messages.

The pre-native `/etc/network-v2/browserless/nv2blwg.conf` and
`/etc/network-v2/gluetun/serialized-candidate.env` remain source inputs
for credential materialization and an explicit recovery route, rather than
being treated as unused cache. The current selected SourceCut requires
`task provider:gluetun:verify` and functional consumer acceptance.

The 2026-11-05 production acceptance demonstrated one unsuccessful native
Asia Pacific endpoint followed by Gluetun-internal recovery, then successful
Singapore/Japan selection and all 12 Network provider/consumer checks.
This does not prove future arbitrary endpoint reachability or an iOS client
actually selecting the Tailscale exit node.
