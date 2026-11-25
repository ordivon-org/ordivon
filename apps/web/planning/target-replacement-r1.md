# Living Web target replacement execution spec R1 (2026-11-26)

Status: candidate source plan, not global technology ratification, installed
truth, Security admission, or release approval. Host G08 V1 #31553 and Web
Work@30 / Topic #32667 are the decision and collaboration coordinates.
Reference R1-R10 remains the behavioral oracle, not a reason to keep patching
SQLite/Fastify indefinitely. Do not create another truth store or service
solely to change language.

## Goal — reality — transition

Goal: Human and Agent consume typed, current, attributable Owner observations
and admitted effects without treating UI state, a tool intention, or transport
success as business authority. Reality: modular Fastify/Node TypeScript and
SQLite canary, real R10 transaction/evidence tests, read-only SSR Grant page;
Solid 2 / UI SDK prior test-only consumer in PR #2625; PG18 R9 primitive
witness is not an adapter. Change: replace one complete consumer boundary
at a time, compare with the reference, then retire reference code only after
source integration, independent validation, installation and real consumer
acceptance. Do not run shadow domain mutations or auto-reissue unknown effects.

## Logical and capability LEGO map

| Logic (what problem is represented) | Thought (invariant / method) | Capability and source seam |
|---|---|---|
| L01 Render actual view | fine-grained reactive graph, accessible native DOM | Solid 2, Vite 8, Rolldown/Oxc; operator.tsx |
| L02 Observation and interaction | freshness != authority; latest eligible generation, semantic action scope | observation.ts reducer, operator-observation.ts full decoder, native select; experimental UI SDK |
| L03 Protocol adaptation | standard Request/Response, no authority hidden in framework | existing app.ts Fastify reference; Hono Fetch or Axum/Tower adapter candidate |
| L04 Human identity/session/challenge | one-shot state, session deadline and explicit denial | W01/W02; existing SimpleWebAuthn and Security contract, store boundaries |
| L05 Agent authority and effects | independently admitted request; exact receipt and terminality | W03-W06; existing Security verifier, Grant, Approval, Effect and Receipt consumers |
| L06 Domain kernel | representation-first, typed invariants, deterministic domain decisions | existing store/effect coordinator reference; Rust/Axum domain kernel candidate, no mandatory extra network hop |
| L07 Owner integration | natural Owner; read/write separately, unknown distinct | Gateway/Host/Harness/Runtime contracts, authorized bounded Journal only; AG-UI projection candidate |
| L08 Persistence | atomic scoped effect, MVCC, identity/revision fence | PG18 native witness, selected async driver/pool pending; TEXT exact receipt representation |
| L09 Build/release | exact source + lock + artifact mapping, rollback explicit | Vite manifest, pnpm lock, existing CI/release provenance; operator-grants-ui.ts |
| L10 Verification | independent falsification, cost-aware real consumer | node:test, TypeScript, TLA+, Playwright, SQLSTATE/fault/differential tests, candidate CI |

Mature substrates and design references: Solid stable and async reactivity
https://www.solidjs.com/blog/solid-2-0-the-long-hold/
https://docs.solidjs.com/concepts/reactivity/ ;
Hono standard transport https://hono.dev/docs/concepts/web-standard ;
PG18 isolation https://www.postgresql.org/docs/18/transaction-iso.html ;
explicit locks https://www.postgresql.org/docs/18/explicit-locking.html ;
ARIA native semantics https://www.w3.org/TR/using-aria/ ;
Axum/Tower https://docs.rs/axum/latest/axum/ ;
Strangler Fig incremental replacement https://martinfowler.com/bliki/StranglerFigApplication.html .
Use stable platform primitives before new general-purpose abstractions.
Strangler-style replacement is by actual consumer, not by permanently retaining two writers.
The same HTTP path switches explicitly at composition time; fallback is an operator decision, never a response-time recovery that hides an unknown effect.
Runtime (Node/Bun/Deno), transport (Fastify/Hono/Axum), renderer (Solid),
semantic UI SDK and domain/persistence choices are separate variables.

## Executable migration sequence and gates

| Package | Actual producer/consumer | Exit condition and retirement |
|---|---|---|
| T01 renderer | current /operator/grants + existing authenticated GET | Solid product build served by createWebApp with explicit configured dist; actual Chromium compares all 8 columns, display name, four availability states, foreign-row isolation, text escaping, native filter, no quota change, no test bridge. Late completion, denied, lifecycle and hints clear private data. Build manifest allowlist; default reference stays until acceptance. |
| T02 semantic UI | same page, native select as baseline | use existing SDK experiment (no tool registration), validate action allowlist, keyboard/ARIA, invalid action, no authority effect; qualify beta pair/publishing/licenses before bundling. AG-UI only actual authorized Journal; WebMCP optional, no new mutation entrypoint. |
| T03 persistence | real Note/Effect/Grant/Approval/Challenge/DPoP | async PG18 driver/pool lifetime, SQLSTATE classification by phase, lock order identity then Grant then approval/note; compare exact observations and rollback/crash. Preserve 11-table schema semantics, migration/backup/restore and old-data acceptance. No SQLite removal without single-writer cutover evidence. |
| T04 domain | identical contract, actual business consumers | Rust type/refinement and independent differential tests; same replay/denial/receipt bytes, no duplicate network service solely for Rust. |
| T05 transport/runtime | existing session/CSRF/DPoP and typed HTTP boundary | Hono/Axum on comparable real workload; exact HTTP method/status/headers, existing auth/denial and late decision tests, resource/crash/throughput. Node/Bun/Deno measured independently. No login or policy changes to make benchmark pass. |
| T06 integration / retirement | authorized real consumers and release | native CI, independent owner review, build provenance, deploy/recover test, then switch configured default and remove redundant reference. Not automatic fallback or dual effect execution. |

T01 R2.1: I existing authenticated GET envelope and immutable build directory;
O accessible rendered observation or explicit denied/unavailable/suspended;
S per-document volatile generation and filter, never owner authority;
pre valid same-owner auth, valid finite time, distinct grant IDs and scope
strings; post exact displayed projection or empty visible private data;
inv only eligible generation settles, foreign rows denied, candidate not
admission, no durable cache or domain effect; eff actual owner read only
(existing session read may extend idle); c fine-grained keyed DOM, one GET
per explicit refresh/lifecycle (no polling); epsilon no continuous revocation,
physical WebAuthn, multi-browser accessibility, installed production or
package provenance certification; prov real source/test jobs and exact Git;
unfold app route -> fixed shell/manifest -> Solid view -> existing reducer
and decoder -> Owner GET. No test bridge in product bundle.

Run from repo root using existing Web toolchain and lock policy:
```sh
pnpm --dir platform/security/contracts/agent-request-verifier-v1 install --frozen-lockfile --ignore-scripts
pnpm --dir apps/web install --frozen-lockfile --ignore-scripts
pnpm --dir apps/web/experiments/solid-grants-r3 install --frozen-lockfile --ignore-scripts
pnpm --dir apps/web/experiments/solid-grants-r3 verify:operator
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
```

Explicit isolated candidate enablement: set
ORDIVON_WEB_OPERATOR_GRANTS_DIST to absolute trusted build directory
dist-operator. Config absent = existing SSR reference; configured but invalid
= fail startup; never silently fall back after a partial build. Serve
only exact manifest assets, not directory traversal or per-request disk paths;
manifest is not a signature or provenance proof. HTML shell contains no private
owner data; private API remains authenticated/no-store. Product build uses
native accessible select and excludes experimental bridge, not a claim of full
semantic UI SDK qualification. Existing experiment path remains a transitional
build substrate to avoid duplicating the package; eventual move/retirement
requires peer coordination. No global dependency upgrades, package skill
activation, source-to-production promotion or new authority claims without
separate evidence.


## R11 source qualification results

- Actual product route built and consumed using Solid 2.0.3 + Vite 8.3.8,
  54 transformed modules, 41.12 kB JS (gzip 16.54 kB); 4 reference rows ×
  8 columns exact parity, actual authenticated data, no foreign rows or
  test bridge, local native filter, no quota write. Native back navigation
  after revoked session and invalid wire projection clear data.
- R11 product probe and 143 owner tests (job-01a21498-e275-74d1-bb2f-df7aa32e310f);
  8 UI tests, 1038 finite transitions/126 expanded states, exact
  generation mutant killed in real Chromium, three decoder/manifest mutants
  killed by actual tests. No claim of exhaustive real lifecycle proof.
- Qualified compatible dependency resolution: Vite 8.3.5 -> 8.3.8,
  Node types 26.6.5 -> 26.6.7, UI SDK beta.16 -> beta.17 paired and
  experimentally scoped; 5 stable ranges relaxed, exact lock retained.
  Actual product and separate SDK browser probes and native async
  witness pass on final resolution (job-01a21499-a885-759d-905f-86ba0e9eb06b).
  Existing minimumReleaseAge 1440 retained; no skill approval or activation.
- Current source build enablement is explicit, not a production default or
  actual install. The initial networkidle wait in the browser fixture was
  unsuitable; final fixture waits for real Response.json decoding and a frame.
  No production backend, PG driver, or Security policy cutover in this round.


## R12 — native Rust/PostgreSQL domain slice execution spec

Host Work@31, Topic #32702; R11 is retained. First T03/T04 implementation:
actual Human Note create/list persistence, not a new authentication route.
The existing R10 business contract is the reference.

| Logic | Thought | Actual capability / remaining qualification |
|---|---|---|
| L04 admitted context | natural owner, no policy duplication | existing Web boundary; trusted caller supplies principal |
| L06 domain state | representation-first | domain.rs Note, NoteState, Audit; error.rs typed storage outcomes |
| L08 native write | atomic exact Note/Audit | postgres.rs async tokio-postgres, row count, parameter binding, READ COMMITTED, deferred-constraint fence, final readback |
| L08 carrier lifecycle | RAII, ambiguous outcome distinct | dedicated local Unix-socket connection per call; discard driver, explicit rollback, CommitUnknown with note ID, no automatic retry |
| L08 read | deterministic principal-scoped projection | same order as R10; reject unrepresentable JS timestamp |
| L10 qualification | native fault, differential, independent observation | tests/native.rs, actual SQLite reference, isolated R9 cluster and one-shot wire fault |

R2.1 I caller-admitted principal, Unicode scalar content, safe JS integer time;
O committed Note or typed error (commit failure UNKNOWN plus note ID);
S private PG carrier per operation, actual Note/Audit tables;
pre valid schema, trusted local socket, representable input;
post exact single Note and Audit after deferred constraints then native commit
acknowledged; inv no partial commit in tested precommit faults, no automatic
reissue or authority inference, no uncertain connection recycling;
eff local PG read/write; c native MVCC and indexed reads, setup per operation;
epsilon no hostile DDL, production TLS/pool/full migration/HTTP integration,
cancellation after COMMIT may be ambiguous, a dropped future loses returned
identity; prov native tests and exact Git; unfold domain -> adapter -> SQL.

PG-only counterexample: DEFERRABLE INITIALLY DEFERRED constraint trigger
changes Note after precommit readback. Force SET CONSTRAINTS ALL IMMEDIATE
before final projection. Without the fence, native mutant returned success.
Actual wire fault discards CommandComplete COMMIT; driver returns
CommitUnknown and independent peer observes one exact committed Note/Audit.
R9 cluster lifecycle reused, private data-directory/no TCP/random guard
verified before destructive fixture DDL.

References: https://www.postgresql.org/docs/18/sql-set-constraints.html ;
https://docs.rs/tokio-postgres/latest/tokio_postgres/struct.Transaction.html ;
https://docs.rs/sqlx/latest/sqlx/struct.Pool.html .
Choose existing native async driver; qualify pooling separately, no homemade
pool or new network hop. Use matched workload before changing carrier.

Exit gates: (1) native Note create/list source qualification (this candidate);
(2) bounded mature pool lifecycle, cancellation/reconnect, no stale transaction,
unknown commit and caller-held operation identity, measured setup/concurrency;
(3) full owner PG schema and other consumers, TEXT exact bytes, safe integer
range, Unicode (PG text excludes NUL; Rust strings exclude lone surrogates),
collation, historical migration and backup/restore; (4) real authenticated
product composition and native Security/HTTP consumer tests; (5) independent
review, deploy/recover, single writer cutover and retirement. Never dual-write
or replay unknown operations. No raw principal public route.

Native isolated reproduction:
```sh
python3 -B apps/web/crates/web-note-pg/tests/run_native.py
cargo clippy --manifest-path apps/web/crates/web-note-pg/Cargo.toml --locked --offline --all-targets -- -D warnings
```
Rust 1.99.1, PG18.7, Node26.12.1 observed. Exact lock retained, direct
dependencies use compatible ranges. No production services mutated.
