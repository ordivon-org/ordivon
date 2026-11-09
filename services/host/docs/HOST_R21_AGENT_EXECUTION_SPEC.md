# Host R2.1 — Zero-base file audit & subtractive modernization SPEC

SourceCut: Git main 7d7dcbe087136ae6249cd47524d1f6e33209f3e5. Live main ef17d6879d12faa61fff3bb762b0d500d73c9113 (2 newer commits, zero Host file changes verified). Local isolated Runtime Workspace ws-gpt6-host-zero-base-modernization-audit-20261110-r1. This replaces the old incremental Host R2.1 Spec in-place; no second canonical global Agent spec.

Scope and standing: 117 Git-tracked Host files, 15990 observed lines, 36 production Python AST-parsed for imports/classes/functions, explicit Git grep file consumers across the monorepo, selected current core implementations read, existing repo and Host rules reviewed. This table is an exhaustive file-by-file FIRST-PASS disposition (not 117 formally proven complete consumer closures). Deep audits and native source tests remain independent evidence. Do not silently infer live production from Git source.

## 1. System role and better problem representation

Host is a PostgreSQL-backed semantic continuity, social collaboration and attention/re-entry journal. Host owns Work identities/revisions, ActorRefs as references, Space, Topic, Message, relations, subscription and read cursor. Runtime owns Job/Attempt/effects; Harness owns Agent execution; Identity/Security owns authorization; Git owns source; actual domain Owner owns Goal success. Work.completed does not equal domain outcome. Host must not become IAM, global task executor, generic queue/scheduler or external-facts registry.

The root problem is not a lack of LEGO or tests. It is *multiple historical planning representations claiming present relevance, tests self-certifying the presence of old plans, and Agents optimizing local file-count or green-lint proxies*. Model this as an ownership-aware typed dependency graph:
- vertices: existing file, executable role, PostgreSQL schema, released MCP contract, migration, unique external consumer, historical archived reference;
- edges typed as import, SQL dependency, manifest, running interface, proof obligation, current test, historical prose, and mere same-name citation;
- DELETE only when the responsibility's unique live semantics are either absent or already covered by another existing owner. Mere static reference is not proof of user value, but absent static imports are not proof of unreachability.
- Keep historical evidence recoverable via exact Git object, separate from current authority.

Optimization target: lower change/maintenance/onboarding cost with current behavior/authority preserved, not minimum file number, maximum tests, or Doctor color.

## 2. Mature foundations and precise use

Parnas information hiding: modules hide likely decisions that change; splitting files is not inherently modularity. Ousterhout/Matt codebase-design: deep modules offer more behavior per interface and localize fixes. CQRS/DDD: Work, Social and Attention have naturally separated command/read semantics under the SAME PostgreSQL Owner; never add a replica/database/Redis/Kafka because the words sound modern. Abadi-Lamport/refinement and assume-guarantee: replacement must preserve observed behavior under explicit environment assumptions; a formal algebra statement is not installed evidence. Recursive LEGO R2.1 11 coordinates (I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold) apply to independently declared responsibilities, NOT one tuple for each file.

STPA: prevent damaging real collaborative navigation by deleting Work identity or forging history. Graph reachability/SCC/deletion dominance: distinguish real consumers from self-referential plan tests. Lean/TOC management: eliminate self-created work/WIP rather than enlarge compliance workflow. PostgreSQL18 MVCC, FKs, JSONB and indexes, Psycopg, Alembic, MCP official SDK, systemd and GitHub are existing mature provider choices; no custom substitutes this wave.

Execute with already approved Matt improve-codebase-architecture/codebase-design/code-review (two axes), ECC brownfield-retrospective (four-gap axes) and Superpowers writing-plans/verification-before-completion. Adopt source-aware methods, not their proprietary hooks, additional review approvers, subagent ceremony, task trackers or new tests.

Primary public sources: Parnas DOI 10.1145/361598.361623; Matt Skills github.com/mattpocock/skills, Zulip architecture, Temporal Server service decomposition as a comparison only, PostgreSQL18 reference manual. Historical method sources bind to local approved Skill packages.

## 3. Current real implementation shape

Gateway/MCP clients -> mcp_server + mcp_tool_registration -> MCP Work/Social/Attention tools -> WorkStore, SocialStore, AttentionStore -> commands and read queries -> Psycopg/PostgreSQL18 with Alembic migrations. Formal proofs, release packaging and config stay under their original natural owners.

KEEP core: current public MCP interface, typed errors, official SDK, Host PostgreSQL transaction ownership, command receipts idempotency, CAS, bounded pagination and query, PG history and schema migration chain. A short file is not necessarily a shallow useless module. In particular, social_read_queries.py groups read-only behaviors and deletion would widen SocialStore's mixin list. REVISIT only after real call-site complexity comparison.

Observed major issues:
F1: planning/lego-plan-r1.json has 57 whole-repo literal filename references, including current Repo graph checkers; R1 is not automatically dead. R3 also has active Repo checks.
F2: planning/host-friction-observatory-r1.json 192 lines holds older fixed measurements, no external filename refs, cited only by older Host guide/plan and R3 freezeRule.evidence. Candidate archive by immutable Git pointer and REMOVE live file, preserving recoverable historical bytes.
F3: historical tests/test_social_work_fabric_architecture.py (9 assertions mostly verifying old R1 plan text and source-string absence) retired under Host Owner. It had no live independent test-file consumer; historical FORMAL_LEGO_ISSUE_CENSUS_20261024_R1.json names it only as a past receipt. Existing current MCP/Work/PG tests stay. The R1 planning JSON itself remains because the Repo Owner still directly reads its historical retirement shape; cross-owner coordination required before retiring that carrier.
F4: the old Host SPEC/PLAN contained prior 2026-11-09 tasks already merged and append-only history. REPLACE them with this source-fresh document and its executable companion; no next duplicate Spec.
F5: 14 migrations and schema replay, current Lean code, PG checks and release scripts are current provenance. Deleting them solely because they are legacy is wrong.
F6: live Host history previously reported invalidWorks=3; do not reclassify Doctor green, reconstruct nonexistent snapshots or delete referenced Work identities for cosmetics. Prior PR #2000 was CLOSED when new directive stopped additional tests.

## 4. Anti-false-positive and review rules

For each action, state exact path and SHA, caller/import and external consumer, DELETE vs REUSE vs REPAIR, location of relocated complexity, change-induced coupling, retained unique proof/history, and native existing verifier. Independently ask whether (a) theoretical foundation applies, (b) Matt/ECC/Superpowers used correctly, (c) decision is overly conservative, (d) merely visual/doc cleanup, (e) representation chosen captures root cause, and (f) it improves whole system. Space advice is evidence, not authorization or a reason to wait indefinitely. UNKNOWN stays UNKNOWN.

## 5. Full 117-file first-pass ledger

KEEP is not equivalent to exhaustive real consumer proof. Candidate means scrutinize before effect; no new features/tests/consumers permitted.

| File relative to services/host/ | Lines | Verdict | Evidence / action |
|---|---:|---|---|
| .gitignore | 8 | KEEP | 当前环境/工具配置或未证冗余的必要文件 |
| .python-version | 1 | KEEP | 当前环境/工具配置或未证冗余的必要文件 |
| AGENTS.md | 26 | KEEP_REFINE | 当前人和Agent自然导航；随整理去过时段落 |
| README.md | 177 | KEEP_REFINE | 当前人和Agent自然导航；随整理去过时段落 |
| alembic.ini | 31 | KEEP | 当前环境/工具配置或未证冗余的必要文件 |
| docs/HOST_OWNER_GUIDE.md | 254 | CONSOLIDATE | 核心导航保留；旧观察与实验回执收缩到Git历史 |
| docs/HOST_R21_AGENT_EXECUTION_PLAN.md | 162 | REWRITE | 旧A1-G1被当前主线部分完成，改为真实减法任务图 |
| docs/HOST_R21_AGENT_EXECUTION_SPEC.md | 251 | REWRITE | 替换旧Host递增spec，保留唯一当期Owner改革规格 |
| docs/SOCIAL_WORK_FABRIC_R1.md | 103 | REVIEW_RETIRE | 历史Schema9，README与test_contract_policy及外部census引用 |
| docs/SOCIAL_WORK_FABRIC_R2_IMPLEMENTATION.md | 105 | REVIEW_RETIRE | 旧版发布回执；核实有无不可恢复证据 |
| docs/SOCIAL_WORK_FABRIC_R2_SPEC.md | 134 | KEEP | 当前SWF契约入口与Repo图校验引用 |
| formal/HostUnicodeGram.lean | 86 | KEEP | 现有Lean/Z3证明及原生验证 |
| formal/HostWorkDAG.lean | 89 | KEEP | 现有Lean/Z3证明及原生验证 |
| formal/work_graph_dag.py | 95 | KEEP | 现有Lean/Z3证明及原生验证 |
| mcp-surface.json | 40 | KEEP | 当前环境/工具配置或未证冗余的必要文件 |
| migrations/env.py | 44 | KEEP | Alembic 0001至0013历史升迁链（含模板） |
| migrations/script.py.mako | 20 | KEEP | Alembic 0001至0013历史升迁链（含模板） |
| migrations/versions/0001_host_v2_core.py | 65 | KEEP | Alembic 0001至0013历史升迁链（含模板） |
| migrations/versions/0002_concurrent_idempotency_claim.py | 21 | KEEP | Alembic 0001至0013历史升迁链（含模板） |
| migrations/versions/0003_product_surfaces.py | 71 | KEEP | Alembic 0001至0013历史升迁链（含模板） |
| migrations/versions/0004_r6_cleanup.py | 54 | KEEP | Alembic 0001至0013历史升迁链（含模板） |
| migrations/versions/0005_explicit_board_task_route.py | 106 | KEEP | Alembic 0001至0013历史升迁链（含模板） |
| migrations/versions/0006_social_work_fabric_work_graph.py | 78 | KEEP | Alembic 0001至0013历史升迁链（含模板） |
| migrations/versions/0007_social_work_fabric_social_graph.py | 120 | KEEP | Alembic 0001至0013历史升迁链（含模板） |
| migrations/versions/0008_social_work_fabric_attention.py | 111 | KEEP | Alembic 0001至0013历史升迁链（含模板） |
| migrations/versions/0009_retire_legacy_task_board.py | 38 | KEEP | Alembic 0001至0013历史升迁链（含模板） |
| migrations/versions/0010_social_work_fabric_r2.py | 61 | KEEP | Alembic 0001至0013历史升迁链（含模板） |
| migrations/versions/0011_retire_external_news.py | 38 | KEEP | Alembic 0001至0013历史升迁链（含模板） |
| migrations/versions/0012_message_literal_trigram.py | 61 | KEEP | Alembic 0001至0013历史升迁链（含模板） |
| migrations/versions/0013_unicode_substring_gin.py | 81 | KEEP | Alembic 0001至0013历史升迁链（含模板） |
| mise.toml | 84 | KEEP | 当前环境/工具配置或未证冗余的必要文件 |
| packaging/install_release.sh | 155 | KEEP | 原生发布/systemd/MCP surface工具 |
| packaging/systemd/host-v2.env.example | 7 | KEEP | 原生发布/systemd/MCP surface工具 |
| packaging/systemd/ordivon-host-v2.service | 38 | KEEP | 原生发布/systemd/MCP surface工具 |
| packaging/verify_tool_surface.py | 76 | KEEP | 原生发布/systemd/MCP surface工具 |
| planning/host-friction-observatory-r1.json | 192 | RETIRE_CANDIDATE | 过期静态观测，仅R3 freezeRule与内部旧文档引用 |
| planning/lego-plan-r1.json | 688 | KEEP | 全仓57处名称引用；Repo类型图真实消费 |
| planning/lego-plan-r3.json | 209 | REFINE | 当前Repo graph校验读取；旧观察指针应改Git历史锚 |
| planning/social-work-fabric-r1.json | 444 | REVIEW_RETIRE | Host旧计划测试+Repo测试仍读取，先协作再删 |
| pyproject.toml | 43 | KEEP | 当前环境/工具配置或未证冗余的必要文件 |
| src/ordivon_host_v2/__init__.py | 4 | KEEP | 当前环境/工具配置或未证冗余的必要文件 |
| src/ordivon_host_v2/attention_projections.py | 324 | KEEP | 现有SQL读侧投影与查询界面 |
| src/ordivon_host_v2/attention_sql.py | 161 | KEEP | 现有SQL读侧投影与查询界面 |
| src/ordivon_host_v2/attention_store.py | 157 | KEEP | 当前唯一PG事务/CAS/幂等写语义 |
| src/ordivon_host_v2/canonical_json.py | 14 | KEEP | 多处复用的Psycopg/规范化/幂等/分页语义 |
| src/ordivon_host_v2/collaboration_inputs.py | 96 | KEEP | 现有输入/异常/输出契约与调用者 |
| src/ordivon_host_v2/collection_pagination.py | 38 | KEEP | 多处复用的Psycopg/规范化/幂等/分页语义 |
| src/ordivon_host_v2/command_receipts.py | 58 | KEEP | 多处复用的Psycopg/规范化/幂等/分页语义 |
| src/ordivon_host_v2/contracts.py | 66 | KEEP | 现有输入/异常/输出契约与调用者 |
| src/ordivon_host_v2/coordination_inputs.py | 38 | KEEP | 现有输入/异常/输出契约与调用者 |
| src/ordivon_host_v2/coordination_intent_commands.py | 123 | KEEP | 当前唯一PG事务/CAS/幂等写语义 |
| src/ordivon_host_v2/errors.py | 14 | KEEP | 现有输入/异常/输出契约与调用者 |
| src/ordivon_host_v2/mcp_attention_tools.py | 111 | KEEP | 现有官方MCP工具注册/输入错误转换 |
| src/ordivon_host_v2/mcp_domain_errors.py | 116 | KEEP | 现有官方MCP工具注册/输入错误转换 |
| src/ordivon_host_v2/mcp_server.py | 104 | KEEP | 现有官方MCP工具注册/输入错误转换 |
| src/ordivon_host_v2/mcp_social_tools.py | 318 | KEEP | 现有官方MCP工具注册/输入错误转换 |
| src/ordivon_host_v2/mcp_tool_registration.py | 32 | KEEP | 现有官方MCP工具注册/输入错误转换 |
| src/ordivon_host_v2/mcp_work_tools.py | 108 | KEEP | 现有官方MCP工具注册/输入错误转换 |
| src/ordivon_host_v2/native_pool_observability.py | 49 | KEEP | 多处复用的Psycopg/规范化/幂等/分页语义 |
| src/ordivon_host_v2/postgres_bounds.py | 3 | KEEP | 多处复用的Psycopg/规范化/幂等/分页语义 |
| src/ordivon_host_v2/postgres_connections.py | 24 | KEEP | 多处复用的Psycopg/规范化/幂等/分页语义 |
| src/ordivon_host_v2/py.typed | 0 | KEEP | 当前环境/工具配置或未证冗余的必要文件 |
| src/ordivon_host_v2/service.py | 211 | KEEP_REVIEW | 在线Doctor与schema读回，不以其已检测历史缺口替代修复 |
| src/ordivon_host_v2/social_contracts.py | 327 | KEEP | 现有输入/异常/输出契约与调用者 |
| src/ordivon_host_v2/social_errors.py | 13 | KEEP | 现有输入/异常/输出契约与调用者 |
| src/ordivon_host_v2/social_message_commands.py | 197 | KEEP | 当前唯一PG事务/CAS/幂等写语义 |
| src/ordivon_host_v2/social_message_queries.py | 305 | KEEP | 现有SQL读侧投影与查询界面 |
| src/ordivon_host_v2/social_read_queries.py | 15 | KEEP_REVIEW | 15行读侧聚合界面，删除可能使SocialStore继承层更复杂 |
| src/ordivon_host_v2/social_space_commands.py | 111 | KEEP | 当前唯一PG事务/CAS/幂等写语义 |
| src/ordivon_host_v2/social_space_queries.py | 342 | KEEP | 现有SQL读侧投影与查询界面 |
| src/ordivon_host_v2/social_store.py | 63 | KEEP_REVIEW | Social PG写权威与混入组合，先核算深模块收益 |
| src/ordivon_host_v2/social_topic_commands.py | 199 | KEEP | 当前唯一PG事务/CAS/幂等写语义 |
| src/ordivon_host_v2/social_topic_queries.py | 181 | KEEP | 现有SQL读侧投影与查询界面 |
| src/ordivon_host_v2/work_inputs.py | 119 | KEEP | 现有输入/异常/输出契约与调用者 |
| src/ordivon_host_v2/work_queries.py | 178 | KEEP | 现有SQL读侧投影与查询界面 |
| src/ordivon_host_v2/work_relation_commands.py | 96 | KEEP | 当前唯一PG事务/CAS/幂等写语义 |
| src/ordivon_host_v2/work_store.py | 239 | KEEP | 当前唯一PG事务/CAS/幂等写语义 |
| tests/conftest.py | 21 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_attention_query_boundary.py | 30 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_attention_single_snapshot_postgres.py | 138 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_canonical_json_property.py | 25 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_clean_room.py | 9 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_contract_policy.py | 293 | KEEP_SIMPLIFY | 源代码合法约束保留，去自维持旧文档断言 |
| tests/test_host_db_preflight_contract.py | 69 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_host_focused_default.py | 16 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_host_history_doctor_postgres.py | 78 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_host_queue_qualification.py | 125 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_mcp_domain_errors.py | 297 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_mcp_native_pool_stats.py | 109 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_mcp_surface.py | 300 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_mcp_surface_identity.py | 73 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_message_get_contract.py | 93 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_native_pool_postgres.py | 196 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_release_packaging.py | 245 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_schema_diagnostic.py | 10 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_social_creation_linearizability.py | 121 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_social_message_digest_postgres.py | 157 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_social_message_read_integrity.py | 58 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_social_query_boundary.py | 75 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_social_store_exact_integer_contract.py | 178 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_social_timestamp_strict_bigint.py | 87 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_social_work_fabric_architecture.py | 95 | RETIRED | 旧R1计划自证性9测试已退役；历史可用Git恢复，当前原生PG/MCP测试仍保留 |
| tests/test_social_work_fabric_attention.py | 136 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_social_work_fabric_postgres.py | 1452 | KEEP_EXISTING | 1452行PG实际验证；不增测试，可择机存量整理 |
| tests/test_social_work_fabric_retirement.py | 47 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_social_work_fabric_social_graph.py | 99 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_social_work_fabric_social_store.py | 171 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_social_work_fabric_society.py | 185 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_social_work_fabric_work_graph.py | 238 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_systemd_liveness_contract.py | 16 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_tool_surface_release_contract.py | 84 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_topic_state_lifecycle_postgres.py | 197 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_work_query_boundary.py | 54 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_work_relation_three_node_oracle.py | 162 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tests/test_work_snapshot_read_refinement.py | 85 | KEEP_EXISTING | 原生存量回归与结构约束，不新增 |
| tools/host_queue_verify.sh | 84 | KEEP | 原生发布/systemd/MCP surface工具 |
| uv.lock | 1061 | KEEP | 当前环境/工具配置或未证冗余的必要文件 |

## 6. Execution and exit

Sequence: audit freeze -> rewrite existing Host Spec/Plan -> retire truly dead static data and repair historical pointer -> simplify Owner Guide where value remains -> challenge thin facade code on real leverage -> coordinate Repo Owner for cross-owner R1 graph retirement -> existing native checks -> Git PR / installed truth separately. The priority is amount of unique maintenance burden removed per unit of risk, not arbitrary source churn. The exact step DAG lives only in the companion existing Plan.
