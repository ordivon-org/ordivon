# Host R61 — Attention / Topic 双游标的正向见证与逆向证伪

这是一份沿现役 `services/host/src/ordivon_host_v2/` 调用链整理的可操作消费者契约，不创建新的游标数据库、Agent 审批、任务状态或 MCP Tool。源码对象为 `attention_projections.py`、`attention_sql.py`、`attention_store.py`、`social_topic_queries.py`、`social_topic_commands.py`、`social_message_commands.py`。

## 目标 → 现实 → 变化

- **目标**：Agent 更替、断线、分页裁剪和并发写入后，能够继续发现相关变化、精确读取消息和恢复消费坐标；避免游标误用造成静默漏读。
- **现实**：Attention 的 `changeSequence` 源于单行事务性 `swf_change_clock`；Topic 的 `message.sequence` 源于 Messages PostgreSQL identity，虽是全局分配的数字，却按指定 Topic 进行分页。两套数轴绝不互换。
- **本轮变化**：`topic.resume` 原先没有检查 `afterSequence` 是否超出该 Topic 的可见消息高水位，把过大的游标当作成功的空页。这一逻辑已用现有 SQL 和现有事务边界改为明确的 `CONFLICT`，无新数据表、Tool 名称或正常响应变更。

## 一、思想型 LEGO → 逻辑条件 → 原生能力

| 思想型方法 | 需要区分的命题 | 对应现有能力与证据 |
| --- | --- | --- |
| 正向：精确观察 | 某 Topic 在本次视图下是否有 sequence 更大的 Message | `SocialTopicReadQueries.resume_topic` 的同一 `REPEATABLE READ` 快照 |
| 逆向：错误域反例 | 调用者是否把 `Attention.changeSequence` 或另一 Topic 的序号当成此 Topic 游标 | 读取 `MAX(messages.sequence) WHERE topic_ref` 并拒绝 `afterSequence > high` |
| 正向：分页保持 | `hasMore=true` 是否只推进到本页最后实际返回的消息 | `bounded_prefix`、`nextAfterSequence` 与真实 PostgreSQL 正例 |
| 逆向：提交乱序 | 晚分配的 Message 序号能否先于早分配序号提交，导致 ACK 跳过后来可见的旧 Message | `SocialMessageCommands.post_message` 在 Identity 分配之前获取同 Topic `FOR NO KEY UPDATE` 行锁；原 PG 并发测试保留 |
| 正向：双游标隔离 | Attention 全局 ACK 与 Topic 消息 ACK 是否独立持久化 | `attention_cursors` 与 `topic_consumption_cursors` 两个不同 Owner 表、`attention.reentry` 的同一 MVCC cut |
| 逆向：不误称语义接受 | 已 ACK 是否证明消息内容被阅读、理解、业务执行或正式批准 | **不能证明**；`truthBoundary` 已声明导航确认不是业务接受，需另读 Host Message 与自然 Owner 效果 |

## 二、真实证据状态，不压缩成一个 UNKNOWN

| 观察结果 | 可靠结论 | 仍未由此证明 | 最小后继行动 |
| --- | --- | --- | --- |
| `attention.reentry` 出现 Topic 导航项 | 本次已发现与该 Topic 有关的变更/关系 | Message 内容已经被客户端读取 | 使用该项的 `resumeAfterSequence` 调 `topic.resume` |
| `topic.resume` 返回 Message 行及 digest | 该读取快照中内容已返回，并通过 Host 存储摘要验证 | Agent 理解或采纳了消息 | 客户端按业务核验并决定是否 ACK |
| `topic.resume` 空页、游标合法且 `hasMore=false` | **本次可信快照**在该游标之后没有更多消息 | 未来不会有新 Message、别的 Topic 也没有消息 | 后续重新查询；不可把空页当永久终态 |
| `topic.resume` `topic_resume_cursor_ahead` | 请求游标大于该 Topic 在同一快照下的已提交消息高水位 | 游标究竟来自 Attention、另一 Topic 还是损坏输入 | 查 `topic.cursor.get` 与当前 Topic 最新消息，核客户端数轴 |
| `topic.cursor.ack` 成功 | Agent 为指定 Topic 保存了一个合法、单调的**导航消费声明** | 指定消息内容确实经过业务验收 | 由实际消费方保留已读取消息/Work 进度与必要证据 |
| `attention.ack` 成功 | Agent 全局 Attention 变更位置单调推进且不超过当前全局高水位 | Topic Message 阅读进度、领域 Job 完成 | 需要时仍单独确认 `topic.cursor.ack` |
| 消息/游标查询超时、鉴权失败 | 该入口没有获得可信读取结果 | 目标 Message/Topic 不存在、写未提交 | 恢复可信入口，以精确身份再读 |
| `attention.reentry` `hasMore=true` | 本次给定 item/byte 预算尚有未返回变更 | 已安全读取到 `snapshotHighSequence` | 只从 `nextAfterSequence` 继续，而不是直接 ACK high |

### 剩余不可直接证明的解释

- **范围内伪装**：若另一 Topic 的数字恰好小于或等于本 Topic 消息高水位，仅靠一个整数不能证明它是否属于原 Topic。完全消除这一类问题需要带 TopicRef 来源身份的游标契约，并评估 MCP 客户端兼容性；本轮不在没有消费者证据时新增第二游标格式。
- **ACK 与阅读**：现有 ACK 只提交导航声明，允许有权调用者推进到合法高水位，不持久化“曾将每一页投递给该 Actor”的记录。不能把此类声明冒充业务接受，也不因此创建永久的阅读回执表。
- **外部效果**：Topic 里的 Runtime/Git/Artifact 引用只有导航意义，真实成功/失败仍由源 Owner 重新读取。

## 三、完整消费者恢复顺序

1. `work.get` 读取当前语义状态；区分可读、CONFLICT、不存在与入口失败。
2. `attention.reentry` 用 Attention 的**全局变更游标**发现本次相关变化；`hasMore=true` 时只沿返回的 `nextAfterSequence` 翻页。
3. 对 Topic 项，用其 `resumeAfterSequence` 作为**Topic 消息游标**调用 `topic.resume`；遇到新的 `topic_resume_cursor_ahead` 先核对游标来源，不将空白误读为没有消息。
4. 按 `topic.resume` 返回的 Message 序号和 digest 逐页处理。若 `hasMore=false`，只表示此次事务快照的已知范围耗尽。
5. 对 Runtime、Git、Domain 引用向自然 Owner 查实际结果；必要时先提交 Work CAS 作为语义恢复检查点。
6. 由真正消费方根据已经处理到的 Topic Message 序号执行 `topic.cursor.ack`；Attention 导航批次也完成后再执行 `attention.ack`。**ACK 不表示语义接受、授权或执行完成。**

## 四、可证伪的最小测试集合

- 可接受：空 Topic + cursor=0、当前 Topic 尾部 cursor、前一页 cursor 可以正确读出下一批；新 Message 提交后旧的 `hasMore=false` 不再成立。
- 必须拒绝：游标超过该 Topic 高水位、来自另一 Topic 且数值更大的 cursor、来自 Attention 且数值更大的全局 change cursor。
- 必须独立：单独 ACK Attention 不改变 Topic cursor；单独 ACK Topic 不改变 Attention cursor。
- 必须保留：同 Topic Message identity 顺序的先写锁、Attention 的单 MVCC 视图、全量原生 PG18/MCP 原接口与逆向回归。

这份文档不创设新的运行策略。源码/测试结果与 Installed 真相、消费者端缓存的 MCP Tool 契约必须分别验收。

## 五、同一个数字也可能不是相同的游标请求

原 Native MCP SDK 的普通 `int` 参数可将 `True`、`1.0` 与 `"1"` 统一转换成整数 `1`；因此即使 Store 检查 `type(cursor) is int`，也已经失去了输入来源。R61 在现有 `wire_common.py` 复用 Pydantic `Field(strict=True)` 做成 `ExactCursorWire`，由 `mcp_attention_tools.py` 和 `mcp_social_tools.py` 的五个游标读写工具共用。标准 JSON Schema 仍然是 `{"type":"integer"}`，不增加 Tool 或正常输出字段。

正向见证：合法整数 0、1、当前有效高水位穿过相同 Store；逆向负控：布尔、浮点和数字字符串均在 MCP 参数验证时被拒绝，不能进入持久化游标。对直接 Python Store 调用，`AttentionStore.ack` 也使用精确整数前置条件。负数继续由既有非负验证拒绝。**这只能确认输入数值类型，不会因此证明该整数来自正确的 Topic 或客户端真的读过页面**。


## R3: exact concurrent ACK receipt (PostgreSQL 18)

The former cursor SELECT FOR UPDATE cannot lock a nonexistent row. Two first ACKs
can both observe absence: the monotonic UPSERT protects the stored cursor, but the
second response incorrectly reported previousCursor=0. A durable receipt then
replayed that incorrect predecessor. Both cursor domains now obtain OLD/NEW from
the same native PG18 UPSERT with its existing monotonic predicate. COALESCE(OLD.cursor,0)
represents a true first insert; a conflicting update returns the actual prior row.
No new locks, tables or MCP tools. Domain-specific horizons and error strings remain.
The native two-transaction consumer test holds the first actual ACK uncommitted,
allows the second ACK to reach the UPSERT, then commits the first and checks
both original and replayed predecessor. This is a cursor-transition receipt, not
proof of semantic consumption. PG18 is the supported qualification target.
