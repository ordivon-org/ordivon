# Convergence Queue Telemetry R1

Date: 2026-09-23
Status: LIVE PROVIDER PROJECTION / NO NEW SCHEDULER AUTHORITY

## Authority boundary

GitHub Merge Queue remains the durable queue authority and GitHub Actions remains
the verification-run authority. Ordivon does not introduce a queue database,
shadow scheduler, mutable queue registry, or copied run state.

tools/repo/queue_telemetry.py is a rebuildable read-only projection over:

- pull-request timeline added_to_merge_queue / removed_from_merge_queue events;
- merge_group workflow runs and their synthetic SHAs;
- required root-verification job timestamps;
- pull-request merge timestamps.

The raw provider snapshot is intentionally not canonical. It may be retained as
an ephemeral diagnostic artifact; the projection can be rebuilt from GitHub.

## Metrics

For each queue-attributed pull request:

- queue dispatch = merge-group run creation - enqueue;
- queue residence = queue removal/merge - enqueue;
- end-to-end queue = merge - enqueue;
- runner wait = required-job start - required-job creation;
- verification = required-job completion - required-job start;
- post-verification merge = merge - required-job completion;
- requeue count and merge-group run count;
- failed/cancelled merge-group verification time as observed CI waste.

Historical queue depth is reconstructed by sweeping enqueue/dequeue events. It
is explicitly a lower bound because a finite observation window can begin with
an already-enqueued item.

## First live baseline

docs/architecture/evidence/CONVERGENCE_QUEUE_TELEMETRY_BASELINE_R1.json
contains the first provider-derived baseline:

- 8 merged queue-attributed PRs;
- 8 merge-group runs;
- observed peak queue depth lower bound: 2;
- median queue dispatch: 18 s;
- median queue residence: 106 s;
- median required verification: 44 s;
- median runner wait: 3 s;
- zero requeues;
- zero unsuccessful merge-group runs;
- zero observed wasted verification seconds.

The longest verification observations are PR #21 (162 s) and PR #20 (138 s),
which were the Harness portability and real Experimental Episode producer waves.
They are not evidence of queue contention: dispatch stayed at 18 s and neither
run was invalidated or repeated.

## Pressure decision

R1 telemetry falsifies the need to immediately add a custom scheduler:

- adaptive speculation: pressure not established;
- batching/bisection: repeated high queue depth not established;
- predictive cost scheduling: no validated historical model exists;
- external smart queue: GitHub-native queue has not failed the measured
  throughput/cost requirement.

The next admissible step is more observation, not scheduler implementation.
When measured pressure appears, the first experiment remains a transparent
AIMD-style speculation control law before predictive ML.

## Commands

Live projection:

    mise run repo:queue:telemetry

Hermetic analyzer tests:

    mise run repo:queue:telemetry:test

The analyzer also accepts --input for deterministic replay of a saved provider
snapshot and --snapshot-output for ephemeral diagnostic capture.
