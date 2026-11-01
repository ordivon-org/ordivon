# Ordivon 高耦合拆解与工程门禁收敛计划 R1

日期：2026-11-02
状态：PROPOSED / SOURCE-AUDITED / NOT-IMPLEMENTED
基线：main 3c69e5b9f3f11e2199b196093ff07a505b7c67a7
范围：只定义分解、消费者切换、证据及验收工作包；不包含生产代码重写，不改变已安装或已部署的权威状态。

## 1. 观测与证据边界

- 真实 Git 树：4,772 个跟踪文件，20 个根条目，18 个登记代码 Owner。
- 根有效 GitHub Actions 工作流：2 个；其他 Owner 目录下发现 9 个嵌套工作流文件，其所在位置不能被 Monorepo GitHub Actions 自动发现；需要核对根 CI 是否等价覆盖。
- Python AST 静态图（排除 tests、scripts、experiments，仅 src）：175 个模块、344 条显式导入边、0 个被发现的强连通环；不声称动态导入、配置或跨语言边不存在。
- Harness Agent Loop：services/harness/src/ordivon_harness/ordivon/loop.py，2,621 行；OrdivonAgentLoop._run 为 2,164 行；15 条静态模块依赖。
- Harness Continuity Store：services/harness/src/ordivon_harness/ordivon/sqlite_run_store.py，3,921 行；SQLiteHarnessRunContinuityStore 91 个方法；12 条静态模块依赖。
- Runtime PG：services/runtime/crates/ordivon-runtime-core/src/pg_admission.rs，2,794 行；自约第 1175 行进入测试，不能把总行数视作生产主体大小。已有 pg_dispatch.rs、pg_readback.rs、runtime/pg_runtime.rs。
- Runtime Windows：services/runtime/crates/ordivon-runtime-core/src/runtime/windows.rs，2,874 行；自约第 1893 行进入测试。
- Host：services/host/src/ordivon_host_v2/social_store.py，1,307 行，28 个 SocialStore 方法；其真实 MCP 消费者为 social_work_mcp.py。
- Gateway：services/gateway/src/ordivon_gateway/service.py，1,164 行；capability_describe 单方法约 315 行；其 MCP 消费者为 mcp_server.py。
- Web：apps/web/src/store.ts，1,356 行；WebStore 由 app.ts、webauthn.ts、security-agent-verifier.ts、server.ts 消费。
- Composition：packages/composition/src/ordivon_composition/verification_obligation_r1.py，1,404 行；select_impacted_obligations 约 231 行、select_manifest_gate_impacts 约 148 行。
- 现有重要规则：tools/repo/owners.toml、tools/repo/dependency_contracts.toml、tools/repo/check_owner_boundaries.py、docs/architecture/STRUCTURE_R2.md。源路径字面量扫描不能替代跨语言真实导入图、运行时消费者或形式化精化证明。

口径：文件大小和导入数量只用于筛选。严重耦合的确认需要进一步的共同变化、无法独立测试、事务/发布边界穿透或失败传播证据。未知不是失败。

## 2. 拆解判断

将问题分成四种，不把一切复杂性等同为结构缺陷：

1. 编排集中：单方法包揽多个阶段和效果，适合在同一 Owner 内做纯函数/状态转移/效果协调分离。
2. 状态与持久化集中：单类实现多种状态事件与租约，必须先定义事务原子性和 replay/cancel 契约，再抽取无效果的判定与投影。
3. 部署/平台耦合：权限与平台物理约束不能直接迁移成抽象接口。必须保留现有平台运行证据与发布边界。
4. 有意组合枢纽：Gateway、Artifact 等需要连接多个公共能力，扇出大不自动构成反模式。优先证明非法的内核依赖、重复逻辑或接口不稳定。

采用 GOAL → REPRESENT → CONTRACT → ANALYZE → FALSIFY → SELECT → EVOLVE。禁止把源码文件、Owner、LEGO 视为同一个实体；不新增通用 Registry、万能总线或一套重复的任务状态系统。

## 3. P0 工作包（按依赖顺序）

### P0-0 生效的工程门禁（优先，可独立于拆解）

- 输入：root .github/workflows/ci.yml、runtime-release.yml，以及 9 个嵌套文件、根 mise 任务。
- READONLY：对照 9 个文件和根 CI 的真实任务，区分“有功能且已覆盖”“有功能但未覆盖”“已被废弃”。
- CHANGE：只将缺失的关键检查纳入真正生效的根工作流；已覆盖文件默认删除，避免镜像维护。核对 GitHub Branch Ruleset 和 merge_group 必过检查（Git 源文件不能证明远端 Ruleset 状态）。
- CHECK：从有效路径触发独立失败注入；确认 CodeQL/安全、Rust/TS/Python、按影响范围验证与发布验收各自的执行证据。Windows 原生执行及真实 PG 物理验收不得以 Ubuntu 源码测试替代。
- SHIP：独立 PR，记录失效工作流 → 现行 Job 的一一映射；不得因为根 CI 只有两个文件便臆断所有嵌套职责都已失效。

### P0-1 Harness Agent Loop 最小抽取（首个实际拆解试点）

- 锚点：OrdivonAgentLoop._run（loop.py:422-2585），嵌套本地函数包括 stop（745-812）、retain_tool_observation（814-948）、execute_tool_calls（950-1173）、evaluate_turn_progress（1175-1258）、restore_projected_cognition_overlay（1260-1360），以及主 while（1537-2585）。
- 真实消费者：standalone.py、domain_tools.py、运行 Demo 脚本和多组 Harness tests。
- 保留契约：公开 run()/resume()、AgentLoopResult、RunBudget、现有 run_store_port 与 ToolBridge；不转移实际 Provider/Tool 效果所有权。
- 子步骤：A. 用现有确定性 Run/恢复样本建立反例与回放；B. 将预算/停止/观察投影/执行意图选择等纯判定提炼为可独立测试的边界；C. 将副作用入口留在单一编排层，由成熟现有 Port 执行；D. 逐段重放、差分验证再删除旧路径。
- 不变量：同一 Provider Claim 在恢复/超时/取消后不得双重派发；Tool 效果与 receipt 的关联不丢失；needs_input 与终态不互相冒充；恢复重放不得重复外部效果；时间预算单调收缩。
- 拒绝条件：拆分后增加新的跨 Owner 依赖、双重状态写入、未证明的临时代理层或更多无消费者“抽象模块”。
- 验收：Harness 原生 queue/verify、确定性 replay、故障注入、同一 SourceCut 的差分输出和必要的 Formal source-refinement；必须给出受影响消费端的真实通过证据。

### P0-2 Harness Continuity Store 内核解耦

- 锚点：SQLiteHarnessRunContinuityStore（sqlite_run_store.py:120-3921，91 个方法）。
- 真正的公开边界：run_store_port.py；现有调用方包含 agent_run.py 与独立 CLI/研究路径；不得自创第二个 Run Truth。
- 先行分组：A. WorkingSet / caller ingress 投影与验证；B. Provider Claim/Dispatch/Outcome/Retry 状态转移；C. ToolStep/Event/Snapshot 读回和一致性；D. Lease/时间/持久化原子提交。
- 首选“同一事务拥有者内部的纯 helper”而非立刻拆成四个独立存储或数据库。Schema、事务所有权、锁语义与 replay 序列保持单一权威；数据库类型变更独立于此项，不能随拆分偷偷迁移。
- 不变量：CAS/lease fencing、event sequencing、合法状态转移、失败后读回、恢复幂等与快照一致。
- 验收：现有 Harness tests + 失败注入，验证历史库 fixture 与新实现读取/重放结果相同；消费者全部切至新内部 seam 后才能删除兼容代码。

### P0-3 Runtime PostgreSQL / Windows（受现有 Cutover Work 约束）

- 不与既有 work:ordivon:windows-pg-first-native-runtime-cutover-r1:20261026、work:ordivon:linux-runtime-pg-cutover-p0:20261031 或 release-currentness 工作包争夺同一写入路径。
- PG 现有 public admission → dispatch/readback → runtime/pg_runtime 分层必须先做消费者和事务分析；pg_admission.rs 含大量内嵌测试，不因文件长就立即切分。
- Windows 的 windows.rs 需按权限授权、环境合成、launcher/proc 生命周期、输入呈现、截止时间处理分组；测试和真实平台资格验证必须分开。
- 解耦前置条件：Windows PG 物理 readback/recovery/replay/conflicting writer 证据、Linux 对应资格验证，以及同一发布 SourceCut；当迁移未稳定时仅做只读依赖图及无效果纯 helper 提案。
- 不变量：单写入者、提交与可见性一致、重放不重复效果、取消不会越过 terminal fence、Windows token/session/elevation 语义不改变。
- 验收：Rust cargo fmt/clippy/test、PG disposable/physical qualification、Rust source/model 精化、Windows native installed consumer；源码 PASS 不作为节点成功声明。

### P0-4 跨 Owner 真实边界图

- 保留 tools/repo/owners.toml 和 dependency_contracts.toml 的原生机制；补充分语言导入/构建图和显式运行时消费者发现，不复制 Owner Authority。
- 第一个范围限定在 Harness / Runtime / Host / Gateway / Composition；分别测量公开 seam 消费、非法内核引用、源路径字面量漏洞、动态配置接口与运行时效果边。
- 注入至少一条非法 Python/TS/Rust 依赖，证明检查器确实拒绝；UNKNOWN 不能假装为“无边”。
- 产物仅为可重建增量图与证据，避免新增持久化的万能跨域 Registry。

## 4. P1 定向拆解候选

| Owner / 源点 | 消费者 / 风险 | 最小目标 | 反例与验证 |
|---|---|---|---|
| Harness sqlite_runtime_bridge.py（1,492 行） | agent_run、adaptive_edit_bridge、plugin_gateway_effect；混合工具降级、执行和恢复 | 抽出纯 lowering/结果归一化；保留同一执行与 reconcile Owner | lost-response、duplicate clientRequestId、terminal readback 差分 |
| Host social_store.py（1,307 行，28 方法） | social_work_mcp；PG 事务与 Social 图读写交织 | 同一数据库事务层下分出 Space/Topic/Message 的明确内部责任，保留一个公开服务入口 | relation target、cursor monotonic、重复 Post/Conflict、消息顺序 |
| Gateway service.py（1,164 行） | mcp_server；Capability describe/search/resolve 与执行路由 | 从 315 行的 capability_describe 中提取纯视图/校验；不要创建第二 Gateway 真值 | 既有路由响应、授权拒绝和上游失败语义等价 |
| Web store.ts（1,356 行） | app、webauthn、安全验证与 server | 先明确 Principal/Session、Credential、Grant/Effect 的原子边界；在同一存储 Owner 内分组 | WebAuthn、过期/撤销、Agent Effect 幂等与攻击测试 |
| Composition verification_obligation_r1.py（1,404 行） | effect_reconciliation + tests；Git 源变化/读集/证明作用域 | 区分纯影响分析、Git 读取/环境观察、CLI；保留公开 obligation API | SourceCut 漂移、假 PASS、manifest 变化、证明反例 |
| Artifact direct_python.py（606 行、广泛 import） | provider 属于有意组合入口 | 仅拆消费者证明存在重复/不稳定的验证 Hook；不按扇出自动拆分 | 产物 digest、VSA/语义验证、发布收据不变 |
| Media resolve_runner_menu.py（约 67 KB） | 需要调用图和 consumer before/after 评估 | 暂列候选，不因文本体积立项 | Owner-native 验证与真实菜单消费 |

P1 的选择准则：若模块具有单一稳定作用、方向正确、测试独立、改变不会扩散，则维持现状，不为了“高度模块化”增加层数。

## 5. P2 文档和协作治理

- 增加根级 CONTRIBUTING/SECURITY/License scope 指引、Issue/PR 轻量模板与现有 ADR 索引；避免复制子 Owner 贡献指南。
- 现有 STRUCTURE_R2.md 仍是候选迁移方向，不自动把 source owner 全部搬到 packages；先证明独立发布和消费价值。
- 统一的记录格式为 SourceCut、Goal、原消费者、pre/post/inv/eff、候选方案与删除方案、反例、真实执行与 currentness；只记录所需字段，不创建多套永续状态表。
- 文档要修复 STATUS 冲突，但文档不高于源码、物理执行和 Owner readback。

## 6. 迭代与验收纪律

每个工作包经过：READ→CONTRACT→COUNTEREXAMPLE→MINIMAL CHANGE→OWNER TEST→CONSUMER REPLAY→SHIP/RETIRE。

- 单轮活跃 P0 拆解保持 3–5 个以下，数据库切换、CI 修复与 Harness 结构拆解不要争用同一编辑区域。
- 每个拆解必须先证明“需要新模块”而非 DELETE、REUSE 或 COMPOSE 既有代码，优先成熟算法/库/工具。
- 变更需一项一项进行；先无行为变化的内部抽取，后影响行为的语义改进；不要把文件搬迁和数据库切换放在同一个 PR。
- 最低证明要求是 SOURCE、CONFIGURED、EXECUTED、CONSUMER、FORMAL（风险适用时）、CURRENTNESS；INSTALLED 仅在安装/部署声明中必需。每项明确 VERIFIED/OBSERVED/UNKNOWN，不以静态 AST 得出运行时结论。
- “拆解成功”不是文件越小越好，而是依赖方向更明确、关键不变量仍被证明、重复逻辑/兼容负担减少、真实消费者无需知道内部结构。

## 7. 已有 Work 的交叉排重

已读 Ordivon Host 2026-11-02 的 open Work 列表，Windows/Linux PostgreSQL Cutover、证明图、Cleanup、问题 LEGO 库与 Formal 任务均已有独立任务。当前文件为拆解总控候选，不重建这些 Work，不抢其 Owner-specific 实现。新代码任务必须先确认消费端和现有 Work 是否被认领。

## 8. 本轮状态

- SOURCE：基于固定 Git commit 的真实目录、AST 和消费者扫描，OBSERVED。
- CONFIGURED：根工作流/Owner 验证配置已静态读取，OBSERVED；Branch Ruleset 未证。
- INSTALLED：无新的安装或部署声明。
- EXECUTED：执行只读扫描任务，未运行完整 Owner CI。
- CONSUMER：标识了若干真实源消费者，尚未形成跨平台动态 readback。
- FORMAL：已找到现有 Formal 任务与证明载体，本轮未声称证明通过。
- CURRENTNESS：绑定 main@3c69e5b9；后续合并与迁移必须重新绑定 SourceCut。
