# Host R7: Work Intake, Claim, Delivery and Consumer Acceptance

Status: native Rust domain / disposable PostgreSQL 18 candidate, not an installed MCP production capability.

## Why Host owns accountability (not execution)

Host answers: which Work exists, who offered it, who has accepted responsibility to produce it, what was submitted, which named consumer accepted or returned it, and which evidence references were declared. It must not schedule Runtime Jobs, store Artifact bytes, infer authentication from ActorRef, replace Security policy or fabricate physical/semantic success from PROCESS_EXITED.

GitHub Issues separate assignees from PR/Checks and evidence; Temporal Task Queues execute worker tasks but do not by themselves establish business acceptance. Kubernetes Leases inspire optimistic claim fencing but an expired lease never undoes an external effect. Reuse PostgreSQL CAS and immutable snapshots, not a new Task engine, database, event log, orchestration layer or duplicate schema authority.

Official references:
- https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/assigning-issues-and-pull-requests-to-other-github-users
- https://docs.github.com/en/rest/checks/runs
- https://docs.temporal.io/task-queue
- https://kubernetes.io/docs/concepts/architecture/leases/
- https://www.postgresql.org/docs/18/transaction-iso.html

## Logical LEGO: contract and natural owner

Use L=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold) with independent specification, PostgreSQL-backed Rust implementation and consumer evidence.

| Capability | Conditions and state effect | Owner / truth boundary |
| --- | --- | --- |
| Offer | Work open; requester is Work creator; consumer ActorRef exists; 1..32 nonempty acceptance criteria. No prior engagement. Creates versioned Offered. | Host accountable intent, not Runtime dispatch |
| Claim | Offered or Returned; two concurrent claims at same revision yield one winner; claimEpoch increases monotonically. Creates Claimed and recorded assignee. | Host responsibility, not authenticated identity |
| Release | Claimed, by current assignee or original requester, reason required. Restores Offered, retains epoch. | Host does not roll back external work |
| Submit | Claimed, matching actorRef and claimEpoch, unique deliveryRef across immutable Work history; output and evidence refs required. Creates Submitted; Work remains open. | References do not prove Artifact content or Runtime success |
| Review | Submitted, only designated consumer ActorRef, matching claimEpoch, verificationRefs required; creates Returned (Work open) or Accepted (Work completed). | Consumer declaration, not IAM |
| Cancel | Nonterminal engagement, original requester with reason; creates Cancelled (Work abandoned), cannot reopen. | Semantic cancellation, not physical effect reversal |
| Discover | Phase/consumer/assignee filters; stable (updatedAt,workRef) descending cursor; 16KiB..4MiB RFC8785 envelope; per-page PostgreSQL RR read-only. | Work standing, not priority, scheduling or cross-page frozen MVCC snapshot |

Returned-to-Claimed increments epoch so an old worker cannot submit or review from an obsolete claim. Missing/unknown historical state must never be replaced by false or inferred completed state. Every transition records a single Work revision, exact canonical request digest, durable command receipt and a replayable response; same identity replay changes admission to existing. A different request payload under the same id conflicts.

## Representation and backward compatibility

Existing PostgreSQL Schema 13 works / work_snapshots / command_receipts are the only durable authority; no new tables or DDL. Work engagement is a distinct versioned JSONB field in immutable Work snapshots, with engagement.schemaVersion=1. Existing Python WorkStore.get_work reads all new snapshot bytes and RFC8785 digests. Old Python WorkSnapshotInput is deliberately extra=forbid and MUST reject this new field when parsing an old generic snapshot-commit input. New operations use a distinct typed engagement contract, never broaden legacy Work.snapshot.commit behind callers' backs. The Rust generic Work CAS refuses to erase engagement by replacing it with an older snapshot type.

New Rust Work module: src/work/engagement.rs provides typed advance_engagement and list_engagements. The backing Work row FOR UPDATE and Work revision are the unique arbitration point; existing indexes are used for a bounded query. No assumption of high-scale indexed JSONB filtering is made: benchmark EXPLAIN ANALYZE with real task inventory before a justified additive index in the existing Alembic authority.

ActorRef is an opaque Host label, NOT proof of caller identity or permission. Gateway or Security must bind authenticated caller identity and verify consumer privilege before exposing mutating operations to untrusted clients. claimEpoch fences Host standing, not Runtime tool effects. Evidence, delivery and output reference strings are declarations until their natural Runtime/Artifact/consumer owner independently verifies them.

## Actual qualification and limits

Run the candidate isolated PostgreSQL tests with: bash services/host/rust/tests/verify_work_engagement_pg18.sh

This refuses inherited production DSNs, creates an isolated Docker postgres:18, runs original Alembic0001..0013 and deletes container. Rust tests cover simultaneous claimant race, CAS conflict, replay, wrong owner, old epoch, return/reclaim, one-time delivery references, consumer review, rejection and cancellation, no generic-CAS accountability stripping, 23 long Unicode offered tasks with byte-bounded paged listing and invalid cursor. Original Python WorkStore independently reads all eight Rust Work snapshots, RFC8785 digests and receipts. A separate Python negative test proves legacy WorkSnapshotInput rejects the new engagement object.

This is *domain source and direct PostgreSQL consumer evidence*, not an installed/production MCP capability. Still pending: C official rmcp output/input-schema and error wrapper, authenticated Gateway caller binding, B Topic/Attention notification projection, cross-component Artifacts/Runtime proof integration, real discoverability/use telemetry, query cost benchmarks and reversible production cutover. Do not claim production delivery automation or reassign stuck workers with time-based leases that do not exist.

## Existing Attention consumer reuse: experimentally proven

A fourth real disposable-PG18 integration test subscribes the designated consumer to a Work using native Attention.follow; then sends Offer, Claim, Submit and Accepted as ordinary immutable Work revisions. The **existing** Attention.delta SQL emits four ordered work_snapshot events, preserves each revision in contextRef, routes navigation to the original WorkRef and acknowledges the observed change horizon with Attention.ack. This proves reusable notification/navigation without a new inbox, event table, scheduler, or duplicate Work-event publisher. It does not imply that the consumer actually read/accepted the work from the Attention ACK itself: acceptance is a separate Work review event.
