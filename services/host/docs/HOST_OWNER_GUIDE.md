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
| migrations/、alembic.ini | schema 0001–0011 必需迁移链，线上版本 11 | 保留全部迁移链；旧编号不等于垃圾 |
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

1. 在线查看：host.status(detail=summary) 观察 Host 自身统计；host.status(detail=integrity) 检查已覆盖的 PG 一致性。不要把 Host 健康等同于 Runtime、Git 或业务验收。
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

## 6. 在线数据归并候选（2026-11-07，只读核查）

以下三个 Space 的功能重叠，属于进一步消费者审计候选，不是已经证明可删的数据：

| Space 标识的关键部分 | Topic 数 | Participation 数 | 当前处置 |
| --- | ---: | ---: | --- |
| ordivon-task-portfolio-and-proof-gates-r1 | 7 | 0 | 有 7 个 Topic，不按“0 人参与”直接删除 |
| ordivon-task-control-r1 | 8 | 2 | 可能是活跃入口；须检查 Message/订阅/引用 |
| ordivon-capability-task-forum-r1 | 13 | 3 | 可能是活跃入口；须检查 Message/订阅/引用 |

这是一份在线读取时刻的快照；没有完成消息/订阅/引用闭包核验，也没有 Host 原生删除 API 的已发布契约。本轮没有直接执行 PG SQL 删除。优先复用现行 Space；确认所有消费者已经转移后再做精确退役，绝不新建第二个全局任务入口。

架构参考：[Martin Fowler CQRS](https://martinfowler.com/bliki/CQRS.html) 强调按 bounded context 局部采用、避免全面复杂化；[Architecture Patterns with Python](https://www.cosmicpython.com/) 提供 Repository / Service Layer / Unit of Work 的成熟边界思想。Host 当前直接复用 PostgreSQL 事务，只有证明额外抽象能减少真实耦合才需要引入 Repository/UoW 包装。

## 7. 待进一步验证的边界

Coordination Intent 与 Work Relation 有内部能力和数据库消费者，但并非全部显式 MCP 工具，不能把“代码存在”直接宣称外部产品可用。跨包更名 ordivon_host_v2、删除 R1 图方案、删除不可逆迁移或重写 PG 状态必须先有消费者迁移与发布验收；重构范围越广，不代表系统越优。
