# Host / Board implementation retirement and responsibility migration

- Source: `/root/projects/ordivon-host-v2`
- Observed revision: `35b9defb1d2e`
- Reopened: 2026-09-13
- New-model disposition: historical implementation retired; responsibility migration remains open until mature external-owner cutover is proven

## Corrected decision

The historical Host and custom Board implementations do not survive as Ordivon architectural entities. However, their responsibilities are not considered migrated merely because old code is retired.

Current target owners are:

- work management/collaboration: Plane;
- durable process: Temporal;
- multi-agent orchestration: Microsoft Agent Framework;
- integration edges: n8n;
- physical execution: Runtime;
- operational observation: Prometheus/Grafana/OTel-oriented stack;
- semantic acceptance: domain-native V&V.

See `docs/MATURE_WORK_COORDINATION_COMPOSITION_R1.md` for the selection and competition analysis.

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
- Plane Community v1.4.2 official installer is staged but activation is `HOLD_RESOURCE` because the current 7.8 GiB workstation is already carrying the existing stack;
- ChatGPT Agent Automation still lacks accepted assistant-output retrieval, so real MAF -> ChatGPT participant integration is not yet closed.

## Current result

`HOST_BOARD_IMPLEMENTATION_RETIREMENT = RETAINED`

`HOST_BOARD_RESPONSIBILITY_MIGRATION = IN_PROGRESS`

The prior `HOST_BOARD_RESPONSIBILITY_CLOSURE = PASS` was premature and is superseded by this record. Final closure requires a real workload to pass the Plane + Temporal + MAF + Runtime/domain cutover gates defined in `docs/MATURE_WORK_COORDINATION_COMPOSITION_R1.md`.
