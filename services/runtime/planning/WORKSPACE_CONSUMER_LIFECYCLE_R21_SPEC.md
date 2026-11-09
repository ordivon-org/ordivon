# Workspace Consumer Lifecycle R2.1 — Formal-first Specification

> 状态：APPROVED_FOR_IMPLEMENTATION（设计/验收目标）；不是 CODE_REFINED / INSTALLED_CURRENT / CONSUMED。
> 基线：Git source cut 3b43977e682d8c7668f6371ffd998c7821e4312a，2026-11-09；如主线先行更新，执行前重新取证并只移植未覆盖增量。
> 自然 Owner：Runtime（物理 Workspace / Job / Attempt / close），Git（源码），Host（Work 目标连续性），Artifact（成果身份），systemd/Windows（进程与目录）。
> 伴随执行计划：WORKSPACE_CONSUMER_LIFECYCLE_R21_EXECUTION_PLAN.md。

## 1. 目标与反目标

系统目标：一个可替换的 Agent 接受 Workspace 清理/实现任务后，不依赖模型性格，也必须通过受保护的消费者结果合同。防止两种偏向：一是无限保留无消费者的临时目录（liveness fail），二是删除尚有有效消费者或尚未完成成果处置的独有内容（safety fail）。

具体业务结果：一次真实任务的源码/Artifact/回执不依赖长期保持工作树；有效消费者可以继续使用；最后一个消费者结束、结果已交付或明确丢弃后，Workspace 被原生 Runtime 有界回收；持续任务可重新物化精确 Git 对象。Agent 不可仅以报告、修改测试或自我声明替代消费验收。

禁止新增：独立 GC 服务、第二 PostgreSQL 事实库、全局跨 Owner LEGO Registry、特制测试 DSL、弱模型对照实验、多 Agent 人工审批链。复用现有 Git worktree、PG Runtime、TLA+/TLC、Kani（仅实际 Rust 纯函数适用时）、Rust/Python 测试、systemd timer、Windows Job Object 和 GitHub CI/merge queue。

## 2. 事实基线与信任边界

- 现有 Runtime Core 的 close_recovery.rs 使用创建后 4 小时延续保护（PR #1960 已合主线）。consumerReleased 为调用方声明，源码明确不将其当作真实性证明。
- 已部署 PG 回收器根据 Git HEAD 已在 origin/main、最后 Job 成功且老化、工作树 clean 和本地 CWD 等条件选择候选，随后调用 Runtime workspace.get / workspace.close；这是一套启发式而非完整消费者证明。
- 现有 WorkspaceConsumerCloseR1.tla 的 Close 在年龄过期、无 liveJob / gitDependent 时可发生，包括 consumer 仍 active 的抽象状态；模型安全性不等于物理消费者已退出。
- 除非具体观察闭包已证明，不可将无进程、无 Git 修改、Job 终态或 Work Abandoned 推导成无消费者。UNKNOWN != FALSE。
- 形式化模型、源码、CI、合并、已安装服务、物理执行和产品消费是不同证据层级；每条结论附 exact source cut 与对应级别。

## 3. 领域词汇（Matt domain-modeling）

- Workspace：Git revision + Runtime 受管隔离工作树的短期物化实例，非长期任务/成果储存库。
- Consumer：当前或约定将继续使用具体 Workspace 的有证据主体；Job、进程、来源依赖工作树、明确的外部继续消费意图都可构成不同类别。
- ConsumerRelease：消费者完成真实工作后解除持有的事件或已满足证据的声明；不能仅因为过了时间就假定它发生。
- Disposition：独有成果的处置，属于 PUBLISHED（已被持久权威接收）、DISCARDED（自然 Owner 明确丢弃）或 UNKNOWN（尚未决定）。
- Quiescence：当前 Runtime Job/Attempt、OS 活动和嵌套 Git 工作树没有有效物理占用。
- Lease：有所有者、有到期/续约规则的有界消费者持有；到期必须通过权威事实判定，不等同于目录创建年龄。
- EvidenceStanding：OBSERVED / FALSIFIED / UNKNOWN，携带 source cut、读集、假设和当前性。
- Reclaimed：Runtime 返回可读的关闭 disposition 且物理工作树/记录状态已复核；不等于业务目标完成。

## 4. 能力型 LEGO：Consumer-rooted Workspace Retirement

采用 R2.1 全十一坐标，使用已有对象，不要求每次执行写出第二份结构化 Registry。

- I (typed)：WorkspaceId × GitCommit × SourceStateDigest × RuntimeJobSet × ConsumerWitnessSet × DispositionEvidence × ObservationEpoch。
- O (typed)：RetirementDecision (CLOSE | RETAIN | RECONCILE) × ScopedEvidence × UnresolvedObligations。
- S (typed)：Runtime-owned Workspace record 和 PG Job/Attempt 状态；现有 Git refs；Host/Artifact 自然 Owner 的持久事实。无新增跨 Owner 可写权威。
- pre：受管 Workspace 身份一致；来源/期望 digest 精确；Runtime 当前 Job/物理占用已检查；消费者观察范围被说明；PUBLISHED/DISCARDED 有可复核证据；不完整则显式 UNKNOWN。
- post：CLOSE 成功时 Runtime close disposition 与物理消失匹配；RETAIN/RECONCILE 不冒充已释放；已有源码/Artifact 不因工作树回收丢失。
- inv：ActiveConsumer -> NOT Reclaimed；UnresolvedExclusiveOutput -> NOT ForceDiscard；UNKNOWN != FALSE；终态幂等；有活跃 Job/嵌套 Git 依赖则不删除；证据过期不可复用。
- eff：仅受管 workspace.close / Git 原生工作树移除；如果存在成果发布，使用该自然 Owner 原生操作；无任意 rm -rf 系统根目录。
- c (typed)：CPU/IO/空间回收、一次 close/观察成本为 Runtime 原生测量值或 UNKNOWN(unmeasured, node, receipt)；不虚构固定收益。
- epsilon (typed)：安全不变量的近似误差目标为零（模型条件下）；实际消费者观察闭包/外部不可观测作用为 UNKNOWN(consumer-world, epoch, independent-witness)；liveness 假设 scheduler fairness 与持续可用。
- prov：Git commit、TLC 模型/config、测试输入/反例、Job/Attempt、安装 digest、consumer receipt 的精确引用；源改动使相关证据失效。
- unfold：L0 可回收性及效应预览，L1 请求/回执和完整拒绝原因，L2 模型读集/证明/真实消费者见证，L3 仅按需要展开原生实现与历史。

思想型 LEGO：Consumer-first Contract Selection。其 I 为目标、已知消费者、成熟 provider/Skill；O 为可实现合同与拒绝条件；S 为现有 Skill/工程文档；pre 为当前源/真实消费者；post 为下一步可测试的实施任务；inv 为 DELETE→REUSE→COMPOSE 及不可凭推理宣布验收；eff 为影响实现选择/文档；c 为 UNKNOWN(agent cost until measured)；epsilon 为 UNKNOWN(human intent ambiguity)；prov 为 Skill 源与当前 Git；unfold 为 Matt/domain-modeling、ECC/contract-first、Superpowers/writing-plans、Runtime 原生 verifier。它是已有思想型 LEGO 的应用，不新增独立 Skill。

## 5. 最小行为合同（ECC contract-first）

运行时不能让清理 Agent 自行把 UNKNOWN 当作已释放，也不应将 UNKNOWN 定义成永远不得调查。

输入事实来自已存在的 Runtime、Git、自然消费者；若未来确需持久续租，仅在 Runtime 当前受管 PG 生命周期内添加明确、可过期的关联，Host 不持有物理 Workspace 锁。

决策表：
1. live Job / held Job / 外部已证实持有 -> RETAIN；不触碰源树。
2. 最近消费者已释放 + Quiescent + Disposition=PUBLISHED/DISCARDED + 源状态当前 -> CLOSE；无需满 4 小时。
3. 没有持有者，但仅靠年龄缺少成果处置证据 -> RECONCILE；自动检查 Git 上游、Artifact、Owner 的可消费成果或选择明确丢弃，不能伪报完成。
4. 放弃的、失败的、脏的临时结果在已完成真实处置后可以原生 force close；dirty != retain。
5. Workspace 已关闭 / 同时关闭 -> 返回幂等的已关闭结果；不可生成新的业务副作用。
6. 证据来源过期、运行环境未安装新版本、目标节点不明 -> UNKNOWN，并在下一次有界再协调中重取证。
7. 源码在 Git HEAD 但 PR 未合，属于已保存而非已被正式消费者接受；保留 Git ref 可与物理 Workspace 回收分开决定。
8. Linux 与 Windows 分别验收；一个节点 PASS 不得代表另一节点安装成功。

合同版本迁移：Expand（新证据字段/观测/消费者可识别）→ Migrate（实际调用方与清理器采用）→ Contract（删除旧重复算法）；新字段不能被部署端静默忽略。

## 6. 形式化性质、限制、反例

既有模型 WorkspaceConsumerCloseR1.tla 是抽象有限状态模型。新证明义务：
- Safety S1：已知的活动消费者/未终止 Job/嵌套 Git 依赖存在时，关闭不应发生；涉及源码结构的真实消费者，需另附实际见证，不能直接冒充。
- Safety S2：Disposition=UNKNOWN 且独有结果未完成处置时，不允许将强制删除记作成功交付。
- Liveness L1：当 Close 在稳定状态下持续可执行且 scheduler 弱公平时，Eventually Closed；公平性是有条件的模型假设，不宣称 systemd 必定调度。
- Non-vacuity：至少一条成功关闭轨迹可达，至少一条违反候选限制的模型变化产生命名反例。
- Refinement R1：现有 Rust workspace.close 和 PG-native cleanup 的请求/拒绝/终态行为，需通过真实公开接口测试对应抽象 transition；TLC PASS 不证明源码已精化。
- Negative witness N1：旧模型允许年龄到期后 consumer 仍 active 的关闭；明确保存作为待关闭设计漏洞的形式化反例，不把它隐去。

模型检查工具仅使用 services/runtime/scripts/tla-formal 和已锁定 TLC。当前第一纵向切片先引入有界活性性质 + 缺失公平性的负向检验；后续使 Consumer/Disposition 对应源代码可观察、可反例检查，并用同一合同修复未闭合的实际缺口。

## 7. Acceptance Matrix（无需弱模型试验）

A1：新 Workspace 有明确消费者；释放前实际活动 Job 导致 close 拒绝；终止后有界可回收。
A2：干净且已交付成果、无消费者 → 可主动 close，不待四小时。
A3：脏但独有内容明确 DISCARDED → 原生 force close，回执验证消失。
A4：脏且独有内容 UNKNOWN → 不能被当作已完成发布；进入有界再协调。
A5：Job orphan / lost / unknown → 不伪造失败或成功；效果证据与物理占用分别处理。
A6：close 响应丢失重放 -> 同一 digest + 已关闭 tombstone，不产生第二次非幂等外部效果。
A7：并发两个 close -> 只有一次物理效果，其他可识别 idempotent terminal。
A8：Agent 断线且 Lease 到期，无有效 Job 且 Disposition 明确 → 在公平调度下最终回收。
A9：Git 源码或实际安装版本变化 → 旧模型/测试不得自动升格为当前安装通过。
A10：Linux 和 Windows 分节点报告 CODE/INSTALLED/EXECUTED/CONSUMED。
A11：定时清理器识别无消费者失败 Job 和没有 Job 的已丢弃 Workspace，不将“最后 Job 必须成功”当普遍业务必要条件。
A12：同一责任被三个脚本实现时，选出唯一生产 Owner，旧实现退役且外部消费者迁移。

正负控制均必须可由机器执行。验收来源优先：Runtime 公共 MCP API、Git、PG 原生事务和 OS owner；禁止人工语言质量打分或不同模型能力比较。

## 8. 变更分段与完成含义

P0：当前源与已安装切口核对；复用现有 Skill；固化以上合同；已有 TLC 添加公平下活性和负向反例，运行完整形式化 owner verify。
P1：Runtime 具体消费者/处置证据入口（先复用，不满足才给当前 PG 生命周期增加薄的状态）；Rust/PG 原生测试先红后绿；避免改变所有 Owner。
P2：清理器围绕同一原生状态决策，移除“最后 Job 成功”之类的错误普遍必要条件；支持脏数据明确放弃后的及时退出。
P3：Host/Artifact 等消费者最小交接，Git 发布和下游验收；连接器消费合同与实际 Core 参数对齐。
P4：Linux PG/Windows 原生场景和服务重启、回执丢失、并发验证；独立 reviewer 审查规范轴与源码轴；GitHub CI/merge queue。
P5：以真实安装 readback 证明新版本加载，再执行端到端消费者验收；确认无消费旧版本后删除重复的旧回收入口/旧文档。

严格状态分离：SPECIFIED / MODEL_CHECKED / CODE_TESTED / MERGED / INSTALLED_CURRENT / EXECUTED / DOMAIN_ACCEPTED；任何中间阶段不自动推出后继阶段。实际改动的范围以独立 PR 和对应验收为准。

## 9. 工程纪律（Matt + ECC + Superpowers）

- Matt domain-modeling：先修正 Workspace/Consumer/Lease/Disposition 术语，避免把 Work/Job/Artifact 当同一对象；决策因果必须能在源码找到。
- ECC contract-first：Runtime Core 是关闭权威；消费 API 只有一份机器可检查合同，不复制 JSON shape 到 Wiki、Mock 与自造 Schema。
- Superpowers writing-plans：小型垂直任务、准确路径/接口/命令、红→绿→重构；每项有独立消费者验收。
- Superpowers verification-before-completion：每项声明仅依据当次真实命令与回执，不用模型自述 PASS。
- 不采用 ECC 通过修改学习日志 mtime 来阻止结束的 hook，也不以模板填充、日志数量、形式化测试数量代替真实产出。
- 任务若遇来源更新先对比精确 Git SHA，已有成熟实现则删除自己重复工作；失败必须成为具体反例/阻塞原因，而非无限会议或防御性审批。

## 10. 数学、计算机科学与成熟工业范式：本次增量精化（2026-11-09）

**不引入新 LEGO 演算。** 下述理论为已有 R2.1 十一坐标指定外部语义源；不能因使用某种数学术语就推导真实产品已经实现。

| 已有理论/实践 | 映射到 LEGO | 可检验义务 | 明确不能推导 |
| --- | --- | --- | --- |
| Floyd–Hoare partial correctness | pre, post, inv | `{P} close(w) {Q}`：若事务完成，则关闭回执、物理对象与读回一致 | 不证明 close 最终执行；必须另证活性 |
| Abadi–Lamport assume/guarantee 并发组件组合 | I,O,pre,post,eff | Runtime 保证无活动 Job 时关闭；Git/Host/Artifact 分别提供可信源/消费/处置假设与回执；交叉检查每个保证是否满足对方假设 | 不能将多个自我声明串联成真实消费者证明 |
| Lamport TLA+ safety、weak fairness、stuttering refinement | inv, prov, unfold | `[] (Closed => NoKnownLiveConsumer)` 与 `(<>[] Eligible) => <> Closed`（仅在 WF(Close) 假设下）；源码、部署分别需要精化见证 | TLC 有限状态 PASS 不代表 Rust/PG/OS 实现正确 |
| Nix GC Roots 与引用闭包 | S,pre,inv | 有效 Root 的可达闭包持续保存；失效时检查动态 Root/观察闭包 | `没有静态引用` 不等于不存在真实动态消费者 |
| Kleene strong three-valued logic（仅证据查询的启发） | epsilon,prov | UNKNOWN、TRUE、FALSE 不混淆；假证与证据缺失分别可观察 | UNKNOWN 不是逻辑 FALSE，也不是永久保持资源的理由 |
| Kleppmann 租约 + fencing token | S,pre,eff | 若续租允许过期/替代，新的拥有者必须拒绝旧 epoch 的滞后写入；在受管 PG CAS 边界实现 | 单有 TTL、进程消失或调用方 boolean 不构成已认证的排他所有权 |
| Kubernetes TTL-after-finished、Owner 机制 | S,post,c | TTL 从可证实的完成状态开始，删除前在权威状态重新读取 | 不应复制 Kubernetes API 及控制器；ownerReference 并非通用保活 Root |
| BuildKit 分级缓存 GC | c,post,unfold | 结果/持久源码与可重建缓存分开；无需对所有缓存保持同一龄期规则 | 不能把不可重现的未发布源码当成可删缓存 |
| Temporal durable event history | S,prov,eff | 已提交的执行意图/物理结果与重放边界分开；不凭响应丢失重新执行外部副作用 | 现有 Runtime/Host 不因此需要再安装 Temporal |
| Matt domain-modeling + TDD、ECC contract-first、Superpowers writing-plans / verification-before-completion | I,O,pre,post,prov | 从消费者出发规定一条公共 seam，RED→GREEN→变异反例→原生执行→Git/服务读回；两轴源码/Spec 评审 | Skill 只是方法，不授予执行权，也不是验收证据 |

### 10.1 逻辑义务与观察边界

以时间索引 `t` 表示一个观察切口；`Roots(t)` 是已确证的当前消费者根，`Edges(t)` 是其依赖关系，`ObsClosed(t)` 表示已经证明观察范围覆盖动态消费入口。

- **保活：** `Live(w,t) := w in Reachable(Roots(t), Edges(t))`。只有 `ObsClosed(t)` 与来源/租约当前性成立，才能由 `not Live` 导出已穷尽的无消费者结论。
- **回收许可：** `Reclaimable(w,t) := Quiescent(w,t) and DispositionResolved(w,t) and NoActiveConsumer(w,t) and CurrentIdentity(w,t)`。`Age >= 4h` 仅触发 reevaluation，不能被替代为 `NoActiveConsumer`。
- **安全性：** `[] (Close(w) => Reclaimable(w,t))` 是目标 Runtime/PG 消费边界的义务（不是现有代码已证明的事实）。
- **有条件活性：** `(<>[] Reclaimable(w)) => <> Closed(w)` 需要动作长期使能、弱公平和持续服务可用；`WF_vars(Close)` 仅为模型假设。
- **状态与知识不同：** `ConsumerFinished` 是世界中的事件，`ObservedConsumerFinished` 是证据，`caller.consumerReleased=true` 是声明。后者不能自行实现前两者。
- **并发真实性：** 观察 epoch、expectedSourceStateDigest、PG Job 保持状态应参与实际原子关闭/重读；如申请使用续租，必须为过期后的迟到写入设置 fencing/CAS 条件。
- **成果语义：** `PUBLISHED(ref,sourcecut)` 表示由持久权威接受；`DISCARDED(owner,sourcecut)` 表示明确不保留；`UNKNOWN(reason)` 不得通过默认 false 转换来消失。

**实用判断：** 对独立机器可验证的边界，采用源类型、数据库 CAS、模型检查和物理回执；对外部语义消费者没有可穷尽读集的情形，保留可执行的补证/退役任务，不发明全知 GC 或一套跨 Owner 审批中心。

### 10.2 一份模型中的两个精化层级

当前 `WorkspaceConsumerCloseR1.tla` **保留历史 R1 Close**：它允许 `age=expired` 后在 `consumer=active` 的抽象状态下关闭，因此旧 AGE-only 负向控制仍应失败。

相同 TLA 文件内新增 **R2 Candidate profile**（`WorkspaceConsumerCloseR1.r2-candidate.cfg`）：`R2CandidateClose == Close /\ consumer="finished"`，不新增第二份语义模型或新的事实权威。它独立检查：
- `R2CandidateClosedConsumerFinished` 不变量；
- `StableR2CandidateEligibleEventuallyClosed` 及 `WF_vars(R2CandidateClose)` 公平假设；
- 合法的消费者完成并显式释放后，必须存在年龄尚为 fresh 的关闭轨迹（非空证明）；
- 移除消费者完成 guard 必须由 TLC 产生命名安全反例；
- 移除公平性必须由 TLC 产生命名时序停滞反例。

此模型候选的 `consumer="finished"` 仍是抽象世界事实，**不属于 Runtime 已认证的 consumer witness**。它必须由 Runtime Core/PG 原生事务、Host/Artifact/Git 下游消费、安装版本和真实工作区回收逐层精化。在无此精化前，状态为 MODEL_CHECKED 而非 CODE_REFINED。

### 10.3 现行生产与并发工作边界（本轮重新核实）

- #1981 已合并，提供 R1 有条件公平活性与年龄误删负向证据。
- #1983 正在建设版本化 PG 原生回收器及自然消费者条件：支持没有成功 Job 但有明确持久 Git 根的清理候选、删除前 PG Job 重读、release manifest/systemd 接入；**不要再写第二套同责任脚本**。
- #1983 在此次观察时 CI repo-preflight/repo-mechanics 未通过，其中 preflight 的 GitHub Actions `mise` 下载 PowerShell 触发未认证 API 403 限流。这是当前 CI 环境障碍，而不是数学模型误证或 PG 回收算法反例；应由现有 GitHub/Workstation/Release 入口对齐认证安装。该 PR 仍处于 OPEN，未达到 MERGED 或 INSTALLED。
- 未来合并/部署与此研究所在分支均以实际 Git SHA 和 installed digest 为权威，不能复用此处历史观察作为不变真理。

### 10.4 一手参考（每一条只为对应语义背书）

- Hoare 1969, *An Axiomatic Basis for Computer Programming*: https://doi.org/10.1145/363235.363259
- Abadi & Lamport 1995, *Conjoining Specifications*: https://www.microsoft.com/en-us/research/publication/conjoining-specifications/
- Lamport, *Specifying Systems*，第 8、10、14 章: https://lamport.azurewebsites.net/tla/book.html
- Stanford Encyclopedia, *Many-Valued Logic*: https://plato.stanford.edu/entries/logic-manyvalued/
- Nix, GC roots: https://nix.dev/manual/nix/2.34/package-management/garbage-collector-roots
- Docker BuildKit GC: https://docs.docker.com/build/cache/garbage-collection/
- Kubernetes TTL-after-finished: https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/
- Kleppmann, *How to do distributed locking*: https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html
- Temporal, event history: https://docs.temporal.io/encyclopedia/event-history
- Matt engineering Skills: https://github.com/mattpocock/skills
- ECC: https://github.com/affaan-m/everything-claude-code
- Superpowers: https://github.com/obra/superpowers

## 10. 反向验证与退出条件

验证链：选择真实消费者 → 定义外部可见性质 → 正常路径测试 → 故意注入违反性质的 mutation → 命名反例 → 最小源实现 → 真实 PG/systemd/Windows 回读 → 删除旧实现/重复文档。

改革成功意味着下次无需人为要求清理大批死 Workspace，且独有价值不因旧 GC 被误丢；不以 Workspace 数量归零或“测试数量增加”为成功。若现实证据不足，保留 UNKNOWN，但必须有 owner、可执行下一步及自然到期/补证机制。
