# Host：从问题逻辑到能力 LEGO 的结构设计（R58）

本文件依据 Host 当前 PostgreSQL schema 14、31 个 MCP Tool 与 `src/ordivon_host_v2/` 真实调用链整理。它是**问题和代码的导航**，不是第二份运行权限策略、MCP Tool 注册表、任务执行引擎或审批机制。

## 1. 最小需求域

**目标（G）**：Agent 退出、换人、并发或断线后，下一执行者能恢复已有工作语义、协作上下文和消费坐标，并把不确定写入与真正已提交效果区分开。

**现状（O）**：Host 通过 PostgreSQL 保存当前 Work Snapshot、Space/Topic/Message/Relation、Subscription、Attention Cursor；MCP 入口使用原生 SDK。消息/工作记录不验证 Runtime/Git/领域执行的外部结果。

**变化（Δ）**：保留独立 Work/Social/Attention 能力与 PostgreSQL 单一真实来源；共享 ActorRef 声明/存在性检查从 Work 业务中抽出；横跨 Work/Social/Attention 的 Doctor 查询从 `HostV2` 服务入口抽出。接口调用结果与源码/安装/领域消费事实各自验收。

### 三种 LEGO 并非文件类型

- **思想型（方法约束）**：正向用消费者目标→最小必要表示→业务操作；逆向用重启、重试、竞态、误删和错误身份等反例寻找最小失效条件；坚持必要事实与 UNKNOWN，删去无消费者机制。
- **逻辑型（问题表征）**：把失败情境改写成状态、不变量、恢复坐标及验收条件。它可以横跨多个能力，不应机械地对应新 Python 文件或新表。
- **能力型（可执行契约）**：有明确入参/结果、数据真相归属、原生 PostgreSQL/MCP 实现与正负测试；多个逻辑模块可以组合调用同一能力。

## 2. 逻辑模块与实际能力映射

| 逻辑表征 / 典型问题 | 思想型方法 | 转换后的可验收需求 | 能力 LEGO（现有实现） |
| --- | --- | --- | --- |
| L1 语义连续性：更换 Agent 后丢当前进度 | 逆向恢复、最小充分状态 | Work.get 找到当前版本；提交只允许 CAS 当前修订 | Work Ledger：`work_store.py` / `work_queries.py` |
| L2 并发与丢响应：重复写、覆盖已提交工作 | 竞争反例、幂等优先 | 同请求重放 existing，异值 conflict；每次状态更新原子提交 | `command_receipts.py`、`canonical_json.py`、Work CAS、Message insert |
| L3 协作因果：消息顺序与关联关系 | 序列不变量、逆向反例 | Topic 顺序有界；回复指向更早 Message；外部引用不伪造来源 | `social_space_*`、`social_topic_*`、`social_message_*` |
| L4 注意力恢复：冷启动漏掉新消息 | 从漏读反推双游标；同一快照裁剪 | Attention change horizon 与 Topic message horizon 区分；分页不跳过相关记录 | `attention_store.py`、`attention_projections.py`、`attention_sql.py` |
| L5 生命周期：老内容清理造成唯一成果丢失 | 消费者闭包、逆向可恢复 | 归档仍能精确读；没有确认外部消费者结束时不物理删除 | Work terminal CAS、Topic archive、原 Owner 读回 |
| L6 身份与权限混淆：ActorRef 被误当认证主体 | 拆分引用和权限；最少信任边界 | 声明/存在性只维护社会引用；认证由 Host/Gateway 入口承担；PG Role 独立 | `references/actor_refs.py`、`http_identity.py`、`http_transport.py` |
| L7 内部真相可信：Work/Social/Attention 之间数据漂移 | 独立证伪、UNKNOWN 不变 PASS | 完整性查询使用同一只读事务快照；跨域真实效果留给 Runtime/Git | `health/diagnostics.py`、`service.py` |
| L8 接口/协议与业务解耦：入口改动影响实体存储 | 表征/执行分离、直接复用成熟 SDK | 既有 MCP 名称、入参/出参、正负认证不变化 | `mcp_*_tools.py`、`mcp_tool_registration.py`、`http_transport.py` |

## 3. 能力边界与共享底座

```text
Agent/Human Client
   |
   v
HTTP identity + native MCP port          [Transport / Access]
   |
   +---- Work semantic ledger ----------- [Work Snapshot / CAS]
   +---- Social causal graph ------------ [Space / Topic / Message / Relation]
   +---- Attention re-entry ------------- [Subscription / two cursors / projections]
   +---- Host diagnostics --------------- [Read-only consistency projection]
             |                    |
       ActorRef reference   canonical digest/receipt
           (not IAM)            (not event bus)
             \                    /
                 PostgreSQL
             (one data authority)

Runtime / Git / Artifact / Security: external truth owners; only refs, no claimed effect proof
```

能力契约最硬的三个交点：① Work 当前修订与 Snapshot 的 CAS 原子性；② MessageRef 与提交回执的同事务身份/重试一致性；③ Attention/Topic 各自游标的同快照分页和确认顺序。若这三个失效，更多 Agent 层级或审批记录也无法修复恢复能力。

## 4. 逐文件目录整理（已实现 vs 待证必要）

```text
services/host/src/ordivon_host_v2/
  service.py                         # 启动/Schema readiness 薄门面
  mcp_server.py, mcp_*_tools.py       # Native MCP 业务接口/注册
  http_transport.py, http_identity.py# HTTP 认证与连接边界（原生 SDK）
  references/
    __init__.py
    actor_refs.py                    # R58 抽出共享 ActorRef 声明/存在校验
    record_refs.py                   # R59 抽出 Work/Space/Topic 存在检查与 Topic 行锁
  health/
    __init__.py
    diagnostics.py                   # R58 抽出跨能力只读 Doctor/Status
  work_store.py, work_queries.py,
  work_relation_commands.py         # Work CAS/关系
  social_*                           # 协作图和消息流（已有领域文件分工）
  attention_*                        # 注意力读投影/消费坐标
  command_receipts.py,
  canonical_json.py,
  collection_pagination.py           # 原生共享机制，不复制实现
  postgres_connections.py           # PG 连接（唯一持久存储）
```

R58 选择只拆**真实重复/跨域职责**：原 `WorkStore.declare_actor` 与三个 Store 各自的 `_require_actor` 迁入共享引用能力；原 `HostV2.status` 迁入 health 只读查询能力。原 `WorkStore.declare_actor`、`HostV2.status` 对外 API 保持不变；没有创建第二份数据库或新的权限系统。需要运行原生 MCP Tool schema、Work CAS、Message retry、Attention、PG Doctor 回归验证。

R59 增量：在 R58 的既有 references/ 包内增加 record_refs.py，只承载三个 Facet 原本重复的 Work/Space/Topic 引用检查；ActorRef 声明/查询继续由 R58 actor_refs.py 独占，不新设第二个 Registry。Topic 写前 FOR NO KEY UPDATE、Work/Space/Topic NOT_FOUND、Attention 静态表名/参数化目标值与 WorkStore/HostV2 公共门面保持不变。原 Social、Attention 和 Work 的 _require_* 方法通过组合复用该 capability，不新增连接、事务、权限检查或迁移。\n\n**暂不为了目录美观移动** `social_message_commands.py` 等约四十个已被测试/正式结构检查消费的源码路径：它们已经按领域分工，整树移动会同时破坏现有 Lean/CrossHair 路径、静态消费者和发布 SHA，而不改善语义。仅在发现实际业务耦合反例后才继续渐进迁移。

## 5. 逻辑模块不是审批流程

`ActorRef` 表示社会协作中谁被引用，不是 Cloudflare Principal，更不是 OS/PG 授权。Work.completed 是语义状态，不证明 Runtime Job 已结束。Participation、MessageRelation、Attention ACK 不是投票、权限、任务分配或领域验收；跨 Owner 写入仍需真实执行边界。整套逻辑不需要新 Policy DB、Agent Owner 审批、二套事件总线或万能任务中心。
