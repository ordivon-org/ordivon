# Host / Board contraction and Host v2 minimal retention

- Source: `/root/projects/ordivon-host-v2`
- Historical migration revision: `35b9defb1d2e`
- Retention validation revision: `756a38412a19`
- Reopened: 2026-09-13
- Superseded/settled: 2026-09-14
- New-model disposition: Host v1 and broad universal Host/Board ownership retired; Host v2 retained as a narrow active continuity/work-state utility; larger mature providers are demand-gated rather than mandatory cutover targets

## Current decision

The broad historical Host/Board architecture and Host v1 do not survive as universal Ordivon architectural owners. That does **not** require deleting every small Host capability. `ordivon-host-v2` has proven useful as a bounded local durability surface and is retained.

Current responsibility split is:

- small durable work/continuity state actually used by Ordivon: **Host v2**;
- durable macro-process when required: Temporal;
- multi-agent orchestration when required: Microsoft Agent Framework or another proven agent framework;
- heavyweight project/work management when workload scale justifies it: Plane or another mature work-management provider;
- integration edges: n8n;
- physical execution: Runtime;
- operational observation: Prometheus/Grafana/OTel-oriented stack;
- semantic acceptance: domain-native V&V.

The decisive rule is not “custom must disappear.” It is “do not retain custom responsibility that a mature component demonstrably replaces at lower total complexity.” Plane currently fails that economic test for this workstation's small work-state need because it is materially heavier than the retained Host v2 utility. `docs/MATURE_WORK_COORDINATION_COMPOSITION_R1.md` is therefore retained as provider/candidate analysis, not as a mandatory Host-v2 cutover plan.

## Disposition classes

- `EXTERNAL_OWNER` — mature external/provider system owns the responsibility;
- `DOMAIN_OWNER` — relevant domain owns semantic meaning/acceptance;
- `SPLIT_OWNER` — the historical primitive mixed several authorities and must be decomposed;
- `PROJECTION_ONLY` — derived view only;
- `DELETE` — historical primitive has no forward responsibility after decomposition.

## Historical surface mapping

| Historical surface | Observed responsibility | Corrected disposition | Target owner/treatment |
| --- | --- | --- | --- |
| `host.status` | aggregate health/integrity/recent activity | `PROJECTION_ONLY` | owner-native health + Prometheus/Grafana; no Host-wide health authority |
| `attention.delta` | sequential change/attention feed | `SPLIT_OWNER` | Prometheus/alerts/n8n for operational attention; Plane work attention for managed work; domain owner for semantic attention |
| `board.list` | list durable coordination/work records | `EXTERNAL_OWNER` | Plane work items/comments/activities/views after cutover |
| `board.search` | search coordination/work history | `EXTERNAL_OWNER` | Plane work search after cutover; evidence search remains domain-native |
| `board.post` | persist collaboration notes/replies | `EXTERNAL_OWNER` | Plane comments/work updates for managed work; specialized review/chat remains task-local where appropriate |
| `news.list` / `news.read` / `news.publish` | generic publication store | `DELETE` after decomposition | Media/Knowledge/Distribution or source-native publication owner |
| `task.list` | inventory managed work | `EXTERNAL_OWNER` | Plane work items; execution owners remain separate references |
| `task.observe` | mixed work context + execution/history | `SPLIT_OWNER` | Plane work context + Temporal/MAF/Runtime/domain exact owner reads |
| `task.resume` | locate/re-enter unfinished work | `SPLIT_OWNER` | Plane resolves work; Temporal/MAF/domain owner resumes actual process/run |
| `task.adopt` | create managed work and continuity | `SPLIT_OWNER` | Plane creates work item; workflow/agent run created separately only when required |
| `task.checkpoint` | mixed semantic/workflow/execution checkpoint | `SPLIT_OWNER` | Plane work state + Temporal process + MAF agent run + Runtime mechanical evidence + domain evidence |

## Non-tool responsibilities

| Historical responsibility | Disposition | Forward treatment |
| --- | --- | --- |
| Host PostgreSQL global authority schema | `DELETE` as global model | owner-specific stores only |
| `WorkingCheckpoint` | `SPLIT_OWNER` | work-management fields to Plane; process state to Temporal; agent state to MAF; semantic evidence to domain owner |
| Host open/completed/abandoned universal state | `DELETE` as universal state | Plane work status and owner-native process/domain states remain distinct |
| Host extension namespaces | `DELETE` | originating owner/provider contract |
| activity log | `SPLIT_OWNER` | Plane work activity where relevant; telemetry/events remain native to owners |
| command/idempotency receipts | `EXTERNAL_OWNER` | system owning the consequential operation |
| cursor/search/pagination mechanics | `EXTERNAL_OWNER` | provider-native APIs/indexes |
| canonical digesting | thin contract only | only where concrete evidence/effect identity requires it |

## Required separation

Do not recreate a universal Task under another name.

1. **Managed work item** — Plane.
2. **Durable macro process** — Temporal when required.
3. **Agentic sub-workflow/run** — MAF.
4. **Mechanical Job/Attempt** — Runtime/native executor.
5. **Domain semantic evidence/acceptance** — domain owner.

A real-world outcome may reference all five; none is authoritative for the others.

## Plane rule

Plane is allowed to be authoritative for work-management facts; it is not merely a dashboard. Operational multi-system dashboards remain projection-only. Plane must reference rather than absorb Temporal, MAF, Runtime and domain truth.

## Legacy data rule

Do not bulk-import the Host database blindly. Classify each historical record:

- durable managed work/context still useful -> migrate selectively to Plane;
- semantic decisions/evidence -> migrate to domain/knowledge owner;
- execution references -> retain as references to native owner evidence;
- Board chatter without continuing value -> archive only;
- generic activity/news projections -> archive/delete unless independently valuable.

## Local standing

- Temporal/n8n/Prometheus already active through the current Operations substrate;
- Grafana is active as the current containerized view;
- MAF 1.18.0 is installed and deterministic concurrent fan-out/fan-in mechanics passed locally;
- Plane Community v1.4.2 official installer is staged but activation is optional/demand-gated; current workload does not justify paying its resource/operational cost merely to replace Host v2;
- ChatGPT Agent Automation still lacks accepted assistant-output retrieval, so real MAF -> ChatGPT participant integration is not yet closed.

## Current result

`HOST_V1_RETIREMENT = COMPLETE`

`BROAD_HOST_BOARD_ARCHITECTURE = RETIRED`

`HOST_V2 = RETAIN_MINIMAL_ACTIVE`

`PLANE_MIGRATION_REQUIREMENT = CANCELLED`

`MAF_AS_HOST_REPLACEMENT_REQUIREMENT = CANCELLED`

A future workload may independently justify Plane, MAF, Temporal or another provider. Such adoption is a new capability decision, not unfinished Host-v2 retirement debt.
