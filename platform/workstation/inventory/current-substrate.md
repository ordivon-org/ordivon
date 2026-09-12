# Current substrate census — 2026-09-11

This is a factual snapshot, not a universal semantic-health declaration.

## Present before Operations v2 R1

| Component | Observed version/path | State |
| --- | --- | --- |
| systemd | 261 | installed |
| Podman | 6.1.1 | installed; Browserless containers running |
| Prometheus | 3.14.0 | installed; Network v2 instance active at `127.0.0.1:29090` |
| Gatus | `/opt/gatus/gatus` | `ordivon-gatus.service` active |
| Temporal | CLI 1.8.3, server 1.31.2 | local server active at `127.0.0.1:7233` |
| restic | `/usr/bin/restic` | installed |
| pgBackRest | 2.59.1 | installed; PostgreSQL backup timer active |
| SOPS | 3.13.3 | installed |
| Trivy | 0.73.0 | installed |
| Toxiproxy | 2.12.0 | installed |

## Adopted by Operations v2 R1

The following mature packages were installed from the configured Arch repositories rather than reimplemented:

| Package | Installed version | R1 state |
| --- | --- | --- |
| ansible-core | 2.21.3-1 | active management substrate |
| ansible | 14.3.1-1 | provides maintained collections including `community.general.pacman` |
| opentofu | 1.12.6-1 | installed; no infrastructure authority migrated yet |
| prometheus-node-exporter | 1.12.1-1 | active, loopback `127.0.0.1:29100` |
| vector | 0.57.0-1 | installed, inactive pending explicit log config |
| osquery | 5.23.1-1 | active generic host inventory authority; direct query contract under `inventory/queries/` |
| open-policy-agent | 1.20.2-1 | installed, no policy authority migrated yet |
| grafana | 13.2.1-1 | installed, inactive pending auth/provisioning config |
| loki | 3.6.6-1 | installed, inactive pending durable local config |

## Operations v2 shared metrics slice

- stock `prometheus.service` is now Operations-v2-managed and active at `127.0.0.1:29091`;
- `prometheus-node-exporter.service` is active at `127.0.0.1:29100`;
- Operations Prometheus scrapes only itself and the generic node exporter in R1;
- both targets were observed `up` after cutover;
- Network v2 Prometheus remains separately active at `127.0.0.1:29090`;
- Gatus remains separately active at `127.0.0.1:8080`.

## Important ownership observations

- Gatus currently carries Network/control-plane reachability semantics; Operations v2 must not copy those semantics blindly.
- Network v2 Prometheus remains Network-owned. Operations v2 does not treat it as shared global monitoring authority.
- Temporal is deployed outside PATH under `/opt/ordivon/external/...`; lack of a `temporal` PATH command never implied absence.
- package installation changed executable-path topology, so Runtime correctly failed closed with `EXECUTABLE_RUNTIME_DRIFT` even though package-manager output showed completed external effects. Physical state was reconciled before continuing; the install was not blindly retried.

## Operations v2 PostgreSQL / pgBackRest owner slice

- desired-state authority: Ansible (`ansible/postgresql-backup.yml`);
- database service/configuration authority: packaged PostgreSQL + `community.postgresql.postgresql_alter_system`;
- backup/PITR authority: pgBackRest;
- schedule/lifecycle authority: systemd;
- owner semantic restore acceptance remains with each database consumer and is not inferred from backup command success.

## Operations v2 local host / WSL owner slice

- systemd system/user manager file-descriptor policy: Ansible-owned file desired state;
- coredump suppression policy: Ansible-owned file desired state;
- `systemd-homed.service` and `systemd-homed-activate.service`: Ansible-owned disabled + stopped lifecycle on this node;
- `/etc/wsl.conf`: Ansible `ini_file`, owned keys only;
- Windows `.wslconfig`: Ansible `ini_file`, owned keys only; the separately present custom `kernel=` entry is deliberately preserved;
- WSL shutdown/restart is not part of routine convergence and must be admitted separately when activation is required.

## Operations v2 Workstation recovery scheduler slice

- systemd service/timer bytes: Operations Ansible desired state;
- current timer policy: disabled + inactive;
- semantic launcher: externally owned `/opt/ordivon-workstation-recovery/current/bin/workstation-backup`;
- this slice does not execute backup, select recovery generations, or establish restore correctness.
