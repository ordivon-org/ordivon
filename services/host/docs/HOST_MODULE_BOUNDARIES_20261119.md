# Host 逻辑—能力边界与目录拆解（2026-11-19）

> 范围：Ordivon `services/host`，起点 Git `161b27aef46999d8d23e4a2b0fcc8b3488965761`。本文是**源码组织与消费者审计记录**，不是新的 Schema、Tool、权限或发布权威。现役服务、源工作区、测试结果各自独立。

## 1. 三步问题表征

- **目标**：多个 Agent 可以在中断、并发、交接后恢复可操作的语义状态、消费位置和协作证据；外部效果由 Git/Runtime/Security/Domain 自然 Owner 独立验证。
- **现实**：Host PostgreSQL14 Work/Social/Attention；MCP31 个已发布工具；Python 模块已按 Work/Social/Attention 部分分离，仍存在共享 ActorRef、读写 MRO、跨域 Attention 投影和双游标协作。
- **变化**：首先减少真正可移动的隐式业务归属，保持现有 SDK Tool ABI、PG Schema 和已安装服务不变。非独立消费者、不需要独立变更的职责不新建抽象与数据库。

## 2. Thought → Logic → Capability

| Thought LEGO 正向/逆向 | Logic 问题契约 | 承载的已有 Capability LEGO | 反例 / 不变量 |
| --- | --- | --- | --- |
| 状态机 + 重放/竞态反证 | Work Continuity | `work_store` / `work_queries` / PG 行锁与 CAS / Receipt | 旧 revision 覆写新快照、终态被重新打开 |
| 因果关系 + 乱序反证 | Social Collaboration | `social_*_commands/queries` / Message Relation / PG FK | 引用不存在、reply 顺序错误、消息摘要漂移 |
| 单调序列 + 漏读反证 | Consumption Continuity | `social_topic_commands`、`attention_store` / PG cursor | Attention change sequence 与 Topic message sequence 混用；未读先 ACK |
| 增量投影 + 冗余状态反证 | Attention | `attention_projections` / `attention_sql` | 已关注的事件被漏掉；把订阅当任务分配 |
| 语义引用 + 假权限反证 | Actor/Record References | `references/actor_*`、`record_refs` | ActorRef 当成已认证 Principal；声明即授权 |
| 权威分离 + 跨边界伪证反证 | External evidence navigation | `referenceRefs` / 自然 Owner readback | 文字中“完成”不等于 Job/Release/Domain 真相 |
| 信息隐藏 + 契约差异反证 | MCP / Lifecycle | `mcp_*_tools`、SDK、Pydantic、Alembic / 发布契约测试 | 源码工具数一样但参数改变；旧历史被错误清理 |

Thought 是设计与证伪方法；Logic 是稳定的输入、输出、状态转移和不变量；Capability 是实际可运行的实现与成熟依赖。不要求三者一对一对应包或服务。

## 3. 当前推荐的**实际**源码边界

```text
services/host/
├── pyproject.toml, mise.toml, mcp-surface.json   # 工具链与外部单一接口清单
├── migrations/                                   # Alembic PG schema 历史，不迁改
├── src/ordivon_host_v2/
│   ├── mcp_server.py                             # 稳定 build_server/main 入口
│   ├── http_transport.py, http_identity.py      # HTTP 传输/工作负载凭据，不是业务权限
│   ├── mcp_tool_registration.py                  # Work/Social/Attention/Actor 组合
│   ├── mcp_actor_tools.py                        # 本轮抽离的 actor.declare MCP 适配
│   ├── mcp_work_tools.py, mcp_social_tools.py, mcp_attention_tools.py
│   ├── references/
│   │   ├── actor_inputs.py, actor_contracts.py  # ActorRef 自有输入/输出类型
│   │   ├── actor_refs.py, actor_store.py         # ActorRef 声明与 PG 承载
│   │   └── record_refs.py                        # Host 内部 Work/Space/Topic 存在性
│   ├── work_store.py, work_queries.py, work_relation_commands.py
│   ├── social_store.py, social_*                 # Space/Topic/Message/Coordination
│   ├── attention_store.py, attention_projections.py, attention_sql.py
│   ├── postgres_connections.py, command_receipts.py, canonical_json.py
│   ├── health/diagnostics.py                     # 只读跨域健康投影
│   └── work_inputs.py, work_contracts.py          # 兼容 Actor 类型的旧导入路径
├── tests/                                        # PG、MCP、并发、因果、边界
└── packaging/                                    # 不可变安装/Release 认证
```

此图**保留**尚无真实独立变更理由的原顶层 Python 文件。不因目录美观而批量 `git mv`。若有消费者需要再拆 `work/`、`social/`、`attention/` 包，先同时修复 Source 路径消费者、规划文件、测试与工具链。

## 4. 本轮具体拆耦及兼容边界

**已从源码拆出的 Actor 声明职责：**
- 旧：`mcp_work_tools.register_work_tools` 注册 `actor.declare`，调用 `WorkStore.declare_actor`；Actor Input/Response 依附 Work 文件。
- 新：`mcp_actor_tools.register_actor_tools` 调用 `references.actor_store.ActorReferenceStore.declare_actor`；Actor Input/Response 由 `references/actor_inputs.py`、`actor_contracts.py` 承载。
- `WorkStore` 不再拥有 actor.declare；仅通过共享 `ActorReferenceLookup` 验证**语义引用存在**，它不判断访问授权。
- `work_inputs.py` / `work_contracts.py` 暂保留旧 Python 导入路径的显式重导出；数据库无迁移，原 `actor.declare` MCP 名/签名与回执格式不变。
- 原 PostgreSQL `actor_refs`、`command_receipts` 是同一权威表；不建第二个 Actor registry，也不新增外部 Tool。

**仍属有意的跨域耦合：**
- Attention SQL 对 Work/Social canonical rows 作**只读投影**；消除这种依赖将引入第二套事件真相，除非证明现实消费者必须缓存。
- Topic Cursor 由 Social 写、Attention Reentry 读，两个时钟域独立；需要契约边界，而非为追求纯包隔离复制状态。
- PG ConnectionPool、Receipt、Canonical JSON 是共享基础能力；保留一个实现。
- Operational Doctor 跨 Work/Social/Attention 检查，不拥有其写入。

**仍应基于实际反例再处理：**
- 多重继承的隐式 self 方法约束：检查 `SocialStore`、`WorkStore` 和各自查询/命令 facet；此前部分消息读取已改用显式 `social_message_records`。
- `CoordinationIntent` / `WorkRelation` 暂不可单凭业务行数少就删除：Attention、测试或内部消费者仍可能调用。
- 归档 WorkRefs 的现时缺失与历史恢复，只标历史引用，不伪造当前 Work。
- 角色 Principal → Social ActorRef 的安全绑定属于 Security/Ingress，不能通过 `actor.declare` 补一套授权逻辑。

## 5. ActorRef 能力型 LEGO（R2.1 scoped）

- **I**：`ActorRefInput(actor_ref, actor_kind)` + stable clientRequestId。
- **O**：原 `ActorRefResponse`（committed / existing），或精确冲突。
- **S**：原 Host PG `actor_refs` 与 `command_receipts`。
- **pre**：命名空间与类型有效；业务连接依照当前 Host PG 凭据进入。
- **post**：同一 ActorRef 相同 Kind 精确可重放；不同 Kind 冲突。
- **inv**：ActorRef 唯一且其 Kind 不会因重复声明静默变化；声明**不授予**执行权限。
- **eff**：同一 PG 事务中的 insert / receipt；没有域外效果。
- **c/epsilon**：PG 单操作成本及跨主体授权完整性尚无独立度量：分别保留 UNKNOWN 并给出独立 PG 负例与 Security/Ingress 消费者作为补充验证责任。
- **prov**：实际 `references/actor_refs.py`、`actor_store.py`、`mcp_actor_tools.py`；当前 Git Workspace SourceCut + Ruff/官方 MCP/独立 PG18 结果，提交与 Installed 须另查。
- **unfold**：`actor.declare` → MCP adapter → ActorReferenceStore → PG Receipt / unique ActorRef → 规范回执。

## 6. 交付门槛与停止规则

必须先验证 Ruff、当前测试、独立 PG18 全量测试、MCP tools/list 的名称与 Schema，以及源工作区的 diff/提交身份。**测试通过不等于已安装或跨 Gateway/Principal 消费者验收**。

除非有真实受影响的消费者，否则停止进一步目录搬移；优先修真实错误，再拆真实隐藏的变更理由。操作不允许清理他人 Workspace、历史 Work/Message PG 行或在线凭据。

## 7. R2 模块拆解：Topic 消费位置规则（2026-11-19）

**反向发现**：原 `SocialTopicCommands.ack_topic_cursor`、`SocialTopicReadQueries.get_topic_cursor`、`AttentionReadProjections.reentry` 分别读写 `topic_consumption_cursors`。即使没有循环 import，也存在三个不同修改位置会影响同一个游标不变量的风险。只把三个文件放到不同包中无法解决这个问题。

**最小源码变化**：新增 `topic_cursor_records.py`，集中提供事务内四个函数：`topic_high_sequence_in_tx`、`get_topic_cursor_in_tx`、`ack_topic_cursor_in_tx`、`list_topic_cursors_in_tx`。各调用方保留自己的事务、查验 Actor/Topic、命令回执及公开工具签名；Attention 保留一个 REPEATABLE READ MVCC cut，不新建第二个 PG 连接。Topic 消息消费游标与 Attention 全局变化游标仍然是两个不同坐标域。

- **正向**：读到 Actor/Topic 的已提交 cursor 和同事务 TopicHigh；ACK 单调推进；Attention 从当前已观察变化页得到精确 TopicRef 及 cursor。
- **逆向**：`cursor=True`、浮点、负数、越界、后退均拒绝；另一个 Topic 的超前游标不能被接收；Attention 不能用新快照覆盖旧事件页的消费位置。调用者尚未消费页时 ACK 是操作层面的误用，不通过多建数据库来假装可以阻止。
- **声明的责任**：`TopicCursor` 能力只负责原生 PG 的消费位置单调性；它不能证明 Agent 已理解消息、业务完成或身份已授权。
- **不变量**：一个 `(actorRef, topicRef)` 的 cursor 不会由合法 ACK 后退，不会超过对应 Topic 消息地平线；读取的事件页和游标在 Attention 中属于同一个 MVCC snapshot；`topic.cursor.get` 与 `topic.cursor.ack` 的外部 Wire 不变。
- **消费证据**：`tests/test_topic_cursor_boundary_r2.py` 覆盖源边界和前向/反向拒绝；`test_dual_cursor_horizon_postgres.py` 与 `test_attention_single_snapshot_postgres.py` 覆盖 PG 真并发和错域游标；最终还必须由完整 PG18 集成和原生 MCP 源测试验收。
- **不做**：不新建全局消费管理器、额外 Receipt registry、缓存、二级 EventStore 或新的 MCP tool，也不修改生产共享游标。

## 8. R2 模块拆解：Attention 的语义表征与 PG 查询分离

**问题性质**：同一 `AttentionReadProjections.reentry` 同时承载多源 PG 增量查询、Topic 消费位置读取、消息归组、原因集合归并、字节约束和继续游标计算。按信息隐藏原则，这里真正相互独立的变化轴不是“Work/Social/Attention”字面目录，而是 **PG 事实读取策略** 与 **Agent 恢复导航表征策略**。

**实际拆解**：
- `attention_projections.py`：仍在同一 READ ONLY / REPEATABLE READ 事务中完成 `_delta_in_tx` 与 Topic cursor 查询；只负责从真实 owner rows 获得精确输入。
- `attention_reentry.py`：无数据库依赖的纯函数 `reentry_topic_refs`、`project_reentry`；仅从有序的 delta 事件页与已取得的 Topic cursor 折叠、分组、裁剪一个可恢复导航投影。
- 原 `AttentionStore.reentry` / `attention.reentry` 工具名、Wire、cursor 语义、分组顺序、字节上限均不变。

**正向逻辑模块**：
`Input = (actorRef, afterSequence, bounded ordered delta events, cursors, maxBytes)`；
`Output = (grouped navigation items, rawEventCount, snapshotHighSequence, nextAfterSequence, hasMore)`；
同一个 `(navigationKind,navigationRef)` 折叠为一组，事件原因去重且排序，最新变更取最大，Topic 附上已消费 Topic cursor，不产生优先级或任务分配分数。

**逆向反例**：
- 若为了容纳字节预算随意丢掉中间事件，即使输出看似短也会破坏 `nextAfterSequence` 可恢复性；本实现只能选原事件页的完整**前缀**。
- 若重新查询 SQL 来生成更短页，便可能将不同时间点的事件与 cursor 拼在一起；本实现不发第二个 SQL。
- 若最后一个原事件之后仍有 `delta.hasMore`，即使投影经过归组变得很短，`hasMore` 仍不能说 false。
- 若把 Actor Social 订阅当成 Agent 任务优先级，会把导航事实升级为决定权；输出始终声明 `rankingApplied=false`。
- 若不能容纳一个导航项，不允许悄悄返回空页并推进消费坐标，必须显式拒绝。

**能力与验证**：复用 RFC8785 canonical JSON 字节长度、有限事件折叠与原生 PG 事务。新增 `test_attention_reentry_pure_r2.py` 验证归组顺序、游标和原因保真、最长有界前缀、拒绝容量不足；原 `test_attention_single_snapshot_postgres.py` 保持真实并发证明。同样不新建 EventStore、评分引擎或消息队列。

**后续变更门槛**：仅当有真实 Agent 导航漏事件、误 ACK 或可量化载荷开销时，才考虑进一步优化投影或分页；不因 Python 文件行数而添加更多中间层。
