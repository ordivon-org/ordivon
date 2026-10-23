# Ordivon Social Fabric LEGO R1

Truth role: planning projection, not project/domain truth.

Audited main: `60322a3af8aff6fd31f79f93f812617bb78a5802`.

## Current local constraints

- Live Host-v2: PostgreSQL schema 5; 2,134 Tasks; 267 open; 1,817 completed; 50 abandoned; 15,028 Task events; 17,155 Board messages; Doctor PASS.
- Host R8 explicitly contracts the kernel to semantic Task/checkpoint continuity, replay-safe mutations, Board discourse, and re-entry projection.
- Generic Host `activity_log` was retired; R1 must not recreate it as a hidden event bus.
- Host already carries `runtime.workspaceId`, `relevantJobIds`, and `observedHeadRevision`.
- Runtime already owns Workspace/Job/Attempt/artifact truth and exposes `foreignReferences` plus exact source bindings.
- Harness + OpenTelemetry/W3C Trace Context are already the documented Tool-call/causal telemetry owners.
- Gateway 0.3.0 currently exposes all 16 northbound tools in this session and reports Host continuity, Linux/Windows execution and Runtime artifacts available.
- Therefore the missing object is chiefly a **cross-owner projection compiler**, not a new coordination database.

## Reposition existing organs

```
Host Task    = durable commitment / semantic re-entry
Host Board   = social discourse
A2A          = direct/synaptic transport
Runtime      = physical realization truth
Git/main     = implementation currentness truth
Harness/OTel = interaction + causal telemetry
Gateway      = thin northbound membrane
Social Fabric= rebuildable signals/references/projections
COP          = shared current picture, never new authority
```

## Executable waves

### W0 — Boundary freeze/census
SF00 current owner census → SF01 Host freeze guard → SF02 cross-owner reference contract.

### W1 — Trace spine
SF10 CloudEvents-shaped SocialSignal → SF11 reference binding → adapters:
SF12 Host, SF13 Runtime, SF14 Git, SF15 Harness/OTel, SF16 Gateway capabilities.

### W2 — Shared reality compiler
SF20 FactSet → SF21 WorkGraph → SF22 Transactive Memory → SF23 Freshness/Supersession → SF24 Reconciliation → SF25 Common Operating Picture.

Initial deterministic findings:
```
workspace_without_durable_coordinate
task_without_live_realization
merged_but_task_open
completed_task_with_dirty_live_workspace
board_machine_status_unrouted
evidence_stale_against_main
capability_projection_owner_disagreement
superseded_workspace_still_active
```

### W3 — Social semantics
SF30 Semantic Receptor; SF31 self/direct/neighborhood/domain/system scope; SF32 TTL/refresh/supersede/retract; SF33 Damage Signals; SF34 Modulatory Signals.

### W4 — Collective coordination (shadow only)
SF40 Candidate/Support/Inhibition → SF41 policy-defined quorum → SF42 commitment projection. Start with one narrow architecture-change seam. No opaque scores and no new authority.

### W5 — UX/hygiene
SF50 `social:current|attention|reconcile` CLI first. SF51 Gateway projection only after dogfood. SF52 replace machine-status Board chatter with traces where possible. SF53 stale/open/merged Task candidates for review, never auto-GC.

### W6 — Dogfood/measure/decide
SF60 Ordivon architecture dogfood; SF61 Paper1/2/3 dogfood; SF62 frozen pre/post metrics; SF63 PROMOTE/HOLD/KILL every LEGO.

## First vertical slice

```
SF00 → SF02 → SF10
             ├─ SF12 Host
             ├─ SF13 Runtime
             └─ SF14 Git
                    ↓
                  SF20
                    ↓
                  SF21
                    ↓
                  SF24
                    ↓
                  SF25
                    ↓
                  SF50
                    ↓
                  SF60
```

This first slice alone should answer: what is current, what is integrated, what is orphaned/superseded, where is exact re-entry, and what evidence supports each claim.

## R1 stop rules

1. No Host kernel reopen without a measured Host-owned defect.
2. No mutable Social Registry.
3. No Kafka/NATS/Redpanda until pull/snapshot insufficiency is measured.
4. No new Gateway tool before local CLI dogfood and connector-freshness proof.
5. No quorum/receptor sophistication before deterministic owner traces and COP are correct.
6. Kill any LEGO that duplicates mutable truth already owned by Host/Runtime/Git/domain owners.
