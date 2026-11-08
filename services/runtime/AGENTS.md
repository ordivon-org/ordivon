# Ordivon Runtime Agent Entry

## Start from reality

Do not preload the documentation tree. Confirm the exact Git state, then inspect the relevant source, tests, and live process state.

Read [`docs/runtime.md`](docs/runtime.md) only when changing or diagnosing cross-component execution semantics: Workspace, request identity, Job, Attempt, reservation, runner bundle, process ownership, terminal result, Artifact, or reconciliation.

Read [`docs/recovery.md`](docs/recovery.md) only when operating on Registry integrity, backups, administrative repair, or restore. Read [`docs/effect-kernel.md`](docs/effect-kernel.md) before adding an operation identity field, retry path, external receipt, authority contract, world precondition, or structured effect adapter.

## Truth and responsibility

- The user owns goals, preferences, risk posture, and final commitments.
- The Agent owns implementation, testing, ordinary repair, and operation.
- Git owns code history, diff, rollback, and Workspace identity.
- The Registry backend used by the **connected installed Runtime node** owns durable request, Job, Attempt, reservation, cancellation, and resolution state. On 2026-11-07 both Linux Runtime services executed `ordivon-runtime-pg`; the unconsumed Linux SQLite Registry and historical Attempts were retired and the legacy Registry root removed. This is time-scoped, not a claim that source dependencies or Windows Runtime are PG-only. Use current installed node, kernel and PostgreSQL evidence—not historical service names—to determine authority.
- Windows must be evaluated independently: on 2026-11-07 the R6 candidate's SQLite Registry file grew during new native Runtime Job activity; do not claim a fleet-wide PG-only state or delete that Windows Registry before native PG cutover.
- Read [`docs/guides/agent-runtime.md`](docs/guides/agent-runtime.md) for execution/replay discipline and the legacy/PG truth boundary.
- Linux systemd/cgroup v2 and Windows Job Objects own native process-group supervision. The Linux launcher already configures `KillMode=control-group`, `TimeoutStopSec=2s`, and `SendSIGKILL=yes`; do not add a duplicate PID walker, custom kill escalation, or arbitrary process manager. A PostgreSQL reservation ceiling is not evidence of kernel CPU/memory/pids exhaustion. Resolve stuck `stopping` Jobs only through exact native identity, cgroup observations and the existing PG atomic terminal transaction—never by inventing a timeout-derived terminal result or manually editing live reservations.
- Result and Artifact files own their Digest-bound bytes.
- Current tools, configuration, deployment, and health must be queried from the live system rather than copied into prose.

For capability/reasoning decomposition, read [`docs/guides/runtime-legos.md`](docs/guides/runtime-legos.md). For measured modernization defects, the dynamic-capacity design alternatives and action ranking, read [`docs/audits/2026-11-08-runtime-modernization-brainstorm.md`](docs/audits/2026-11-08-runtime-modernization-brainstorm.md); distinguish observed facts from hypotheses. Keep source-level LEGOs distinct from deployed authority and never infer formal equivalence from a successful build.

## Component boundary

This repository implements **Ordivon Runtime**, not the complete Ordivon system. Cognition, planning, memory, coordination, and product interfaces remain outside this repository unless a concrete Runtime contract requires them.

## Change rule

Every persistent addition must solve an observed failure or repeatedly missing operation and state what existing path it replaces or extends. Effect semantics must be enforceable by a structured adapter; never trust a caller-declared effect class for arbitrary execution. Prefer mature host CLIs through `workspace.exec` over bespoke adapters, while treating arbitrary execution as opaque. Preserve unrelated user changes, use isolated Git Workspaces for substantial work, and keep one execution path.

Prefer an absolute executable and explicit arguments. Use `bash -c` only for a genuine compound command; use `bash -lc` only when the task explicitly requires login-shell initialization. Group related micro-checks into one logical Job rather than paying one durable admission per shell fragment.

Ordivon Runtime is trusted-local. Put untrusted code behind an external isolation boundary rather than adding a second policy or sandbox Runtime inside it.

## Verification

Verification is **Formal-first, not test-count-first**. Use the existing Runtime TLA+/TLC dispatch model for finite concurrent safety claims, the production `pg_runtime/native_stop.rs` decision function's Kani harness for all finite cancellation evidence inputs, and existing PostgreSQL CAS/schema tests for actual atomicity. Trace specification → bounded model/proof → executable refinement → real native consumer; none may substitute for another. Kani checks on code are not proof that systemd or PostgreSQL returned truthful observations. An ignored physical test is not a PASS until explicitly run.

Delete or consolidate a conventional test only when an actually executed proof covers its exact property and the relevant implementation refinement is established. Keep the single opt-in `pg_vertical` native systemd/PG test for cancellation, terminal evidence, capacity release and real deployment behavior; neither Kani nor TLC can prove Linux cgroup behavior. Never mark unrun checks PASS, skip formal counterexamples, or invent a new verification DSL. See `formal/README.md` for the traceability contract.

Run the smallest checks that can invalidate the changed boundary. CI is the machine-owned default verification contract.
