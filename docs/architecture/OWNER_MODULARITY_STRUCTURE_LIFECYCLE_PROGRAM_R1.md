# Ordivon 全仓存量现代化执行 Spec R3（2026-11-10）

> **当前执行范围**：重新核验本地源代码与远端主线，按实际责任对存量文件执行删除、合并、重命名、行为保持的内部重构和已知缺陷修补。**冻结新增功能、新测试/测试框架、新消费者线路、第二套治理/LEGO Registry/工作流。**此文件沿用唯一现有全仓 Program 入口，不新增独立框架。
>
> **SourceCut**：本机 /root/projects/ordivon 的 main=93780417c71600873a0847f02c17d094f2416082（干净）；对照已 fetch origin/main=ef17d6879d12faa61fff3bb762b0d500d73c9113（2026-11-10），两者 **1 个本地独有提交 / 140 个远端新提交**。不得把本地主线误称远端权威、重置其独有改动或未经确认改其他 Agent 的工作树。实际代码 PR 以发起时最新远端 SourceCut 为准。
>
> **证据分级**：文件枚举/静态引用、代码行为、native verify、GitHub CI、MERGED、INSTALLED、CONSUMED 各有不同范围，UNKNOWN 不是 FALSE 也不是 PASS。

## 1. 目标和反目标

本项目只优化已经存在的系统：减少重复实现、过时配置/计划、无当前消费者的中间层、复杂且无必要的自研工具和错误的“当前权威”文本；保留能由真正自然 Owner/消费者说明必要性的责任。**不是**以删除行数、重命名数量或额外审计记录数量制造成绩。

形式化目标可以写成：在现有消费者可观察行为、权限与外部副作用不扩大约束下，最小化已有系统的维护复杂度、重复实现、跨边界变更和人/Agent 理解成本。没有测量的维护收益、性能变化、风险改善一律 UNKNOWN，不能凭主观编造百分比。

文件是审计单位，不是 LEGO。正式声明的独立责任才使用 R2.1 完整 (I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)；没有证据时带来源/范围标明 UNKNOWN。历史回执、Git 存在、字面无引用分别都不能自动推出业务完成、当前部署或可删权限。

**正向允许**：DELETE / CONSOLIDATE / RENAME / MOVE / REFACTOR（行为保持）/ REPAIR 已知缺陷；只运行既有测试与 Owner native verification。**反向禁止**：新能力、扩大 API、新测试或新消费者链、新通用 Verifier、第二个源码/状态权威、没有真实收益的大爆炸重写。

## 2. 理论、工程与管理学基础

| 已成熟的范式 | 本次用途 | 不允许的外推 |
| --- | --- | --- |
| Parnas 信息隐藏、DDD bounded contexts、系统工程 | 以独立变化原因/职责/自然 Owner 划定模块，不按目录数拆分 | 相同路径前缀或大文件不是错误模块的证明 |
| Eppinger/Browning Design Structure Matrix | 由真实 import/call/config/readset 和共同变更形成稀疏图，定位循环/交叉耦合 | 相关性、同词/同名不当作消费者依赖 |
| Fowler Refactoring、代码异味 | 小步行为保持的内聚改进、消除 Middle Man/Speculative Generality/重复逻辑 | 仅根据行数、格式、命名或自动评分进行重写 |
| Nix GC Root、Git reachable objects | 真实根及当前可达依赖保留，消除可恢复且无消费者的临时载体 | 仅靠 git grep 零结果推断所有动态消费者不存在 |
| Lean Muda / Theory of Constraints / A3-PDCA | 从全系统维护瓶颈下手，停止无效任务循环和重复 PR | 自造审批流程、统一硬 WIP 数量或持续堆积计划 |
| Hoare/Assume-Guarantee/观察精化 | 现存公开契约和副作用不被新内部结构破坏 | DOC/MODEL 的结论升级为安装或领域业务证明 |

复用已有 Ordivon 思想型 Skills：recursive-lego-calculus（DELETE→REUSE→COMPOSE）、project-kernel-decomposition / systems-engineering（自然 Owner）、design-structure-matrix（结构耦合）、external-capability-evaluation（外部成熟替代）、compositional-contracts（仅真实形式化 seam）。执行按 Matt code-review **Standards×Spec** 两轴，ECC brownfield-retrospective / orch-refine-code 的逆向现状与行为保持，Superpowers writing-plans / verification-before-completion 的精确提交与当前命令。显式跳过这些外部模板中与本轮冻结新功能/新测试相冲突的选项。外部出处：martinfowler.com/books/refactoring.html、nixos.org/guides/nix-pills/11-garbage-collector.html、lean.org/lexicon-terms/theory-of-constraints/、docs.cloud.google.com/docs/cloud-approach-to-change。

## 3. 当前真实文件盘点及解释

在精确远端 SourceCut ef17d6879d12 上对 **全部 5,002 个 tracked paths** 做过机器清查：Python 1,460、JSON 1,315、Markdown 849、Rust 131、TypeScript 89、GDScript 86。主要 Owner 文件量：Harness 731，Media 553，Runtime 452，Artifact 425，Capital 399，Game 387，Workstation 265，Network 236，Security 162，Host 117，Gateway 107，Composition 86。

**事实边界**：已覆盖全部文件的 *机械枚举、类型、行数/大小、散列/精确重复候选*，不代表全部 5,002 个文件完成逐行语义审计，也没有证明所有动态消费者闭包。逐文件语义复核应当在有限切片中深入开展，通常约 15 个文件或 2,000 行一组；巨型文件按实际调用职责解剖，而非一看到行数就拆文件。全量明细可由 Git 重算，不要维护第二套 5,002 行注册表。

现有根源重点：
- C01 Git drift：本地 main 比远端少 140 个提交并多一个独有提交，必须先分清权威。
- C02 Distribution：30 个文件，现有 Workstation n8n 脚本确实消费 R7 fixture；**开放 PR #1950 已经覆盖其中 21 个旧文件**，复用它，绝不再开重叠 PR；其余可选外部探针需另判。
- C03 Harness research：research/README.md 是当前 owner research 恢复根，authority/CURRENT.json 有发布绑定；不能仅凭“Markdown 无 import”删整条历史链。
- C04 Harness run_continuity.py 3,186 行；Runtime runtime/tests.rs 10,788 行；Repo check_architecture_docs.py 2,524 行。三者都是高复杂度调查候选，**不是**已确认的代码缺陷或必须拆分的命令。
- C05 Harness browser-security 存在几组逐字节相同的历史 JSON；需辨别独立实验身份、冻结摘要和实际读集；未核实前不能仅靠哈希删除。
- C06 Media 大体积真实媒体资产有可能是用户交付或可复现素材，不以字节大为垃圾判断。
- C07 已有多个清理 PR（#1950、#1940、#1937、#1930 等），应先使用已提交的本地证明与自然 Owner，而不是按 Agent 数量复制代码。

## 4. 20 个自然 Owner（复用原 manifest，不新建）

本表提供待调查的语义切分候选，不代表未经代码与消费者验证就要新建每个子目录。

| ID | Owner 与根目录 | 候选高内聚单元 | 核心验证 |
|---|---|---|---|
| O01 | Runtime — services/runtime | Job admission/identity；Attempt 执行/重试；Workspace 源码与隔离；Artifact 引用；恢复、租约与 PG 持久化；Linux/Windows Provider | Job/Attempt 状态机精化、单写入者、故障恢复、实际客户端、SQLite 活动写路径清退 |
| O02 | Host — services/host | Actor；Work Graph；Space/Topic/Message；Attention/Subscription；Social 读写；PG Receipt；Alembic | 事务/幂等、真实 MCP/网关消费者、分页、关系完整性、重放 |
| O03 | Harness — services/harness | Agent 生命周期；模型适配；计划/Tool 调度；Observation/Trace；Recovery；Browser Harness | 工具轨迹/失败重放、取消恢复、执行接口；不复制 Runtime Job 或 Network 路由 |
| O04 | Gateway — services/gateway | 能力发现与路由；授权委托；传输映射；错误/流式协议 | 实际北向 API/Host/Runtime 路由和拒绝语义 |
| O05 | Network — platform/network | DNS；VPN；代理；路由；连接状态；出口策略；故障恢复；OS 适配 | NS2 实际 DNS/出口/策略/故障注入，配置与物理出口一致 |
| O06 | Security — platform/security | Principal/Capability；策略决策；凭据权威；执行适配；审计 | 无隐式权限升级；决策与效果分离；原生系统凭据管理 |
| O07 | Skills — extensions/chatgpt-skills-mcp | Discover/Bind/Resolve/Read/Verify；Skill currentness；供应方适配 | 精确绑定、版本/来源、真实 Skill 使用者；无第二注册表 |
| O08 | Workstation — platform/workstation | OS/WSL 环境；清单；部署；systemd；版本安装；回滚；维护 | 已安装实例与 SourceCut；系统级真实恢复与幂等 |
| O09 | Artifact — capabilities/artifact | 内容类型/转换；来源；生命周期；存储/验证 | 产物摘要、转换损耗声明、发布/媒体消费者 |
| O10 | Distribution — capabilities/distribution | 打包、分发目的地、传输、发布回执 | 原生目的地确认；不接管 Artifact 内容权威 |
| O11 | Media — capabilities/media | Provider、摄取、素材、编码/渲染、导出、缓存 | 真实媒体输出、资产/来源与可复现性 |
| O12 | Preservation — capabilities/preservation | 保留策略、完整性、归档、恢复、介质适配 | 恢复演练及实际保留义务，删除多余归档层 |
| O13 | Game — domains/game | ECS、规则、AI Agent 操作、关卡/UI、素材、存档、回放 | Bevy/Godot 原生消费者与可运行游戏；冻结 R7 消费 |
| O14 | Capital — domains/capital | 数据采集标准化、因子、组合、回测、仿真、风险、交易适配 | look-ahead 约束、可重放研究，仿真与实盘权威隔离 |
| O15 | Web — apps/web | 页面/路由、客户端状态、API 适配、构建部署 | 浏览器端 E2E 与真实 API，不复制业务模型 |
| O16 | Control Plugin — extensions/ordivon-control-plane | Plugin Manifest、Tool 桥接、可用性投影 | 原生控制接口消费者；薄适配，删除无用外壳 |
| O17 | Composition — packages/composition | 类型化 Port/绑定、代数/约束、验证器、等价/精化 | 成熟 SMT/SHACL/约束组合；不建第二 Owner 注册表 |
| O18 | Authority Catalog — catalogs/authorities | 权威来源、观察、证据、currentness | 验证路径和可观测来源、原生 Catalog 验证 |
| O19 | Capability Catalog — catalogs/capabilities | Provider 能力、发现、组合绑定、路由元数据 | 真实 Provider 解析与调用边界；不冒充执行权威 |
| O20 | Chaoxing — apps/chaoxing-autosign | 课程/会话发现；签到操作；交互适配；状态回放 | Windows Chrome 真消费者、真实动作与干跑语义 |

正式源码区域另外包括 profiles/、studies/、tools/repo/、docs/architecture/；它们不自动成为新的业务 Owner。Meta/Next 已经通过 PR #1539 退役，不再恢复新的总控目录。语言优先 Rust、TypeScript、Python；TS 使用 pnpm、锁文件，依赖升级以当前自然 Owner 为权威。

## 5. 完整执行 DAG（存量专用）

| Task | 既有入口和动作 | 退出条件 |
| --- | --- | --- |
| T0 固定权威 | Git root / origin/main / owners.toml / AGENTS.md / GitHub PR 文件清单 / 当前 Host Space | 0 次无依据覆盖本地独有提交，0 次触碰他人 Worktree；对开放 PR 逐路径避碰 |
| T1 逐文件机械审计 | git ls-files -z，文件类型、大小、哈希、符号链接、生成/历史分类、显式/动态入口风险 | 全部当前跟踪文件枚举，可重算；不建持久第二数据库 |
| T2 语义切片深审 | 根入口→真实责任→现有代码/配置/CLI/Service/验证→自然 Owner；使用 DSM/Parnas/Fowler | 改动候选给出明确职责与代码/证据路径，不以名称/大小猜测死代码 |
| T3 Space 交叉审计 | 使用既有 Whole-System Optimization Space，Matt Standards×Spec、ECC brownfield 及 Superpowers 当前验证 | 每个实质候选明确理论、保守性、表面化、表征、成熟替代、真实引用、SourceCut 与反例；Space 不是审批权威 |
| T4 存量执行 | 只对不与活跃 PR 重叠的切片进行 DELETE/MERGE/REFACTOR/修补，尽量利用语言、Git、现有成熟工具 | 无新增功能/测试/消费者链；旧实现实物退出而不是只写新 README |
| T5 原生验证 | 直接运行已有 owner:verify、编译/格式检查、受影响 repo:ci 与 Git 差量检查 | 限定实际测试/命令退出码，任何未运行状态明确 UNKNOWN |
| T6 真实发布与退役 | GitHub PR、原生必需检查/merge queue、Git Main 读回、必要时 Owner 安装态核对 | SOURCE/CI/MERGED/INSTALLED/CONSUMED 分级，临时工作树和审计本身不永久扩张 |

T1 已完成当前 SourceCut 的机械清单；T2 后续按 Owner 分片并行，T3 不得成为所有模块必须同步等待的中央委员会。已有成熟提交直接复用并按需独立审计；缺少一项边界证据只阻断该项相关删除，不能自动冻结全部工作。

## 6. 每个候选必经的十维交叉核验

1. **真实目标**：所删/改的责任对人类或产品究竟产生什么既有价值？
2. **理论严格性**：Hoare、A/G、观察精化、可达性等所援引定理的假设是否满足？
3. **R2.1 合法性**：是否将文件、Job 或测试冒充独立 LEGO，是否将 UNKNOWN 伪装成 FALSE？
4. **Matt/ECC/Superpowers**：双轴审查、基线重建和新鲜验证是执行过还是只被引用？
5. **过度保守**：是否因抽象“可能有人用”永久保留垃圾，是否自造多余门禁？
6. **表面工作**：是否只修改名字、字数、行数，而未减少真正的重复权威或维护成本？
7. **问题表征**：此对象是现役代码、研究记录、生成缓存、可复现资产、依赖关系还是无价值桥接？
8. **成熟替代**：语言生态、Git、OS、PG、当前 Owner 或外部顶级项目有没有现成方案？
9. **消费者和避碰**：是否真实引用、动态加载或外部消费？有没有现存 PR、并行 Agent、唯一不可恢复字节？
10. **动作与反例**：精确 source path、单一可执行下一步、已有 native command、负面证据和 GO/REVISE/NO-GO 是什么？

裁决类别：KEEP、DELETE、MERGE、REFACTOR、REPAIR、HOLD(reason,scope,evidence)。历史 Git 证据留在 Git；无需每个文件单独写一份十一坐标证明或建立计划数据库。

## 7. 当前协作及真实执行

已在现有 Space 的 Continuous Maintenance Topic 发布全仓工作避碰请求（seq25886）和 Distribution 30 文件专项交叉审核（seq25908）；同行有效反例必须依据当下 Git SHA 与自然 Owner 读集，不得以自述 PASS 代替。已执行 Distribution 原生 mise run verify：退出 0（Runtime Job job-01a1c172-0787-70ed-b16f-1caf4910f7ec）。

**下一批具体任务**：1）自然 Repo Owner 收敛本地与远端 SourceCut 边界；2）优先审查已开放 #1950/#1940 等减法 PR，避免重复实施；3）Distribution 剩余无生产消费的探针及其唯一内部依赖评审，必要时删现役树；4）Harness 对 run_continuity.py 和已发布 research 根做维护切片；5）Runtime/Repo 对大聚合实现先查误置责任再做内部重构；6）停止增加与现有 Owner、Build/CI/Runtime/Host 重复的自研层。

**本 Spec 退出条件**：本轮存量切片由原生源码和 GitHub PR 承担后，本文件只保留当前的 Owner 导航与必要工程约束，历史逐波次叙事仍可从 Git 历史恢复。不能永久维持一个与 Host Work、Git、Runtime 平行的维护看板。
