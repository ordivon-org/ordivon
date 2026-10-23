# Package: Operations

Last census: 2026-09-22
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
- OpenTelemetry + OTLP for vendor-neutral traces, metrics, logs and context propagation; use `capabilities/providers/opentelemetry.md` and `knowledge/lessons/otel-openinference-observability-kernel.md`;
- OTel GenAI semantic conventions as the preferred standards-native AI telemetry direction when supported; use OpenInference selectively when its instrumentors/richer AI semantics/backend compatibility materially help, via `capabilities/providers/openinference.md`;
- mature metrics/log/trace/backup/storage systems as required by the target service.

Do not collapse these different responsibilities into a new Ordivon operations daemon or private telemetry ontology.

## Observed local capability

Current local implementation/owner record: `capabilities/providers/workstation-v2.md`.

- Workstation v2 (`/root/projects/ordivon@a003ca18b7e43ea4012d62db8d8d71198d68d961`, owner path `platform/workstation`);
- Runtime execution/evidence (`/root/projects/ordivon/services/runtime@7741c2e9e53fc4954ce16b692cfe19b27703caee`);
- Temporal-oriented production configuration/templates exist under Workstation v2, but no active `temporal` CLI or Temporal container image was observed during the 2026-09-14 study; Temporal is therefore an available mature provider choice, not a proven current local runtime dependency;
- n8n;
- Ansible / ansible-playbook;
- OpenTofu (`tofu`);
- systemd;
- Docker / Podman;
- accepted OTLP logs+metrics composition in Workstation v2: Vector 0.57.0 receives OTLP gRPC/HTTP; logs flow to Loki 3.6.6; metrics flow as OTLP to Prometheus 3.14.0; node_exporter remains for host metrics;
- traces are intentionally routed to a deferred blackhole because no trace backend/use-case is currently admitted; no `otelcol`, Jaeger or Tempo executable was observed in the current shell during the 2026-09-14 study;
- no Langfuse or Phoenix executable/Docker image/local project was observed during the 2026-09-14 comparison;
- PostgreSQL/backup substrate where required.

## Concrete current gaps

No generic Operations framework gap is proven.

A real workload that requires durable orchestration across crashes, long timers/waits, retryable Activities or interactive Workflow state may justify activating Temporal. Until such a workload exists, do not create installation/cluster debt merely to satisfy the capability catalog.

A real workload that requires causal trace queries may justify admitting a trace backend or AI-engineering product. For lightweight internal Agent/eval work, Phoenix is the first candidate; for shared production AI engineering with collaborative prompt/eval/annotation workflows, Langfuse is the first candidate. Their overlap is high, so deploy at most one unless distinct measured workloads justify both. See `capabilities/providers/phoenix.md`, `capabilities/providers/langfuse.md`, and `knowledge/lessons/langfuse-phoenix-ai-engineering-platform-kernel.md`. Until such a workload exists, the current deliberate no-trace-storage boundary is valid; do not install tracing infrastructure for diagram completeness.

Cloud/Kubernetes, scheduler, backup, HA, SLO, secret-management or monitoring components become gaps only when the operated workload actually requires them.

## Acceptance workload

Use a useful real long-running workflow/service:

`desired state -> start/deploy -> observe -> reproduce/induce a safe failure -> recover/resume -> verify final domain result`

If Temporal is selected, the acceptance should kill/restart a Worker and prove the Workflow resumes from durable Event History, while separately verifying that any external Activity effects remain idempotent/reconciled according to the provider contract.

If trace storage is selected, acceptance should prove cross-boundary context propagation and one useful causal query that changes or validates an operational decision; merely seeing spans in a UI is insufficient.

Operational green status or a successful span is substrate evidence, not proof that the business/scientific/product outcome is correct.

## External references

- Temporal: https://docs.temporal.io/
- n8n: https://docs.n8n.io/
- OpenTelemetry: https://opentelemetry.io/docs/
- OpenInference: https://arize-ai.github.io/openinference/
- Langfuse: https://langfuse.com/docs
- Arize Phoenix: https://arize.com/docs/phoenix/
- Ansible: https://docs.ansible.com/projects/ansible/latest/
- OpenTofu: https://opentofu.org/docs/
