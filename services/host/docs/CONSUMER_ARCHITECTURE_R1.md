# Host Consumer Architecture R1 — bounded decision and source readset

Status: reviewed source design candidate, **not a second API/schema authority**.
Baseline: `origin/main` d16820900f1d74bcfef512f0f009d4cfbd99b06a
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
- `I`: immutable candidate Host release, installed baseline manifest, native MCP tools/list
- `O`: accepted release contract or typed/terminal schema drift failure
- `S`: current/candidate manifests and SDK tool model; no second database
- `pre`: source and package identity fixed, tools discoverable
- `post`: acceptance implies matching manifest/tool schemas and advanced epoch/version if changed
- `inv`: names alone cannot permit input/output drift; old missing digest is changed
- `eff`: read-only SDK introspection and pre-symlink rejection; no production mutation
- `c`: UNKNOWN(runtime cost on actual deployment; obligation: measure if material)
- `epsilon`: UNKNOWN(stale external client capture; obligation: real Agent re-discovery)
- `prov`: source at stated Git cut, native test output, manifest, installed observation separately
- `unfold`: SDK tools/list → schema projection → digest → versioned manifest → installer gate → consumer readback

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
| \`social/\` | \`collaboration_inputs.py\`, \`social_errors.py\`, \`social_store.py\`, \`social_read_queries.py\`; \`social_space_commands.py\`, \`social_space_queries.py\`, \`social_topic_commands.py\`, \`social_topic_queries.py\`, \`social_message_commands.py\`, \`social_message_queries.py\`; \`coordination_inputs.py\`, \`coordination_intent_commands.py\` | Space, Topic, Message, Participation/relations and optional internal Coordination Intent; no IAM/Work scheduler |
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


## 9. R28 M1 narrow implementation evidence — branch candidate, not installed

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
new inbox/event store, separate identity registry or Rust replacement. The
R26 M2 wire/domain package split and M3 internal `git mv` remain **not
implemented**; they require independent review of source-path consumers and
real Agent cost before promotion. The prior R26 section is historic design
baseline, not a claim the current source still has those hidden methods.
