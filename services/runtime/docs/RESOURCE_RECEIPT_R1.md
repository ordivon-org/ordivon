# Runtime Resource Receipt R1

Status: IMPLEMENTATION CANDIDATE

## Goal

Add durable, attempt-scoped physical resource evidence without making Runtime a pricing engine, telemetry warehouse, scheduler, or GPU provider registry.

## Owner / authority

- Runtime Attempt remains the execution identity owner.
- Linux systemd/cgroup v2 remains the physical process-tree and resource-accounting owner.
- Runner observes the cgroup it already proves in runner-start evidence.
- Runtime validates and registers the resulting receipt as an ordinary immutable Attempt Artifact.
- Higher-level workload/TCO analysis consumes receipts; it does not become Runtime authority.

## R1 artifact

Each Linux Runner MAY write `resource-receipt.json` beside `result.json`.

The receipt is deliberately separate from `RunnerResult`: result JSON has strict `deny_unknown_fields`, so extending it would create a new-Runner/old-Runtime reconciliation hazard during releases.

Receipt identity binds:
- schemaVersion
- taskId
- jobId
- attemptId
- launchTokenDigest
- observedUnixMs
- scope = `attempt_cgroup_including_runner`
- provider = `linux_cgroup_v2`

Measurements:
- CPU: usageUsec, userUsec, systemUsec
- memory: peakBytes; optional swapPeakBytes
- memory events: low, high, max, oom, oomKill where present
- IO aggregate: readBytes, writeBytes, readOps, writeOps, discardBytes, discardOps

All counters are physical observations, not semantic cost/accounting claims.

## Failure semantics

Resource observation MUST NOT reinterpret the execution result. Collection is best-effort:
- a successful observation creates the receipt;
- an unavailable/unsupported observation leaves the receipt absent;
- Runtime remains backward-compatible with historical bundles with no receipt;
- if a receipt file is present, malformed content or identity mismatch fails closed during evidence registration rather than silently accepting false evidence.

## Scope boundary

R1 measures the complete Attempt cgroup, including Runner overhead and descendants. It does not claim payload-only attribution.

R1 explicitly excludes:
- NVML/DCGM GPU accounting;
- Windows Job Object accounting;
- power/energy estimation;
- cloud prices or procurement recommendations;
- a new metrics database or second Registry.

Those are separate provider/enrichment LEGO.

## Workload profile

A later read-side profile consumes valid `resource_receipt` Artifacts and produces statistical summaries. Runtime Registry remains execution truth; analytic projections are derived evidence and may be rebuilt.

## Verification

R1 is accepted only when:
1. parser tests fail before implementation and pass after it;
2. historical bundles without receipt still reconcile;
3. valid receipt registers as `resource_receipt`;
4. mismatched receipt identity fails closed;
5. a real systemd/cgroup-v2 Attempt produces a readable receipt with non-zero CPU and memory observations;
6. existing Runtime portable and owner-local acceptance remains green.