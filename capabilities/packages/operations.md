# Package: Operations

Last census: 2026-09-14
Standing: **READY_FOR_REAL_WORK**

## Outcome scope

Keep a service, environment or long-running process in the required operational state, make its behavior observable, and recover it when failures occur.

Operations supplies execution/configuration/observability mechanics. It does not establish domain-semantic success for Research, Game, Security, Finance or other workloads.

## Mature external knowledge/capability owners

Select by problem:

- systemd and container/runtime mechanisms for local service lifecycle;
- Ansible for host/configuration automation where appropriate;
- OpenTofu for declarative external/cloud infrastructure state;
- Temporal for durable workflows that must survive failures and resume; use `capabilities/providers/temporal.md` for the provider boundary and `knowledge/lessons/temporal-durable-execution-kernel.md` for the extracted kernel;
- n8n for API/app integration automation and human-facing workflow edges; use `capabilities/providers/n8n.md` for the provider boundary and `knowledge/lessons/n8n-integration-kernel.md` for the extracted method kernel;
- OpenTelemetry for vendor-neutral traces, metrics and logs instrumentation/collection;
- mature metrics/log/backup/storage systems as required by the target service.

Do not collapse these different responsibilities into a new Ordivon operations daemon.

## Observed local capability

- Operations v2 (`/root/projects/ordivon-operations-v2@a2a1d8b995ff53cef8fedf1c1d40051f0582f404`);
- Runtime execution/evidence (`/root/projects/ordivon-runtime@b44f192c4c8ca7500307596bab7ed6ddb05a9d4c`);
- Temporal-oriented production configuration/templates exist under Operations v2, but no active `temporal` CLI or Temporal container image was observed during the 2026-09-14 study; Temporal is therefore an available mature provider choice, not a proven current local runtime dependency;
- n8n;
- Ansible / ansible-playbook;
- OpenTofu (`tofu`);
- systemd;
- Docker / Podman;
- existing OpenTelemetry/Prometheus/Vector/Loki/Grafana composition knowledge in Operations v2;
- PostgreSQL/backup substrate where required.

## Concrete current gaps

No generic Operations framework gap is proven.

A real workload that requires durable orchestration across crashes, long timers/waits, retryable Activities or interactive Workflow state may justify activating Temporal. Until such a workload exists, do not create installation/cluster debt merely to satisfy the capability catalog.

Cloud/Kubernetes, scheduler, backup, HA, SLO, secret-management or monitoring components become gaps only when the operated workload actually requires them.

## Acceptance workload

Use a useful real long-running workflow/service:

`desired state -> start/deploy -> observe -> reproduce/induce a safe failure -> recover/resume -> verify final domain result`

If Temporal is selected, the acceptance should kill/restart a Worker and prove the Workflow resumes from durable Event History, while separately verifying that any external Activity effects remain idempotent/reconciled according to the provider contract.

Operational green status is substrate evidence, not proof that the business/scientific/product outcome is correct.

## External references

- Temporal: https://docs.temporal.io/
- n8n: https://docs.n8n.io/
- OpenTelemetry: https://opentelemetry.io/docs/
- Ansible: https://docs.ansible.com/projects/ansible/latest/
- OpenTofu: https://opentofu.org/docs/
