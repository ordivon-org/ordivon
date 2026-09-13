# Operations E2E v2 Migration R1

## Objective

Build v2 from mature external substrates first. Do not copy legacy Operations code into this repository. Migrate only proven residual semantics after an upstream replacement is working.

## Current local substrate observed on 2026-09-11

Present before v2: systemd, Podman, Prometheus, Gatus, Temporal, restic, pgBackRest, SOPS, Trivy and Toxiproxy.

Adopted in R1 from Arch repositories: Ansible, OpenTofu, node_exporter, Vector, osquery, OPA, Grafana and Loki. Installation alone does not confer production authority.

## Legacy disposition table

| Legacy surface | External owner | R1 disposition | Ordivon residual |
| --- | --- | --- | --- |
| `scripts/agent_workstation_doctor.py` giant global checks | Prometheus/node_exporter, osquery, Gatus, OTel, owner-native facts | DECOMPOSE; do not port | operation-scoped semantic verifier only |
| `scripts/node_incident.py` generic incident mechanics | NIST IR process + telemetry/alert stack | DECOMPOSE | evidence binding, generation binding, causal-claim fencing |
| `scripts/ordivon-gatus-daily.py` | Gatus + metrics/alerting | DELETE candidate after dependency proof | none unless exact evidence export remains required |
| generic backup scheduling/check wrappers | systemd timers + restic + pgBackRest | REPLACE | owner restore acceptance assertions |
| generic software/process census | osquery | REPLACE | owner-specific facts not represented generically |
| Network continuity / Surfshark monitoring | Network E2E + its selected mature substrates | MOVE OUT | no Operations semantic ownership |
| Cloudflare provider implementation and local operational lifecycle | Operations maintenance + Cloudflare/provider-native remote authority + consuming-domain semantic authority | ABSORB MAINTENANCE; use OpenTofu for suitable declarative resources | Operations owns source/install/systemd/config/upgrade/rollback/SLO plumbing only; remote provider truth and consumer meaning stay outside Operations |
| generic retry/timer workflow code | Temporal/systemd | DELETE | Runtime execution evidence remains separate |
| generic policy `if/deny` gates | OPA where policy is declarative | REPLACE | owner supplies policy inputs and owns semantic meaning |
| generic security scanning | Trivy | REPLACE | Security E2E owns interpretation/admission policy |

## Migration gates

A legacy component may be deleted only when all applicable gates are met:

1. an upstream mechanism covers the generic capability;
2. its production consumer has been rebound to the replacement;
3. rollback/recovery is understood;
4. owner-specific semantic assertions have a new home;
5. no evidence-binding requirement is silently discarded;
6. the legacy path is no longer first-PATH authority.

A component MUST NOT survive merely because it has tests or historical evidence.

## First vertical slice — shared node metrics

R1 deliberately starts with the generic facts most duplicated by the giant Doctor.

Implemented:

```text
prometheus-node-exporter.service
    127.0.0.1:29100
          |
          v
prometheus.service
    127.0.0.1:29091
```

Accepted facts:

- both services are enabled and active;
- both listeners are loopback-only;
- Operations Prometheus reports the node-exporter and self targets `up`;
- `up` returns `1` for both targets;
- Network v2 Prometheus remains active and separate at `127.0.0.1:29090`;
- Gatus remains active and separate at `127.0.0.1:8080`.

This is the first concrete replacement path for generic CPU/memory/filesystem/process-host observation formerly duplicated inside the global Doctor. It does **not** authorize deletion of owner-semantic checks yet.

## Next migration frontier

1. journald -> Vector -> Loki, keeping Grafana disabled until explicit loopback/auth/provisioning configuration is versioned;
2. osquery for generic software/process/package inventory;
3. classify Doctor checks into external fact vs owner semantic verifier, then delete the external-fact implementations after consumer proof;
4. split `node_incident.py` generic incident mechanics from its retained evidence/causal-claim boundary;
5. maintain the extracted Cloudflare Edge provider under `providers/cloudflare/`; migrate suitable declarative Cloudflare resources to OpenTofu only after import/plan proves no unintended change, while keeping imperative request/reconciliation logic provider-native.
