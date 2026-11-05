# Gluetun owned provider cold-start reconciliation

This is a native systemd timer and oneshot service, not a custom polling loop.
It periodically tries to start the already-selected
network-v2-gluetun-owned.target if the selected mode is installed and the
target remains enabled. Starting an active target is an idempotent no-op.

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
