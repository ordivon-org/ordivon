# Business Operations / ERPNext R1 acceptance

Date: 2026-09-13

## Decision

Use mature ERP/business-system semantics directly rather than creating an Ordivon-native CRM, accounting, sales, project, quality, customer, invoice or general-ledger model.

Current local owner for this capability is ERPNext `16.34.2` / Frappe, deployed as a rootless Podman/Quadlet service under the dedicated `ordivon-erpnext` account.

`BUSINESS_OPERATIONS_ERP_OWNER = ERPNEXT`

`BUSINESS_OPERATIONS_CURRENT_WORKLOAD = ACCEPTED`

This acceptance is deliberately scoped. It proves that the current local substrate can own and preserve a representative business transaction chain. It does not claim that PRC tax filing, banking, payment providers, statutory invoicing, payroll, inventory, procurement or other future company-specific workflows are already configured.

## Authority boundary

ERPNext owns business facts that belong naturally to the ERP domain, including as applicable:

- Company/master data;
- Customer;
- Opportunity / CRM records;
- accounting documents and General Ledger effects;
- sales/invoice lifecycle;
- business Project records;
- Quality records;
- other ERPNext-native business records introduced by real company workloads.

ERPNext does **not** become a replacement global Ordivon Host or Task database.

- Plane remains the selected future work-management authority when resource activation is justified.
- Temporal owns durable macro-process state when needed.
- Microsoft Agent Framework owns agent-team orchestration state.
- Runtime owns mechanical execution evidence, not ERP semantic truth.
- n8n owns integration mechanics only; ERPNext remains authoritative for business records reached through n8n.
- Market Capital remains a separate read-only market/capital domain and is not collapsed into ERP accounting.
- domain-specific scientific/artifact/game/security acceptance remains with those domains.

## Accepted local realization

Observed local composition:

```text
systemd --user / linger
  -> Podman Quadlet
     -> erpnext-pod.service
        -> MariaDB 11.8
        -> Redis cache
        -> Redis queue
        -> ERPNext backend
        -> websocket
        -> scheduler
        -> long/short workers
        -> frontend
```

Externally reachable host surface remains loopback-only:

```text
127.0.0.1:18080 -> ERPNext frontend
```

The service lifecycle is owned by Podman Quadlet/systemd, not by a custom Ordivon daemon.

Named persistent volumes retain site, database and Redis queue state. Podman secrets are used for database credential material.

## Business semantic acceptance

The following acceptance objects were created through Frappe/ERPNext native document APIs and lifecycle methods rather than direct database writes:

- Customer: `E2E Customer 20260913`;
- Opportunity: `CRM-OPP-2026-00001`;
- Project: `PROJ-0001` / `E2E Project 20260913`;
- Quality Procedure: `E2E Quality Procedure 20260913`;
- non-stock service Item: `E2E-SVC-20260913`;
- Sales Invoice: `ACC-SINV-2026-00001`.

The Sales Invoice was first validated as a draft and then submitted through the standard Frappe document submit lifecycle.

Accepted accounting effect:

```text
Sales Invoice ACC-SINV-2026-00001
Grand total: CNY 100
Status after submit: Unpaid

Dr 1310 - Debtors - ORD   100
Cr 4110 - Sales - ORD     100

Total debit  = 100
Total credit = 100
Balanced     = true
```

This proves `business document -> ERPNext submit lifecycle -> General Ledger` for the acceptance slice.

These `E2E-*` records are test/acceptance data. They are **not** evidence of a real external sale, customer contract, tax invoice, payment or statutory accounting event.

## Persistence and recovery acceptance

A destructive service lifecycle check was performed:

1. verify ERPNext HTTP `200`;
2. stop the complete ERPNext Pod;
3. prove the endpoint is offline;
4. start the Pod again;
5. recover HTTP `200`;
6. re-read Company, Customer, Project, submitted Sales Invoice and GL entries;
7. re-prove the two GL entries remain balanced.

A Frappe-native `bench --site erp.ordivon.local backup --with-files` backup was also completed before the live Quadlet ownership migration. The backup included site configuration, database, public files and private files.

The old manually realized Pod was then removed while preserving volumes/secrets, and the same persisted business data was successfully read after systemd/Quadlet recreated the Pod and containers.

## n8n integration acceptance

n8n remains on its existing rootless Podman/Quadlet substrate.

Its existing pasta network already uses the gateway mapping required for host-local services:

```text
n8n container: 10.89.10.2
host gateway:  10.89.10.1
ERPNext:       10.89.10.1:18080 from the n8n network namespace
```

The existing n8n -> PostgreSQL path through `10.89.10.1:55434` remains healthy, so no new bridge, host-wide listener or `0.0.0.0` exposure was added.

A real n8n workflow was registered and published using n8n's supported `publish:workflow` CLI:

- workflow ID: `ordivon-erpnext-transport-smoke-v1`;
- trigger: loopback-only n8n Webhook;
- action: n8n HTTP Request to ERPNext `/api/method/ping`;
- live result after n8n restart: HTTP `200`, `{"message":"pong"}`.

Therefore:

```text
host loopback webhook
  -> live n8n main instance
  -> n8n HTTP Request node
  -> existing pasta --map-gw path
  -> ERPNext loopback publication
  -> Frappe ping
  -> pong
```

This is transport/integration evidence only. n8n does not become business truth.

## Authentication boundary

Administrator is enabled as a Frappe System User and server-side Frappe APIs successfully created/submitted the acceptance documents. Automated REST session login using the Administrator credential was not promoted as an integration mechanism.

Future authenticated n8n/agent ERP workflows should use a dedicated least-privilege ERPNext/Frappe integration identity and owner-native API authentication rather than reusing Administrator credentials.

## Evidence jobs

Representative Runtime mechanical evidence:

- Customer creation: `job-01a09b09-92c1-7680-862e-7a4795ac7c3b`;
- Opportunity/Project/Quality creation: `job-01a09b09-ea8c-7811-9e70-fa3a8c1ae334`;
- Item / submit contract inspection: `job-01a09b0a-4943-7390-bf95-2fea185c6f25`;
- draft Sales Invoice validation: `job-01a09b0a-b7e8-74e3-a3da-a44b3b60b8ae`;
- Sales Invoice submit + balanced GL proof: `job-01a09b0c-0393-7063-a091-2a9c2f6fbb51`;
- full stop/start persistence proof: `job-01a09b0c-7914-7250-a63c-0d582b5d274c`;
- Frappe backup proof: `job-01a09b0f-18cd-74a2-a1a5-0c903401921b`;
- live manual-Pod -> Quadlet ownership cutover: `job-01a09b0f-ad56-7182-8b75-c8240d707652`;
- n8n existing-gateway ERPNext transport proof: `job-01a09b17-e078-7933-b4f1-aacd31c5c4c1`;
- n8n supported publish + live webhook execution proof: `job-01a09b21-cbd0-7881-880b-14914983d499`.

Runtime evidence is mechanical evidence for the commands and observations above; business semantic acceptance is the ERPNext-native document/GL result, not Runtime's process exit alone.

## Forward rule

Do not expand ERPNext because modules exist. Activate/configure a module only when a real business event needs it.

Default path:

```text
real company/business event
  -> determine the natural ERPNext owner/module
  -> configure minimum required native semantics
  -> use native API/document lifecycle
  -> verify ERP-native resulting state/effect
  -> use n8n only for bounded integration edges
```

Build custom Ordivon business semantics only after a repeated, measured substitution failure in mature ERP/provider capabilities.
