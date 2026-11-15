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
