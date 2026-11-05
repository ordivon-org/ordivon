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
