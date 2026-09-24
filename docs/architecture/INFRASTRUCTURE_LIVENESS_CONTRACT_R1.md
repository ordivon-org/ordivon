# Infrastructure Liveness Contract R1

Status: **ACCEPTED / LIVE LINUX+INGRESS RECOVERY VERIFIED / WINDOWS RECOVERY CONFIGURATION-ONLY / COLD-START NOT PHYSICALLY EXECUTED**

## Decision

Ordivon Runtime, Host, Gateway, and production ingress are infrastructure. Their intended steady state is running. Normal release, restart, or transient upstream unavailability must converge back to the intended running state without a human `start` operation and without turning independent components into one shared failure domain.

## Contract

1. Linux Runtime, Host, and Gateway use the OS service manager as their supervisor and declare `Restart=always`. Explicit operator `systemctl stop` remains authoritative; systemd does not auto-restart an explicitly stopped unit.
2. Gateway has `Wants=` plus `After=` relationships to Linux Runtime and Host. It must not use `Requires=`, `PartOf=`, or `BindsTo=` for those owner services. Capability dependency is not process-lifecycle dependency.
3. Host has `Wants=` plus `After=` for PostgreSQL rather than a stop-propagating `Requires=` relationship. PostgreSQL remains the Host authority substrate, but a database maintenance/restart event must not permanently deactivate Host.
4. Windows Runtime keeps native SCM Automatic start plus failure recovery. Windows Gateway defaults to Automatic start plus its existing SCM failure actions; Manual remains an explicit operator override.
5. No Ordivon watchdog, lease controller, heartbeat database, or custom supervisor is introduced. systemd and Windows SCM remain the lifecycle authorities.

## Required live acceptance

- restart Linux Runtime: Gateway remains active and keeps the same process identity; Linux-backed capability may transiently degrade and then recover;
- restart Host: Gateway remains active and keeps the same process identity; Host-backed capability recovers without Gateway restart;
- terminate Gateway process unexpectedly: systemd automatically creates a replacement process;
- explicit `systemctl stop ordivon-gateway.service`: Gateway remains stopped until an explicit start, proving operator intent wins;
- terminate production ingress A and B unexpectedly, one at a time: the failed tunnel self-recovers, the peer remains running, and public Gateway ingress remains reachable;
- Windows Gateway is Automatic and retains SCM restart actions; destructive Windows recovery is recorded separately and must not be claimed if it was not executed;
- boot/cold-start standing is recorded separately because this change does not claim a machine reboot that was not physically executed.

## Acceptance standing

Live acceptance evidence is recorded in `docs/architecture/INFRASTRUCTURE_LIVENESS_ACCEPTANCE_R1.md`.

The Linux Runtime, Host, Gateway, and production ingress failure-isolation/recovery cases passed live acceptance on 2026-09-24. Windows SCM configuration was freshly verified, but destructive Windows live recovery was intentionally not executed during concurrent Windows authority-cutover work. No machine reboot/cold-start was executed.

## Truth boundary

This contract proves service-manager liveness and failure isolation only. It does not make an unavailable owner healthy, does not change Runtime/Host/Gateway semantic authority, and does not make domain effects idempotent. Configuration evidence for Automatic/enabled startup is not physical cold-boot evidence.
