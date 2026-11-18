# Ordivon Host R1：Thought → Logic → Capability LEGO 与源码边界

> 基线：2026-11-19，services/host 源码、PG Schema14、origin/main 587b6f74；本文件是架构与源码重构证据，不是现役发布证明。

## 一、目标—现实—变化

- 目标：Host 是 Agent Collaboration & Continuity Kernel。Agent 离开、重连、换执行者后可以找回原 Work、Topic、Message 和错过的变化。
- 现实：Work、Social、Attention 已有独立状态域和成熟 PG 事务、CAS、幂等回执、变化序列、有界游标；源码是平铺的 Python 模块组合，并不等于没有边界。
- 必要变化：让跨域引用检查成为一份 PG Capability；让 ActorRef 声明成为独立语义命令；保持已有 31 个 MCP Tool、PG14 Schema 与现有消费者行为。
- 禁区：Host 不负责执行 Runtime Job、Git Commit、领域效果真相、访问授权和任务调度。ActorRef 与用户真正的身份 Principal 是不同概念。

## 二、四个最小业务问题

| 消费者问题 | 可验收答案 | 失败反例 |
|---|---|---|
| 我正在做什么？ | Work.Get 得到原 Work 与精确 revision；snapshot.commit 用 CAS 提交 | 恢复到过期快照或并发更新被覆盖 |
| 我们讨论过什么？ | Topic.Resume(afterSequence) 有界读到正确的 Message 与 reply 因果链 | 同 Topic 并发写序列与提交可见性不一致 |
| 我错过了什么？ | Attention.Reentry 得到订阅对应的变化、可恢复 Topic 消费坐标 | 处理前 Ack 导致事件永久跳过 |
| 什么是真的？ | Host 只证明自己语义记录的完整性，外部效果向自然 Owner 查询 | Work 完成被误认成进程已经退出或源码已部署 |

## 三、Thought LEGO：正向与逆向作为逻辑设计约束

**正向 Thought**：Consumer-first、Natural Owner、DDD 聚合一致性、原生 PG/MVCC、确切类型/字节分页、简单稳定的接口与最少新状态。

**逆向 Thought**：失去工具响应、进程断开、双写者并发、Topic Archived、旧 Work 缺失、伪造 ActorRef、未知外部执行结果等反例。UNKNOWN 不能直接变成 FALSE。

Thought 是约束与审计方法，不需要每次请求都经过独立的“思想审批器”。

## 四、逻辑 LEGO → 需求 → 能力 LEGO → 源文件

| Logic LEGO（问题重组） | 核心不变量（需求） | 主要 Capability LEGO（执行） | 当前实现 |
|---|---|---|---|
| ActorReference | ActorRef 稳定/幂等，非认证与授权 | PG unique + receipt + input schema | 新 domain/actor_reference_commands.py、work_inputs.py |
| WorkContinuity | 一 Work 当前 revision、历史精确可读、CAS 拒绝冲突 | PG transaction、digest、CAS、bounded query | work_store.py、work_queries.py、work_relation_commands.py |
| SocialCausality | Space/Topic/Message 归属、回复只指向本 Topic 更早消息、并发顺序可见 | PG Topic row-lock、Message sequence、receipt | social_*_commands.py、social_*_queries.py、social_message_records.py |
| CollaborationIntent | 只声明协作意图，不等于派工、资源锁或成功效果 | PG intent rows、唯一键、状态转换 | coordination_intent_commands.py、coordination_inputs.py |
| AttentionReentry | Follow 与 Topic 消费游标分离；只有实际处理后 Ack | ChangeClock、MVCC、bounded cursor、SQL projection | attention_store.py、attention_projections.py、attention_sql.py |
| SemanticIntegrity | 参数化引用检查、精确错误、相同请求重放、冲突不写入 | PG References、Canonical JSON、Command Receipt | 新 capabilities/postgres_references.py、canonical_json.py、command_receipts.py |
| Lifecycle/History | Archived 不等于不存在；旧历史不能无证销毁 | Topic state、explicit archived query、Alembic | social_topic_commands.py、social_topic_queries.py、migrations/0014 |
| TruthBoundary | 自己的语义事实不推导其他系统效果 | Domain contract、Error mapping、Doctor | service.py、contracts.py、mcp_domain_errors.py |

一个 Logic 可组合多个 Capability，一个 Capability 可以服务多个 Logic；不是每个思想/逻辑都必须对应一个进程、一张表或一个目录。

## 五、现实的 Capability 边界

- **PostgreSQL Session/Transaction**：postgres_connections.py 与 Alembic Schema14，只有一份 Host 语义 Authority；业务命令控制事务。
- **Reference Integrity**：新 capabilities/postgres_references.py，工作/社交/注意力三 Store 共享 Actor/Work/Space/Topic 检查；Topic FOR NO KEY UPDATE 锁保持写前时序；不存在就用原异常，绝非鉴权。
- **Idempotency/Identity**：command_receipts.py、canonical_json.py；响应丢失重连不重复写，内容改变同 Request ID 则 Conflict。
- **Read Projections**：work_queries.py、social_read_queries.py、attention_projections.py 与 collection_pagination.py；均从主数据构建，不再创建缓存权威。
- **MCP DTO/Adapters**：mcp_server.py、mcp_tool_registration.py、mcp_work_tools.py、mcp_social_tools.py、mcp_attention_tools.py，保持稳定 31-tool API。
- **Authentication/Ingress**：http_identity.py 与 http_transport.py，已由 PR #2456 源码合并，复用官方 MCP Bearer/Auth 中间件；不能在 Work/Social/Attention 重造一套 IAM。
- **Operator Observation**：service.py、native_pool_observability.py 的 Doctor/Pool 只做真实 Host 数据完整性与容量，不是 Agent 任务管理。

## 六、本轮真实目录重构

~~~text
services/host/src/ordivon_host_v2/
  domain/
    __init__.py
    actor_reference_commands.py      NEW：ActorRef 声明与原 PG receipt
  capabilities/
    __init__.py
    postgres_references.py           NEW：参数化引用检查和 Topic 行锁
  work_store.py                      保留 Work 命令、CAS、兼容公开 declare_actor
  social_store.py                    保留 Social Facet 命令和读组合
  attention_store.py                 保留 Follow、Unfollow、Ack，复用引用适配
  http_identity.py                   既有身份校验边界
  http_transport.py                  既有 HTTP 入口边界
  mcp_*.py                           既有 31 Tool 对外适配
~~~

从三个 Store 里删除了重复的数据库引用判断，将它们组合到一个 capability。原 actor.declare 本来在 WorkStore 中，现在移动到 ActorReferenceCommands，但 WorkStore 继续继承该方法，因此老 MCP/SDK 不必换接口。

**Topic row lock 保证顺序的现有语义完全不变**。Attention 只接受 Work/Space/Topic 三种静态表映射；引用值用 PostgreSQL 参数传递，不参与 SQL 代码构造。没有引入新的 AuthZEN、Actor Registry、事件总线、权限数据库或中间代理层。

## 七、后续可演进目录（不是先建空目录）

~~~text
ordivon_host_v2/
  domain/
    actor_reference_commands.py       DONE
    work/                             在真实消费者验收后才搬现有 Work 命令/查询
    social/                           在真实消费者验收后才搬 Space/Topic/Message/Intent
    attention/                        在真实消费者验收后才搬 Follow/Reentry/Cursor
  capabilities/
    postgres_references.py            DONE
    postgres_connections.py           当前已有，不急着机械搬迁
    command_receipts.py               当前已有，不急着改名包装
    canonical_json.py                 当前已有，不急着复制
    collection_pagination.py          当前已有，不急着复制
  adapters/
    mcp/                              原 mcp_*.py 可在 Tool ABI 不变时归类
    http/                             原 http_identity/http_transport 已经解耦
  service.py                          保持兼容组合/Doctor 入口
~~~

坚持 DELETE-CUSTOM → REUSE → COMPOSE；只有实际相互纠缠且测试提供价值时才移动。避免仅为“层级好看”新增重导出、兼容代理、审批器及模块循环。

## 八、必须保护的事实和未完成事项

1. ActorRef / Participation 只表示社交记录，不能隐式授权任何 Work/Topic/外部资源访问。
2. Host 的 Work.state 和 Intent 不等于 Runtime Job/Attempt 成功、Git commit 或 Artifact 已交付。
3. 同 Topic 事务提交顺序不能靠自增 ID 推断；写前 Topic 行锁继续保留。
4. Attention Ack 必须发生在消息/变化确实完整被消费之后；不能将游标抢先推进。
5. Archived Topic 不能被误判为不存在；18 个已从离线存储恢复的旧 Work/101 Snapshots 尚未成为当前业务状态，不自动导入。
6. 当前 PostgreSQL14、数据、表结构、系统服务、旧 Host 8898/受保护 19008/Gateway 不因纯源码拆分而变更。
7. 最低验证为完整 Python pytest / Ruff、MCP 工具接口回归。源码合并不代表 Installed；现役安装另需真实 Work/Message/Attention 消费者、正负 Bearer 和 PG role 边界验收。
