# Ordivon 架构改革执行 Spec · 2026-11-26

本文件是当前 Host 领域 Spec 的跨域执行索引。每项交付仍进入原有 Work、Owner 的源码、GitHub 检查和实际消费入口。源切片为 monorepo `f8426d952f29aed8d4bb35c424144e87ac78bb62`，共 5,735 个 Git 跟踪路径。以下盘点覆盖现有顶层语义职责、21 个仓库验证辖区及外部 Research 入口。仓库路径清单属于源码证据，动态依赖和生产消费者的覆盖各由对应证据限定。

## 1. 目标、现实与变化

**目标。** Agent 从已认证入口恢复可续作任务，选择已验证的能力，接收可查询、可对账的效果回执。跨域调用各自独立发布，任一替换能用真实消费者证据判断等价、收益、回退与退役。

**现实。** Host 现场返回 PostgreSQL journal、应用 schema 14、44 Space / 269 Topic / 32,165 Message。应用 schema 编号与 PostgreSQL 服务端大版本属于不同坐标。Gateway 0.10.20 现场返回非权威路由投影，Linux、Windows、Host 和 Skills 已配置，Harness 专用 Runtime profile 路由未配置。Linux 新 PG epoch 接受并完成本轮源码盘点 Job。Windows 现场读到原生 Runtime Workspace 及活动 Job，Windows 工作区可用与同一 PG 写入链闭环需要不同证据。

| 已有选择 | 当前证据 | 本轮沿用的执行约束 |
| --- | --- | --- |
| Linux Runtime Rust / PostgreSQL / systemd/cgroup | 当前 PG 入口执行了实际 Git 盘点，主线已合 Artifact 索引与来源修复 #2800/#2685 | 沿现有 Runtime R12 #32712。下一条原生可证义务由 Job/Attempt/Artifact 回执闭合 |
| Windows Runtime Rust / PostgreSQL / Job Object | Host Work@33 有 Windows PE 与独立 PG 的试验，#2469/#2471 仍为开放候选 | 同一 admission/Attempt 的 Job Object、Session 1、取消排空、终态及输出回执一起验收 |
| Host PostgreSQL 19 | Host Work@118、#32704/#32726、#2818 记录优化构建、原生 suite 和两恢复点 PITR。直接读取的是应用 schema 14 | 复用已发表证据。真实服务部署须验证目标介质、扩展、排序、消费者及回退 |
| Harness Rust + PG | Harness Work@140 记录候选和既有 Python/Rust 演进。Gateway 的 Harness profile 当前未配置 | 以具体 Run 的 Provider、Tool effect、Journal/CAS/reconcile 和恢复链验收，保留尚有消费者的兼容入口 |
| Gateway Rust / rmcp / Tokio / reqwest | Host #32664/#32695 和 #2801 为进行中的 Rust 迁移。运行入口仍报告 0.10.20 | 依现有 Draft 比较 Rust 与现有实际 MCP 输入输出，涵盖工具发现、错误、未知结果、重附与顺序 |
| 依赖工具链独立滚动，Owner 保持锁文件 | #2304 的同源分支已落后。当前 uv 0.13.10 被两个真实项目的 `required-version` 拒绝 | 首批执行原 PR 的已确认迁移，用受影响项目和根验证的实际运行证明 |

Host 来源坐标包括全局 Topic `topic:ordivon-whole-system-optimization:global-architecture-mature-substrates-r1:20261031`，跨核数据 Work `work:ordivon:crosscore-data-architecture-r1:20261125@11` 与 #32025/#32714，Host #32666/#32704，运行 #32712，Gateway #32664，网络 #32719，Research #32645，Finance #32706，Media #32674。其余领域以就近的现有 Owner 入口重新取当前证据。

## 2. Thought LEGO 与外部能力

| Thought LEGO | 在 Ordivon 中的决策 | 成熟能力及验收边界 |
| --- | --- | --- |
| 表征优先、逻辑与效果分离 | 命令、意图、已准入操作、执行事实、领域验收分别有类型及标识 | Rust / TS / Python 的原生数据类型、显式接口。具体调用者需能重附原标识 |
| 事件因果与显式恢复 | Work CAS、Run Journal、Job Attempt、Artifact 和交付回执独立，跨层只持有因果引用 | PostgreSQL 事务、唯一约束、版本列和 native runner 证据。NOTIFY 仅可作为唤醒，重连靠耐久读 |
| 端口与适配器、生产者权威 | Gateway 持有路由和协议投影。各 Owner 持有事实、幂等和版本 | MCP / 官方 Rust SDK。原生 tool schema、错误、分页及丢包后重附对比承担验证 |
| 源码依赖的反向闭包、计算复用 | 用 Git SourceCut 和已有检查读集失效，保留调用者真正依赖的门 | Git、GitHub merge group、Bazel Skyframe 的增量思想。当前保留 mise 及现有分片和工作流 |
| 可恢复性与单写者 | 迁移后用同一自然权威读回并验证恢复点，按版本比较历史来源 | PostgreSQL 原生升级、pgBackRest WAL/PITR，Git 原生对象和独立归档读取 |
| 可证伪、行为精化、成本测量 | 先写不变量与可观察反例，再挑性质、故障、差分和端到端测试 | TLC / Lean、Hypothesis / Rust 原生测试、Nextest、真实 PG / Windows / 浏览器 / 编解码器 |
| 科研与仿真范式 | 论文用贡献、证据、独立复核闭合。投资用时点数据、仿真成交与账本对账闭合 | ACM SIGSOFT Empirical Standards、FAIR/TOP、已选 Qlib/MLflow、风险模型和 Paper/OMS 真实消费者 |
| 兼容范围与生成锁 | 开发工具允许滚动，受控复现依赖锁和已构建的签名版本 | mise 解析 `latest`、uv 管缓存和锁，Cargo/pnpm 各自维护原生锁，实际供应链物料记录精确版本/摘要 |

外部原始材料：[PostgreSQL 19](https://www.postgresql.org/docs/19/) · [PostgreSQL 通知](https://www.postgresql.org/docs/19/sql-notify.html) · [MCP Rust SDK](https://rust.sdk.modelcontextprotocol.io/) · [Git 差分](https://git-scm.com/docs/diff-options) · [GitHub merge group](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#merge_group) · [Bazel Skyframe](https://bazel.build/reference/skyframe) · [Mise 版本](https://mise.jdx.dev/dev-tools/versions.html) · [uv 锁](https://docs.astral.sh/uv/concepts/projects/sync/) · [uv 缓存](https://docs.astral.sh/uv/concepts/cache/) · [pgBackRest](https://pgbackrest.org/user-guide.html) · [ACM SIGSOFT](https://www2.sigsoft.org/EmpiricalStandards/docs/standards)。

## 3. Logic LEGO → Capability LEGO 与验收

以下为源码职责和消费者边界索引。具体候选与验收状态沿用原 Owner 证据。

| 源码职责 | Logic LEGO | Capability LEGO / 当前入口 | 验收消费者 |
| --- | --- | --- | --- |
| `services/host` | 身份引用、Work 与 revision/CAS、Space/Topic/因果消息、参与与订阅、Attention 双游标、快照/回执/历史恢复 | Host MCP、PG 事务和迁移、原生 replay、CJK 搜索、增量 attention | Agent 重入能恢复同一 Work 与因果边，同一请求可回放，弱或缺失证据保持未知 |
| `services/harness` | Run 合约、上下文编译、循环/选择、Provider 适配、Tool intent、收据和断点继续 | Rust harness-core/harness-pg、现有 Provider/外部 Harness 接口、实际 Runtime 连接、锁定 Python 比对环境 | 已知同一 Run 在响应丢失后恢复，已提交外部作用只消费一次，由领域判定结果 |
| `services/runtime` Linux | Workspace/源、幂等准入和 allocation、病态进程与恢复、输出保留、资源回收、发布 | Rust Runtime MCP、PG、systemd/cgroup、Git worktree、Artifact 与 runner readback | 原生进程/结束/取消/输出有同一 Attempt，调度被拒、缺失见证和可恢复状态可解释 |
| `services/runtime` Windows | Session/身份、Job Object 生命周期、Ready/ACK、PG 单写入链、Artifact 登记 | Rust PG 候选、Win32 Job Object/Launcher、Windows 原生测试 | 实际 Session 1、Job Object 排空、PG terminal/output、重复允许与响应丢失恢复 |
| `services/gateway` | 路由、目录投影、capability binding、transport、错误、重附、readiness | 现有 MCP Gateway、Rust rmcp/Tokio/reqwest 候选、AuthZEN 接口 | 同一客户端跨协议版本选到同一 Owner；未知、禁止、缺失和真实 owner 错误各自回传 |
| `platform/security` | principal、许可决策、策略修订、证据绑定、发布分级 | 现有 AuthZEN PDP 与 OPA/Rego、签名 attestation 验证、Owner 原生权限 | 真实业务授权上下文、正负样例，策略身份/源与实际消费回执一致 |
| `platform/network` | 出口/路由、节点/命名空间生命周期、漂移与未知、恢复 | 现有 systemd / Podman / WireGuard / sing-box / Tailscale、原生任务及只读观测 | 各真实节点和设备读出使用的出口，切换和恢复保留已有连通义务 |
| `platform/workstation` | 可执行工具供应、用户/服务上下文、锁与缓存生活周期、安装与回读 | mise、uv/Node/pnpm/Python、平台服务管理、已验证发行资产 | Linux 及 Windows 实际消费身份读取安装的二进制，按真实使用者验证缓存 |
| `extensions/chatgpt-skills-mcp` | 技能检索、精确绑定、版本和授权读取 | 当前 Skills MCP 兼容面、`.agents/skills` 与原生 Skill 格式 | 指定技能版本可重读，已安装的真实客户端取得对应字节 |
| `extensions/ordivon-control-plane` | 便携入口声明与组合分发 | 当前 Agent Plugin 配置、Gateway MCP、标准 Skill 装配 | 真实插件客户端只通过其已声明能力入口调用 |
| `catalogs/authorities` | 外部标准身份、版本、资格与当前性 | Authority Catalog CLI、Python/uv、schema 校验 | 下游用规范版本读回可追溯来源 |
| `catalogs/capabilities` | 能力发现、候选证据、直接消费者与替代决策 | 现有 Catalog/ELE、GitHub upstream、本地验证入口 | 匹配消费任务，供应链与兼容性资格由真实 Owner 产生 |
| `catalogs/knowledge`、`catalogs/data-products` | 方法/知识来源、数据产品血缘、许可和消费引用 | Git、现有 Composition 和 Data 验证、ODRL/有消费者的标准载体 | 维护者按版本追溯知识/数据到原始权威 |
| `packages/composition` | 定向 assume/guarantee、变更影响、证据读集、资格和替换 | 既有 Composition CLI、Git、Policy、Lean/有限模型/原生检查 | 原有调用者能消费精确证据，交叉边变化触发相关验证 |
| `packages/data` | 源身份、批量 Git 对象读取、数据切片、固定元数据与保留闭包 | 已合 Git 原生批处理和流式边界，PG/数据集载体 | SHA-1/SHA-256、大小/数量边界、旧新结果和相同对象多路径的差分 |
| `capabilities/artifact` | 证据与成果身份、标准封包、校验、可感知一致性和交付 | 当前 native validator、OpenXML、Playwright/浏览器、签名与 digest | 原始成果和最终可读/可编辑材料来源完整，可重验 |
| `capabilities/distribution` | 发布上下文、分发意图、通道交付和接收回执 | 原生发布/渠道与 Artifact 证据，现有结构检查 | 指定交付对象准确读回发布版以及可验证回执 |
| `capabilities/preservation` | 可达保留根、修复/恢复、独立备份和记录保全 | pgBackRest / Git / SQLite 原生备份，当前档案清单和恢复验证 | 从实际保留介质在独立位置恢复，引用、重放和校验一致 |
| `capabilities/media` | 源素材闭包、视听处理、时间线、测量和导出 | FFmpeg/ffprobe、Remotion、native loudness 和既有数值算子 | 实际导出、编辑性、字幕和可重放素材；算子对真实排序/窗口输出做差分 |
| `domains/game` | 产品合约、可玩规则、资源和编辑/导出证据 | 现有引擎及原生导出和自动化游戏验收 | 真实导出能运行、关键关卡/交互和输出可重复验证 |
| `domains/capital` | PIT 数据、研究情景、风险/目标、模拟撮合/执行和账本 | Qlib / MLflow / 已选风险模型 / Paper OMS 等候选，各接口由实际 Owner 资格决定 | 同一天真实 ETF paper 交割链、净值与账本可对账，来源和风险可解释 |
| `apps/web` | grant、effect 回执、恢复、视图投影、终态与浏览器交互 | TypeScript/pnpm、现有路由和 Playwright/browser tests | 操作者能追溯 grant/version/receipt，刷新后恢复，并区分展示状态与生产效果 |
| `apps/chaoxing-autosign` | 独立端侧应用的验证与退役资格 | 现有 `chaoxing:verify`、Draft #2017 提议 | 明确现存消费者及退役后果，保留联合验证至正式退役 |
| `profiles/research`、`studies`、外部 Research repo | 研究问题、实验设计、数据与证据溯源、论文和复现交付 | 真实 Research 仓、Work #32645、native 搜索/统计/实验与论文验证 | 论文或任务逐项消费可复核证据，实验冻结边界和作者面验证成立 |
| `tools/formal`、`tools/repo`、`.github` | 模型边界、SourceCut、验证选择/分片、证据失效、依赖更新和集成 | 原有 TLC/Lean/Kani、Git、mise、GitHub Actions、Renovate/Dependabot | 当前合并队列保持完整影响域，已验证效果可追溯到精确来源 |

### 跨域最小依赖

1. 调用者 → Gateway → 目标 Owner。Security 提供授权判断，Host 提供语义续作，运行事实由 Runtime 或 Harness 的对应接口返回。
2. Harness → Runtime / 外部 Provider → 同一尝试的效果回执 → Harness Run 与 Host Work 消费。Runtime 保管其执行证据，业务消费者完成验收。
3. Git → Owner 检查/Composition 定向影响 → GitHub merge group → 发布/已装载 → 业务消费者。
4. Artifact → 交付和 Preservation 通过已引用字节及其身份关联。历史 carrier 的数据清理要求明确保留根和独立读回。
5. Toolchain 是验证依赖，由根和 Owner 的 mise 配置解析。每个项目继续维护独立包锁和原生测试。

## 4. 执行顺序与完成条件

### P0 · 已确认切换和因果阻塞

| 工作包 | 复用与操作 | 交付关口 |
| --- | --- | --- |
| UV · 延续 #2304 | 主线所有实际 mise uv 声明改为 `latest`，去掉真实项目中的旧精确工具拒绝，吸收历史 PR 的有效意图并保护新主线测试 | 原生 latest 实际解析、两项目旧版本拒绝复现、候选锁定检查、原生架构/依赖门、原 PR SourceCut 读回 |
| WIN-PG · #32712 / #2469/#2471 | 复用旧有真实 Windows 原生测试与 PG 候选，优先同一 Admission→Session 1/Job Object→终态/取消排空→Artifact | 正常 MCP 入口及真实 Windows、同一 PG 中验证成功/取消/重启和读回。具体服务的切换以当前 release/恢复证据为准 |
| HOST-PG19 · #32704/#2818 | 复用已测优化构建、copy upgrade、pgBackRest 两点恢复和 exact replay，补消费和运维残差 | 应用 schema 与 PG 版本分别读回，现行独立恢复点正负用例和实际支持的消费者闭环 |
| GATEWAY/HARNESS Rust · #32664/#2801、Work@140 | 复用原生 Rust SDK 和已有 PG Journal，补实际 northbound 调用、Run 故障重附和安装版兼容 | 真实 Rust 跨层消费、不同工具错误和同一响应丢失义务、双发布期间的等价及切换读回 |

### P1 · 解耦、算法和测试

- 先用当前 Git delta 和真实读集定位定向依赖与循环，构建临时 DSM。只有同一业务不变量且具有同一自然 Owner 的重复职责才融合。依赖边以接口和调用证据为准。
- 延续 #32714 的 PG/历史数据原生比较以及 #32665 的数学算子工作。优先批量和顺序/稀疏实现，保留 multiplicity、比较边界、错误和恢复义务。对热点在同硬件、同输入和同输出范围报告延迟、内存、I/O 与偏斜下的退化，基线须可复现。
- 数据保留沿现有可达性与真正的备份链执行。度量即时可清理与容量压力，再做独立恢复/重放；旧事实保存在其适用 epoch。
- 用现有 Owner 原生语法/性质/差分/并发/故障测试，补实际入口不足的案例。模型与实现有独立结果，发布后消费者按其原生方式验证。根 CI 使用既有 GitHub merge group 及影响闭包，避免引入第二个调度体系。
- 其余依赖按 Owner 的现有更新机制推进。直接依赖约束采用已证明兼容的范围，解释需要精确版本的 ABI、外部资产摘要、发布或复现前提。锁文件用原生更新器生成，用 `--locked` 或等价命令验收。
- P1 优先用已有候选的源码加原生证据，合并前和当前主线及相关 PR 对照，沿原有分支推进。收益未成立的改写继续以对照样本记录。

### UV 首批执行合约（R2.1）

| 项 | 内容 |
| --- | --- |
| I | 精确源切片、现有 #2304 正常分支、所有当前 Git 跟踪的 mise 与项目元数据、明确解析的当前稳定 uv、既有项目锁 |
| O | 现有真实 mise 用户解析 `latest` 后得到可运行的 uv，项目锁结果和旧有原生验证义务维持 |
| S | 源码、已解析工具、uv 自有缓存、各项目已有锁字节、CI 和 PR 精确 commit 的独立证据 |
| pre | 旧 PR 状态/远端 HEAD、当前主线、供给与冲突范围可读取，使用隔离 Workspace |
| post | 两个旧拒绝点转为可运行，无锁文件变更，真实项目/根验证证据可定位，原 PR 读回 |
| inv | 缓存由 uv 自己管理。工具需求与锁的包版本各自保持独立。源/运行/交付证据保留作用域 |
| eff | 按现有 PR 正常 fast-forward 发布源码，native uv 正常读取/生成其既有缓存。主机的 updater 使用原运维责任 |
| c | 以实际 uv 版本、声明数、项目锁结果、CI 和失败归因为成本与进度证据 |
| epsilon | 锁文件字节差异零。工具解析满足 `latest`，结果依赖当次 mise 上游解析与安装。未跑的平台读取保留 UNKNOWN |
| prov | Host Work/Topic、Git、当前 uv 发行及 native job 回执，精确绑定观察时间 |
| unfold | 声明纳管 → 版本解析 → 项目锁可执行性 → Owner/root 门 → 原远端 PR → 合并及用户侧生效 |

## 5. 证据闭合

任务状态以 Host 原 Work CAS 维护。合并由真实 GitHub 状态证明，安装/装载由对应服务或 OS 读回，业务完成由真正的消费者判定。单个阶段失败记录最小反例、下一可执行动作及具体验收条件。跨层联结保留 Work、源码提交、Job/Attempt、Artifact 与业务证据各自的身份；证据为空、过期、不可达或超出采样范围时，保留未知。
