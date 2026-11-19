# Host — UNKNOWN 的证据解压（R59）

本页源自最新 Host 主线真实目录 `work_queries.py`、`work_store.py`、`mcp_domain_errors.py`、`attention_projections.py`、`social_topic_queries.py`。不是第二套状态机、权限系统、消息总线或新的 MCP 工具。

## 一、思想型 LEGO：正向与逆向必须成对

一个断言需要五个坐标：**命题、自然 Owner、观测作用域、正向见证、逆向反例**。再给出可区分的剩余解释、最小后继观测和禁止的危险动作。

- 正向：查精确对象及修订、PG 行与摘要、回执和消费游标，能够证明本次数据库视图内什么已存在/已提交。
- 逆向：查错误请求、丢响应、并发竞争、损坏摘要、错误身份/入口、过去状态缺失是否还能满足相同断言。
- 即使两边没有发现错误，也只能给有证据覆盖的命题 TRUE；外部 Runtime、Git、Security、领域消费者不由 Host 提供证明。
- UNKNOWN 不得直接当 FALSE。将 UNKNOWN 拆为本次观察失败、实体行不存在、历史记录缺失、当前数据不一致、证据矛盾、外部结果未验证等不同类，逐一确定后继行动。

## 二、一个真实修复：请求 Work 修订不存在

`read_work_in_tx` 原本遇到任何修订缺失都抛同一 `ConflictError`。已经读取当前 Work 行与请求 Snapshot 的同一事务足以将其拆为三类，不需要额外数据库、事件表或确认投票。

| 正向源事实 | 可确认 | 不能由此确认 | 后继最小操作 |
| --- | --- | --- | --- |
| WorkRef 本身查无 | 本次 Host PG 观察无此 Work 行 | 历史曾否存在、其他 Owner 是否有引用 | Work 清单/历史 Topic / 外部 Owner 交叉查验 |
| 请求 revision 大于当前 revision（即使数据库误存了更高版本 Snapshot 行） | 本次读取时该目标版本不属于已提交 Work 修订链 | 将来是否会提交、未来孤立行产生原因 | `work.get` 当前修订；不要把孤立行当作已提交内容 |
| 请求 revision 小于当前 revision 且 Snapshot 缺失 | 这个旧版本目前没有可读取的行 | 是正常裁剪、意外删除还是从未完整保存 | 检查旧版保存政策及原可恢复归档 |
| 请求 revision 等于当前 revision 且 Snapshot 缺失 | 当前指针与快照不一致；内部完整性违例 | 是否不可恢复、损坏原因 | 停止用该 Work，原 Host Doctor、原 PG 恢复 |
| 存在 Snapshot 且匹配存储 digest | 此时读取的 Snapshot 字节匹配 Host 摘要 | 其中所写 Runtime/Git/领域事实是否完成 | 向自然 Owner 的真实运行结果读回 |
| Snapshot 摘要损坏 | 不可把这份存储内容当作已核验快照 | 谁造成损坏、是否有原归档 | 保全证据，PG/备份修复，不返回假结果 |

`WorkRevisionUnavailable` 是原 `ConflictError` 子类：MCP `CONFLICT` 与详细报错保留，但新增 `reason`、`observedCurrentRevision`、`requestedRevision`、`evidenceBoundary` 和有区分度的 `suggestedAction`。不把历史缺失命名为“已经合法裁剪”，也不宣称必须重试。

### 仍需谨慎的历史状态

现有业务源码保证：Work 创建时为 open；提交新版本需要当前 Work 为 open；一旦终态，便不能通过该代码路径提交后继版本。因此 **在所有写入都遵守该业务路径** 的条件下，历史上存在后继版本可推论其写入前为 open。

但 Host 没有持久化每个 revision 对应的 lifecycle state；该推论不能反向证明过去所有写入都经过唯一业务路径。故保留现有的 `historical_state_unknown`，不虚构“PG 已记录该历史 state”。这不是不分析 UNKNOWN，而是说明为什么目前无法将它无条件升级为已证事实。

## 三、其它核心不确定性：已有能力如何正逆验证

| 表面 UNKNOWN | 正向验证 | 逆向验证 | 修复/行动边界 |
| --- | --- | --- | --- |
| `message.post` 断线 | 精确 MessageRef 的 `message.get` 与摘要；幂等同请求 existing | 同 MessageRef 异值必须 CONFLICT；检查 Gateway 是否具备精确读而非仅全文搜索 | 未核结果先读回，不能当未提交重做有副作用写 |
| `topic.resume` 无消息 | 同 TopicRef 与 afterSequence 下本次 MVCC 快照未返回后续消息 | TopicRef 错误、使用 Attention 全局 cursor、历史归档过滤 | 不把本次空页认成全系统无消息 |
| `attention.delta` 无待处理变更 | 证明本次 `snapshotHighSequence` 之内无遗漏，`nextAfterSequence` 匹配 | 反例：非终页提前跳高、下一次提交发生在快照后、两个 cursor 域混用 | 仅推进当前消费 horizon，不声明内容已被接受 |
| Work.state=completed | 当前 Host 语义 Work 完结 | Runtime Job 可能仍有实体进程/Artifact 未交付 | 外部副作用的完成只由 Runtime/Git/领域 Owner 证明 |
| Host ActorRef 已声明 | Host 社会引用存在 | Cloudflare Principal / AuthZEN / PG Role 不一致 | 不能把 ActorRef 当登录用户或访问批准 |
| Gateway 超时/Unauthorized | 当前入口未提供成功的 Host 观察 | 未连接、认证拒绝、对象不存在各不相同 | 不以传输错误推断对象不存在 |

## 四、何时允许消除 UNKNOWN

对某命题，优先寻找能够**区分其两个相反解释**的最小测试。只有相同 Owner、版本/时间、对象身份、可信观测范围的正向见证和足够的逆向负控才允许收敛为该范围内的 TRUE/FALSE。若仍有未被排除的解释，必须带着已排除集合、剩余集合及下一项鉴别操作继续。不得为了统一报告把真空证据变为审批 Gate，也不为新增概念创建第二份永久数据库。

### 逆向新增负控：比当前修订更高的孤立快照

Schema14 的 `work_snapshots` 表没有把 `revision <= works.current_revision` 做成跨表物理约束。旧 `read_work_in_tx` 先读取请求 revision 对应行，可能把一个意外存在的未来行作为已提交版本返回。现在先用 Work 当前修订边界拒绝任何请求 `revision > current_revision`，再检查 Snapshot 有无与 digest。独立 PG18 回归会在测试私有 Work 内插入“未来但未提交”的有效 digest 行，必须被拒绝。这是**真实反例驱动的代码修复**，不是为 UNKNOWN 增加一种叫法。

## 五、双游标恢复的进一步实证

[DUAL_CURSOR_EVIDENCE_R1.md](DUAL_CURSOR_EVIDENCE_R1.md) 以同一 PG18 Snapshot 为证据边界，将 Attention 变更发现、Topic 消息读取、两个独立游标 ACK 和语义接受拆开。现有 `topic.resume` 超界游标不再返回误导性空页，而是兼容 `CONFLICT` 的具体来源诊断。超过 Topic 当前高水位可直接证伪；同一数字位于合法范围内但属于另一 Topic，则必须保留来源不确定性并在消费者侧核对。

## 六、游标整型归一化的逆向反例

原 MCP 的普通 `int` 会把 `True`、`1.0`、`"1"` 正规化为 `1`；这与当前 Topic 高水位判断是两个独立维度。R61 共用 `ExactCursorWire` 在原生 MCP 参数边界拒绝这些别名，保持正常整数 JSON Schema 不变；见 [双游标的正逆验证](DUAL_CURSOR_EVIDENCE_R1.md)。正确数值类型不等于拥有正确游标来源或真实阅读回执。
