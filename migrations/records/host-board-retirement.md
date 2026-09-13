# Host / Board retirement responsibility closure

- Source: `/root/projects/ordivon-host-v2`
- Observed revision: `35b9defb1d2e`
- Closure audited: 2026-09-13
- New-model disposition: retired mixed-responsibility container; no replacement Host or authoritative Board

## Decision

Host and Board do not survive as Ordivon architectural entities. Their historical responsibilities are decomposed to the natural domain or mature external owner. Any future cross-owner overview is a disposable read projection, not a new source of truth.

The closure uses four disposition classes:

- `EXTERNAL_OWNER` — a mature external/provider system owns the mechanics or state;
- `DOMAIN_OWNER` — the relevant domain/case owns semantic meaning and acceptance;
- `PROJECTION_ONLY` — useful only as a derived view over authoritative sources;
- `DELETE` — no forward Ordivon primitive or compatibility surface is justified.

## Historical surface closure

| Historical surface | Observed responsibility | Disposition | Forward owner / treatment |
| --- | --- | --- | --- |
| `host.status` | aggregate Host schema/task/board/news integrity and recent activity | `PROJECTION_ONLY` | owner-native health/readiness plus OTel/Prometheus/Grafana where an aggregate operational view is useful; no Host-wide health authority |
| `attention.delta` | sequential change-navigation feed over Host-local activity | `PROJECTION_ONLY` | owner-native events/telemetry; Prometheus/Alertmanager/n8n for operational attention; domain queues/queries for semantic attention |
| `board.list` | list durable coordination messages | `DELETE` | use collaboration/work-management owner chosen by the active domain; aggregate listing, if needed, is a read projection |
| `board.search` | search coordination-message history | `DELETE` | search the owning collaboration/domain system; no Ordivon-global message index |
| `board.post` | persist note/question/proposal/warning/reply messages | `DELETE` | GitHub issue/comment/discussion, document review, chat/email, workflow approval or other task-local collaboration owner |
| `news.list` | inventory retained external-news editions | `DELETE` | knowledge/research/media/release owners retain their own publications; cross-source reading is query/projection only |
| `news.read` | read one retained external-news projection | `DELETE` | query the owning source or retained artifact directly |
| `news.publish` | revisioned publication persistence | `DELETE` | Media/Distribution or provider-native publication path owns publishing and read-back |
| `task.list` | inventory universal Host Tasks | `PROJECTION_ONLY` | domain work items/cases, Temporal workflows, Snakemake DAGs, CI runs and Runtime Jobs remain distinct; aggregate only for display/query |
| `task.observe` | task checkpoint/history plus extension projection | `PROJECTION_ONLY` | observe the natural owner: domain record, Temporal/Snakemake/CI or Runtime; never reconstruct universal Task truth |
| `task.resume` | read/re-enter Host continuity checkpoint | `DELETE` | durable process resumes in Temporal or its native workflow owner; semantic cases reopen/continue in the domain owner |
| `task.adopt` | create a universal Host Task with initial semantic checkpoint | `DELETE` | create the appropriate domain case/work item and, only when required, a separate workflow execution |
| `task.checkpoint` | revision universal semantic working state | `DELETE` | domain/case records own semantic progress/evidence; workflow engines own durable process state; Runtime owns mechanical execution evidence |

## Non-tool responsibilities

| Historical responsibility | Disposition | Forward treatment |
| --- | --- | --- |
| PostgreSQL Host authority schema | `DELETE` as global model | PostgreSQL remains a storage substrate; schemas belong to bounded domain/application owners |
| `WorkingCheckpoint` (`objective`, `frontier`, `established`, `unresolved`, `nextActions`, runtime references, `workStanding`) | `DOMAIN_OWNER` | retain only fields that a real domain/case requires, using that domain's vocabulary and lifecycle model |
| Host `open/completed/abandoned` Task state machine | `DELETE` | domain work-item/case state and workflow-execution state are separate concepts |
| Host extension namespaces | `DELETE` as generic extension mechanism | data belongs to the originating bounded context/provider contract |
| activity log | `PROJECTION_ONLY` | derive operational/event views from native owners; do not make a replacement global activity ledger |
| Board message persistence | `DELETE` | collaboration stays with task-local mature systems |
| News revision store | `DELETE` | publication/version authority stays with Media/Distribution/knowledge/provider-native systems |
| command/idempotency receipts | `EXTERNAL_OWNER` | preserve idempotency/reconciliation only at the system that owns the consequential operation (Runtime, Temporal, Distribution/provider, etc.) |
| cursor/search/pagination machinery | `EXTERNAL_OWNER` | use owner-native query APIs and indexes |
| canonical digesting | `EXTERNAL_OWNER` / local thin contract only | retain exact digests only where a concrete evidence/effect contract requires them; no global Host digest ontology |

## Required separation after retirement

Ordivon must not recreate a universal `Task` under another name. Keep these identities separate:

1. **Case / work item** — semantic goal, requirements, decisions, evidence and domain completion. Owner: the active domain/project/work-management system.
2. **Process / workflow execution** — ordered/durable process state. Owner: Temporal, Snakemake, CI or another selected workflow system.
3. **Mechanical Job / Attempt** — concrete command/process execution and physical evidence. Owner: Runtime or the native execution provider.

A single real-world outcome may reference all three, but none is authoritative for the others.

## Board replacement rule

There is no authoritative replacement Board. Use mature task-local collaboration/work-management surfaces when humans need to coordinate. A future Ordivon overview is permitted only as a read model/materialized projection with these constraints:

- every displayed field identifies or can resolve to its authoritative source;
- the projection owns no domain transition, workflow transition or execution transition;
- deleting and rebuilding the projection must not destroy authoritative work state;
- writes go to the natural owner, never to the projection database;
- no new global Task schema is introduced merely to populate the view.

At current scale, existing owner-native views (Git/GitHub, Temporal, Runtime, Snakemake/CI, PostgreSQL domain queries, Prometheus/Grafana) are preferred over building a custom Ordivon overview.

## Legacy data disposition

Do not bulk-import the Host database into a new global schema.

- Task checkpoints: selectively extract only durable domain knowledge, decisions, evidence or references that a current domain still needs.
- Board messages: archival collaboration history only unless a specific message is cited as evidence/decision provenance.
- News editions: archival/generated projection; migrate only independently valuable research/knowledge/media artifacts to their natural owner.
- Activity log: derived navigation history; no forward authority migration.
- Host command receipts: retain with retirement evidence where needed; consequential effect receipts belong to the effect-owning provider.

Git history of Host v2 remains provenance. Host v2 does not remain an active provider dependency of Ordivon Next.

## Local replacement evidence

Current local capabilities already cover the residual mechanical roles without a Host successor:

- durable workflows: Temporal through Operations v2;
- integration edges/human-facing automation: n8n;
- scientific DAGs: project-local Snakemake;
- build/test/release workflow: native CI/build systems;
- physical execution and execution receipts: Runtime;
- host/infrastructure desired state: Ansible/Nix/DSC-facing composition and OpenTofu;
- structured domain data: PostgreSQL as substrate, with owner-specific schemas;
- observability: OpenTelemetry/Prometheus, with Vector/Loki/Grafana available when justified;
- semantic acceptance: domain-native V&V through task-local Capability Packages.

## Mature external reference model

The decomposition follows established separation rather than a new Ordivon ontology:

- BPMN — process modeling: https://www.omg.org/bpmn/
- CMMN — case management modeling: https://www.omg.org/spec/CMMN/
- DMN — decision modeling complementary to process/case modeling: https://www.omg.org/dmn/
- CQRS / materialized read models — separate authoritative writes from optimized query projections: https://learn.microsoft.com/azure/architecture/patterns/cqrs and https://learn.microsoft.com/azure/architecture/patterns/materialized-view

These references guide responsibility separation; Ordivon does not require BPMN/CMMN/DMN engines or a new CQRS platform unless a real workload proves that need.

## Closure result

`HOST_BOARD_RESPONSIBILITY_CLOSURE = PASS`

No audited Host/Board responsibility requires a successor Host, successor Board, global Task state machine, global collaboration database, or global activity ledger. Reopen this decision only if a real workload demonstrates a repeated cross-owner capability gap that cannot be solved by owner-native query, mature work-management/case tooling, or a disposable projection.
