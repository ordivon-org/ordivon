# Host Owner — current navigation and operational guide

Audit SourceCut: 7d7dcbe087136ae6249cd47524d1f6e33209f3e5 (2026-11-10). Always verify installed Git tree, PostgreSQL schema and current MCP tools independently. This is navigation, not an alternative authority.

## 1. What Host does and must not own

Host retains versioned Work semantic continuity (CAS and immutable snapshots), stable ActorRef references, Social Space/Topic/Message and relations, subscription and bounded Attention/re-entry. Work.completed is Host continuity only, not external Goal fulfillment. ActorRef is not authentication; Participation is not authorization; Attention is not scheduling.

Runtime owns Workspace/Job/Attempt/physical effects; Harness owns Agent-run/tool-step cognition; Gateway owns ingress/routing; Identity/Security owns access policy; Git owns source; domain Owners own real outputs. A Host stored foreign reference is navigational evidence only. UNKNOWN must not become a made-up success or failure.

## 2. Source map and real interfaces

| Concern | Actual Owner implementation |
| --- | --- |
| Work CAS and snapshots | src/ordivon_host_v2/work_store.py, work_inputs.py; reads in work_queries.py |
| Work relation graph | work_relation_commands.py; native PostgreSQL transaction/acyclicity, not global scheduler |
| Social write + read facade | social_store.py, social_space_commands.py, social_topic_commands.py, social_message_commands.py, coordination_intent_commands.py; SocialReadQueries uses three native query facets |
| Social read | social_space_queries.py, social_topic_queries.py, social_message_queries.py |
| Attention change/re-entry | attention_store.py, attention_projections.py, attention_sql.py |
| Shared canonical/receipt/page semantics | canonical_json.py, command_receipts.py, collection_pagination.py, postgres_connections.py |
| MCP and schema | mcp_server.py, mcp_tool_registration.py, mcp_work_tools.py, mcp_social_tools.py, mcp_attention_tools.py, social_contracts.py, mcp-surface.json |
| Schema migration | migrations/versions/0001..0013, Alembic; do not delete historical revisions of migration scripts |
| Build, release and service | pyproject.toml, uv.lock, mise.toml, packaging/install_release.sh, packaging/systemd, packaging/verify_tool_surface.py |

The official MCP tools/list of the running Host is authoritative for published tool availability. Internal WorkRelation/CoordinationIntent Python methods are not necessarily published MCP capabilities. Do not infer internal implementation availability from a source file or an old planning graph.

## 3. Human and Agent work paths

Human:
1. Read host.status(detail=summary|integrity|history). A check may be true for current pointers while old revisions are missing; health is scoped and not Runtime/Git/domain success.
2. Read work.get(current or explicit revision) and topic.resume. Use work.list / space.list / message.search with their native count and byte budgets; paginate with their own cursor types.
3. For source qualification, run cd services/host && mise run verify. For real SQL race, migrations and matching tests run mise run test:postgres:disposable using isolated PostgreSQL18, not production.
4. For real publication, obtain expected Host Git subtree ID independently, use official packaging/install_release.sh source-review argument, verify installed service and tool readback. Commit/CI PASS is not installed evidence.

Agent:
1. Declare ActorRef only as stable semantic reference. Read current Work before submitting expectedRevision CAS update.
2. Recover via work.get, attention.reentry, topic.resume, foreign Owner reference readback, Work snapshot commit and cursor acknowledgement when needed.
3. Attention change sequence is not Topic message sequence; acknowledgement is not domain completion.
4. Referenced Git/Runtime/Artifact/Security/domain claims must be re-read from their natural Owners.
5. Every genuinely declared R2.1 LEGO has 11 typed coordinates; ordinary files do not become LEGOs. Prefer DELETE custom -> mature reuse -> compose before new implementation.

## 4. What is live, what is history

- Current constraints are the checked-in Python/SQL, Alembic schema and native MCP public surface, not old numbered design receipts.
- The historical Social Work Fabric R1 description remains marked as historic. The R2 semantic specification is docs/SOCIAL_WORK_FABRIC_R2_SPEC.md; for historical implementation detail refer to docs/SOCIAL_WORK_FABRIC_R2_IMPLEMENTATION.md and exact Git revision.
- planning/lego-plan-r1.json remains in use by the **repo-wide** graph verifier despite its R1 label; planning/lego-plan-r3.json is a current Host responsibility projection. Neither is a new registry.
- The historical Host friction measurement originally at planning/host-friction-observatory-r1.json has been retired from the current source tree. Original immutable content: Git blob a5503d5be27a121b7b9a3d5fa2088ea44cac4c79, committed at SourceCut 7d7dcbe087136ae6249cd47524d1f6e33209f3e5. Read via git show 7d7dcbe087136ae6249cd47524d1f6e33209f3e5:services/host/planning/host-friction-observatory-r1.json. The old numbers are not current Host measurements.
- docs/HOST_R21_AGENT_EXECUTION_SPEC.md is the file-by-file modernization audit and docs/HOST_R21_AGENT_EXECUTION_PLAN.md is its bounded execution plan. Neither is external effect authority.
- Real PostgreSQL Doctor may report missing Work revision history. Do not fabricate old snapshots or delete navigated terminal Work identities to make this warning disappear.

## 5. Existing formal verification, not a second implementation

Existing commands: mise run formal:reply-source, formal:work-graph (bounded Z3 with negative control), formal:dag-theorem (general Lean Work DAG law), formal:unicode-search (Lean necessary-gram theorem). Proof implementations are formal/work_graph_dag.py, formal/HostWorkDAG.lean and formal/HostUnicodeGram.lean.

Lean theorem PASS does not by itself refine the live PostgreSQL recursive CTE, GIN Unicode index, systemd release or current foreign Goal. PG 0013 host_unicode_ngrams3 keeps exact strpos post-filter; native owner tests and live planner/consumer readbacks remain different evidence. Keep current native verification rather than adding tests or another theorem for documentation claims.

## 6. Mature platform sources

PostgreSQL18 MVCC/FK/GIN; Alembic official migrations; Psycopg native PostgreSQL connections; MCP Python SDK; Pydantic typed inputs; RFC8785 canonical JSON; pytest/Hypothesis; pinned Lean/Z3; systemd and Git immutable release. No duplicate query engine, hand-written MVCC, universal task scheduler or extra audit database. Treat obsolete implementation stories as Git history, not perennial current user instructions.
