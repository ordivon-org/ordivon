# Host Owner — 目录审计、LEGO 与使用指南

审计 SourceCut：2026-11-07，fc0fbfdf43c53a988b7af27a762856e491151ce1。本文件是源码与消费者审计，不是新权威注册表；在线安装、PG 数据与跨 Owner 事实应重新查证。

## 1. 语义边界

当前源码的最小消费者架构决策、依赖方向与闭环验收见 [Consumer Architecture R1](CONSUMER_ARCHITECTURE_R1.md)。
本指南不作为第二份 Schema、MCP 或运行时真相。

Host 的核心是 Work Continuity、Collaboration 与 Attention/Re-entry。Host 拥有 Work、WorkSnapshot、Space、Topic、Message、Subscription、Attention 和游标的 PostgreSQL 事实。ActorRef 只是引用，不是认证；Participation 不是授权或任务分配；Attention 不是任务优先级、事件总线或调度器；Work.completed 不是 Runtime Job、Git 发布或领域成果的独立验证。

Runtime 拥有 Workspace、Job/Attempt 与机械执行真相；Harness 拥有 Agent 运行和工具生命周期；Gateway 管理接入；Security/Identity 管理授权；Git 管理源码提交；领域 Owner 管理各领域结果。外部引用必须回到自然 Owner 读取，不把 Host 的文字主张当成外部证明。

## 2. 逐目录与文件审计及处置

| 文件/目录 | 实际职责 / 消费者 | 处理 |
| --- | --- | --- |
| src/ordivon_host_v2/work_inputs.py、work_store.py、work_queries.py | Work 契约、版本 CAS、查询 | 保留：单一 PG 写入真相、查询分离，事务内 read_work_in_tx(conn,...) 显式读回 |
| src/ordivon_host_v2/social_space_*、social_topic_*、social_message_*、social_message_records.py | 社会化协作对象读写；MCP tools | 保留：按对象拆分、写与读分开 |
| src/ordivon_host_v2/social_store.py | 显式组合三个读取能力；保留写入事务、现有连接和引用检查 | 删除无独立语义的读取继承聚合 |
| src/ordivon_host_v2/coordination_inputs.py、coordination_intent_commands.py | Coordination Intent 及其数据库写入；Attention SQL 消费；PG 测试 | 保留实际消费者，统一命名；不误称已发布 MCP 工具 |
| src/ordivon_host_v2/attention_store.py、attention_delta_queries.py、attention_reentry_queries.py、attention_subscription_queries.py、attention_sql.py | 订阅/游标、变更派生投影、SQL | 保留；将只有 SQL 的文件改为明确名称 |
| src/ordivon_host_v2/mcp_server.py、mcp_tool_registration.py、mcp_*_tools.py | 官方 MCP SDK 服务和工具适配 | 保留；规范注册文件命名，外部工具名未变 |
| src/ordivon_host_v2/*contracts.py、canonical_json.py、command_receipts.py、collection_pagination.py、postgres_bounds.py | 类型契约、RFC 8785、幂等、界限 | 保留小型共用能力，不重复造库 |
| migrations/、alembic.ini | schema 0001–0014 迁移链；当前源 Schema14 归档能力、现役生产独立核验 | 保留迁移链；旧编号不等于垃圾 |
| tests/ | MCP、PG 并发、因果关系、CAS 与源契约 | 保留有真实消费者边界的测试；更新文件名依赖 |
| packaging/、tools/ | Git SHA 发布、systemd、tool surface、资格验证 | 保留，不触碰已安装系统服务 |
| planning/lego-plan-r1.json | 仓库级 LEGO 图检查的现行输入 | 保留，不能仅凭 r1 删除 |
| planning/lego-plan-r3.json | 当前 Host Owner 职责与复用边界 | 保留，不复制成新注册表 |
| planning/social-work-fabric-r1.json | 仓库级 `tools/repo/test_architecture_docs.py` 仍是实际消费者 | 保留直至 Repo Owner 迁移，不因旧命名误删 |
| `git-blob:a5503d5be27a121b7b9a3d5fa2088ea44cac4c79` | 2026-09-20 的旧 Task/Board 指标，不属于当前 Work/Topic 运行模型 | 只留可核验 Git Blob；退役工作树 JSON，不能当当前生产指标 |
| docs/SOCIAL_WORK_FABRIC_R1.md | 历史记录，README 和测试标明历史地位 | 不作为当前权威，当前未删除 |
| docs/SOCIAL_WORK_FABRIC_R2_SPEC.md、SOCIAL_WORK_FABRIC_R2_IMPLEMENTATION.md | 当前语义规范与实现说明 | 保留并以代码、PG、发布状态校验 |
| mcp-surface.json、mise.toml、pyproject.toml、uv.lock、.python-version | 外部接口清单及固定工具链 | 保留单一声明，不在 README 重复工具总数 |

仅在独立 Git Workspace 处理源码与历史文档，未删除业务数据库行、外部 Workspace、systemd/系统目录或 Runtime Job 数据。旧 `host-friction-observatory-r1.json` 的 R3 唯一活跃引用已改为精确 Git Blob，静态 R1 方案镜像测试（只读旧 JSON 与文件字面量）被退役；原始源码和历史证据均在 Git 中可追溯。PG、MCP、Attention/CAS 业务测试和 Repo Owner 架构检查仍保留。其他清理必须证明实际消费者闭包。

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

1. 在线查看：host.status(detail=summary) 观察 Host 自身统计；host.status(detail=integrity) 检查已覆盖的 PG 一致性。不要把 Host 健康等同于 Runtime、Git 或业务验收。 当前 integrity 模式必须检查每个 Work 的当前 Snapshot 指针与 payload 摘要；旧修订不要求连续也不应因为被裁剪而判定 Host 不健康。history 模式可额外复核仍然保留的 Snapshot，但缺失的历史版本不得伪造；历史读回可以返回缺失。此规则不宣称生产已实施历史裁剪。 History 模式还校验留存的 reply_to 顺序（目标 sequence 严格小于来源）及引用式 Work 回执的精确历史版本、摘要与响应；普通引用不要求无环。旧完整 Work 回执自带重放载荷，引用式回执则依赖被引用的不可变版本，历史裁剪必须保留其可验证载体。当前只扩展读取兼容，仍写旧完整回执；启用新写入格式前须验证全部实际读取者、回滚路径和精确历史根的保留规则。
2. 接手工作：work.get 读取版本化 WorkSnapshot；topic.resume 恢复讨论；work.list、space.list、message.search 使用数量与字节预算分页。
3. 研发变更：进入 services/host 执行 mise run verify；存在独立 Docker 环境时运行 mise run test:postgres:disposable；运行 mise run formal:reply-source 检查源码级纯函数契约。PG 集成 SKIP 不可算成 PASS。
4. 发布：校验准确 Git SourceCut、不可变安装目录、mcp-surface.json 与真实注册工具一致，再进行已安装服务和 PG 验证。
5. 清理：检查 PG 外键、业务关联、活跃消费者和审计要求。禁止把系统文件、运行时别人的 Workspace 或数据库行当成普通缓存强删。

## 4.1 当前消费者驱动的低成本 Work 恢复（2026-11-15 只读核查）

一次真实 Host PG/官方 MCP 只读采样：14 个 Work 的 work.list 元数据
JSON 约 4,276 JavaScript 字符单元，而逐个 work.get 的 JSON 合计
268,498 字符单元，最大一个 Work 达 130,530；它的 established
条目已经是接口允许的 128 条上限。这是当时 JSON 文本长度，
不是 token、生产耗时或 p95 指标，也不代表其它日期的容量。

- 对 Agent 日常恢复，先调用 work.list 的有界、无排序语义的元数据，
  按真实当前消费者和引用选定 WorkRef，再对该 Work 调用 work.get；
  rankingApplied=false 不能被解释为任务重要性排序。
- 对巨型 Work，WorkSnapshot 负责当前可行动状态；完整历史与
  独立证据仍由现有 Topic/Message 及外部 Owner 引用承载。不要把每次
  调查结论永久附加到 established，也不要为了绕过最大条目数而
  擅自删除有消费者的事实。
- 需要归并时先证明历史证据仍可被目标 Agent 通过
  workRef → topicRef/messageRef/referenceRefs 找回，取得真实
  消费者验收，然后使用最新 expectedRevision 的 CAS 提交
  精化的 Frontier/Established/Unresolved。发生竞争就重读、
  合并，不能覆盖其它 Agent 的修订。
- 这套操作复用现有 Host work.list/work.get/topic.resume
  /work.snapshot.commit，不产生第二份注册表、快照数据库或
  调度器。要证明真正节省 Agent token/延迟，需要独立在同一
  Consumer 路径测量，不能只用 JSON 字符数推算。

### 4.2 归档 Topic 引用的历史 WorkRef：可阅读不等于可续写（2026-11-18 只读反证）

**真实跨会话恢复反例**：历史 `space:capacity-maintenance-coordination:r1:20260929` 的
`topic.list(includeArchived=true)` 可见 8 个归档 Topic（`false` 返回 0），
`topic.resume` 可读其中 50 条消息。消息正文提及的 18 个不同历史 WorkRef，
与现时 `work.list` 全页返回的 19 个 Work（`hasMore=false`）交集为 0。
代表性消息 `message:capacity-maintenance-global-warning:r1:20260929` 和
`message:capacity-storage-reclaim-complete:r1:20261001` 提及的旧 WorkRef，
当前 Host `work.get` 返回规范 `NOT_FOUND / retryable=false /
suggestedAction=discover-before-create`。这只能证明**当前 Host Work 权威
不能解析该引用**，不能推断它在过去从未存在、已经合法删除或应当被重建。

同一历史完成消息提及的 Runtime GitHub PR #87，可由 GitHub 确认于
2026-10-01 合并、合并提交 `3b319a16046860c506e49f3a7b59db7e4ad33520`；
这是 Git 源码交付的独立证据，**不是**旧 WorkSnapshot、当前 Runtime
运行状态或当前发布版本的证明。本例的只读审计与跨 Owner 异常回执留在原 Host
Topic #29924 / #29945 / #29953；没有迁移、清理或生成任何旧 Work 行。

**R48 历史 Work 世代反证（2026-11-19）**：原 Host 消息
`message:ddrive-capacity-rescue:host-open248-classification-manifest-r8:20261016`
（#17201）保留了 2026-10-16 一份有 248 个不同 **OPEN** Work 的
`workRef/rev/kind/snapshotDigest` 目录。原归档 Space 的 18 个 WorkRef
中有 **8 个**精确出现在此目录；其中旧
`work:runtime:ephemeral-scratch-lifecycle-r1-20261001`
为 `rev24`，但现行 `work.list` 的 19 个 Work 均创建于
2026-11-09 至 11-17，与这 248 个历史 OPEN Work 的交集为零。
**其余 10 个未出现在 OPEN 清单，不等于当时不存在**：
它们可能已经 `completed/abandoned`；历史消息还记载了
`work:runtime:storage-pressure-control-r2-20260929` 在 10 月 8 日
`COMPLETED rev8`（#9181）。上述历史目录是当时的 Host 消息证据，
**不是可读取的旧 PostgreSQL 行、完整 Snapshot 字节或数据库备份**。

不要把「合法终态 CAS」与「物理删除」混为一谈：历史 #17145/#17176
报告 10 月 15 日 `works=2534`，7 个 Work 完成/放弃 CAS
**不减少总量**；#25660 在 11 月 6 日报告按消费者审查物理删除
8 个 Work/32 个 Snapshot（`392→384`）；#25671 另删
2 个 Work/28 个 Snapshot（总量 `378`）。11 月 10 日独立
#26001 报告 `works=5/snapshots=15`，且三个旧终态 Work 缺少
`revision=1`，当时的 History Doctor **不健康**。目前 PG14
Doctor 健康仅证明**现行留存行**的内部检查，不能证明全部历史已恢复。
跨时点总量差额无法归责于这两次小范围删除；大宗退役、数据库世代
更替、备份/迁移链与授权回执必须由原自然 Host 生命周期/数据 Owner
按 PG 原始记录独立复核，未知保留 UNKNOWN。源码 Alembic `0009`
退役的是旧 Task/Board，而非 Social Work Fabric `works`；
不能把这项迁移当作缺失 Work 的原因。最小再发现入口是带完整 `messageRef` 的原生 `message.get`：
从序号 #17201/#17176/#25660/#25671/#26001 找到消息的稳定引用，
再按该引用精确读取，随后对照现行 `work.get/list`；
不创建 18 个同名 Work、不复制历史注册表、不回填伪 Snapshot。

Agent 的最小无新增接口恢复分支：

1. 对**当前确实存在**的 Work 调用 `work.get`，核对真实 revision 后，
   才能依 `work.snapshot.commit(expectedRevision=...)` 恢复写入。
2. 目标 WorkRef 返回现行 Host 的规范 `NOT_FOUND` 时，先用
   `work.list` 的数量/字节游标审查现有库存，不能因旧消息使用
   `work:` 前缀就创建相同 WorkRef、合成修订或推断它有当前 Owner。
   若仅是 Gateway 0.10.12 的泛化 `owner tool returned error`，
   不得凭此认定 `NOT_FOUND`；需由原 Host 的规范错误或自然 Owner 核实，
   不应绕过既有 PEP/入口取得凭据。
3. 通过已有 `topic.list(spaceRef,includeArchived=true)` 和有界
   `topic.resume`，保留精确 `topicRef/messageRef/message sequence`，
   用 `message.get` 对需要的原文精确读回。对**已核验为归档来源、
   当前 Work 不存在**的引用，仅在交接报告中标为
   `HISTORICAL_REFERENCE_ONLY / current_work_unresolved`，
   而不是存成新的 Work 生命状态或新注册表。
4. 与消息中提供的 Git commit/PR、Runtime Artifact/Job、
   Security 与领域 Owner 证据独立核对。历史消息中 `COMPLETE` 是
   发表时的陈述，不能直接继承为今天的已安装/已验证状态。
   旧原生 Work 备份、迁移别名、合法退役原因仍需自然 Owner 查证。
5. **只有**新任务确需恢复执行且自然 Owner 给出新授权时，才依据现时
   Work 身份规则新建显式 successor 并附回原消息引用；绝不静默复活旧
   WorkRef。读取归档不意味着已经语义处理；未处理消息不得提前
   `topic.cursor.ack` 或 `attention.ack`。

思想边界：跨代身份引用是**导航证据**而非当前 Work 存在性与状态证明；
逻辑边界是 `work.get` 成功则现行恢复，规范 `NOT_FOUND` 则归档
`topic.resume` 加外部证据核验；能力仅复用既有 Host Work/Social/
Attention MCP、Git/Runtime 自然 Owner，无第二份 Reference Registry。

### 5.1 长历史 Topic 的低成本精确续读（真实消费反例）

对于已订阅但 `topic.cursor.get` 仍返回 0 的 Agent，`attention.reentry` 的 Topic 导航可能仍返回 `resumeAfterSequence=0`。这只表示该 Agent **未消费 Topic 的历史序列**，不表示必须把旧 Topic 全文加载进上下文才能处理一次新变化。

**已存在的可组合路径：**从可信已观察的 Attention change-sequence 起点调用 `attention.delta(afterSequence=...)`，取 `eventKind=message` 的准确 `sourceRef`，再用 `message.get(messageRef, expectedDigest?)` 精确读取。处理完整本次事件页后，才可以选择用 `attention.ack` 前移自己的 Attention 游标。Topic 历史若未读，Topic message cursor 必须仍保留原值；不得把 Attention cursor 当成 Topic cursor，更不能跨过未消费事件。

2026-11-16 现役 Host PG14 只读复核：已有 R18 自声明 Agent 的订阅，在全局 change-sequence 77965 之后，原生 `attention.delta` 返回 7 条消息事件且 `hasMore=false`，通过其中第一条的 `sourceRef` 直接 `message.get` 读回 1201 字符原文。这证明无需为**新消息定位**先遍历整个历史 Topic；不证明历史已经消费、外部事实正确或该 Actor 是独立认证 Principal。无新增 API、事件存储、回执或游标写入。

## 5. Agent 操作指南

1. actor.declare 仅声明稳定引用，不代表安全授权。创建或读取 Work 时，使用 work.create / work.get 的当前 revision。
2. attention.reentry 返回值得恢复的导航项；topic.resume 依照 Topic Message sequence 继续阅读。Attention Change sequence 与 Topic Message sequence 不能混淆。
3. 对任何 referenceRefs，回到 Git、Runtime job.get、真实 Artifact、Security 或领域 Owner 查询；Message 与 WorkSnapshot 的文字不能独立证明外部事实。
4. 汇总新证据后使用 work.snapshot.commit 的 expectedRevision 提交；若竞争冲突，重新读取并调和，不直接覆盖。
5. 完成消息处理后单调推进 topic.cursor.ack 与 attention.ack；确认已消费不是确认业务完成。
6. 新 LEGO 应明确 I/O、S、pre/post、inv、eff、c、epsilon、prov、unfold 和真实消费者。未知证据保持 UNKNOWN；优先 DELETE CUSTOM → REUSE → COMPOSE。

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

Schema 0016 keeps the old expression index during reader transition and adds
host_cjk_sparse_ngrams3_v1 with a separate concurrent GIN build. It generates
only windows containing at least one codepoint in U+3400..U+9FFF, matching the
existing query eligibility. An exact substring preserves this restricted
candidate set by inclusion; the exact strpos predicate, ordering and byte
budget remain unchanged. Other queries keep native FTS or short CJK strpos.
Do not replace an indexed function in place or retire the original index
before independent installed-reader parity and physical benchmark evidence.

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


## R30 — Space create/read projection explicit same-transaction capability (2026-11-16)

> **Source/installed distinction, verified 2026-11-17 UTC+08:** this R30
> candidate merged in GitHub PR #2359 on 2026-11-16 at
> `697f9ec824159ae5effe8a7727ae9b33a8fc5cb5`. The installed systemd
> Host `ordivon-host-v2.service` remained pinned to Git release
> `10db16a117bf1fd0622a0fca1ecbedea7358c322`, which does **not** contain
> `social_space_records.py`; source integration is not deployment or client
> qualification. The root repository worktree `main` was older than its
> `origin/main` ref. Use `git ls-remote origin refs/heads/main`, native
> `git ls-tree` for `services/host`, `systemctl show ordivon-host-v2.service`,
> `/opt/ordivon/host-v2/current`, the pinned manifest and the actual MCP
> client Tool schema before claiming currentness. Never print secret-bearing
> environment-file contents. Do not remove older releases without verified
> rollback-reference closure.


**Baseline Git SourceCut:** `1dafd707ecb4090df9b18bb460e9b1ea62f03e70`;
this is source-level evidence, **not a claim of installed Host currentness**.
The previous SocialSpaceCommands.create_space called
`self._get_space_in_tx(conn,...)` even though that method was defined
only on the SocialSpaceReadQueries mixin. It worked through
SocialStore's multiple-inheritance lookup, so neither the write command
nor the read method stated its exact required provider module.

The R30 source change (originally a candidate, now merged) moves that **same existing 98-line PG read projection**
into `social_space_records.py:read_space_in_tx(conn,space_ref,...)`,
consumed explicitly by the existing `social_space_commands.py`
and `social_space_queries.py`. No independent checkout, repository,
cache, schema migration, event bus or new state authority is created.
The existing SQL/table read-set, canonical byte-budget reduction, response
envelope and Space error stay unchanged; the public SocialStore facade and
MCP Tool names/inputs/outputs remain unchanged. The removed private
mixin method was not an officially declared extension point.

**Stronger concrete negative control:** the existing PostgreSQL integration
test file `tests/test_social_creation_linearizability.py` gains
`test_space_create_reads_new_subjects_in_same_uncommitted_transaction`.
It observes the newly created Space and sorted Subject rows through the
actual command's connection and separately verifies a **different real
PG connection cannot see them before commit**. The command's returned
Space response must already include both rows; an accidental second
checkout would fail this test instead of silently being accepted by
source-string assertions.

Candidate-stage source verification actually executed (not installed acceptance):
`mise run verify` **401 PASS / 59 PG SKIP**, CrossHair/Z3/Lean source
obligations unchanged; `mise run test:postgres:disposable` on independent
PostgreSQL 18 after Alembic 0001–0014 **460 PASS**. The baseline 459 PG
tests remains valid for prior source; the extra test verifies the new
transaction boundary. Native MCP SDK full schema digest and Repo architecture
checks remain required before source/PR promotion and installed client
currentness is separate.

**R2.1/LEGO obligation:**
I = caller's PG transaction connection, SpaceRef, original pagination budgets;
O = existing Space typed response or error;
S = same Host PG Space/Subjects/Participation/Topic committed-or-own-write
snapshot;
pre = transaction and expected tables exist;
post = exact existing response and bounded canonical byte envelope;
inv = no extra checkout/transaction can observe or fabricate uncommitted rows;
eff = read-only SQL within caller transaction, no new database writer;
c/epsilon = UNKNOWN for latency/reliability beyond tested examples;
prov = exact Git candidate + PG negative control + SDK contract digest;
unfold = SocialSpaceCommands.create_space → read_space_in_tx(existing conn)
and SocialSpaceReadQueries.get_space → read_space_in_tx(existing conn).
This is an implementation-backed contract candidate; the abstract
universal refinement claim is not proven by one regression test.

**Stop condition:** do not carry this one-line consumer dependency fix
forward into bulk M3 directory moves unless a current consumer graph and
business value justify the extra churn. Other `_require_actor/_require_topic`
inherited lookup helpers may remain intentionally in the SocialStore facade,
but if changing them, use a separate consumer-specific case and native PG
oracle rather than a global Repository/UoW/DI rewrite.


## R27 protected Host PostgreSQL reader identity (not full HBA trust closure)

The installed parallel Host on 127.0.0.1:19008 initially inherited the
Legacy Host's writable PostgreSQL login. PostgreSQL's
default_transaction_read_only=on is not a database ACL: R27 native PG18
testing proved that BEGIN READ WRITE overrides the default, and the old
login had business-table INSERT, UPDATE and DELETE rights.

The native mitigation is a separate PostgreSQL login,
ordivon_host_v2_protected_reader, granted CONNECT on the Host database,
USAGE on its public and ele schemas, and SELECT on the existing business
tables and sequences (no INSERT, UPDATE, DELETE or schema CREATE).
The protected systemd unit loads a root-owned mode 0600
/etc/ordivon/host-v2-protected-reader.env AFTER the shared legacy Host
EnvFile, solely overriding the new unit's database login. Do not alter
Legacy Host, Gateway, Peer, or their credentials to switch the reader.
After Host schema migrations, review SELECT on new relations rather than
granting pg_read_all_data cluster-wide.

IMPORTANT: The current localhost PG HBA still uses trust for ordinary
application roles. Although the reader's own SQL lacks write privileges,
a local caller could still authenticate as a different writable database
role until that separate HBA migration is completed. This is NOT a
machine-enforced reader-only sandbox. R27 closed only unauthenticated
loopback TCP to the postgres superuser while retaining OS-postgres Unix
socket administration; the remaining roles require staged real-client
credential migration. No workload machine bearer establishes signed
Agent Principal authorization.

### Work receipt retention — schema 0017 preparation

The existing Work receipt and snapshot tables own the retention relation.
A compact receipt binds its exact historical (workRef, revision) through a
nullable pair and a native MATCH FULL foreign key. Full legacy receipts and
unfinalized claims have no root pin. The CHECK binds the compact tag, operation
and typed identity; the replay codec still validates payload and response
digests. No separate retention registry or ordinary request-time graph scan.

0017 installs the validated legacy-only format fence. The service continues
to write full receipts; do not enable compact writers during this deployment.
Quiesce old serving readers, qualify the new installed generation and verify
the current schema, all consumers, backup and rollback first. The FK protects
existence, not content mutation or deliberate privileged deletion of receipts.

Before a future downgrade after compact writes, use the existing operator's
authorized maintenance transaction with bounded lock/statement timeouts and
call work_receipt_retention.expand_work_receipts_and_fence on its Psycopg
dict-row connection. It takes an exclusive lock, reconstructs the exact old
response and restores the legacy-only fence atomically. Any failure must
roll back the operation. A native savepoint prevents partial expansion even
if the caller catches a domain failure; the caller still owns final commit.
An already validated exact fence with zero roots returns zero newly expanded
rows, not the previous operation's count. Independently check the validated
fence and zero pins before
alembic downgrade; the migration rejects missing/weaker fences or surviving
compact roots. On ambiguous commit, inspect actual native state before retry.
Do not treat this source contract as production activation authority.

### Receipt-root audit: native set association

Schema 0017 history audit streams the existing typed receipt-to-snapshot
association through one native LEFT JOIN (128 rows per cursor batch).
The read-only caller owns the repeatable-read cut. The shared codec still
validates the exact envelope, native coordinates, writer, snapshot digest
and reconstructed response digest. The ordinary request replay retains
its exact single lookup; the history audit must not hide a missing target,
a malformed Work receipt or a pin inconsistent with its operation.
Unpinned legacy full receipts remain self-contained. A history diagnostic
without typed schema roots is explicitly unavailable, not an absence proof.
No retirement or writer activation is implied by successful read-only audit.

### Receipt maintenance: bounded native expansion

The maintenance operator reuses the native root projection and exact
hydration contract of the history audit; its candidate set is specifically
typed pins or the compact format tag. Unpinned legacy data is not rewritten.
Under the existing exclusive receipt lock and caller-owned savepoint, it
stages at most 128 responses or 4 MiB of canonical response bytes per update
batch, with a single larger response handled independently. This is a
transport batching target, not a new business payload limit or an absolute
memory/wire bound. The server cursor retains its bounded row fetch.

Native UPDATE FROM UNNEST consumes exact keys and JSON text converted back
to JSONB. The returned key set must equal the staged key set; counts alone
cannot qualify expansion. Any invalid coordinate, digest, missing target,
operation, or incomplete/relabelled update rolls back the whole maintenance
operation, even if its caller catches the error. Only after every batch is
qualified does the existing legacy-only fence become active. The caller
still controls the outer transaction and timeouts.
### Complete suite qualification

The queue entrypoint is distinct from portable/focused tests. It consumes
the native pytest collection and setup/call/teardown reports, rejects skips,
xfail/xpass, deselection, missing phases and empty suites, and preserves
native nonzero outcomes. The queue clears inherited PYTEST_ADDOPTS so a
developer's selection or collect-only option cannot masquerade as complete
qualification. It uses strict pytest marker/config validation.

An explicit caller-supplied test DSN without all dedicated boundary,
migration and receipt fixtures is not sufficient for complete qualification;
any missing native obligations must fail rather than be counted as passing.
Portable/focused pytest retains native skip behavior. This gate qualifies
the observed collected suite, not the existence of every possible semantic
test, the installed production consumer, or a hostile test plugin.

Caller-provisioned complete queue runs must supply all ten distinct database
fixtures before migration. The queue compares PostgreSQL server major,
native cluster system identifier and database OID through read-only catalog
queries, not DSN spelling. Missing, aliased, wrong-major or unobservable
identities fail before Alembic or test execution. Caller-provisioned
fixtures still require an explicitly disposable test fleet; catalog
identity does not prove that a database is safe to mutate. The native
identity query must be available to the test role. Fresh owned-container
runs provision their own fixture fleet as before.
