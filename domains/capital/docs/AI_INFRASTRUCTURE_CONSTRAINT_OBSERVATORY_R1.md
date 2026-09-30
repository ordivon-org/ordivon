# AI Infrastructure Constraint Observatory R1

The observatory is a **research re-entry control** that turns the populated AI-infrastructure constraint state into an owner-watch plan and decides which bounded research layer should be reopened when new evidence arrives. It is not a crawler, scheduler, provider database, external-truth owner, investment signal, graph writer, or financial authority.

```text
Natural external owner
  -> caller-qualified ObservationCandidate
  -> WatchSpec
  -> freshness fence against current Graph state
  -> gap / graph-trigger match
  -> ReentryDecision
       NO_REENTRY
       REENTER_MEASUREMENT
       REENTER_GRAPH_AND_MEASUREMENT
```

`WatchSpec` is exact-digest bound to both the constraint graph and measurement document. Its 13 pairs exactly equal the 13-item fill queue, while `nextObservations` are inherited from the measurement owner rather than independently restated.

A candidate must already be `CALLER_QUALIFIED`; this module cannot create that standing. It additionally requires an admitted source class, material delta, observation date strictly newer than the watched graph state's `observedAt`, and either a required-gap match or an explicit graph-reentry trigger.

A gap match reopens measurement evaluation only. It never claims the gap is fully closed or that headroom is admitted. A graph trigger requests jurisdiction-frontier recomputation and never mutates the graph.

The existing Capital architecture intentionally does not recreate a Prometheus/Temporal/research-platform owner here. If periodic execution is later required, an admitted scheduler may consume `prioritized_watch_specs`; provider capture and scheduling remain outside this control.

R1 uses day-granular freshness and therefore fails closed on same-day ordering. Prospective use should record false-positive re-entry, missed frontier migration, and stale-source cases before any policy refinement.
