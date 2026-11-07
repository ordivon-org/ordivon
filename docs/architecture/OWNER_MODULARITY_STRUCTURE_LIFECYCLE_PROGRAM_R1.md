# Ordivon 六主线执行计划 R2（Current）

> 更新基线：2026-11-06。范围聚焦：（A）Owner 高内聚低耦合拆解；（B）目录、命名、表征标准化；（C）Host、Runtime 及各 Owner 的最终消费者穿透清理；（D）成熟能力型与思想型 LEGO 的证据驱动发现和替换；（E）分别面向 Human/Agent 的使用指导；（F）将可证明的关键性质由成熟形式化工具验证，并仅保留不可替代的真实消费者验证。本文是可在任务完结后删除的协调工件，不是新的 Owner、Board、Meta/Next、数据库或治理机制。状态以最新 Git、PostgreSQL、Runtime、systemd、GitHub PR 和实际消费者为准。

## 一、目标函数、认识论与执行纪律

原则：Representation-first、Formal-first、天然 Owner、消费者闭包、单一状态权威。目的不是多创建模块，而是降低语义变化面、消除双写与重复实现、减少无法被最终消费者证明有用的残留。

- 语义边界：共享同一不变量与持久化权威的数据/行为聚合；依赖稳定契约的能力可以拆分。使用 Parnas 信息隐藏、DDD Bounded Context、Ports & Adapters、状态机精化和 Hoare/Assume–Guarantee，不按文件行数或名字机械拆分。
- LEGO 描述：输入 I、输出 O、状态 S、前置条件 pre、后置条件 post、不变量 inv、效果 eff、成本 c、误差 epsilon、来源 prov、展开 unfold。思想型与能力型 LEGO 均可，但必须有真实使用场景。
- 图关系：调用、导入、配置、依赖、运行消费者、状态转移、策略执行、等价/精化、证据有效性、SourceCut、安装实例、发布。状态分 SOURCE、CONFIGURED、INSTALLED、EXECUTED、CONSUMER、FORMAL、CURRENTNESS。
- UNKNOWN 不是 FALSE。历史消息、Git 提交、外键、回执只构成调查证据，不自动证明继续保留。与之相对，不曾观察到消费者也不自动证明不存在；必须穿透已知权威边界。
- 选择次序：DELETE-CUSTOM → REUSE → COMPOSE → EXTEND → CREATE。避免新增定制框架、通用门禁、备份格式、发布通道、任务看板。
- 执行闭环：GOAL → REPRESENT → CONTRACT → TRACE CONSUMERS → ANALYZE → FALSIFY → SELECT → IMPLEMENT → VERIFY → PUBLISH → RECHECK → RETIRE。每轮 3–5 个独立 WIP，按依赖图推进，不要求所有工作只能串行。
- 交付验收：自然 Owner 的公开契约保持或显式替换；实际消费者通过；源码、安装实例及数据库状态一致；自然 Owner 验证和受影响仓库 CI 通过；GitHub Merge Queue 发布；旧实现/残留删除；临时 Workspace/Worktree 清退。
- 执行权限：使用已授权管理员身份及操作系统原生机制；安全、形式化和 CI 检验只保留对真实故障模式有价值的必要部分。不因原生规则而重造通道或伪装成功。

## 二、源代码层次与自然 Owner（当前 20 个）

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

## 三、前三项工程主线 Work Package

每项都需写明：真实输入和最终消费者；需要保持的不变量；前置依赖；变更最小 SourceCut；验证证据；删除条件和实际发布状态。

### P0：当前真实状态权威与发布闭环

| WP | 所属 | 操作顺序 | 完成条件 / 下一节点 |
|---|---|---|---|
| H1（已完成） | Host | PR #1553 中 Schema 11 及 PostgreSQL 队列断言已经修复，经 GitHub Merge Queue 合并 | 合并提交 cb640db5613d；root-verification 和全部 CodeQL 通过 |
| H2（已完成） | Host + Workstation | 已停止旧写入，安装不可变 Host release cb640db5613d，执行生产 Alembic 0011，启动 systemd | 安装 SHA、Schema 11、doctor=healthy、Host 与 Gateway 双消费者均通过；旧 news 表已无；无双写 |
| H3（进行中） | Host | 复核最近清理后的 Work/Snapshot/Receipt/Message relation，追踪开放 Work 当前快照、Topic/Space/Subscription、消息游标和 Actor 引用 | 不再存在悬空结构化边；无开放 Work 消费被删除对象；执行 bounded SQL 与 doctor |
| R1（进行中） | Runtime | 获取 Linux/Windows Workspace、Job、Attempt、Artifact、Worktree/分支当前真值，合并当前 Host 开放 Work、GitHub PR、进程及已部署 SourceCut | 每个候选有 LIVE / REPLACED / HISTORICAL_ONLY / ORPHAN / UNKNOWN 明确证据 |
| R2（进行中） | Runtime | 对无消费者 clean Workspace 用原生 close；Dirty 差量按有效性迁入自然 Owner 或删除；清理悬空 Job/Attempt/Artifact；合并 Git 分支与 worktree 管理 | 不能只看干净、年龄或独立 SHA；当前真实 PR 和运行中的 Job 不受损 |
| D1（进行中） | Host | 终结 Work、幂等回执、失效 Topic/Space、subscription、Message Graph 的消费闭包清查与真实事务删除 | 同一事务删主体+确切关联；消息正文独立判断；PostgreSQL 原生 VACUUM ANALYZE |
| D2（进行中） | Repo/Workstation | 已合并 worktree、临时 Workspace、缓存、过期 release、无消费文件和重复资料清理 | Git/Runtime/systemd/OS 原生工具，无手写删除框架 |

当前观测仅作基线：Host 生产于 2026-11-06 完成 Schema 11 切换，切换后为 384 Work、44 Space、233 Topic，doctor 健康；Runtime 仍有大量 Dirty Workspace，不能沿用旧数量直接删除。历史已删除的数据不得因重新盘点而再次执行过期批处理。

**2026-11-06 已实现的执行证据：**
- H1：GitHub PR #1553 合并至 main，原生 Root Verification / CodeQL 通过。
- H2：Host 安装 release cb640db5613d667479f5bd050883fb71e23a99ee；Alembic 0011、Journal Schema 11，Host 与 Gateway 的 integrity 均 healthy。
- R1/R2：通过 Runtime 原生 MCP 的完整当前摘要比较和显式消费者释放，清除 11 个无活跃消费者的旧 Workspace；当前提交仍由 Git 或自然 Owner 保存的对象不因关闭物理 Workspace 丢失业务能力。Browser 未合并 PR 与当前开放 Work 消费者仍需保留。
- D2：已验证后移除旧 Host release 2c36b98aefa7 和 a1a0a6998906 两个无运行消费者的安装目录；约 133.5 MB 为表观文件大小，非保证的实际释放空间。首次切换时安装了 cb640db5613d；随后 PR #1559 的更新版本 b979fb0a0649 已被其他 Agent 安装并验证为 Schema 11、healthy=true。后续 current 以实时 systemd/符号链接和 doctor 为准，cb640db5613d 当前为可回退的 Schema 11 版本。
- 计划自身已通过 GitHub PR #1558 合并至 main；当前事实更新不另建治理系统。
- H3/D1：2026-10-03～10-16 的 28 条已无消息关系实体、无开放 Work 当前快照或近期消息消费的历史 message.relation.add 回执，已在一笔 PostgreSQL 事务中删除；未删消息正文和有效关系，Host Schema 11 doctor 仍 healthy。
- R2：旧 Dirty Workspace ws-gpt6-pg1210-ci-symlink-regression-fix-20261101-r1 的两份文件（Rust 测试与 Cargo Kani cfg）经当前 main 等价测试上下文和 TOML 语义核验、开放 Work 核验后，通过 Runtime 原生精确摘要 compare-and-close 并显式 consumerReleased=true 移除。此前已关闭 15 个 Workspace，本轮再关闭 1 个；并发其他 Agent 清理不计入。对当时 93 个 Dirty Workspace 小规模差量扫描未发现逐文件 Git Blob 全部等价的其他可批量删除候选。
- M4 Gateway：PR #1572（尚待 GitHub Merge Queue）提取 Research/Skills 解析至自然 Gateway Owner 的 research_resolution.py；Gateway 全量 Owner 测试和公开 API/解析摘要等价测试通过。本地整套 repo:ci 后续阶段达到 Runtime 时限，不能当作全项 PASS，仍以 GitHub 必需检查为发布依据。
- M7 Skills：PR #1576（尚待 GitHub Merge Queue）提取 JWT/Bearer/ASGI 身份验证至 Skills Owner 的 http_auth.py，保留旧入口同一实现对象；157 项测试、51 子测试、Wheel 打包及 413 拒绝下游调用负向测试通过。合并后仍需核对实际安装 SourceCut，不以 PR 代替部署。
- C5/P2 消费者审计：ordivon-control-plane 两个 Plugin Manifest 有原生打包工具、Harness 和仓库验证消费者，不能仅按文件少就删除。


### P1：核心服务与平台拆解

| WP | 候选切分 | 真实测试与完成条件 |
|---|---|---|
| M1 | Runtime Job/Attempt/Workspace/Artifact/Recovery 状态机、事务存储、Provider Adapter 分层 | 源码图消除双写，真实 Job 恢复和 Workspace 生命周期消费者 |
| M2 | Host Work/Social/Attention/Receipt/Alembic 表达与数据访问边界 | 已拆的 Social Read 不回退；PG 事务、查询和真实分页保持 |
| M3 | Harness Lifecycle/Model/Tool/Trace/Recovery 分层 | Tool 调用与失败重放；不创造第二 Job |
| M4 | Gateway routing/adaptation 与 Host、Runtime 原生契约切分 | 北向公开接口 E2E，无隐藏权限/数据权威 |
| M5 | Network Policy/Resolver/Tunnel/Proxy/Route/Recovery 组合 | NS2 当前真实出口，故障注入后恢复；成熟 Provider 优先 |
| M6 | Security Policy/Principal/Credential/Enforcement 分层 | 权限有可测试的职责边界，不复刻 OS/Seccomp/systemd |
| M7 | Skills 探索/绑定/验证、Workstation Inventory/Release/Recovery 分层 | 当前 Skill consumer 及 Windows/Linux 原生系统验证 |

### P2：能力/领域整理与共性归并

| WP | 主要拆解目标 | 判定 |
|---|---|---|
| C1 | Artifact/Distribution/Preservation 区分内容、目的地和长期恢复 | 删除自制重复的打包/存储机制 |
| C2 | Media 素材/Provider/渲染/导出/缓存 | 实际 Media Consumer、内容摘要/许可证 |
| C3 | Game ECS/行为/Agent Tool/素材/UI/存档/回放 | 可运行原型与 Agent 原生交互 |
| C4 | Capital Data/Research/Backtest/Portfolio/Risk/Execution | 单数据权威；不把研究接入直接当实盘权限 |
| C5 | Web 与 Control Plugin 薄适配 | 若原生接口已覆盖使用者，直接删除外层包装 |
| C6 | Composition 组合契约、抽象、约束、证明系统 | 复用成熟 SMT/SHACL/Lean/状态机，不造新算法框架 |
| C7 | Authority/Capability 两 Catalog 的发现、观测、绑定、验证 | 避免多套 Catalog/Provider 注册 |
| C8 | Chaoxing 业务流程与 Harness、Browser Adapter | 不重复造通用浏览器操作层 |

### P1/P2：目录、命名、表征标准化

| WP | 实施细节 | 验收 |
|---|---|---|
| N1 | 建立 20 Owner 的入口、文件、公开 API、跨 Owner 调用、配置、测试、CLI、数据库、安装实例索引 | 每个实际源路径归自然 Owner 或明确的非 Owner source region |
| N2 | Rust crate/module、Python package/module、TS package/模块命名、大小写和文件路径规范化 | 必须有真实消费者价值；改名同步 imports、构建、文档、配置 |
| N3 | 收敛 src/tests/scripts/packaging/migrations/research/studies/fixtures 的自然摆放 | 消费者行为保持且源变更不扩大；真实迁移用 git mv |
| N4 | 清理 Next/Meta、旧版活跃别名、重复封装和失效 CODEOWNERS/mise/Skill/README | 不存在旧代码入口；Git 历史用于追溯，不存平行活跃源 |
| N5 | 更新 SourceCut/消费者依赖图、发布锁定和安装映射 | 每个 SOURCE/INSTALLED/EXECUTED 证据不混淆 |
| N6 | 取消无实际消费的历史文档、验收重复物、日志、缓存与临时工作区 | 当前文档唯一入口；删除完成后本计划本身也退役 |

### P0/P2：各类最终消费者清理闭包

| WP | 数据对象 | 删除所需的事实 |
|---|---|---|
| X1 | Host Work/Snapshot/Receipt/WorkRelation | 终结状态、无当前开放 Work 引用，无近期活跃消息、订阅/业务消费者；事务清理 |
| X2 | Host Space/Topic/Message/Actor/Subscriptions/Cursors | 穿透 Social + Attention Graph，不能仅凭空 Topic 或有旧回执判断 |
| X3 | Host 表/索引/旧 Schema/新闻遗留 | Alembic 作为结构 Authority；PG 事务和 doctor；无兼容中的旧二进制 |
| X4 | Runtime Job/Attempt/Workspace/Artifact | 活动 Job、恢复租约、Git SHA、PR、Host Work 最终消费者 |
| X5 | Git Worktree/分支/无意义历史实验 | 原生 Git 机制；未提交差量与 SourceCut；允许删无价值独立提交但不能误删有效唯一工作 |
| X6 | Network/Security/Workstation 临时安装/凭据/路径/旧配置 | 当前系统进程、服务、安装版本、真正策略消费者 |
| X7 | Media/Game/Capital/Artifact 生成文件、失败研究、重复实验 | 许可、独特不可恢复字节、实际当前产品/论文消费者 |
| X8 | Preservation/Distribution 重复归档、旧发布和快照 | 证明现有内核满足恢复与交付；只保留必要原生恢复点 |
| X9 | Skill/Catalog/Plugin 旧别名、桥接层、注册信息 | 当前绑定/调用者已经改为自然 Owner；删除外层 |
| X10 | C/D 盘、WSL VHDX、日志与缓存、历史大目录 | 物理容量、仍存活消费者、真实恢复资源；原生系统/WSL 操作 |

处置类别只有 DELETE、MIGRATE_THEN_DELETE、REUSE、KEEP_ACTIVE、UNKNOWN_EVIDENCE。历史性记录不是永久 KEEP_ACTIVE；若源在 Git、Consumer 已终结、并无合法持有义务，优先实际删除。UNKNOWN 先定点补证据，而不是扩大永久防护。

## 六主线 F：形式化性质逐步取代冗余样例验证

- **规格与真实实现分离。** Owner 先标明不可违反的安全性质、允许的状态转移、活性前提和调用者边界；模型证明必须注明有限状态/参数、假设、SourceCut 以及实现精化尚未覆盖的部分。模型 PASS 不自动提升为已安装实例 PASS。
- **成熟工具各归其位。** Runtime/Harness/Composition 继续复用现有 digest-verified TLA+/TLC；Runtime Rust 代码按实际可用范围使用 Kani/Verus；跨模块契约优先组合现有 Lean/Z3/Pacti；Host Python 纯决策优先复用已锁定的 CrossHair，而不是新建验证解释器。
- **Host 当前具体范例。** social_message_commands._reply_target_precedes_source 证明回复边遵循严格递减顺序；work_store._next_work_revision 证明 Work CAS 修订号单调且不超过 PostgreSQL BIGINT 上界。两者均是实际业务代码，而非另写的等价影子实现；正式入口仍负责输入类型、PG 事务及消费者验收。
- **移除标准。** 当形式化性质覆盖、源代码连接、工具证据和负向反例均独立核实后，删除仅重复同一性质的样例断言；不得以抽象证明删除 PostgreSQL 行锁/事务、MCP 协议、实际部署、网络/系统效果以及跨 Owner 最终消费者验证。
- **发布顺序。** 按自然 Owner 的 mise run verify 与根仓库 mise run repo:ci 验证、经 GitHub Merge Queue 合并，然后确认安装 SourceCut；不为验证再造 Owner、审计数据库或独立发布管线。

## 四、分波次实施、验收与关闭

- **Wave 0（P0）**：H1 → H2；并行 R1、H3、D1，完成后 R2、D2。先协调源码与安装状态，不在运行 Schema 10 代码时擅自升级其数据库。
- **Wave 1（P1）**：M1–M4 的语义模块边界与 N1；同步整理 Network/Security/Skills/Workstation 的自然消费者。避免一次 PR 改动多个不相关 Owner。
- **Wave 2（P1/P2）**：C1–C8，结合 N2–N5 完成真实消费者验证与旧路径清理。
- **Wave 3（持续）**：X1–X10 周期性消费者穿透；每项本身具有完成态并清理临时支撑，减少而非扩张治理层。

协作使用已有 Host Task Space 承接任务、最大交流 Space 用于沟通；Agent Loop 内自规划：MCDT in the loop, Human on the loop。声明 SourceCut 避免与其他 Agent 同时修改同一路径，但不因内部审批拖延工作。每次发布仍通过 GitHub PR、原生必需检查与 Merge Queue，并对安装侧单独验收。

本文件自身退出条件：各 Work Package 已在自然 Owner 源码和安装证据中闭环，无未知当前消费者；移除此文件而不建一个新的长期维护看板。


## 五、成熟 LEGO 的证据驱动发现、采用与退役

本主线是既有自然 Owner 的工作方法，而不是新的注册表、治理 Owner 或通用执行平台。区分能力型 LEGO（有界读/转换/求解/效果）与思想型 LEGO（表示、拆解、选择、组合、验证方法）。Skill、Tool、文件、Provider 卡片并非天然独立的已准入 LEGO；只有明确声明/准入时才按 R2.1 完整十一坐标建模。

1. 从 Human/domain 目标和实际消费者反推必要责任，先 DELETE 不必要自制实现；再复用自然 Owner；仍不足时比较成熟外界 Provider、组合/薄适配，最后才考虑自造。非消费证据不能伪装为“无消费者”。
2. 外界只补实质未知：官方 SourceCut/文档、许可证、维护状态、效果与权限、替换契约、成本、可验证反例。优先使用 `catalogs/capabilities/packages/INDEX.md` 与已有 `catalogs/capabilities/providers/`，不建立平行 Provider 索引。
3. 根据问题选择最小思想型 LEGO：Bounded Context / `project-kernel-decomposition` 定责任，`design-structure-matrix` 查耦合，`compositional-contracts` 证明组合前提，`recursive-lego-calculus` 查最终消费者闭包。方法结论与真实源代码、安装、运行、领域验收互相独立。
4. 每次替换以同一消费者验收谓词比较旧与新，保持天然 Owner 单一真值。正常 GitHub Merge Queue 发布，原生 Release 安装及消费者读回后删除旧实现和可再生残留。

| 成熟外部基础 | Ordivon 已有入口 | 边界与采用结论 |
| --- | --- | --- |
| DDD / Team Topologies / DSM | `tools/repo/owners.toml`、Owner Boundary、现有方法 Skills | 按语义权威与独立变化原因拆分，不按文件大小拆分 |
| Agent Skills 开放规格 | `.agents/skills/`、`extensions/chatgpt-skills-mcp/` | Skill 包按需读取；文件存在不等于在线 Skills 服务已注册或可解析 |
| Git 原生 worktree / Worktrunk | Runtime Workspace、`catalogs/capabilities/providers/worktrunk.md` | Worktrunk 目前只具备只读 Git 对照证据，可研究 Workstation UX，不代替 Runtime Workspace/Recovery |
| PostgreSQL / GitHub Merge Queue | Host 原生 PG、Alembic、GitHub PR | 重用状态与发布权威，不自造中间 Ledger 或第二发布队列 |
| OpenSSF Scorecard / SLSA / OpenTelemetry | Provider 评价、Artifact/Distribution、原生日志与追踪 | 分别用于风险线索、构建来源、统一事件命名；均不是形式化正确性证明 |

官方参考：https://martinfowler.com/bliki/BoundedContext.html 、https://teamtopologies.com/key-concepts-content/team-interaction-modeling-with-team-topologies 、https://agentskills.io/specification 、https://openssf.org/projects/scorecard/ 、https://slsa.dev/spec/v1.2/provenance 、https://opentelemetry.io/docs/specs/semconv/ 。

## 六、分别面向 Human 与 Agent 的原生入口

**Human：** 直接提出目标、最终可观察收益和愿意承担的影响，不必手动写十一坐标。先在 `catalogs/capabilities/packages/INDEX.md` 选择 Package，再寻找 Owner 原生能力；比较不做、自带能力、外界成熟能力三个方案；验收要看真实读回、变化与代价。例如“关闭旧的 Host Topic，但保留历史消息可读”，应复用 Host `topic.state.set` 的 CAS，而不是另写删除服务。详细步骤见 `.agents/skills/recursive-lego-calculus/references/owner-provider-human-agent.md`。

**Agent：** 从 `AGENTS.md`、Owner Manifest、`origin/main` SourceCut、实际已安装实例和真实消费者开始；用 `method-router` 选最少的专业方法；对独立声明的 LEGO 填全 R2.1 契约；采用现成 Port/工具并做有针对性的消费者验证；经受保护主线发布、安装读回后退役旧 Carrier。Skill 文件仅被 Git 跟踪，不代表当前 Skill Server 的绑定；必须用当前 `resolve/read` 证实可见性。具体工作路径见同一 reference 的 Agent 部分。

**同一能力、两种视图：** Human 看收益、效果、可恢复性；Agent 看精确身份、前置条件、不变量、效果、证据和作用范围。两者不分别创建 Owner、状态表、规则引擎或工作流。
