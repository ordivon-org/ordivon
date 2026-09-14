# Ordivon Operations E2E v2

Operations E2E v2 is an external-first composition layer. It does **not** implement a second monitoring platform, scheduler, service supervisor, backup engine, incident manager, inventory database, policy engine, or infrastructure state engine.

## Core rule

Use mature upstream systems for generic operations capability. Keep Ordivon code only where an owner-specific semantic verdict, exact evidence binding, or Runtime execution-truth handoff cannot be delegated without losing meaning.

## Selected responsibility map

- host/service lifecycle: systemd + Podman/Quadlet
- host desired state: Ansible
- external infrastructure desired state: OpenTofu
- durable workflow: Temporal (generic substrate only; the retired Research v1 campaign worker is not part of the current Research path)
- integration edge: n8n (rootless Podman/Quadlet, official digest-pinned OCI images + external task runners)
- execution truth: Ordivon Runtime
- metrics: Prometheus + node_exporter
- black-box probing: Gatus
- telemetry semantics/protocol: OpenTelemetry
- logs: journald -> Vector -> Loki
- visualization: Grafana
- alert routing: Alertmanager-compatible Prometheus alerting path
- generic host facts: osquery; native package/application inventory: pacman + WinGet/Windows uninstall registry; on-demand standard SBOM: Syft
- file backup: restic
- PostgreSQL backup/PITR: pgBackRest
- secrets-at-rest: SOPS + age
- policy-as-code: OPA
- vulnerability/config/secret scanning: Trivy
- dependency update automation: Renovate
- load testing: k6 when admitted
- deterministic network fault injection: Toxiproxy
- maintained Cloudflare Edge provider: `providers/cloudflare/` (provider source/install/service realization only; remote Cloudflare state and consumer semantics remain externally owned)

## Non-goals

Operations v2 MUST NOT become:

1. a second Runtime;
2. a second Temporal scheduler;
3. a semantic truth owner for Research, Finance, Network, Host, Workstation, Security, Media, Game, or other E2Es;
4. a wrapper around an upstream tool merely to rename its concepts with Ordivon terminology;
5. a universal `health = green/red` oracle.

## Retained Ordivon residual

Only three classes of custom behavior are expected to survive migration:

1. **Evidence binding** — bind an observation/action to exact source, policy, binary/config identity, Runtime Job/Attempt, time, and artifact/evidence digest when that binding matters.
2. **Owner semantic verification** — an owner decides whether restored bytes or a mechanically healthy service are semantically usable for that owner.
3. **Cross-E2E handoff contracts** — explicit transfer between desired state, physical realization, Runtime execution truth, and owner verdict.

See `docs/ARCHITECTURE.md` and `docs/MIGRATION_R1.md`.

## Maintained provider implementations

Operations may physically maintain a concrete provider implementation when there is a real local operational lifecycle to own: source upgrades, installation, systemd realization, policy/config materialization, rollback tooling, and health/SLO plumbing. This does **not** transfer provider-native remote truth or consuming-domain semantics into Operations.

The first retained provider is [`providers/cloudflare/`](providers/cloudflare/), absorbed on 2026-09-13 from the short-lived standalone `ordivon-cloudflare-provider` extraction. Cloudflare remains authoritative for Worker/R2/request/receipt state; callers remain authoritative for intent, authorization, and semantic verification.

## Shared PostgreSQL backup substrate

Operations v2 owns only the generic node-operational substrate for the shared PostgreSQL service: Ansible desired state, packaged PostgreSQL, pgBackRest configuration/PITR, and the systemd backup timer. Consumer schemas, database meaning, migration admission, and restored-state semantic acceptance remain with Host/Research/Finance/other data owners. Routine Operations convergence never restarts PostgreSQL implicitly when `postgresql_alter_system` reports a restart requirement.

## Local host / WSL substrate

Operations v2 owns generic host desired-state for systemd manager limits, coredump policy, the disabled `systemd-homed` lifecycle on this non-homed node, and the bounded WSL settings used by this node. WSL INI files are managed key-by-key rather than replaced wholesale: unknown or separately owned entries such as the current custom `kernel=` path remain untouched. Applying bytes does not activate a new WSL generation; distribution shutdown/restart is a separate explicit operation boundary.

## Workstation recovery scheduler substrate

Operations v2 owns only the generic systemd scheduling substrate for the existing immutable Workstation recovery launcher: service/timer lifecycle and host-level scheduling mechanics. It does not build, select, execute, or reinterpret the recovery generation, Restic snapshot/mirror verification, authority backup, semantic-state backup, or restore acceptance.

As re-observed on 2026-09-14, `ordivon-workstation-backup.timer` is intentionally **enabled and active**, with a daily ~03:30 schedule, while the oneshot service executes the immutable `/opt/ordivon-workstation-recovery/current/bin/workstation-backup` launcher. The most recent completed run succeeded. This is a retained minimal recovery capability, not a revival of Workstation E2E. See `docs/WORKSTATION_RECOVERY_RETENTION_20260914.md`.

## Standards-first integration composition

The integration edge is **n8n**, deployed by Operations as a rootless Podman/Quadlet pod using official digest-pinned OCI images and external task runners. Temporal remains the durable-workflow authority and Ordivon Runtime remains the physical-execution authority. Cross-system event envelopes use CloudEvents 1.0; asynchronous contracts use AsyncAPI; reliable database-to-event handoff uses the Transactional Outbox pattern; synchronous HTTP APIs use OpenAPI only where a real API exists. n8n host-execution nodes are explicitly excluded so integration workflows cannot bypass Runtime. See `docs/STANDARDS_FIRST_COMPOSITION.md` and `contracts/`.
