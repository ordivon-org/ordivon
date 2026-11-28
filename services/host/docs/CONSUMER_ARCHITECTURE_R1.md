# Host Consumer Architecture R1 — bounded decision and source readset

Status: historical source/consumer architecture evidence, **not a second API/schema authority or installed-service inventory**.
Historical design baseline (not current `origin/main`): d16820900f1d74bcfef512f0f009d4cfbd99b06a
(2026-11-16). Installed service/current Connector must always be observed independently.

## 1. Problem and real consumers

The hard problem is **Agent semantic continuity with bounded read cost and
recoverable collaboration**, not a universal task scheduler or execution engine.

| User story | Consumer | Host output | External acceptance owner |
| --- | --- | --- | --- |
| Resume interrupted work | Agent/Harness | current WorkSnapshot + revision | Harness trajectory, native effects |
| Independent peer takes over | second authenticated Agent | Work+Attention+Topic coordinates | actual independent principal and owner readback |
| Parallel discussion and challenge | multiple Agents | Space/Topic/Message/Relation | original author, reviewer, domain owner |
| Discover relevant new activity | subscribing Agent | rebuildable Attention delta | consumer verifies and ACKs processed page |
| Finish or archive | Agent/operator | Work terminal CAS; archived Topic navigation | source/runtime/domain completion checked separately |
| Detect API drift at release | Gateway/connected clients | native MCP input/output contract | official MCP SDK tools/list and receiving client |
| Operate and recover service | operator | PG integrity/pool stats; restorable evidence | PG, pgBackRest and installed release |

A Work is a **semantic checkpoint**, not a Runtime Job. Message assertions
do not establish Git, external provider or domain truth. ActorRef is not a
verified Principal; Subscription is not assignment; Attention is not a queue.

## 2. C4 level-2 ownership boundaries

```text
Authenticated Agent / Human / Harness consumer
                 |
              Gateway (routing and current access decisions)
                 |
                MCP
                 |
 Host:  Work    Social     Attention  [one PostgreSQL authority]
         |        |            |
         +--------+------------+
                PG 14
                 |
      referenceRefs / message targetRefs
                 |
 Owner-native read: Git / Runtime / Artifact / Security / Domain
```

An external reference points to an Owner, **never** grants Host an external
write or lets Host attest the foreign fact. Gateway is a projection rather than
a second Work writer. The native PostgreSQL schema is owned by Alembic.

## 3. Source-grounded design structure matrix (DSM)

Edge semantics: `A -> B` means A depends on B's public responsibility or
canonical rows, not that A may use B's private implementation.

| A | B | Evidence | Decision |
| --- | --- | --- | --- |
| MCP adapters | WorkStore, SocialStore, AttentionStore | mcp_tool_registration.py | Keep thin composition |
| WorkStore | PostgreSQL works/work_snapshots/receipts | work_store.py | Keep native transaction/CAS |
| WorkStore | WorkReadQueries / WorkRelationCommands | explicit native checkout composition | Preserve internal DAG command, no additional MCP route |
| Work mutation and relation command | conn-scoped ActorRef / WorkRef checks | references/actor_refs.py, references/record_refs.py | Explicit reference prerequisites, no MRO or IAM decision |
| SocialStore | PostgreSQL topics/messages/relations, WorkRef lookup | social_* | Keep one social write authority |
| Attention projections | existing Work/Social owner rows + subscription/cursors | attention_sql.py | Keep rebuildable SQL, no extra event store |
| Gateway | Host published tools/contract | installed Gateway and MCP server | Contract-test real SDK input/output |
| Harness Agent | Work+Topic+Owner-native readback | existing Golden Road Work | Independent consumer proof still missing |
| Host references | Runtime/Git/domain by navigation only | work_inputs.py referenceRefs | No coupled foreign Owner write |

Observed dependency hub is PostgreSQL, intentionally. Attention reads Work
and Social canonical rows; it must not maintain a second durable inbox. No
dependency cycle justifies a new coordinator or abstract repository layer.

## 4. Architectural decisions / rejected alternatives

- **D1—One semantic Writer:** Work, Social and Attention are distinct logical
  responsibilities backed by one Host PG. No Task/Board/Workflow/Agent scheduler.
- **D2—Checkpoint-first:** Work contains current objective/frontier/unknowns
  and references. Full social history belongs in Topics; exact external proof
  belongs with its natural Owner. Historical Work revisions are optional.
- **D3—Two cursors:** Attention change sequence discovers relevant owner rows;
  Topic message sequence resumes a conversation. ACK only after the respective
  page has been processed; neither ACK implies domain success.
- **D4—Contract-based delivery:** MCP Tool name equality is insufficient.
  Keep `mcp-surface.json` as the existing release manifest and derive the
  complete schema digest from **official SDK tools/list**. Changed input/output
  contract requires new epoch/version, immutable-release verification and
  connected client re-discovery; no new public Tool or schema registry.
- **D5—Identity split:** Host M2M bearer verifies workload transport, not the
  person/Agent identity or per-object Security grant. The currently installed
  compatibility ingress is a transition state; do not claim unified principal.
- **D6—Lifecycle before purge:** Work completed/abandoned and Topic archived
  remove active navigation clutter; PG physical deletion requires actual
  consumer release and restore evidence. No age-only GC.

## 5. Failure modes and acceptance

| Case | Failure oracle | Native verifier |
| --- | --- | --- |
| Concurrent Work update | stale expectedRevision cannot overwrite latest | Host PG integration / Work CAS |
| Topic archive | archived rejects post but resume/get restore bytes | PG lifecycle tests, real SDK client |
| Attention page | cursor skips unseen relevant event | TLA+ finite model and PG consumer test |
| MCP schema change | tool names equal but signature differs | release gate + native SDK negative test |
| Agent reentry | second Agent loses evidence or repeats effect | independent authenticated end-to-end consumer |
| Source vs deployment | local main/manifest newer or older than current service | exact Git SHA + installed tools/list + Host status |
| Credential migration | Gateway positive passes while unauthorized call also forwards | real Gateway/Security positive+negative consumers |

An official SDK source verifier does **not** force a remote ChatGPT connector
to refresh an older captured tool signature. That is a separate installed
consumer acceptance.

## 6. Narrow LEGO decision

**Thought LEGO:** DDD bounded context; PostgreSQL MVCC/linearization;
causal ordering; information bottleneck; source-to-implementation refinement;
consumer-driven contracts and explicit UNKNOWN.

**Logical LEGO:** Work continuity; Social causality; Attention re-entry;
API contract currentness; lifecycle. These are responsibilities, not filenames.

**Capability LEGO:** existing PG transactions/constraints, Psycopg pool,
Alembic, official MCP SDK, Pydantic, bounded queries, native Git source
fencing, pytest/Hypothesis, TLA+/Lean/Z3 on selected properties.

Schema-currentness release responsibility (declared local contract, not a new
global calculus or independently proven formal LEGO):
- Inputs: immutable candidate Host release, installed baseline manifest, native MCP tools/list
- Results: accepted release contract or typed/terminal schema drift failure
- State: current/candidate manifests and SDK tool model; no second database
- Assumptions: source and package identity fixed, tools discoverable
- Required behavior: acceptance implies matching manifest/tool schemas and advanced epoch/version if changed
- Preserved properties: names alone cannot permit input/output drift; old missing digest is changed
- Effects: read-only SDK introspection and pre-symlink rejection; no production mutation
- Resource observations: UNKNOWN(runtime cost on actual deployment; obligation: measure if material)
- Limits of the claim: UNKNOWN(stale external client capture; obligation: real Agent re-discovery)
- Evidence: source at stated Git cut, native test output, manifest, installed observation separately
- Implementation and verification: SDK tools/list → schema projection → digest → versioned manifest → installer gate → consumer readback

## 7. Executable work and stop conditions

**P0** Release schema fidelity: implement and test native SDK contract gate;
verify real consuming client schema after new deployment or recapture.
**P0** Efficient long-Topic delta re-entry: the native `attention.delta`
event `sourceRef` already supports direct `message.get` without paging a
zero-cursor historical Topic; do not acknowledge unprocessed Topic history.
The current Skill `.agents/skills/task-space-reentry/SKILL.md` and Owner Guide
carry the consumer method (live read-only R18 subscription verified
2026-11-16). Do not add another Host inbox or new MCP Tool.
**P0** Independent Agent handoff: two genuinely distinct authenticated
principals, Work→Attention→Topic→owner-native readback→CAS, measure missed
facts, tool calls and model context.
**P1** Snapshot cost: current large Work payloads are consumer-owned; do not
drop facts without a consuming Agent-approved compact checkpoint.
**P1** M2M/Principal: migrate real Gateway/Cloudflare consumers on Security
Owner terms, then remove installed legacy direct-HTTP compatibility.
**P1** Rust candidate: prove compatibility with production PG14 archive,
recovery, tools/list, identity, and single Writer prior to replacement.
**P2** Legacy WorkRelation/CoordinationIntent, overlapping Spaces, old
documents, history GC: require actual consuming roots and current facts;
do not infer deletion authority from zero table rows.

Stop decomposing when a proposed split has no independent consumer, does not
reduce observed coupling or can be satisfied with existing mature Owner API.

Primary source links: `mcp-surface.json`, `src/ordivon_host_v2/`,
`docs/SOCIAL_WORK_FABRIC_R2_SPEC.md`, `docs/HOST_OWNER_GUIDE.md`,
`packaging/verify_release.py`, existing PG and native MCP tests.


## 8. R26 source-grounded DSM and proposed **internal** file boundaries (2026-11-16)

Standing: **INVESTIGATED / PROPOSED, NOT REFACTORED OR DEPLOYED**.
Git SourceCut: \`659e526e60bd6bf02ed068fa92be49819a12e4c4\`.
Production sampled separately: PostgreSQL Schema14, Host Doctor 8/8.
Method: Parnas information hiding, bounded-context vocabulary, exact Python AST
direct-import DSM, static SQL/table-reference scan, explicit inherited-method
lookup, Git history change-coupling, and cross-Owner source-path consumers.
Static import topology does not prove runtime coupling absent.

### 8.1 Structural measurements and their limits

- Host Git inventory **125 tracked files**, of which 36 non-\`__init__\` Python
  owner package modules (~4,874 source lines); tests **38 tracked files**.
- 100 directed intra-package static imports, **zero nontrivial import SCCs**.
  Grouped AST imports: social-to-social 20; social-to-shared 19;
  transport-to-transport 8; work-to-work 5; attention-to-social 1.
- Most imported: \`canonical_json\` 14, \`errors\` 13,
  \`social_errors\` 9, \`command_receipts\` 7. Most imports made:
  \`social_store\` 8, \`work_store\` 8,
  \`mcp_tool_registration\` 7. Common imports are not automatically bad.
- File line concentration: social-labelled modules 2,072; transport 1,048;
  Attention 689; Work 636; DB 79; shared 350 (heuristic name groups, not a
  verified DDD context count).
- Recent Git source changes since Nov 1: 40 commits touched owner Python
  module paths (includes legacy renamed/deleted paths), with \`service\` 9,
  \`social_store\` 9, \`work_store\` 8. Co-change does not prove a
  dependency/cause.
- \`social_contracts.py\` defines public wire \`WorkResponse\`,
  \`SpaceResponse\`, \`MessageResponse\`, \`SubscriptionResponse\` and
  \`AttentionDeltaResponse\` in one module: logical domains are mixed in
  a file although it has only three direct import consumers.
- \`SocialStore\` composes **six direct mixin bases** plus \`SocialReadQueries\`
  (itself three read mixins). \`SocialMessageCommands\` calls
  \`_verify_message_content_digest\` and \`_require_message\` implemented
  in **SocialMessageReadQueries** without an explicit import.
  \`SocialTopicReadQueries\` also uses the message digest helper.
  \`WorkStore\` calls \`_get_work_in_tx\` supplied by \`WorkReadQueries\`.
  These are real implicit execution dependencies not detected as import cycles.
- \`attention_sql.py\` is a 162-line SQL query spanning
  \`work_snapshots\`, \`work_relations\`, \`participations\`, \`topics\`,
  \`messages\`, \`message_relations\`, \`coordination_intents\` and
  \`subscriptions\`. This is intentional **read-only projection coupling**:
  isolate/query-test it, **do not** create duplicate event authority.
- \`service.py\` status/Doctor reads canonical rows from all three Host
  responsibilities. It is intentional cross-domain operational integration;
  do not install health as a second writer.
- \`topic_consumption_cursors\` writes are currently in Social topic
  command/query mixins and read in \`attention_projections.reentry\`. The
  cursor ownership seam must be made explicit before moving it.
- \`tests/test_social_work_fabric_postgres.py\` is ~1,520 lines / 26
  top-level test functions spanning Work CAS, social, Attention, topic cursors,
  concurrency and replay; split by **invariant and consumer**, not randomly
  by file length.

### 8.2 Source-path and published consumer boundary

- Current external CLI:
  \`pyproject.toml: ordivon-host-v2-mcp =
  ordivon_host_v2.mcp_server:main\`.
  The existing \`packaging/verify_release.py\` and Repo Owner
  \`tools/repo/check_host_gateway_mcp_consumer_surface.py\` import
  \`ordivon_host_v2.mcp_server.build_server\`. Preserve that explicit
  package entry point **even if internals move**.
- \`planning/lego-plan-r1.json\` names 27 existing Python modules and
  is read by current Repo Owner architecture tests. Filename citations
  also occur in root Owner/docs/formal tests. A broad \`git mv\` requires
  synchronized consumer changes; archived inventory snapshots are
  historical and need not be rewritten.
- \`services/gateway\` retains its own Host MCP forwarding and tool
  schemas; source parity does not establish installed ChatGPT connector
  capture currentness. Transport refactoring **must not rename the 31 Host
  public MCP tools, schemas, HTTP endpoint or native identity policy**.
- Alembic \`0001\`–\`0014\` are immutable migration history, not ordinary
  module folders; no file reshuffle or retroactive SQL rewrite.
- Skills/Harness and authenticated Principal continuity are external Owner
  consumers, not Host source-import dependencies.

### 8.3 Proposed minimal Python **package map** (not a new service fleet)

Retain \`src/ordivon_host_v2/mcp_server.py\` as the stable external
\`build_server/main\` entrypoint. Group the internal modules by change reason
and information hidden, using shallow packages.

| Internal target package | Existing source files moved/refined there | Intended responsibility |
| --- | --- | --- |
| \`kernel/\` | \`canonical_json.py\`, \`collection_pagination.py\`, \`errors.py\` | Pure JSON, byte bounds, typed core errors; no Owner state |
| \`storage/\` | \`postgres_connections.py\`, \`postgres_bounds.py\`, \`command_receipts.py\` | Psycopg connection/pool checkout, PG bounds and transactional receipts; one authority |
| \`work/\` | \`work_inputs.py\`, \`work_queries.py\`, \`work_store.py\`, \`work_relation_commands.py\` | Current Work CAS, bounded discovery, optional relation DAG |
| \`social/\` | \`collaboration_inputs.py\`, \`social_errors.py\`, \`social_store.py\`; \`social_space_commands.py\`, \`social_space_queries.py\`, \`social_topic_commands.py\`, \`social_topic_queries.py\`, \`social_message_commands.py\`, \`social_message_queries.py\`; \`coordination_inputs.py\`, \`coordination_intent_commands.py\` | Space, Topic, Message, Participation/relations and optional internal Coordination Intent; no IAM/Work scheduler |
| \`attention/\` | \`attention_store.py\`, \`attention_projections.py\`, \`attention_sql.py\` | Subscription, Attention cursor, delta/reentry and single-snapshot read view; read canonical Work/Social rows only |
| \`transport/\` | \`mcp_tool_registration.py\`, \`mcp_work_tools.py\`, \`mcp_social_tools.py\`, \`mcp_attention_tools.py\`, \`mcp_domain_errors.py\`, \`http_identity.py\` | Official MCP tool adapters, stable schema and HTTP workload authentication |
| \`operations/\` | \`service.py\`, \`contracts.py\`, \`native_pool_observability.py\` | Host readiness, cross-domain integrity diagnostics and pool observability; read-only cross-domain integration |
| \`{work,social,attention}/wire.py\` | Split **only** \`social_contracts.py\` TypedDict definitions by existing Work/Social/Attention response owner; preserve schema byte-for-byte | Typed wire contracts live near the actual producer and consumer; no new wire schema registry |

These are *candidate locations*, not a requirement to move every file. The
consumer-based partition reduces navigation coupling only **after** hidden
method contracts have been exposed. Avoid creating new Repository/Service/
UnitOfWork interfaces merely to implement this folder layout. Keep package
depth shallow (one bounded-context folder, not three directory layers).

### 8.4 Proposed high-return semantic correction **before any mass move**

1. **Expose inherited provider contracts:** pull message content verification
   into one explicit pure/internal helper used by both Message commands and
   queries and by Topic resume; pull shared \`_require_message\` lookup into
   explicit conn-scoped helper. For Actor/Space/Topic lookups, either use
   explicitly imported conn-scoped functions or retain a documented facade
   with tested declared methods. Do not replace everything with DI framework.
2. **Work CAS readback:** make the existing read-in-tx helper explicitly
   imported/owned rather than depending invisibly on MRO; preserve current
   transaction, response-loss replay, revision, and PG lock semantics.
3. **Separate domain wire types:** move same existing \`TypedDict\` definitions
   from \`social_contracts.py\` into adjacent domain contract modules,
   preserving exact emitted MCP \`tools/list\` input/output schemas.
4. **Cursor ownership:** after independent consumer proof, align
   \`topic.cursor.get/ack\` implementation with Attention consumption
   navigation, while public \`topic.cursor.*\` MCP names and the distinct
   Topic Message / Attention Change sequence types remain unchanged.
5. **Leave the global Attention SQL union alone** until a real PG EXPLAIN,
   missed-event counterexample, or replay consumer demands change. It is a
   read projection with foreign canonical-table inputs, not a second write model.
6. **Retain one process + one PG authority**. No microservices, graph DB,
   custom event store, generic runtime broker, or extra IAM layer.

### 8.5 Safe migration DAG and independent acceptance

- **M0 (architecture/readset only):** freeze git SourceCut; current installed
  PG14, MCP31 schema digest and Gateway/ChatGPT consumer distinctions.
  Audit \`planning/lego-plan-r1.json\`, repo tests, entrypoint, formal source
  paths and every literal source-file consumer before moving anything.
- **M1 (highest-value behavior-preserving refactor):** extract hidden
  \`SocialMessageReadQueries\`/commands digest and readback helpers and
  \`WorkReadQueries\` CAS readback dependency. Verify reply-before-source,
  message canonical digest, Work CAS races/response-loss, topic archive/resume.
- **M2 (wire boundaries):** split \`social_contracts.py\` into domain
  wire files using existing TypedDict definitions. Same SDK 31-tool
  \`inputSchema/outputSchema\` digest and no changed production DB.
- **M3 (internal path regrouping):** one bounded context per change;
  update internal imports, external tests, \`lego-plan-r1.json\` and active
  source-path contracts in the **same atomic Git change**. Stable
  \`mcp_server.py\` remains externally importable. No long-lived aliases if
  direct consumers can be migrated together.
- **M4 (consumer tests/doc cleanup):** split the 1,520-line PG integration
  file into Work, Social, Attention and cross-domain golden-road sections
  with shared existing fixtures; do not delete or replace actual PG tests
  with a pure proof.
- **M5 (optional semantic retirement):** evaluate actual
  \`CoordinationIntent\`/\`WorkRelation\` consumers, live SQL projection,
  PG table retention, migration and restore; retire only with real closure
  evidence. Keep physical message history while external refs remain.

For each M1–M4 source candidate: native \`mise run verify\` (**report DB
SKIPs**); \`mise run test:postgres:disposable\` for real PG/Alembic
and contention; Repo owner \`check_architecture_docs.py\`,
\`test_architecture_docs.py\`, \`check_host_gateway_mcp_consumer_surface.py\`;
official SDK \`packaging/verify_release.py\`; exact unchanged released
MCP 31 tools/schema digest; source/installed/Gateway/Agent evidence separately.
For M1 specifically retain CrossHair reply/revision obligations, Z3/Lean DAG,
Attention TLC only for affected formal properties. Source AST import SCC=0
should stay 0; this is **not** a sufficient acceptance condition.

Promotion stop law: do not move a module until the move demonstrably
reduces hidden assumptions, consumer change blast radius, or ongoing
navigation/test cost. A reorganized directory that only relocates the same
100 dependency edges does not pass this gate. No live migration, Docker
upgrade, schema rewrite, or remote MCP catalog recapture is implied by this
candidate.


## 9. R28 M1 historical source evidence — subsequently merged, not proof of installation

> **2026-11-17 stocktake correction (UTC+08):** M1 was merged as PR #2337 at `bc30e4377fad481846275346e74abf52978cd135`; M2 merged as PR #2347 at `e99aeb7abb3134dc597c65d13bab2d93530479ce`; R30 Space projection merged as PR #2359 at `697f9ec824159ae5effe8a7727ae9b33a8fc5cb5`. These are **source** facts, not installed or consumer-current claims. The live unit `ordivon-host-v2.service` on 2026-11-17 resolved to immutable Git release `10db16a117bf1fd0622a0fca1ecbedea7358c322` (PG schema 14, manifest epoch 7 / 31 tools). That installed release did **not** contain `social_message_records.py`, `work_contracts.py`, `attention_contracts.py`, or `social_space_records.py`. The remote `main` was `5d1721fdd75cea53ee7d3ae023378becaff525c3`, while the separate local root worktree `main` was still `9f98468fc81385fe0361e8fbd624ea289b227932`. Read all three currentness boundaries again before acting; the ChatGPT client-captured archived/includeArchived parameter shapes also require independent verification.


The actual R28 source experiment converts only two cross-Mixin private
execution dependencies, **without moving existing modules or changing DB
schema**:

- `src/ordivon_host_v2/social_message_records.py` owns a pure
  `verify_message_content_digest(row)` and a
  `require_message(conn, message_ref)` query on the **caller's same PG
  transaction**. Message post/replay, relation add, message get/search and
  Topic resume import the exact same helpers. The old private MessageReadMixin
  methods are no longer required on SocialStore. The digest's seven immutable
  fields and RuntimeError text remain unchanged.
- `work_queries.py:read_work_in_tx(conn,work_ref,revision)` is the one
  transaction-bound Work snapshot projection shared by WorkReadQueries and
  WorkStore create/commit; it preserves canonical digest/current pointer
  checks and historical_state_unknown. The inherited hidden
  `_get_work_in_tx` method is removed; the externally available WorkStore
  methods and MCP responses remain unchanged.
- The former `test_social_query_boundary.py` and
  `test_work_query_boundary.py` MRO/private-method location assertions now
  guard explicit helper reuse/public read API and no-duplicate-query-write
  boundaries. All four Work mock-connection digest/refinement examples were
  redirected to the actual new function; new Message helper valid/corrupt
  row and conn-scoped missing-message examples added to the existing test.

**R28 isolated source evidence at head-before-commit** (not an installed
service claim): `mise run verify` **401 PASS, 58 DB SKIP**; locked CrossHair,
Z3 bounded DAG/negative control, axiom-free Lean DAG/Unicode PASS;
`mise run test:postgres:disposable` **459 PASS** on an isolated PostgreSQL
18 container after Alembic migrations 0001→0014. The previous unchanged-main
baseline was 399 source PASS/58 DB SKIP and 457 real PG PASS, so this branch
adds exactly two direct helper tests; it **does not** claim extra database
semantics or a performance improvement. Repo architecture 198 PASS, official
Host/Gateway source tool-name/required/dispatch observation PASS. Native
Host public tools/list complete input/output Schema must remain at the
existing manifest digest; installed Connector recapture and authenticated
principal handoff remain separate UNKNOWN obligations.

**Consumer and review boundaries:** retain `mcp_server.py` public entrypoint,
SocialStore/WorkStore public methods, same PG transaction and lock scope,
`mcp-surface.json` 31-tool/epoch/digest, Alembic0001–0014, Attention's
MVCC-only union and both independent cursors. No generic Repository/UoW,
new inbox/event store, separate identity registry or Rust replacement. At the original R28 candidate cut, the R26 M2 wire/domain package split
had **not yet been implemented**; M2 subsequently merged in PR #2347.
The proposed M3 bulk internal `git mv` remains **not approved** without
source-path consumer review and measured Agent benefit. The prior R26 section is historic design
baseline, not a claim the current source still has those hidden methods.


## 10. R29 M2 domain-owned response wire (historical candidate, subsequently merged in PR #2347)

R28 M1 is now **GitHub MERGED** into main at `bc30e4377fad481846275346e74abf52978cd135`
(PR #2337); this establishes the source baseline, **not** installed production
currentness. The original R29 M2 source candidate, subsequently merged, keeps the flat Python package,
same published `mcp_server.py` entry point and all 31 native MCP Tool functions.
It does not move Work, Social, Attention persistence or modify PostgreSQL/Alembic.

- `work_contracts.py` now owns five existing Work/Actor response TypedDicts.
  `mcp_work_tools.py` imports them directly from their Work owner.
- `attention_contracts.py` owns six existing Subscription/Attention
  TypedDicts. `mcp_attention_tools.py` imports them directly.
- `social_contracts.py` retains fifteen existing Space/Topic/Message/
  Participation/Coordination response TypedDicts; `mcp_social_tools.py`
  remains its actual consumer.
- `wire_common.py` holds only the existing
  `AdmissionWire = Literal["committed", "existing"]` vocabulary. It contains
  no state, validation system, registry, new source of truth, or public Tool.
  The old cross-domain re-export is deliberately not duplicated: an exact
  repo search found only the three native `mcp_*_tools.py` imported response
  types from `social_contracts.py`, and all those imports are updated.
- No TypedDict field, `Literal`, `NotRequired`, default, model type, input
  annotation or return annotation is changed; only the **owning module** and
  imports change. This is narrower than a bulk `git mv` for M3.

**Independent actual candidate acceptance:** after native Ruff-isort repair,
`mise run verify` reported 401 passed + 58 PostgreSQL cases SKIPPED
(these skips are not PG evidence); full standalone PostgreSQL 18 disposable
instance with Alembic 0001–0014 reported **459 passed**; repository architecture
pytest **198 passed** and architecture doc checker passed. The official native
MCP SDK `packaging/verify_release.py` enumerated exactly **31 tools**,
package/server version **0.9.0**, epoch **7**, and exact unchanged
input+output `contractDigest =
sha256:0c3553e4fb9b9134d9e3867e0419d7b119c78b3a55d48463e5d938810b4a2f3a`.
`tools/repo/check_host_gateway_mcp_consumer_surface.py` returned exit0
while still reporting existing 16 shared inputSchema / 30 outputSchema
differences; its source coverage is not a full schema or installed consumer
compatibility proof. Do **not** claim Client tool recapture or two distinct
authenticated principals from this verification.

**Consumer acceptance boundary:** the authoritative Postgres data contract,
MCP tool-name/arguments/output bytes, immutable release manifest, and
Gateway route remain unchanged. If a future domain wire change alters the
native SDK digest, it is an explicit new public contract requiring controlled
version/epoch and installed Agent re-discovery; do not silently hide it via
alias/re-export. This M2 source-level organization does not independently
prove a reduction in Agent model tokens or p95; its intended measurable
benefit is smaller *source-level* domain contract navigation/change radius.

**Remaining:** M3 bulk file moves are not approved absent demonstrated
consumer benefit, accurate source-path closure and formal/prod tests. M4
PG integration test organization awaits consumer-driven evidence. Principal
identity, legacy ingress and Plugin archive parameter capture remain P0
with their natural Gateway/Security/Harness owners.


## R3 Work read composition (2026-11-24)

WorkStore now composes WorkReadQueries with an explicit native connection factory;
readback inside create/commit still uses read_work_in_tx on the caller transaction.
The pure bounded revision successor lives in work_revision_logic.py and the existing
CrossHair source target follows it. Public WorkStore/MCP and PG schema are unchanged.
The older inherited read facet descriptions above are historical.


### R5 Attention explicit read composition

The public AttentionStore surface stays unchanged. It composes three concrete read
capabilities using the existing native connection checkout. Actor and target
existence use the canonical conn-scoped reference lookup; Reentry owns one
REPEATABLE READ, READ ONLY transaction and invokes Delta's transaction-local
query before reading Topic consumption coordinates on that same connection.
No secondary transaction, event authority, routing permission or assignment is
introduced. The obsolete inheritance-only read facade is removed.

R44/R47 synthetic benchmark scripts now inject SQL at the actual executing
Delta module instead of the retired facade. The native PG test intentionally
injects an undefined relation through the benchmark path, checks that both
Delta and Reentry fail, then restores the real query. Prior benchmark measurements
are historical evidence for their source cuts, not fresh measurements for R5.
### R6 Social explicit read composition

The existing SocialStore API explicitly delegates Space, Topic and Message
queries to concrete capabilities using the same native checkout. Canonical
Actor/Space/Topic reference lookups receive the caller-owned PG connection
directly. The inheritance-only SocialReadQueries facade has no independent
state or semantics and is removed. Every public read still owns exactly one
REPEATABLE READ, READ ONLY transaction; command mixins and same-transaction
command readbacks are unchanged. This is independent of Social MCP port
registration (#2589); no public Tool, schema, credential or new read database.

### R6 Social command composition (candidate following explicit reads)

`SocialStore` remains the public write/read facade and owns its native
`HostPostgresConnections` adapter. The Space, Topic, Message and Coordination
Intent command providers each accept the caller's checkout function explicitly;
their ActorRef/record checks call the canonical reference provider on the
same transaction connection. There is no separate writer, transaction manager,
authorization decision or connection pool. The ten read and eight command
methods retain their existing signatures and native MCP contract.

The eight commands' concrete acceptance includes direct and pooled single
checkouts, typed missing-reference failures, successful reuse of a request ID
after rollback, exact receipt replay apart from the existing admission marker,
and opaque external reference versus real ActorRef mention behavior.
`test_topic_message_identity_waits_for_real_pg_topic_no_key_update_lock`
continues to verify the real same-topic ordering fence, independently of
inheritance or source formatting. These are finite implementation witnesses,
not a universal proof or installed production qualification.
