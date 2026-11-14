# Host Owner — 目录审计、LEGO 与使用指南

审计 SourceCut：2026-11-07，fc0fbfdf43c53a988b7af27a762856e491151ce1。本文件是源码与消费者审计，不是新权威注册表；在线安装、PG 数据与跨 Owner 事实应重新查证。

## 1. 语义边界

Host 的核心是 Work Continuity、Collaboration 与 Attention/Re-entry。Host 拥有 Work、WorkSnapshot、Space、Topic、Message、Subscription、Attention 和游标的 PostgreSQL 事实。ActorRef 只是引用，不是认证；Participation 不是授权或任务分配；Attention 不是任务优先级、事件总线或调度器；Work.completed 不是 Runtime Job、Git 发布或领域成果的独立验证。

Runtime 拥有 Workspace、Job/Attempt 与机械执行真相；Harness 拥有 Agent 运行和工具生命周期；Gateway 管理接入；Security/Identity 管理授权；Git 管理源码提交；领域 Owner 管理各领域结果。外部引用必须回到自然 Owner 读取，不把 Host 的文字主张当成外部证明。

## 2. 逐目录与文件审计及处置

| 文件/目录 | 实际职责 / 消费者 | 处理 |
| --- | --- | --- |
| src/ordivon_host_v2/work_inputs.py、work_store.py、work_queries.py | Work 契约、版本 CAS、查询 | 保留：单一 PG 写入真相与查询分离 |
| src/ordivon_host_v2/social_space_*、social_topic_*、social_message_* | 社会化协作对象读写；MCP tools | 保留：按对象拆分、写与读分开 |
| src/ordivon_host_v2/social_store.py、social_read_queries.py | 复用协作能力的轻聚合，不持有第二份数据 | 保留；重命名含混查询聚合文件 |
| src/ordivon_host_v2/coordination_inputs.py、coordination_intent_commands.py | Coordination Intent 及其数据库写入；Attention SQL 消费；PG 测试 | 保留实际消费者，统一命名；不误称已发布 MCP 工具 |
| src/ordivon_host_v2/attention_store.py、attention_projections.py、attention_sql.py | 订阅/游标、变更派生投影、SQL | 保留；将只有 SQL 的文件改为明确名称 |
| src/ordivon_host_v2/mcp_server.py、mcp_tool_registration.py、mcp_*_tools.py | 官方 MCP SDK 服务和工具适配 | 保留；规范注册文件命名，外部工具名未变 |
| src/ordivon_host_v2/*contracts.py、canonical_json.py、command_receipts.py、collection_pagination.py、postgres_bounds.py | 类型契约、RFC 8785、幂等、界限 | 保留小型共用能力，不重复造库 |
| migrations/、alembic.ini | schema 0001–0013 迁移链，已升级至版本 13 | 保留全部迁移链；旧编号不等于垃圾 |
| tests/ | MCP、PG 并发、因果关系、CAS 与源契约 | 保留有真实消费者边界的测试；更新文件名依赖 |
| packaging/、tools/ | Git SHA 发布、systemd、tool surface、资格验证 | 保留，不触碰已安装系统服务 |
| planning/lego-plan-r1.json | 仓库级 LEGO 图检查的现行输入 | 保留，不能仅凭 r1 删除 |
| planning/lego-plan-r3.json | 当前 Host Owner 职责与复用边界 | 保留，不复制成新注册表 |
| planning/social-work-fabric-r1.json | 架构测试实际使用 | 暂保留；消费者迁移后可退休 |
| planning/host-friction-observatory-r1.json | R3 规划明确引用的旧测量证据 | 保留为旧证据；不能当作当前数值 |
| docs/SOCIAL_WORK_FABRIC_R1.md | 历史记录，README 和测试标明历史地位 | 不作为当前权威，当前未删除 |
| docs/SOCIAL_WORK_FABRIC_R2_SPEC.md、SOCIAL_WORK_FABRIC_R2_IMPLEMENTATION.md | 当前语义规范与实现说明 | 保留并以代码、PG、发布状态校验 |
| mcp-surface.json、mise.toml、pyproject.toml、uv.lock、.python-version | 外部接口清单及固定工具链 | 保留单一声明，不在 README 重复工具总数 |

本轮仅在独立 Git Workspace 修改源码、文档、引用和测试。未删除业务数据库行、外部 Workspace、systemd/系统目录或 Runtime Job 数据。尚无已证明无消费者的本地垃圾文件值得无条件删除。清理前必须证明消费者不可达，并区分历史材料、PG 数据与可重建缓存。

## 3. 外部成熟 LEGO 与本地 LEGO

| 能力/思想 LEGO | 类型 | 复用或实现来源 | 最小契约 |
| --- | --- | --- | --- |
| Work Snapshot CAS | 能力型 | Host + PostgreSQL MVCC | 精确 revision、事务冲突、幂等回执 |
| Collaboration Journal | 能力型 | Host + PostgreSQL FK、索引 | Topic/Message 有界恢复，Work 状态不靠聊天推断 |
| Re-entry Projection | 能力型 | Host 的 PG 查询 | 两种游标单调且分域，不能替代调度真相 |
| Reference Revalidation | 思想型 | 自然 Owner 原则 | 引用不是权限、效果或成果证明 |
| Evidence Before Completion | 思想型 | Formal-first / Owner-native readback | 外部事实先由 Owner 核验，再更新 Work 语义 |
| Canonical JSON | 外部能力 | RFC 8785 库 | 确定性字节与摘要 |
| Transaction & schema | 外部能力 | PostgreSQL 18、Alembic | MVCC/锁/约束/有版本的迁移 |
| Protocol & schema | 外部能力 | MCP Python SDK v2、Pydantic | 类型边界与标准协议 |
| Verification | 外部能力 | pytest、Hypothesis、CrossHair | 纯函数证明不冒充 PG 并发或线上发布证明 |

上游参考：
- https://www.postgresql.org/docs/current/mvcc.html
- https://alembic.sqlalchemy.org/en/latest/
- https://py.sdk.modelcontextprotocol.io/
- https://www.rfc-editor.org/rfc/rfc8785
- https://docs.pydantic.dev/latest/
- https://hypothesis.readthedocs.io/
- https://crosshair.readthedocs.io/

## 4. Human 操作指南

1. 在线查看：host.status(detail=summary) 观察 Host 自身统计；host.status(detail=integrity) 检查已覆盖的 PG 一致性。不要把 Host 健康等同于 Runtime、Git 或业务验收。 当前 integrity 模式必须检查每个 Work 的当前 Snapshot 指针与 payload 摘要；旧修订不要求连续也不应因为被裁剪而判定 Host 不健康。history 模式可额外复核仍然保留的 Snapshot，但缺失的历史版本不得伪造；历史读回可以返回缺失。此规则不宣称生产已实施历史裁剪。
2. 接手工作：work.get 读取版本化 WorkSnapshot；topic.resume 恢复讨论；work.list、space.list、message.search 使用数量与字节预算分页。
3. 研发变更：进入 services/host 执行 mise run verify；存在独立 Docker 环境时运行 mise run test:postgres:disposable；运行 mise run formal:reply-source 检查源码级纯函数契约。PG 集成 SKIP 不可算成 PASS。
4. 发布：校验准确 Git SourceCut、不可变安装目录、mcp-surface.json 与真实注册工具一致，再进行已安装服务和 PG 验证。
5. 清理：检查 PG 外键、业务关联、活跃消费者和审计要求。禁止把系统文件、运行时别人的 Workspace 或数据库行当成普通缓存强删。

## 5. Agent 操作指南

1. actor.declare 仅声明稳定引用，不代表安全授权。创建或读取 Work 时，使用 work.create / work.get 的当前 revision。
2. attention.reentry 返回值得恢复的导航项；topic.resume 依照 Topic Message sequence 继续阅读。Attention Change sequence 与 Topic Message sequence 不能混淆。
3. 对任何 referenceRefs，回到 Git、Runtime job.get、真实 Artifact、Security 或领域 Owner 查询；Message 与 WorkSnapshot 的文字不能独立证明外部事实。
4. 汇总新证据后使用 work.snapshot.commit 的 expectedRevision 提交；若竞争冲突，重新读取并调和，不直接覆盖。
5. 完成消息处理后单调推进 topic.cursor.ack 与 attention.ack；确认已消费不是确认业务完成。
6. 新 LEGO 应明确 I/O、S、pre/post、inv、eff、c、epsilon、prov、unfold 和真实消费者。未知证据保持 UNKNOWN；优先 DELETE CUSTOM → REUSE → COMPOSE。

### 5.1 Agent 日常 Golden Road（2026-11-14 真实消费者核查）

**优先级：Agent 完成工作，而不是 Host 拥有更多状态或验证系统。**
本节是对现有 \`work.*\` / \`attention.*\` / \`topic.*\` 的**调用编排**，
不增加数据库、MCP 工具、评分器、调度器或另一份事实权威。
真实入口取决于当前安装的 \`tools/list\` 和 Gateway 授权；源码工具存在
不等于已安装或调用方具备权限。

| Agent 实际问题 | 思想型 LEGO | 逻辑型 LEGO | 已存在的能力型 LEGO |
| --- | --- | --- | --- |
| 我现在有什么工作？ | Consumer-first、最小充分状态 | Work Discovery / Work Identity | \`work.list\`（有界元数据），已知 Ref 直接 \`work.get\` |
| 我做到哪里、下一步是什么？ | CQRS、事务一致性 | Current Work Snapshot / Revision | \`work.get\` / PG \`work.snapshot.commit\` CAS |
| 上次之后谁说了什么？ | 增量视图、因果导航 | Attention Delta / Topic Resume | \`attention.reentry\` / \`topic.resume\` |
| 我需要跟谁协作？ | 消息传递、显式关系 | Space / Topic / Message / Relation | \`message.post\` / \`message.relation.*\`；不凭 ActorRef 自动授权 |
| 怎样避免多 Agent 相互覆盖？ | 乐观并发、MVCC | Work CAS Conflict / Reconcile | PG 原生事务 + \`work.snapshot.commit(expectedRevision)\` |
| 怎样不再读一遍完整历史？ | 增量消费、信息预算 | Dual Cursors / Bounded Pagination | \`attention.ack\`、\`topic.cursor.ack\`（严格不同的坐标） |
| 外部结果是不是还成立？ | 自然 Owner、证据溯源 | Owner Readback / Currentness | Git / Runtime / Security / 领域 Owner；Host 仅存引用 |

**既有工具的可重复消费顺序：**

1. 已知 \`workRef\` 直接读 \`work.get\`；未知则先用 \`work.list(state=open, limit, maxBytes)\` 找到候选的 **Ref/Kind/Revision**，再只取相关 Work 的当前 Snapshot。不用历史快照或更新时间自动推断重要性。
2. 从 Work 当前 \`referenceRefs\` 找真实 \`topic:\` / \`space:\` 引用。**只有已确认业务关联时才添加该引用**。缺引用时不能声称该 Work 不存在协作讨论；可从已知 Space/Topic 或受控搜索定位后，经 Work CAS 明确关联。
3. 用当前 **Actor 的真实授权**读取 \`attention.reentry\`。其中 \`afterSequence\`、\`nextAfterSequence\` 和 \`snapshotHighSequence\` 均属于 **Host Attention ChangeSequence**，不是消息序号；\`items[].resumeAfterSequence\` 才是对应 Topic 的 **Message Sequence** 消费坐标。
4. 对所需 Topic 使用 \`topic.resume(topicRef, afterSequence=resumeAfterSequence, limit, maxBytes)\`。若 \`hasMore=true\`，下一页用本次 Topic 的 \`nextAfterSequence\`，直到需要的信息消费完整。**不得**把 Attention 的 \`nextAfterSequence\` 填给 \`topic.resume\`；同一 Topic 的两页必须无重叠、不跳过已返回的消息。
5. 如果 Work 引用了外部 Runtime、Git、Research、Security 信息，仅对当前行动真正依赖的 Ref 回到原 Owner 读取；历史状态和聊天主张不自动升级为当前事实，UNKNOWN 继续是 UNKNOWN。
6. Agent 在完成所需外部消费后，按需 \`message.post\` 留下真实协作记录，使用最新 \`work.get.revision\` 调用 \`work.snapshot.commit(expectedRevision,...)\` 提交新的**完整八字段** Snapshot。出现 CAS 冲突则重新读取当前 Work，合并他人真实贡献后再尝试；不能盲目覆盖或由 Message 推断 Work Completed。
7. **最后才 Ack。** 仅在已经处理相应消息与当前变更后，单调提交 Topic 的 **Message Sequence** \`topic.cursor.ack\` 与 Attention 的 **ChangeSequence** \`attention.ack\`。如果 Attention \`hasMore=true\`，只能按已处理页的 \`nextAfterSequence\` 逐页确认；不得跃过尚未处理的事件、也不能自动推进到 \`snapshotHighSequence\`。Cursor Ack 表示“已消费”，不表示任务成功、协作接受、外部执行效果或权限批准。

**实际只读消费（2026-11-14，一次观察而非性能承诺）：**

- 在本轮补充导航引用和新建主线 Work 之前，生产 Host 有 **9 个 open Work**，其中 **2 个**的当前 \`referenceRefs\` 显式包含 \`topic:\`。这是直接导航覆盖率的观察，**不证明**另 7 个 Work 必须有 Topic，不能无依据批量改写。
- 原有 Host 证据 Work \`work:ordivon:host-agent-proof-applicability-r3:20261114\` 的真实关联 Topic \`topic:ordivon:host-optimization-tri-agent-plan:20261110\` 原来不在 \`referenceRefs\`。现已仅增补该真实 TopicRef，Host Work CAS **rev12→13**，Gateway 读回 \`snapshotDigest\` 一致，\`frontier\` 没有变化。
- 对相同 Actor \`actor:agent:chatgpt:gpt6-host-business-q1-20261113\`，\`attention.reentry\` 从 **changeSeq 77453** 返回 12 个原始变化聚成 1 个 Topic，下一 **changeSeq 77622**；该 Topic 自己的 \`resumeAfterSequence\` 却是 **messageSeq 27535**。这两个坐标属于不同域，不能比较大小或互换。
- \`topic.resume(afterSequence=27535, limit=8)\` 第 1 页 8 条消息，下一 **messageSeq 27609**，\`hasMore=true\`；第 2 页再读 6 条，下一 **messageSeq 27669**，\`hasMore=false\`。两页没有消息重叠。两次完整 JSON 序列化文本的观察长度约 18,638 和 17,649 **字符**；这不是准确的 Token 消耗、实际网络流量、p95 或上下文压缩率。
- **绝不为了演示而推进现有 Actor 的生产消费游标。** 本次做了只读恢复，没有 \`attention.ack\` 或 \`topic.cursor.ack\`。
- 新建真实 Host 主线 Work：\`work:ordivon:host-agent-continuation-golden-road-r1:20261114\`，把“Agent 日常发现、恢复、协作”与之前只关注证据适用性的 Work 分开；关联已有 Topic，不新建重复的 Space/Topic。
- 两项实际变更之后再次读回：**10 个 open Work，其中 4 个有显式 TopicRef**。这是两个时间点的导航观察，并不是“完成度提高到 40%”的产品指标；是否需要额外 Topic 必须由每个 Work 的消费者决定。
- 正式独立 Agent B、Harness 自动 Re-entry、真实 Token/时间预算目前 **UNKNOWN**。当前只是一个 Actor 经 Host/Gateway 只读消费和正常 Work CAS 的证明，不可替代多 Principal 验收。

**最小 R2.1 消费契约：** I=ActorRef、WorkRef、当前 Snapshot/Revision、
Attention ChangeSequence、Topic MessageSequence、真实 TopicRef；
O=可解释的当前工作状态、需恢复消息、真实下一步和仅已消费的确认坐标；
S=Host PG 现有 Work/Social/Attention 行；pre=当前可授权 Actor、合法
Work/Topic 引用和各自合法游标；post=不漏已消费页、不把一种序列当另一种、
Work CAS 按精确 revision 决议；inv=消息不是执行事实、Attention 不是优先级、
游标确认只代表消费、Work 竞争不能静默覆盖；
eff=按需 Owner 只读、受授权的 Work/Message 写、实际消费完才 Ack；
c=以 Harness 原生调用轨迹测量真实调用/Token/延迟，尚未取得；
epsilon=跨网络/多 Agent 延迟与失误率均 UNKNOWN；
prov=Host 原生 MCP、PG 当前读回与本节精确 Work/Topic 对象；
unfold=Discovery → Work.get → Attention.reentry → Topic.resume 分页 →
必要 Owner Readback → Message/Work CAS → 安全双 Ack。

**成熟机制：** PostgreSQL MVCC 与 CAS、MCP 已安装工具合同、CQRS 的局部
Read/Write 分离、单调增量消费坐标和有界字节/条目分页。无需新建 Host
事件总线、VectorDB、排序模型、完备历史恢复或第二套 Run/State。


## 6. 在线数据归并候选（2026-11-07，只读核查）

以下三个 Space 的功能重叠，属于进一步消费者审计候选，不是已经证明可删的数据：

| Space 标识的关键部分 | Topic | Message | Participation | Space Subscription | 处置 |
| --- | ---: | ---: | ---: | ---: | --- |
| ordivon-task-portfolio-and-proof-gates-r1 | 7 | 216 | 0 | 0 | 有实际消息和 Subject，暂不删除 |
| ordivon-task-control-r1 | 8 | 140 | 2 | 1 | 存在消息和关注者，暂不删除 |
| ordivon-capability-task-forum-r1 | 13 | 158 | 3 | 0 | 有实际消息和参与者，暂不删除 |

线上 PostgreSQL 的只读事务已核查全部 35 个 Space 对应的 Topic、Message、Participation、Subject、Space/Topic Subscription 与 Coordination Intent。**这些维度全部为零的 Space 数量为 0**。三个重叠候选合计 514 条 Message；不能简单以“空间名称重复”断定是可删除垃圾。

这是一份在线读取时刻的快照；跨 Owner 和 WorkSnapshot 的完整引用闭包未全部核验，也没有已发布的 Host 原生删除 API 契约。本轮没有直接执行 PG SQL 删除。优先复用现行 Space；确认所有消费者已经转移后再做精确退役，绝不新建第二个全局任务入口。

架构参考：[Martin Fowler CQRS](https://martinfowler.com/bliki/CQRS.html) 强调按 bounded context 局部采用、避免全面复杂化；[Architecture Patterns with Python](https://www.cosmicpython.com/) 提供 Repository / Service Layer / Unit of Work 的成熟边界思想。Host 当前直接复用 PostgreSQL 事务，只有证明额外抽象能减少真实耦合才需要引入 Repository/UoW 包装。

## 7. Work Graph 关系模块二次拆解

本轮将 add_relation、_reject_cycle 从 work_store.py 抽取至 work_relation_commands.py。WorkStore 仍然是唯一组合入口：关系命令使用现有 PostgreSQL DSN、Actor/Work 存在性检查、事务级 advisory lock、递归图环检测与幂等回执。WorkSnapshot CAS 和只读 Work 查询保持原来的语义所有权。

**能力型 LEGO — WorkRelationInsert**：I 为 WorkRelationInput 与 clientRequestId；O 为 committed/existing 回执或类型化冲突；S 是 Host PG 的 works、work_relations、actor_refs 与 command_receipts；pre 是有效引用及非自环；post 是原子写入与可重放回执；inv 是 parent_of 与 depends_on 各自图内无环；eff 是单个 PG 事务内的原生锁/递归查询/插入，没有域外执行；c 与 epsilon 仍为 UNKNOWN，不能将测试通过伪装成生产故障率证明；prov 使用真实代码、PG oracle 和精确 SourceCut；unfold 为 WorkStore → WorkRelationCommands → PG lock/check/insert/receipt。

**思想型 LEGO — OwnerNativeRelation**：Host Work 关系是语义引用，不自动产生 Runtime Job、任务调度、Actor 权限或领域验收；依赖/父子关系不证明实际执行先后。公开 MCP 工具清单没有 work.relation.add，所以 Human 和 Agent 都不得将 Python 内部能力当成线上已公布工具。

**Human 使用**：继续通过 work.get、work.snapshot.commit 和自然 Owner 验证状态；涉及关系源码时用原生 PostgreSQL 并发与三节点关系 Oracle 证伪。**Agent 使用**：先检查实际 tools/list，不尝试未发布的 Work Relation 写接口；读取引用后到 Runtime、Git 和领域 Owner 重新验证，再更新 WorkSnapshot。

参考成熟能力：PostgreSQL MVCC (https://www.postgresql.org/docs/current/mvcc.html)、MCP Python SDK (https://github.com/modelcontextprotocol/python-sdk)、Cosmic Python (https://www.cosmicpython.com/book/chapter_06_uow.html)、CQRS 的局部采用原则 (https://martinfowler.com/bliki/CQRS.html)。当前未引入二次数据库、ORM、事件总线或自建 UoW。

## 8. 待进一步验证的边界

Coordination Intent 与 Work Relation 有内部能力和数据库消费者，但并非全部显式 MCP 工具，不能把“代码存在”直接宣称外部产品可用。跨包更名 ordivon_host_v2、删除 R1 图方案、删除不可逆迁移或重写 PG 状态必须先有消费者迁移与发布验收；重构范围越广，不代表系统越优。

## 9. Formal-first evidence: Work Graph DAG (2026-11-08)

The owner-native task `mise run formal:work-graph` evaluates `formal/work_graph_dag.py` using the existing CrossHair/Z3 formal dependency group. It checks **all directed adjacency assignments** for 2, 3, and 4 labeled vertices using SMT transitive closure; under the **acyclic pre-state** assumption, insertion `source → target` preserves acyclicity exactly when `target` cannot already reach `source`. A deliberately swapped guard must yield a SAT counterexample. This is `MODEL_VERIFIED` for finite sizes, not a general theorem for arbitrary vertex counts.

The SQL implementation performs `pg_advisory_xact_lock`, a recursive CTE and `INSERT` in one transaction in `work_relation_commands.py`. The existing three-vertex PostgreSQL oracle, concurrent insertion tests and receipt tests remain necessary **implementation/refinement and real-consumer evidence**. No source-derived model alone proves PostgreSQL lock fairness, transaction atomicity, negative evidence closure or installed state. The SQL CTE, Python command and model must each be checked at the same exact Git SourceCut.

Verification tier: `Specification → finite SMT Model → source/SQL refinement via native PG tests → installed consumer readback`. The five CrossHair obligations remain limited to the actual pure helper functions. This package does **not** automatically migrate every Host test to SMT: contract parser, persistence, races, MCP, Alembic and installed API tests remain meaningful. Do not remove a consumer test until a stronger proof and an actual refinement bridge cover its property. `MODEL_VERIFIED`, `CODE_REFINED`, `INSTALLED_CURRENT` and `DOMAIN_ACCEPTED` are separate claims.

Human: use `mise run formal:work-graph` and `mise run test:postgres:disposable`, record both SourceCut and actual result, preserve independent counterexample controls. Agent: discover `services/host/AGENTS.md`, inspect the current live MCP tools, verify the model source binding, and label any unverified proof step **UNKNOWN** rather than PASS. Do not create a second DAG implementation or runtime registry.

## 10. General Lean theorem (2026-11-08)

`formal/HostWorkDAG.lean` proves `insert_acyclic_iff_no_backpath` for an arbitrary type of vertices and arbitrary binary edge relation. The inductive `Walk` construction covers paths of any finite length; if the original relation is acyclic, inserting `source → target` preserves acyclicity exactly when `target` does not already reach `source`. `#print axioms` must report **no axioms**. This replaces a merely bounded graph law with a general abstract theorem. It does not establish runtime transaction isolation, the recursive SQL implementation, or installed behavior.

The theorem reuses the existing pinned Lean 4 toolchain from `tools/formal/mise.toml` instead of adding Lean to Host's Python lock or global package manager. Run `mise run formal:dag-theorem` from the Host directory; Host source verification invokes CrossHair, Z3 and this Lean theorem with its existing pinned upstream toolchain; the exact Lean proof can also be rerun on demand. For Work DAG changes run both the Lean theorem and disposable PostgreSQL 18 integration/oracle checks. Do not substitute toy-model PASS for implementation refinement or physical consumer verification.

Proof classification: `ABSTRACT_THEOREM_PROVED`; `BOUNDED_MODEL_VERIFIED`; `IMPLEMENTATION_REFINEMENT_PARTIAL` (SQL semantics plus real native PG oracle); `INSTALLED_CURRENT` must be checked against exact release SHA after publication.


## 11. PostgreSQL-native literal search, no second search authority

The original Host CJK substring lookup used strpos(body, query) without an
index-supported predicate. Schema 0012 installs the trusted PostgreSQL
pg_trgm extension and a concurrent GIN index on messages.body. For unspaced
CJK queries with three or more CJK codepoints, the implementation generates
a bound LIKE pattern with ESCAPE '#', escaping '#', '%' and '_'. Shorter
CJK queries retain strpos. Non-CJK and spaced queries retain simple FTS.
Order stays descending message sequence, not relevance ranking.

Human: run the isolated PostgreSQL 18 consumer verification and inspect
EXPLAIN for actual indexed semantics, not assumed speedups. Agent: call the
published message.search with a literal phrase and bounded cursor. A '%',
'_' or '#' in a phrase is content, not a search operator.

Upstream: https://www.postgresql.org/docs/current/pgtrgm.html


## 12. Unicode index refinement, driven by production counterexample

The production database has LC_CTYPE=C. On the actual schema 12 release,
show_trgm('终端消费') returned the empty set. A valid 54 MB pg_trgm index
was never used for CJK retrieval: EXPLAIN still selected Seq Scan + Sort.
This falsified the performance hypothesis; isolated correctness tests had
not measured production index extraction.

Schema 0013 replaces that index with a PostgreSQL GIN array_ops expression
over host_unicode_ngrams3(body), an immutable, strict, parallel-safe SQL
function returning distinct 3-codepoint text windows. For unspaced queries
with three-or-more CJK characters, Host uses the necessary candidate filter
host_unicode_ngrams3(body) @> host_unicode_ngrams3(query), followed by the
unchanged exact predicate strpos(body,query)>0. Short CJK queries still use
strpos and other queries native FTS; returned order stays message sequence.

Soundness argument: if q is a contiguous substring of b, every 3-codepoint
window in q also occurs in b, so grams3(q) is a subset of grams3(b).
The reverse implication is false; exact strpos remains the final semantic
oracle. This preserves '%' '_' '#' and backslashes literally and avoids
locale-dependent byte reinterpretations. The new index is built CONCURRENTLY
before retiring only the known obsolete 0012 index. PG GIN array_ops, not
a second search engine, remains the sole derived index authority.

Human: run the disposable PostgreSQL consumer tests and compare production
EXPLAIN with the same bound query before and after release, including
physical index validity and Host integrity. Agent: use public message.search
and do not infer ranking or domain completion from search results.

Sources: https://www.postgresql.org/docs/current/gin.html
https://www.postgresql.org/docs/current/sql-createindex.html


## 13. Unicode-gram proof and real consumer refinement (2026-11-08)

Theorem source: `formal/HostUnicodeGram.lean` (pinned Lean 4), invoked by
`mise run formal:unicode-search` and by Host `mise run verify`. The
abstract model treats a UTF-8 text as a finite sequence of Unicode scalar
values and each three-codepoint window as a contiguous sublist. It proves,
for arbitrary sequences and lengths, that **every true substring match is
retained by the 3-gram candidate filter**. A second theorem proves that
candidate containment combined with the original exact substring predicate
is equivalent to exact substring matching. Axioms must be reported as none.

The theorem assumes that the PostgreSQL `host_unicode_ngrams3(text)` SQL
function computes those codepoint windows and that `@>` implements set
containment. These are **implementation refinement obligations**, not
consequences of the Lean theorem: maintain real PostgreSQL 18 tests for
Unicode, %/_/#, backslash, and an adversarial false positive where all
3-grams are present but the complete substring is absent. Preserve the
published MCP `message.search` readback for installed evidence.

Production observed after schema 13 release `79cb0d7538b9...`:
`message_unicode_ngrams3_idx` valid and ready, 118 MB; read-only SQL
EXPLAIN for the literal phrase 终端消费 used Bitmap Index Scan (6.271,
0.336, 0.175, 0.164 ms over four sequential executions); 25 matches.
The 0.256 ms median is **not** a workload-level latency or throughput
promise, nor an independent proof of PostgreSQL implementation correctness.
Host integrity reported all six checks OK and live MCP readback preserved
sequence_desc and bounded cursor behavior.

Proof tiers: SPECIFICATION → ABSTRACT_LEAN_THEOREM → NATIVE_SQL_REFINEMENT
→ INSTALLED_INDEX_PLAN → MCP_CONSUMER. None proves provenance or domain
acceptance of the retrieved messages.


## 14. Attention re-entry single-snapshot MVCC contract (2026-11-08)

attention.get, attention.delta, and attention.reentry each establish one native
PostgreSQL REPEATABLE READ, READ ONLY transaction per public call.
For re-entry this single snapshot covers the actor's attention cursor (when
omitted), the change horizon, the delta event projection, any adaptive maxBytes
page reduction, and the related Topic consumption cursors. It does not hold
a database transaction across multiple MCP calls; separate pages may
legitimately observe later commits.

Counterexample addressed: after delta captures a prior change horizon, another
Agent commits topic.cursor.ack. Under the former multi-connection implementation
reentry could return a Topic resume cursor from that newer commit while
returning older delta events. The new read keeps the prior cursor; a fresh
re-entry request sees the newer acknowledgement. No event bus, copy of messages,
custom MVCC algorithm, schema migration or extra cross-request lock is needed.

Proof tier: native PG18 tests schedule concurrent ack after _delta_in_tx
under both pooled and direct Psycopg connections. Separate checkout-count tests
require exactly one DB checkout per public read. These are concrete SQL/behavior
oracles, not a general proof of future latency or all possible schedules.

Human: run mise run test:postgres:disposable; distinguish Attention change
horizons from Topic Message sequences. Agent: attention.reentry is navigation,
not scheduling or domain acceptance. Never infer latest global state from a
historical page; call the published tool again to obtain a fresh snapshot.

## Host release SourceCut content-anchor refinement

The native packaging entrypoint accepts an optional fourth argument:
install_release.sh <repo> <main_commit> <prefix> <reviewed_host_tree_oid>.

Human: obtain expected Host Git tree ID from the independently reviewed PR
head via git rev-parse <head>:services/host; cross-check the actual merge
event against fetched main ancestry and commit subject. Pass the reviewed
tree ID as argument four. A wrong adjacent Merge Queue SHA with a different
Host tree fails before directory creation, dependency resolution or symlink
mutation. The three-argument native installation path stays compatible.

Agent: never compute the expected tree from the *same untrusted release
commit*: that would prove an identity against itself. Git native tree objects
obviate a second hash or independent custom release registry. This is a
content identity witness, not a signed SLSA provenance attestation or proof
of builder identity. Continue Git chronology, Merge Queue checks, immutable
archive verification and live MCP consumer readback. UNKNOWN remains UNKNOWN.
