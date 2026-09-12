# Package: Operations

Last census: 2026-09-13
Standing: **READY_FOR_REAL_WORK**

## Outcome scope

Keep a service, environment or long-running process in the required operational state, make its behavior observable, and recover it when failures occur.

Operations supplies execution/configuration/observability mechanics. It does not establish domain-semantic success for Research, Game, Security, Finance or other workloads.

## Mature external knowledge/capability owners

Select by problem:

- systemd and container/runtime mechanisms for local service lifecycle;
- Ansible for host/configuration automation where appropriate;
- OpenTofu for declarative external/cloud infrastructure state;
- Temporal for durable workflows that must survive failures and resume;
- n8n for API/app integration automation and human-facing workflow edges;
- OpenTelemetry for vendor-neutral traces, metrics and logs instrumentation/collection;
- mature metrics/log/backup/storage systems as required by the target service.

Do not collapse these different responsibilities into a new Ordivon operations daemon.

## Observed local capability

- Operations v2 (`/root/projects/ordivon-operations-v2@047ca7f2a943`);
- Runtime execution/evidence;
- Temporal-facing durable workflow capability;
- n8n;
- Ansible / ansible-playbook;
- OpenTofu (`tofu`);
- systemd;
- Docker / Podman;
- existing OpenTelemetry/Prometheus/Vector/Loki/Grafana composition knowledge in Operations v2;
- PostgreSQL/backup substrate where required.

## Concrete current gaps

No generic Operations framework gap is proven.

Cloud/Kubernetes, scheduler, backup, HA, SLO, secret-management or monitoring components become gaps only when the operated workload actually requires them.

## Acceptance workload

Use a useful real long-running workflow/service:

`desired state -> start/deploy -> observe -> reproduce/induce a safe failure -> recover/resume -> verify final domain result`

Operational green status is substrate evidence, not proof that the business/scientific/product outcome is correct.

## External references

- Temporal: https://docs.temporal.io/
- n8n: https://docs.n8n.io/
- OpenTelemetry: https://opentelemetry.io/docs/
- Ansible: https://docs.ansible.com/projects/ansible/latest/
- OpenTofu: https://opentofu.org/docs/
