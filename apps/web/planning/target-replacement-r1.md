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


## R13 — bounded native carrier and caller-held operation identity

Host Work@32, Topic #32747. Advance T03/T04, not legacy SQLite repair.
R12 is historical evidence; its dedicated carrier and implicit async identity
have been replaced in the Rust candidate, not in installed production.

| Logic LEGO | Thought LEGO | Actual Capability |
|---|---|---|
| L06 Operation representation | caller-held immutable identity | PreparedNote::new/restore, UUID note + audit coordinates, representability gate |
| L08 Admission to storage resources | bounded allocation, reuse mature allocator | deadpool-postgres 0.14 with Tokio, configurable capacity and checkout wait |
| L08 Carrier terminality | default discard, affirmative terminal evidence | Lease; Object::take, ClientWrapper Drop; explicit commit/rollback acknowledgement |
| L08 Reuse and isolation | clean session before reuse | RecyclingMethod::Clean, native reconnect; no custom pool |
| L08 Effect execution | exact atomic Note/Audit | execute(&PreparedNote), existing native transaction and deferred constraint fence |
| L08 Observation | absence is not proof of failure; consistent snapshot | observe(&PreparedNote), read-only REPEATABLE READ, exact two-coordinate binding |
| L10 Verification | independent native evidence, failure injection | real PG PIDs, session residue, saturated pool, two real COMMIT wire faults, differential oracle |

Operation contract: caller prepares and retains complete immutable intention
(note/event IDs, admitted principal, content, timestamp) before first await.
Restoration is representation only, not authorization. execute never creates
a new identity or automatically replays. A second explicit execute with the
same ID can fail with native 23505; there is no promised idempotent response.
Observation is Exact(original Draft and exact Audit), Unobserved(snapshot
has neither coordinate), Mismatch(partial/conflicting/changed creation
projection), or typed error. Later Published is not the original Draft
projection and returns Mismatch, not proof of failed creation. Unobserved
does not justify re-execution or assert noncommit, including while in flight.
No new public route, credential or authority; trusted caller only.

R2.1 I prepared immutable operation or principal-local read, bounded pool config;
O exact committed Note or typed error, observation sum type; S native PG plus
pool leases; pre trusted owner caller/schema/socket, retained operation;
post exact write and evidence, only acknowledged terminal carrier reusable;
inv no automatic reissue, no uncertain carrier recycling, no authority from
observation, one coherent snapshot; eff local database only; c pool checkout
queue and native MVCC, Clean reset, no second driver; epsilon logical pool
capacity is not an instantaneous global physical connection bound, checkout
timeout is not execution deadline, caller must persist operation if restart
recovery required, no production throughput or TLS/migration claims;
prov native PIDs, wire fault, actual differential and Git; unfold pool library
-> small terminality fence -> native transaction -> observation.

Native qualification: two independently waiting PG backends, third checkout
times out; cancel both, exact PIDs removed; disjoint transaction proceeds.
Same PID reused after acknowledged operation; session work_mem changed by
fixture trigger is reset; idle backend terminated and replaced. Actual
CommandComplete COMMIT discarded once, and separately held until caller
cancels after server commits: retained operation recovers exact single
Note/Audit, retired carrier disappears while pool remains alive. Duplicate
note/audit IDs reject without extra durable write; wrong principal/content or
audit identity, orphan audit, later Published distinguish Mismatch.
Three targeted native mutants killed: return uncertain carrier, Fast recycle
leaks work_mem, invert exact audit binding. Existing R12 fault and R10
SQLite differential retained. Job-01a214b0-62bc-7754-9bd7-28c7ac4e32d0.

Local benchmark uses same actual list query and two rows, five alternating
samples of 40 reads, fresh one-slot pool per call versus reused one-slot
pool, all outputs identical. Three prior successful runs had ratios
5.37x/9.86x/15.95x, restored-mutant run 150.199ms -> 29.990ms (5.01x).
Variability explicit; not comparison of production services or end-to-end
throughput, no claim of exact R12 binary benchmark. Use measured evidence
rather than treating pool defaults as production sizing.

Mature substrate references:
https://docs.rs/deadpool-postgres/latest/deadpool_postgres/ ;
https://docs.rs/deadpool-postgres/latest/deadpool_postgres/enum.RecyclingMethod.html ;
https://docs.rs/tokio-postgres/latest/tokio_postgres/struct.Transaction.html ;
https://www.postgresql.org/docs/18/transaction-iso.html .
Direct dependency ranges; exact lockfile for reproduction.

Next: full schema and real domain consumers including Effect/Grant/Approval,
explicit caller operation coordinate durability at composition boundary,
execution deadlines/cancellation and production pool sizing, native
authenticated HTTP consumer via selected transport without duplicating
Security, historical data/collation/backup/restore and single-writer cutover.
Only retire the installed old writer after independent qualification.


## R14 — Web test architecture replacement execution spec

Host Work@33 and shared verification Topic #32805, #32814, #32866.
No duplicate global runner or registry; root selector/Host/Composition are
other active owners. Source baseline 95eba099 (R13 plus main da283e36).
Goal: qualify actual target consumers without treating a green legacy suite,
coverage percentage, ignored tests, or test count as proof of replacement.

| Logic LEGO | Thought LEGO | Actual capability / next gate |
|---|---|---|
| V01 test obligations and impact | consumer-first, completeness | existing Owner verify, native Nextest discovery; unknown nonempty test targets fail full native gate |
| V02 representation and oracle | independent falsification | independent Note/Audit maps + exact PG peer facts, TS reference, existing Solid generation fence |
| V03 generation | state-machine traces, shrinkability | Proptest std-only dev dependency, bounded trace 1..32, 48 new cases and saved seeds |
| V04 counterexample replay | regression closure | persisted Proptest seeds plus stable concrete command sequences, no replay of real effects |
| V05 native execution | isolation, resource scope | existing disposable PG18 Unix socket/guard; Nextest process-per-test, serialized within shared fixture; precompile/discover before launching one-shot fault carriers |
| V06 physical faults | actual effects versus ACK | native triggers, lock/cancel, COMMIT wire cuts, PID readback; existing R9 primitive and R13 domain cases |
| V07 verdict | PASS/FAIL/SKIP/UNKNOWN distinct | Nextest JSON inventory, fresh JUnit exact identities, no skip/retry/zero test; no success until cleanup |
| V08 consumer | behavioral differential | existing SQLite reference, real Chromium on /operator/grants, native field/identity/late-response assertions |
| V09 nonfunctional | measure not assert uncalibrated timings | move prior R13 timing diagnostic out of correctness path; separate benchmark task is future work |
| V10 integration and evidence | source-bound and natural owner | owner verify:target, native tool version/run IDs and report digests; root CI/release acceptance remains independent |

P0 completed source candidate: 4 independently named original PG tests,
generated trajectory test and stable regression test (6 named tests);
test support reuses exact existing isolated fixture. Native report consumer
rejects ignored/deselected obligations, unknown nonempty target, missing
or stale report (unlink before launch), mismatched identities/counts and
nonpassing/flaky verdict. It is not a custom test execution framework.
Report PASS is a suite verdict, overall qualification only after wire
fault confirmation and native cleanup. Full target must discover all Rust
test targets, empty lib test binary is allowed, newly nonempty target is
an explicit obligation to integrate, not silently discarded.
Focused --lane native/stateful is not full target PASS. Requires isolated
worktree per run (JUnit paths scoped to worktree; no concurrent runs in
same worktree). Native process timeouts are not a claim of server statement
deadlines. Disposition remains UNKNOWN on lost Runtime execution evidence.

Independent model: maintain plain BTreeMaps keyed separately by Note and Audit
identities, no production helpers for expected facts. Generated operations:
execute, observe arbitrary/known, publish imported row, remove/corrupt audit,
insert orphan, list. After each step compare both principals, raw Note/Audit
rows and counts, plus exact observation when invoked. UUIDs are controlled
fixture identities, not authorization. This is bounded sequential modeling,
not proof of all interleavings; native concurrency tests cover distinct named
fault cases. 3 shrink-derived regression sequences: one-step cross-principal
leak, two-step shared audit identity, two-step orphan plus execute. Saved
seeds versioned; explicit minimized sequences survive generator evolution.
Mutation kill requires actual native assertion and fresh JUnit failure;
compilation/timeout/fixture failure not a kill. No global mutation-score
claim. Avoid fork/timeout/bit-set proptest features since Nextest owns process
lifecycle. Exact lock retained; no production dependency changes.

Execution (Linux with native PG18, Rust, Nextest >=0.9.143, Node/pnpm,
matching Playwright Chromium and native Clippy/rustfmt):
```sh
cd apps/web
# provision locked browser if missing, using existing Playwright tooling
pnpm --dir experiments/solid-grants-r3 install --frozen-lockfile --ignore-scripts
pnpm --dir experiments/solid-grants-r3 exec playwright install chromium
mise run verify:target
# focused native source qualification, not whole target
pnpm run test:pg-domain
```
Browser path is caller-owned (PLAYWRIGHT_BROWSERS_PATH if a private XDG
cache is used); missing runtime or browser is failure, never skip. Existing
portable web:verify remains unchanged; root required CI must explicitly
consume verify:target after native environment and selector qualification
by root owner. Do not silently strengthen root job prerequisites without
cross-owner review. Actual authenticated Rust route and full PG schema,
cross-owner consumer, physical authenticator, production and installed
release remain unqualified. Next: independent multi-seed discovery,
concurrent state-machine/linearizability model, schema migration/restore
qualification, full Effect/Grant/Approval model, browser lifecycle, formal
model-to-native refinement, mutation automation in isolated job, and
cost/flake observation. Adopt mature upstream tools only as real consumers
require, no universal test registry.

References: https://proptest-rs.github.io/proptest/proptest/failure-persistence.html ;
https://www.nexte.st/docs/design/why-process-per-test/ ;
https://www.nexte.st/docs/features/retries/ ;
https://nexte.st/docs/machine-readable/junit/ ;
https://mutants.rs/timeouts.html .


## R15 — Concurrent history and native isolation qualification

Host Work@34, shared verification spec #32838, scope #32888; exact composed
source b9864a34 (R14 plus main a888290e). No root CI or other Owner changes.

| Logic LEGO | Thought | Capability and actual evidence boundary |
|---|---|---|
| V11 operation history | linearizability, causal partial order | Rust call/return event stamps, exact complete responses, no clock-duration claims |
| V12 sequential oracle | representation-first | separate clean Note/Audit maps and projected list semantics, no production transition helpers |
| V13 refinement check | Wing-Gong bounded history search | exhaustive precedence-respecting permutations, response and final fact equality; bound eight operations, actual history length four |
| V14 concurrent generation | falsification | existing Proptest, two actual seeds, overlapping writes + concurrent observation + final list |
| V15 deterministic scheduling | native effect evidence | PostgreSQL advisory locks, unique-index transaction-ID waits, actual Audit relation lock; poll witnessed state, not assumed timing |
| V16 isolation counterexample | snapshot consistency | peer atomic Note/Audit commit between two observable read statements; Repeatable Read passes, Read Committed native mutant returns Mismatch |
| V17 verifier qualification | independent negative control | stale nonoverlap, legal overlap, duplicate success, wrong final state; remove precedence guard and native test must reject |
| V18 evidence and cost | no repeated framework | existing Nextest strict discovery/JUnit, required concurrent profile, no new production/test dependencies |

R2.1 I finite complete admitted call history and independently observed
terminal facts; O valid linearization order or no witness; S clean Note/Audit
maps, disjoint operation coordinates; pre unique invocation/response stamps,
<=8 calls, no external modifications in generated history; post a witness
matches all results, real-time precedence, final facts; inv no unknown result
translated into collision, no hidden writes or inferred authority; eff
isolated test database only; c bounded factorial search, four calls at
most 24 total permutations before precedence/response pruning;
epsilon bounded generated operation shapes, not all database schedules,
not full domain or crash/unknown linearizability, cancellation tested
separately by R13/R14. Native fixture errors fail qualification, not an
observed business rejection. prov exact Git, Nextest report IDs/digests,
Runtime receipts, two explicit seed runs; unfold generator -> native calls
-> independent history/model and final peer facts -> finite search.

Real identity race controls: first transaction holds a native advisory lock
after INSERT Audit; second transaction waits on transactionid, confirmed
by pg_stat_activity. Test both same Note/different Audit and different
Note/same Audit. Independent precommit counts zero; release lock, first
success, second SQLSTATE23505, exact single Note/Audit and mismatch for
loser. No sleep used as proof; bounded polls only to await witnessed state.

Snapshot control: peer obtains ACCESS EXCLUSIVE on Audit, inserts both
facts within one transaction. Observer reads old Note, then blocks at
Audit SELECT; peer verifies actual query lock wait and commits. Under
Repeatable Read observer returns Unobserved, new read returns Exact.
Read Committed mutant returns Mismatch despite both facts atomically
committing. Restore production source unchanged. This is a consumer-level
coherent observation guarantee, not a claim that all PG transactions
are linearizable or all externally mutated history is clean.

Existing R14 corrupted historical-state oracle remains independent because
it has a different precondition/transition set. Do not prematurely merge
it with clean concurrent history model. Use no generic checker service.
For larger histories consider mature linearizability engines, compositional
partitioning only when cross-coordinate independence is established. Future
work: model pending/unknown outcomes explicitly, generate multiple waves and
fault schedules; independent oracle and cross-owner qualification, schema
migration/restore and actual Effect/Grant/Approval domain. Root CI and
production Rust HTTP/physical authenticator remain separate gates.

Reproduction:
```sh
cd apps/web
pnpm run test:pg-domain
# focused not whole-owner qualification:
WEB_NOTE_CONCURRENT_SEED=20261127 python3 -B crates/web-note-pg/tests/run_native.py --lane concurrent
mise run verify:target
```
References: https://onlinelibrary.wiley.com/doi/full/10.1002/cpe.3928 ;
https://www.postgresql.org/docs/18/transaction-iso.html ;
https://proptest-rs.github.io/proptest/proptest/failure-persistence.html .


## R16 — full PG owner representation and offline migration candidate

Host Work@35, #32988 and shared verification #33017, R15 composed
becedb2c. First remove the repeated reduced fixture/schema bottleneck before
expanding Effect/Grant/Approval authority. No legacy SQLite mutation.

| Logic | Thought | Actual capability |
|---|---|---|
| M01 owner schema | representation-first | schema/owner-v1.sql, all 11 tables/8 explicit indexes, PK/FK/CHECK |
| M02 source acquisition | consistent snapshot, raw representation | migration/sqlite-export.ts, caller-owned read-only SQLite WAL, one read transaction, actual storage class/hex bytes |
| M03 compatibility | reject nonrepresentable; no silent coercion | migration_schema.rs static ordered columns, raw typed Cell, UTF8/NUL/safe JS integer/nullability/key ordering |
| M04 target binding | natural owner, isolation | explicit matching empty UTF8 schema, no temp namespace, local search_path, caller-exclusive carrier |
| M05 import operator | reuse native bulk transfer | tokio-postgres BinaryCopyInWriter, COPY FROM STDIN BINARY per table in FK order, count and exact readback after constraints |
| M06 observation | exact evidence | read_snapshot in caller-owned consistent transaction, no JSONB normalization, C byte ordering |
| M07 failure and recovery | atomicity, UNKNOWN distinct | rollback DDL and rows; commit/rollback unknown errors; no automatic retry |
| M08 restore | genuine consumer, recovery-first | native pg_dump / pg_restore fresh private database; restored full snapshot; actual Rust Note create/observe |
| M09 falsification | independent native effects | strict Nextest migration lane, actual old SQLite schema, independent byte SQL/index inventory, malformed/FK/CHECK/trigger omission/mutation, empty snapshot |
| M10 writer cutover | single authority | NOT qualified: source freeze, durable manifest/digest, real live census, resource bounds, security/permissions, writer switch and recovery |

R2.1 I=typed ordered complete source snapshot, explicit destination schema;
O=acknowledged exact install or typed error/UNKNOWN; S=caller-exclusive
maintenance connection/empty schema; pre=quiesced source for cutover,
read-only source connection UTF8, destination UTF8 empty/exclusive,
no temp namespace, source representability; post=all table rows exact after
COPY/constraints and COMMIT; inv=never overwrite existing schema, no
automatic replay, no partial commit in tested precommit failures;
eff=local PG DDL+COPY; c=one bulk COPY per table, whole snapshot in memory
and final readback O(rows/bytes), no production throughput claim;
epsilon=no live data, no arbitrary hostile DDL, no durable migration manifest
or source freeze orchestration, no TLS/role/ACL recovery qualification,
connection owner must discard uncertain/cancelled carriers, no proof of
source semantic validity solely from byte identity; prov=native tests/Git;
unfold=SQLite raw types->typed snapshot->static schema->COPY->exact readback.

Preserve TEXT even when JSON-looking (historical exact receipt/audit bytes
and duplicates must remain visible), BYTEA for credential, BIGINT validated
safe-JS integer, original NULL vs empty, explicit C ordering matching
tested SQLite BINARY UTF8. SQLite storage classes are independently
observed; malformed historical values are refused, never repaired during
transfer. A complete empty snapshot is valid; a missing table is not.
Source export uses SQL hex before JS string decoding to preserve invalid
UTF8 for explicit refusal. Actual on-disk synthetic source uses original
WebStore schema and independent read-only connection, 21 rows in all 11
tables. Source unsafe integer and REAL rejected before import; target six
malformed and three FK/CHECK faults rejected; native COPY row suppression
and mutation detected and all relations rolled back. Restored exact rows
then actual PgNoteStore creates one Note/Audit only, all other tables equal.

Use native pg_dump/pg_restore of disposable fresh database; archive includes
public schema DDL, so remove only template-created empty public in private
restore fixture. Do not use --clean on a populated destination. Archive
does not qualify production role/ACL preservation. Target qualification
includes migration lane by default; focused lane is not full target PASS.
Native mutation: removal of exact readback or native quota CHECK killed;
isolated count-check removal survived because exact readback still catches
omission (defense in depth, not reported as kill).

References: https://sqlite.org/datatype3.html ;
https://www.postgresql.org/docs/18/collation.html ;
https://www.postgresql.org/docs/18/sql-copy.html ;
https://www.postgresql.org/docs/18/app-pgdump.html ;
https://docs.rs/tokio-postgres/latest/tokio_postgres/binary_copy/index.html .

Next: actual PG Effect create/publish and Grant/Approval transaction using
this schema, original owner-admitted context and R9 lock ordering. Do not
create a second Security/OPA authority. Then real authenticated HTTP
composition, streaming import and digest receipt/cutover rehearsal with
actual source census, cross-owner independent review and root CI.


## R17 — Native PG Effect and cooperating authority writers

Host Work@36, #33057 (Effect), #33088 (verification handoff), #33091
(cooperating writers). R16 exact 633e461f; fetched main 4d85a831 already
ancestor, no extra source delta. Do not implement second authorization or
repair SQLite. Reuse the full R16 schema, R13 pool lease, R9 advisory/row
lock order, R14 mandatory native discovery and R15 concurrency evidence.

| Logic | Thought | Actual capability |
|---|---|---|
| E01 admitted request | representation and natural owner | EffectRequest, GrantFence, EffectOperation, caller-held UUIDs |
| E02 identity | exact replay before mutable authority | PG transaction advisory try-lock, fresh READ COMMITTED receipt |
| E03 mutable Grant | version and scope fence | row NOWAIT, validated raw row, revision CAS, safe integer quota |
| E04 effect-bound Approval | single consumption | explicit binding and live expiry, Approval/Note NOWAIT, publication only |
| E05 business writes | atomic owner-local effect | native note create/publish, quota, receipt and audit |
| E06 observations | evidence first | exact raw receipt/audit/Grant/Approval and Note after deferred constraints |
| E07 lifecycle | no implicit retry or false ACK | shared owner_write, terminal lease reuse, typed BUSY/UNKNOWN |
| E08 pending registration | revalidate after asynchronous STEP_UP | same identity then Grant lock, immutable pending binding, expiry refresh and final exact observations |
| E09 verified approval writer | terminality / credential binding | same identity, live pending and Principal/credential binding, closed receipt/consumed guard, exact readback |
| E10 revocation | single authority writer | Grant-only NOWAIT row lock, exact revision update + caller-held audit identity |
| E11 verification | independent falsification | actual old SQLite reference, generated model, two-writer histories, native trigger/ACK faults, mutation checks |
| E12 integration | consumer and authority boundary | actual Rust HTTP/Security/WebAuthn/Grant issuance NOT implemented here |

Effect lock order: identity -> fresh receipt -> Grant -> Approval -> Note.
Pending order: identity -> receipt -> Grant -> pending. Approval refresh
order: identity -> receipt -> pending -> credential SHARE -> Approval.
Revoke only locks Grant; never acquire Effect identity after Grant.
All writer paths cooperate; advisory hash collision can conservatively
yield BUSY and must not imply noncommit. READ COMMITTED fresh statement
snapshot after identity lock, no retry. Replay verifies actor/digest/action/
resource, retains historical receipt even after grant change; no claim of
historical audit authenticity. Native API is a trusted internal persistence
boundary; upstream authenticates Agent/Principal, recomputes content digest,
binds concrete request and policy decision, supplies time/TTL. Risk policy,
physical credential verification, and HTTP wire adapter remain Security /
Web consumers; raw result_json is storage evidence, not HTTP response shape.

R2.1 I=admitted typed intent/selected grant and caller-held identities;
O=new or replay receipt, pending/approval/revocation result, typed error
or UNKNOWN; S=R16 tables and R13 bounded pool; pre=trusted caller, all
writers follow lock order, appropriate admission/context; post=acknowledged
exact intended new rows or verified historical replay, approval consumed
once, quota decremented once; inv=no terminal reopening, no automatic
retry, no success on uncertain commit, exact observations after deferred
triggers; eff=local PG only; c=per-identity and per-row conflict isolation,
no measured production throughput claim; epsilon=not full linearizability,
not arbitrary hostile DDL or uncooperative writers, caller timestamps must
be trusted, durable cross-process prepared intent and authority UNKNOWN
observation/cancellation require additional composition; prov=jobs and Git;
unfold=request->identity/Grant/approval->write->exact observation->commit.

New internal pending transition deliberately rechecks mutable Grant/receipt
under lock and returns AlreadyCommitted for exact replay; no refresh of a
committed effect's pending row. Verified approval rechecks live pending
inside the write and credential belongs to Principal, which is stronger
than the old split caller/SQLite storage API; does not perform WebAuthn
or establish credential revocation policy. Revocation preserves the old
explicit repeat semantics when using a fresh audit ID; duplicate audit ID
fails atomically, never increments revision twice on same identity. No
automatic replay. Full authority ACK reconciliation and later credential/
Grant issuance writers must be separately qualified.

Verification: actual old SQLite reference selected 11 create/publish
outcomes/five projections, including wrong approval digest + foreign
actor priority; native independent model seed20261126 48 fresh+1 replay
49 histories/663 commands plus fixed one-step regression. Model originally
found binding-before-approval divergence, corrected to original approval
fence priority. 32 two-writer histories/64 actual calls (same identity
different Grant, different identities same Grant), four independently
held lock types, 8 native effect trigger faults, actual native COMMIT ACK
loss followed by observation and explicit replay. Subsequent actual
pending/approval/revocation writer lifecycle, three authority trigger
faults with all 11 table facts unchanged, real refresh/publication and
revoke/commit races. 8 named mandatory effect tests in split fixture/
contract/concurrent/model/authority modules. Targeted source mutants
identity lock, Grant revision, deferred fence, Approval readback, pending
Grant readback, credential Principal and pending expiry all killed by
native test assertions, not compilation or setup failure. No global
mutation percentage or exhaustive proof.

External foundations: PostgreSQL 18 transaction isolation, explicit locking,
application consistency https://www.postgresql.org/docs/18/transaction-iso.html
https://www.postgresql.org/docs/18/explicit-locking.html
https://www.postgresql.org/docs/18/applevel-consistency.html .
Retain existing Proptest/Nextest with locked compatible resolution.
serde_json moves from dev to actual domain dependency without new package
or lock delta. No old WebStore source or JS lock changes.

Next P0: native Grant issuance/digest and read projection, coherent
authority UNKNOWN observation and actual security/authenticated Rust HTTP
composition; native session/challenge/DPoP and credential consumers;
root CI/native prerequisites, real migration freeze/single writer, and
independent natural-owner review before production. No root CI or
production cutover claim.


## R18 — Grant identity, lifecycle and coherent authority observation

Host Work@37 #33098; verification handoff #33113. R17 a8a9f3a1
plus fetched main ca1b34e6, composed 950e8373. No legacy repair or new
authorization authority.

| Logic | Thought | Capability |
|---|---|---|
| G01 Grant identity | representation-first | GrantCreate / PreparedGrant; fixed v1 field order, SHA256, UTF16 normalize |
| G02 issuance | atomicity | native insert and exact issuance audit under shared owner_write |
| G03 projection | typed refinement | GrantRow checked decoding, GrantSnapshot and fence |
| G04 selection | natural owner | principal listing, candidate scope match, explicit ambiguity, no risk decision |
| G05 issuance observation | historical evidence | RR snapshot, original immutable fields and exact audit, current mutable projection |
| G06 revocation observation | recovery first | retained audit UUID/binding/time, exact audit and currently inactive Grant |
| G07 authority view | coherent observation | pending/approval/receipt in one read-only RR snapshot |
| G08 verification | independent falsification | actual SQLite vectors, native writer races/trigger/ACK and forced interleaving |
| G09 integration | consumer-driven | actual R17 Effect consumes newly issued Grant |
| G10 next | security boundary | Principal/Credential/Session/Challenge/DPoP, authenticated HTTP, durable operation receipts |

Preserve legacy v1 ordered JSON serialization, not RFC8785 object-key
sorting. Precompute UTF16 keys once per list element, sort/dedup and
serialize with serde_json, use existing sha2 0.11 graph as direct dep.
No custom cryptographic algorithm. Grant digest excludes mutable quota,
revision and active, so it is NOT a digest of current authority. Reject
nonrepresentable values; Rust UTF8 has no lone JS surrogates, NUL in
identity text/actions rejected, integer safe range, canonical resource
prefix and recognized risk class. Caller owns admission/digest context.
No extra risk policy or new public API. Selection deliberately includes
exhausted matching grants when deciding ambiguity, as original does;
a later commit enforces quota under row lock. Decode all candidates before
scope selection, even corrupt nonmatching candidates must not disappear.

Grant issuance exact postconditions after deferred constraints; duplicate
identity is a native conflict, not hidden replay. Caller holds prepared
row+audit UUID before await. Observation checks original immutable raw
projection and exactly one matching issuance audit (including wrong audit
coordinate and duplicate evidence). Once revision advances, original
quota cannot be reconstructed by the legacy audit/digest. Revocation
checks exact original event identity/fields and inactive matching grant
with current revision greater than supplied fence; no reconstructed
historical revision. Missing audit is UNOBSERVED, not proven failure.
Pending/approval are refreshable; coherent current view never asserts
an individual historical write committed. Receipt validation uses existing
R17 actor/digest/action/resource binding and principal, not authentication.

R2.1 I=trusted Grant request/prepared identity or retained observation
coordinate; O=exact snapshot/typed result/error/UNKNOWN; S=R16 full schema
R13 pool R17 writer; pre=trusted authenticated caller, representability,
all writers cooperate; post=acknowledged exact new grant/audit or read-only
coherent evidence; inv=no hidden retry, no duplicate issuance, no
current-state-to-history inference, no silent corrupt candidate removal;
eff=local PG; c=precomputed UTF16 sort, native indexes and snapshot,
issuance audit duplicate lookup may need dedicated partial index after
real workload census, no production perf claim; epsilon=not cryptographic
admission, not all JS strings, no historical original quota or historical
revocation revision proof after later writes, pending/approval have no
immutable operation receipt, no arbitrary hostile writer/DDL; prov=Git
and native JUnit; unfold=identity->issue->select->effect->revoke->observe.

Six added named native tests in the existing effect lane: 32 actual old
SQLite reference vectors with Unicode astral/BMP order, combining
characters, control escape and safe JS integers; exact normalized JSON,
SHA256, audit bytes and projections; actual newly issued Grant consumed
by Effect/revoke; 4 native trigger faults rollback, competing Grant ID
one winner, duplicate audit mismatch; native issuance and revoke ACK loss
via separate one-shot native wire proxies; coherent authority view and
foreign principal rejection. Forced native table lock proves second read
waiting while peer commits pending and approval atomically: old complete
snapshot, then fresh new complete snapshot. Five targeted mutants
(UTF8 instead of UTF16, skip issuance row readback, skip issuance audit
readback, skip revocation audit match, RC instead of RR observation)
killed by actual native assertions. No global mutation score.

Reference: https://www.rfc-editor.org/rfc/rfc8785.html
https://www.postgresql.org/docs/18/transaction-iso.html
https://www.postgresql.org/docs/18/sql-set-transaction.html .
Next actual Principal/Credential, Session/Challenge/DPoP and authenticated
Axum/Tower consumer; qualify durable prepared intents, authority receipts,
root CI, full source freeze and single-writer production migration. Independent
Security/Data/Verification review not yet received.
