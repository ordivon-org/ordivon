# Host R44｜Attention 增量消费查询：实际消费者基线、SQL 精化与隔离 PG18 验收

> 2026-11-18。原 Host Golden Road Work `work:ordivon:host-agent-continuation-golden-road-r1:20261114` 的 HST Attention 业务优化，不创建第二个 Work/Registry。原指导 Host Topic #29877。生产 Host 未切换。

## 业务场景与入口

多个 Agent 离线后回到 Space，只关心自己上次已处理游标后的少量变更；原始 MCP `attention.delta` / `attention.reentry` 调用 `AttentionStore → AttentionReadProjections._delta_in_tx → ATTENTION_DELTA_SQL`。同一 `REPEATABLE READ, READ ONLY` 事务获取 `swf_change_clock` 高水位、actor-scoped 变化和 Topic cursor。原 `after_sequence`、`high`、稳定排序、`limit+1`、按字节截断、事件多原因 `bool_or` 与处理后 `attention.ack` 语义完全保留。Attention 本身只返回 identity/sourceRef/nav，不搬运消息正文。

当前 Git SourceCut `0480182c5b2fd9310adb02569f61f78d2308fc46`；实际安装 Host 仍是 `10db16a117bf1fd0622a0fca1ecbedea7358c322`（Python、PG14）。本轮修补只在隔离源码/测试，**不是 Installed/Client 性能声明**。

## 技术选择：订阅驱动的有界 LATERAL

原 SQL 虽有 `UNION ALL` 和正确的 `bool_or`，但在外层 LIMIT 10 之前可能构造大量 Topic/Space 已关注消息。既有索引包括 `messages(topic_ref,change_sequence)`、`messages(space_ref,change_sequence)` 和 `messages(change_sequence)`，不先新增索引。

首先反证了“直接给两个关注分支 ORDER BY/LIMIT”的版本：热 Topic P50 34.18→29.75 ms，但稀疏叶节点行次 28,019→66,936、空 Actor 28,003→80,805，故**拒绝**直接排序候选。随后在两个关注分支使用 PostgreSQL 原生 `CROSS JOIN LATERAL`，每个订阅只取首 K 个符合 `after < change_sequence <= high` 且严格晚于订阅生效序列的消息，然后各分支取首 K，保留提及/回复分支不裁切，最后按原顺序 `GROUP BY` 合并原因、外层 LIMIT K。

正确性理由：每条 Message 只有一个 Topic/Space，同一 Actor/TargetKind/TargetRef 订阅有唯一键，且系统原变更时钟提供单调唯一的消息变化序列。任何全局首 K 的消息在对应的单一订阅目标内的名次必不大于 K。每个关注分支截 K 不会丢全局前 K；提及与回复仍不截断，`bool_or` 保留所有首 K 消息的匹配原因。既有物理索引仍由 PostgreSQL 优化器自行选择；本次 Hot EXPLAIN 实际使用 `message_change_idx` 等，不能宣称特定复合索引一定被使用。

## 一次性 PG18 Schema14 同数据交替对照

数据：16,000 条稀疏消息、8,000 条同一热门 Topic、2,400 条多原因场景、一个作者消息与 1,600 条 Relation，共 26,401 Messages、1,600 Relations、测试正文各约 329 B。每组基础与候选交替运行 **24 次热态采样**，同一 PG 实例和同一数据；首个已相关结果取首个 Delta 页和 Agent Reentry 导航页，各取 10 个事件。原 SQL 直接从不可变 Git `0480182c...` 读取，没维护另一套生产查询副本。完整原始延迟样本及 Hot `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` 保存在 `attention-r44-final.json`。

| 场景 | Delta P50 原→新（ms） | Delta P95 原→新（ms） | Reentry P50 原→新（ms） | Reentry P95 原→新（ms） | 叶节点行次 原→新 |
|---|---:|---:|---:|---:|---:|
| 稀疏订阅 | 36.084→31.892 | 40.913→35.916 | 36.737→31.340 | 41.311→37.797 | 28,019→28,015 |
| 热门 Topic | **35.808→29.778** | **46.572→36.135** | **35.059→28.667** | **39.937→32.109** | **36,004→28,015** |
| 重复命中 | 37.732→35.919 | **40.618→42.976（退化）** | 38.290→35.607 | 43.880→41.415 | 40,805→36,027 |
| 空 Actor 落后于 high | 34.462→29.030 | 39.986→34.443 | 32.029→28.317 | 39.369→31.640 | 28,002→28,002 |

Hot 整条 SQL EXPLAIN：执行 17.241→8.818 ms；Shared Buffer Hits 4,484→3,700；Shared Buffer Reads 0→0。扫描行是所有叶节点的 `Actual Rows×Actual Loops` 合计（可能重复），**不是**唯一被读取的堆行数。其他查询的 Buffer 表示于原始 JSON；PG 热态不代表彻底清空 OS/DB 缓存的冷启动。首个单次样本也记录在 JSON，但不能称控制好的真正冷缓存测试。

实际 Attention `delta` 消费者每页执行 actor 存在性、high、Attention SQL 共 **3 次查询**；`reentry` 有 Topic 导航时再查 Topic 游标共 **4 次**；恰好 `after==high` 时跳过重查询只需 **2 次**。后者在隔离 PG 中的 P50 9.514→9.309 ms，P95 10.483→10.003 ms；现有快速路径已经有效，不单独引入缓存/通知机制。所有 Attention Delta/Navigation 查询的**正文解码字节=0**（只取 Message Ref；要读正文仍由独立精确 message.get 消费者完成）。

本轮**没有添加索引、迁移或写入路径逻辑**，因此新增索引维护负担为 0；并未另外开展“索引上线前后”的实际写入吞吐基准（本轮没有新索引）。同时不得根据几毫秒的单机测试推断 ChatGPT 远端 Agent 的端到端 Token 成本或真实 LLM 认知速度。

## 正确性与回滚

- 真实隔离 PG14 SQL 全页逐项相等：热门 Topic **71 页 / 8,000 事件**；Space+Topic+提及+回复 **80 页 / 4,000 事件**；稀疏 **3 页 / 15 事件**；同一 Message 只返回一次、四原因完整。
- 新关注严格晚于生效 `change_sequence`，旧消息不被追补。空页 `after==high` 不错误推进。
- 断线前已有未读页，然后提交新消息：原 high 28118 → 28119；新消息通过旧 high 的后续读取可见，未读页面游标未跳到 high。
- 真实并发写事务尚未提交时，Agent 在另一 PG 连接进行 `REPEATABLE READ` 恢复：原 high 28119，未提交消息不可见；写事务提交后 high 28120，后续 Delta 从 28119 精确返回该消息。**没有提前 ACK**。
- 源码 SQL 无 Migration，原消费参数/Response Schema 不变。若生产观测显示退化，直接按受保护 Git Release 回滚至旧 SourceCut；保留既有 Host immutable Release，不回滚 PG14。
- Python Host 现有完整测试与 Ruff 在原生 Runtime 作业中通过；SQL 形状回归独立新增了针对 LATERAL、K 限制、原因合并的测试。隔离测试成功不等于生产发布成功。

## 增量价值、代价与下一步

**热门 Topic 重连**：首个导航页 Reentry P50 从 35.059 到 28.667 ms，在相同隔离 Host/PG 条件下平均中位数提前 **6.392 ms（18.2%）**；Delta P50 提前 6.030 ms。业务上仍是少量定向导航事件，不必在登陆时下载数千条无关正文。

**反例/成本**：重复命中 Delta P95 40.618→42.976 ms（+2.358 ms）；同一批测试下 Reentry P95 反而下降，不能宣称所有尾延迟场景改善。继续监视不同订阅密度、热缓存、超大 Topic 的高分位，并由真实 Agent 消费者验证客户端 schema 与 Host Installed 一致性。

尚未完成：生产 Release 发布/回滚/真实 Agent 端 Token/P95；多 Agent 多会话真实认证；跨日冷缓存/写入并发高压；其他 Owner 安全发布仍 NO-GO。本轮不移动生产指针，不复刻事件总线，不修改 ACK 语义。

## R47 独立反证：重复命中 P95 与高扇出订阅（2026-11-18）

**决策：不修改已合并的 Attention 生产 SQL；不新增缓存、索引或查询路由器。**
本节按同一原 Golden Road HST Attention 消费场景复核上一节的重叠
Delta P95 负数，源/安装/远程 Agent 三种状态仍须分开。原先 24 次样本的
`40.618→42.976 ms` 仅是一条需证伪的反例，不是确定的尾部回归。

### 双数据库同负载交替复验

在原源码 `0480182c5b2fd9310adb02569f61f78d2308fc46`
读取旧 SQL，在主线 `f772df2a897c6e7b9d2ddde8efccdf936f52a085`
读取优化 SQL，不另建生产 SQL 副本。原生 Runtime Job
`job-01a1ef4f-c2cf-75bb-9cd5-e26c8bcc880e`
通过环回 Docker PostgreSQL 18 + Alembic Schema14 建立两个**独立空数据库**，
每库分别生成 26,401 条合成 Message 和 1,600 条 Relation。
固定 Actor、订阅、生效变更序列、数据量、高水位、分页参数，各版本
64 次 ABBA 交替热态调用真实 `AttentionStore.delta/reentry`。

| 场景及数据库 | Delta P50 旧→新（ms） | Delta P95 旧→新（ms） | Reentry P50 旧→新（ms） | Reentry P95 旧→新（ms） |
| --- | ---: | ---: | ---: | ---: |
| Hot A | 48.651→38.600 | 63.195→51.738 | 42.738→34.658 | 48.306→41.879 |
| Hot B | 45.573→35.230 | 59.327→46.191 | 40.503→33.137 | 53.439→40.728 |
| Overlap A | 51.740→47.359 | **71.803→74.071（新SQL慢2.268）** | 52.350→48.899 | 74.506→75.194 |
| Overlap B | 43.526→40.886 | **64.117→53.240（新SQL快10.877）** | 43.135→41.094 | 62.854→49.438 |

对每个数据库的 64 对 Delta 原始样本，以固定随机种子执行
3,000 次**配对索引重采样**，以原脚本最近秩 P95 统计量计算
`candidate_p95 - baseline_p95`。描述性 95% 区间分别为
A **[-18.040, 22.928] ms**、B **[-19.651, 2.969] ms**，
均跨零；A 64 对中候选快于原版 45 对，B 46 对。
这不是严格独立的生产置信区间，不能证明未来 P95 无退化；
但**足以否定“单次合成 P95 为正就必须再改 SQL”**的决策前提。
当前仅重复同形状合成数据、热缓存及同进程交替，没有刷新
内核页缓存或实测并发真实认证 Agent。

每个独立数据库原 SQL 与候选在全部分页、命中原因、订阅生效、
断线后追加消息、真实第二连接未提交写隔离及后续再可见性
的既有原生 PG Oracle 均通过；其中 Overlap 80 页/4,000 事件，
Hot 71 页/8,000 事件，Sparse 3 页/15 事件，未推进任何真实 ACK。
完整已抽取采样序列、EXPLAIN 摘要、负控和原始运行报告 SHA256
收敛于 `attention-r47-evidence.json`，不再复制三份大型完整
原生 EXPLAIN JSON 到仓库；原生 Runtime Job 保留执行回执。

### 多订阅：沿能力边界检验 LATERAL 代价

新增**仅测试用途**脚本 `tools/bench_attention_fanout_r47.py`：
直接从原 Git SHA 读取旧 SQL，以现有 Python Host
`AttentionStore.delta/reentry`、`EXPLAIN(ANALYZE,BUFFERS,FORMAT JSON)`
和原 `compare_pages` 逐页相等算法为 Oracle。输入只允许
**全新、空白、环回** `hostbench` 一次性数据库；不创建第二个系统，
不需源码运行时分支、订阅存储或查询索引。第三个独立 Docker PostgreSQL18
原生 Job `job-01a1ef55-31d9-7654-837a-f45f6e86ae7e`
以 256 Topics、8,192 条轮转分布的合成 Message、
同一高水位测一位 Agent 关注 1/8/32/128/256 Topics，以及
同时关注 Space + 其中 128 Topics；每一配置两版交替各 24 样本，
最终全页完全相等（6 个配置依次 1/3/11/41/82/82 页）。

| 单 Actor 订阅 | Delta P50 旧→新（ms） | Delta P95 旧→新（ms） | SQL EXPLAIN 执行旧→新（ms） | 叶节点行次旧→新 |
| --- | ---: | ---: | ---: | ---: |
| 1 Topic | 20.898→20.845 | 25.649→28.233 | 0.293→0.310 | 33→12 |
| 8 Topics | 20.154→20.008 | 23.589→23.758 | 0.602→0.258 | 264→96 |
| 32 Topics | 22.372→19.965 | 26.420→24.133 | 5.632→0.947 | 8,224→384 |
| 128 Topics | 34.215→26.519 | 53.614→48.040 | 5.625→1.552 | 8,320→1,536 |
| 256 Topics | 27.419→22.916 | 35.732→27.218 | 10.280→3.941 | 8,448→3,072 |
| Space + 128 Topics | 30.575→20.899 | 38.253→30.829 | 11.794→1.983 | 16,513→1,548 |

所有配置首批 `reasons` 与完整页一致；Space + Topic 双命中
没有重复事件。256 Topics 的 `shared_hit` **397→3,346**，
却实际执行更快：访问缓冲区次数不是唯一行扫描次数，也不是
消费者时延的直接代理。单 Topic 的新 SQL P95 增 2.584 ms、
8 Topics 增 0.169 ms，同样只有各24次样本；
**不能把这两项也隐去或认定稳定回归**。
截至这轮，现役 Host 全局只有约 97 条 Subscription（分布在多个 Actor），
“256 Topic 属于一个 Actor”只是容量压力反例，不是生产请求分布。

独立重做可使用现有 `uv`、Alembic 与官方 `postgres:18`
一次性 Docker，先创建环回空数据库 `hostbench`，
在 `services/host` 下执行
`uv run python tools/bench_attention_fanout_r47.py --dsn "$DISPOSABLE_DSN" --iterations 24 --output "$REPORT"`；
脚本对 DSN、Schema14、空库存进行 fail-closed 检查。
不可连接或改动生产 PG14/Host/Gateway，也不可借此跳过
Cloudflare Access、AuthZEN、独立 Principal 和旧 Peer 迁移。

PostgreSQL 18 官方语义依据：
[LATERAL 关联子查询](https://www.postgresql.org/docs/18/queries-table-expressions.html)、
[索引与 ORDER BY LIMIT](https://www.postgresql.org/docs/18/indexes-ordering.html)、
[EXPLAIN / BUFFERS](https://www.postgresql.org/docs/18/sql-explain.html)。
本轮思想型 LEGO 是**先证伪共同瓶颈，再删减方案**；
逻辑型 LEGO 是在原分页/多原因/ACK不变量下按选择率与扇出
区分 SQL 执行时间、Host 正常入口和远端 Agent 消费时延；
能力型 LEGO 继续复用 Python Host+PG18+原 SQL Oracle，
只增加可重复执行的测试探针。下一步有价值的验收是
**已安装不可变 Release + 真实独立认证 Agent + 冷启动/并发分布**，
不是在当前隔离 SQL 上继续叠加复杂度。
