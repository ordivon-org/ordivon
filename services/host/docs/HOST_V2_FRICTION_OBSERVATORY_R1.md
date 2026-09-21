# Host v2 Friction Observatory R1

## Purpose

This pass applies the Host freeze rule: do not reopen the semantic kernel because a local abstraction looks imperfect. Measure current production friction first, classify each observation by natural owner, and change Host only when the measurement identifies a Host-owned defect.

The repeatable read-only measurement is `experiments/host_friction_observatory_r1.py`; its first production observation is `planning/host-friction-observatory-r1.json`.

## Production population

At the R1 observation cut:

- 269 Tasks were open across 136 Goals.
- 17,120 Board messages were retained.
- 7,954 reply edges had **0 lost Task routes, 0 conflicting Task routes, and 0 route introduction mid-thread**.
- 129/269 open Tasks (47.955%) had not been checkpointed for at least 14 days.
- 170/269 open Tasks (63.197%) belonged to Goals containing more than one open Task; the largest Goal contained 35.
- Exact current checkpoint-digest, objective, frontier, and nextActions equality found **0 strict duplicate candidate groups**. Goal parallelism is therefore pressure, not duplicate-work evidence.

## Navigation cost

Current minimal product paths are:

| Known coordinate | Host calls to exact checkpoint |
| --- | ---: |
| exact Task ID | 1 |
| Goal ID | 2 |
| exact routed Board message | 2 |
| attention cursor hit | 2 |
| lexical Board search hit | 3 |

With no narrower coordinate, the current global `task.list` requires six 50-item pages for 269 open Tasks. Under a uniform open-Task target, the target is on page 3.212 on average and exact re-entry costs 4.212 Host calls on average (list pages plus one exact `task.resume`).

For the 50 most recently updated open Tasks, 46 are still on global page 1, three on page 2, and one on page 3. Creation-time ordering is observable friction but is not currently strong enough to justify changing the canonical list ordering.

## Payload cost

The six compact global inventory pages total 82,291 UTF-8 bytes.

`task.resume` over all open Tasks is 7,779 bytes mean / 7,185 p50 / 11,690 p90. `task.observe` is 8,163 bytes mean / 7,588 p50 / 12,148 p90.

A uniform open-Task re-entry through the global inventory costs 55,508 bytes on average before and including exact resume. When the caller preserves the Goal ID, the corresponding mean is 10,246 bytes, a **81.541% reduction**. The call-count comparison is 4.212 global-discovery calls versus two Goal-scoped calls, a **52.517% reduction**.

This supports preserving better navigation coordinates at the caller rather than making `task.list` more semantically authoritative.

## Board reconciliation pressure

154 open Tasks have no Task-routed Board messages; 115 have at least one. Of the latter, 43 (37.391%) have a routed Board message newer than the current Task checkpoint:

- <1h: 13
- 1–6h: 15
- 6–24h: 10
- 1–3d: 2
- 3–7d: 3

This is a reconciliation-pressure measure only. A newer collaboration record is not proof that the Task checkpoint is stale or wrong.

A recent 100-sequence `attention.delta` window encoded 79 messages into 31,110 bytes and five routed Task coordinates. Pulling the latest 50 full Board messages encoded 78,859 bytes. These projections have different semantics, so the byte comparison is descriptive rather than an equivalence benchmark.

## Observability ownership

Host can establish its durable Task/Checkpoint/Board state, revision fences, committed mutation receipts, and Board-to-Task routing integrity.

Host cannot establish:

- the actual number of Host Tool calls made by a fresh Agent across a client session;
- whether parallel Tasks are semantically duplicate work;
- whether an old open Task should be abandoned;
- how many foreign-owner revalidations an Agent performed;
- whether a connector is presenting a stale Tool catalog.

The existing Harness event model already represents Tool-call proposal, dispatch, observation, rejection, and unknown outcome, and retains seen Tool-call identities and provider usage. Cross-process correlation belongs to OpenTelemetry/W3C Trace Context. Semantic duplicate/stale-work judgement remains with the Goal/domain owner.

Therefore R1 adds **no Host telemetry table, counter store, duplicate detector, stale-task GC, or priority model**.

## Connector catalog residual

The live Host `tools/list` returns exactly ten Tools, `ttl_ms=0`, `cache_scope=private`, and advertises `tools.list_changed=true`. Yet the current connector-visible catalog can still contain the retired `news.*` Tools and an obsolete `host.status.recentLimit` parameter. Invoking the retired Tool reaches the live server and fails as `Unknown tool: news.list`.

This is classified as a connector/client catalog-freshness defect, not a Host tool-discovery defect. Host must not reintroduce `surfaceVersion` or maintain a second Tool directory to compensate.

The only Host-side standards alignment admitted by R1 is to populate the standard MCP `serverInfo.version` from the existing PEP 621 package version (`0.1.0`). That field is implementation identity only; it is not deployment, Git revision, schema, or Tool-surface truth.

## Stop rule

Freeze the Host semantic kernel by default. Reopen a retained Host LEGO only when a repeatable measurement demonstrates one of:

1. an invariant failure in Host-owned durable state;
2. materially excessive re-entry cost that cannot be reduced by preserving a more specific caller-owned coordinate;
3. a reproducible Host-owned stale/concurrency failure;
4. an external mature owner that can replace local machinery with lower total coupling.

Current R1 evidence triggers none of those gates.

The next measurement owner for real Agent-call counts and duplicate physical calls is Harness telemetry/event projection, correlated across processes with OpenTelemetry when required. Client Tool-catalog freshness remains an MCP connector/client residual.
