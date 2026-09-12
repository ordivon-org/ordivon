# Optional capabilities

Reusable mechanisms that are not required by every workload live here. They must remain composable and must not become a universal Network controller.

Current capabilities:

- `wireguard/` — encrypted-tunnel materialization and WSL userspace lifecycle acceptance
- `failover/` — deterministic ordered TCP primary/backup acceptance
