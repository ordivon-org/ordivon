# AUDIT_REPORT — Ordivon 2025–2026 现代范式源级审计

**基线** `ef17d6879d12faa61fff3bb762b0d500d73c9113`，2026-11-10；根 `/root/projects/ordivon`。本报告使用 `MODERN_CRITERIA.md` 的 M01–M12，涵盖全部 **21** 个自然 Owner 的模块结构、全部 **5,002** 跟踪路径的机械盘点和若干核心高风险文件的代码深读。**没有**完成全部文件的逐行语义审查，没有验证所有实际产品消费者，不能声称整仓架构严格符合/不符合某一个外部项目模板。

## 1. 结论摘要

**整体**：源码组织具备 21 个显式自然 Owner、对应已有 `mise` 验证、跨 Owner 源边界检查、Rust/Python/TypeScript/Godot/PG/形式化适配路径。结构并非从头建设的“乱堆”；真正的不足集中在 **当前性文字与可执行事实不一致、部分历史依赖与现行能力混淆、源码检查覆盖的边界限制，以及难以维护的个别超大单元**。

现代化标杆选择应是 Nx 的边界约束思想、DDD/Hexagonal 的语义责任与端口、Modular Monolith 的自主管理原则，而非把现有 Rust/Python 迁成 Nx/Turbo 工程，也非把已有 Owner 强行打散成更多微服务。Nix 可回收性、ADR、Journal/CAS 等概念只在其拥有严格的实际前提时才应用。

## 2. 各自然 Owner 逐模块判定

评级：**✓** 本轮有支持的源级符合；**△** 仅部分或有值得检查的缺口；**✗** 有可复现的反例；**?** 没有充分消费者/运行证据；**—** 该维度不适用。列号 M01–M12 与 `MODERN_CRITERIA.md` 精确对应。**不能把 ✓ 解读为部署验收**。

| Owner（根目录） | M01 | M02 | M03 | M04 | M05 | M06 | M07 | M08 | M09 | M10 | M11 | M12 | 证据焦点 / 范围 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | --- |
| Authority Catalog `catalogs/authorities` | △ | — | △ | ? | ? | △ | — | ✓ | ? | ✓ | △ | ? | `README.md`, `mise.toml`, registration JSON；当前安装权威待核 |
| Capability Catalog `catalogs/capabilities` | △ | — | △ | ? | — | △ | — | ✓ | △ | ✓ | **✗** | △ | `providers/distribution-v2.md:9–14` 仍称退役审批为当前；`packages/distribution.md:25–34` 混合历史来源与当前 |
| Composition `packages/composition` | △ | △ | △ | ? | ? | △ | ? | ✓ | ? | ✓ | △ | ? | `src/`, `formal/`, `policies/`, `mise.toml`；语义变化与工具壳分离，精化未全验证 |
| Control Plugin `extensions/ordivon-control-plane` | △ | ✓ | △ | — | — | ✓ | — | ✓ | ✓ | △ | ✓ | ? | 仅 `mcp.json`/`plugin.json`；真正薄插件，外部装载/运行未知 |
| Runtime `services/runtime` | △ | △ | △ | △ | △ | ✓ | △ | △ | △ | ✓ | △ | ? | `crates/.../pg_admission.rs`，`runtime/tests.rs` 10,788 行，`scripts/backup.py` 等历史 SQLite；PG/OS 生产效果另验 |
| Host `services/host` | △ | △ | △ | △ | ✓ | △ | △ | ✓ | ? | ✓ | △ | ? | `src`/Alembic/Journal；Host 连接实测 journalSchema 13（见下面运行事实），来源比 README 历史叙事高 |
| Harness `services/harness` | △ | △ | △ | △ | △ | ✓ | △ | △ | △ | ✓ | △ | ? | `src/ordivon_harness/ordivon/run_continuity.py` 3,186 行，`sqlite_store.py` 旧 API；研究 authority 不等于生产消费 |
| Gateway `services/gateway` | △ | △ | △ | ? | — | ✓ | △ | ✓ | △ | ✓ | △ | ? | `src/ordivon_gateway/upstream.py:166–186,264–319` 共用 HTTP 池但每次建 MCP Client session；代价未测，不认作 bug |
| Skills `extensions/chatgpt-skills-mcp` | △ | △ | △ | ? | ? | ✓ | ? | ✓ | ? | ✓ | △ | ? | `src/ordivon_skills` 等、版本和来源绑定需独立当前 Tool/Skill 观测 |
| Security `platform/security` | △ | △ | △ | ? | ? | △ | △ | ✓ | ? | ✓ | △ | ? | `contracts` / `labs` / OPA owner；两份同字节 tsconfig 在不同独立工程，不是自动重复缺陷 |
| Workstation `platform/workstation` | △ | △ | △ | △ | ? | ✓ | △ | △ | △ | ✓ | △ | ? | `inventory` / `providers` / `tofu` / `mise.toml`；本轮 CI 有 osquery 真实查询，但未核完整部署 |
| Network `platform/network` | △ | △ | △ | △ | — | △ | △ | ✓ | ? | ✓ | △ | ? | `consumers` / `capabilities` / `provider`；生产 VPN/出口不可从 SourceCut 推断 |
| Artifact `capabilities/artifact` | △ | △ | △ | △ | △ | △ | △ | △ | △ | ✓ | △ | ? | 425 文件，旧 `artifact-delivery` / `shadow-v2` 双世代需要按实际生效权威审计，不能裸删 |
| Distribution `capabilities/distribution` | △ | ✓ | △ | — | — | △ | △ | ✓ | △ | ✓ | ✓ | △ | `README.md:3–53` 已退役自造 EffectAuthority，Workstation 只读 `evidence/r7...json`；#1950 已占 21 个历史文件 |
| Media `capabilities/media` | △ | △ | △ | △ | ? | △ | △ | △ | ? | ✓ | △ | ? | 素材/项目/成品/证据，有 553 跟踪文件；大视频不等于冗余资产 |
| Preservation `capabilities/preservation` | △ | △ | △ | ? | ? | △ | △ | ✓ | ? | ✓ | △ | ? | 保存/恢复与历史 XML/BagIt，删减必须核权威归档和恢复义务 |
| Game `domains/game` | △ | △ | △ | △ | ? | ✓ | ? | ✓ | △ | ✓ | △ | ? | `examples/` Godot/Bevy + 第三方 Dialogue Manager，代码体积与第三方 licence 独立判断 |
| Capital `domains/capital` | △ | △ | △ | △ | ? | △ | △ | △ | △ | ✓ | △ | ? | `tools/legacy_replay` / `quickfixn_1_14_1` 锁文件重复，均是历史资格候选，不能自动删除 |
| Data `packages/data` | △ | ✓ | △ | △ | — | ✓ | — | ✓ | ? | ✓ | △ | ? | `src/ordivon_data` / `AGENTS.md` / `mise.toml` 存在，**根 Program 漏登记该自然 Owner** |
| Web `apps/web` | △ | △ | △ | ✓ | — | △ | ? | ✓ | ? | ✓ | △ | ? | `package.json` / `pnpm-workspace.yaml` + 薄 TypeScript 应用；实际网页后端可用性未知 |
| Chaoxing `apps/chaoxing-autosign` | △ | △ | △ | ? | △ | △ | △ | ✓ | ? | ✓ | △ | ? | `chaoxing_mvp/ledger.py` 含 SQLite，本域独立任务场景不等于 Runtime/Host 双写 |

**M01 重新判定**：21 个 Owner 在 manifest/README 中的领域命名是成立的正向证据，但仅凭声明与部分源码无法证明整个领域模型满足严格限界上下文或全部依赖倒置，因此统一列 △（部分符合），不能把结构表全 ✓ 等同完全合规。

**口径**：M03 多为 △ 而不是 ✓，是因为现有 `check_owner_boundaries.py:85–106` 按 `ACTIVE_EXTENSIONS` 和 `IGNORED_COMPONENTS` 扫活跃字面依赖而非完整动态跨语言依赖图。存在原生强制机制（已验证），但不能声称等价于 Nx 全语言包图约束。M10 ✓ 只指存在原生 Owner 验证入口且 repo:ci 已验证，不等于某个 Owner 的所有专项完整场景均在本轮执行。

## 3. 已证实或高价值问题清单（严重度优先）

| ID | 级别 | 精确文件与证据 | 违反准则及技术问题 | 建议动作 / 风险 / 本轮状态 |
| --- | --- | --- | --- | --- |
| A-01 | **高** | `tools/repo/owners.toml` 有 **21** 个 `[[owners]]`；`docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md:18–45` 声称 20 个并未列出 `packages/data` | M01/M06/M11：架构 Program 相比原生 Owner manifest 漏 Data，误导 Agent 的自然 Owner 分配 | 在现有 #2013 Program PR 修正数字与 Data Oxx 行；可一提交 revert；**确认缺陷，已在现有 PR #2013 增量提交 90ed1ce0 修补；待 GitHub CI/MERGED** |
| A-02 | **高** | `catalogs/capabilities/providers/distribution-v2.md:9–14` 的「Current capability standing」含「exact approval ingress exists」；`capabilities/distribution/README.md:37–48` 明确 EffectAuthority/approval producer 已退役 | M06/M11：当前性语义冲突，风险是 Agent 把历史权限入口当现役生产能力 | 使用本地自然 Catalog Owner 修正 Provider card 的当前与历史事实，不恢复原服务；**确认缺陷，PR #2023（2118686b）已提交；待 GitHub CI/MERGED** |
| A-03 | **中** | `catalogs/capabilities/packages/distribution.md:25–34` 介绍独立项目 `ordivon-distribution-v2@03ccc...` 为现有能力且写「exact approval ingress exists」；`packages/README.md` 将 READY_FOR_REAL_WORK 定义为能力调查阶段 | M11：历史资格与现役 Owner 混合。**READY_FOR_REAL_WORK 标签本身没有被证伪**（可使用 provider-native 交付），不应机械清零 | 仅重述历史 SourceCut 语义、保留宽泛工作资格和原生消费者边界；风险中；Phase4 |
| A-04 | **中** | `services/harness/src/ordivon_harness/ordivon/run_continuity.py` ~3,186 行；`runtime/pg_admission.rs` ~3,026 行；`tools/repo/check_architecture_docs.py` ~2,524 行 | M08/M12：大单元可变更复杂度线索，**目前不是已证实的边界违规** | 先按方法/状态/接口拆审，而非先拆文件；不新增测试；待 Owner 空闲与变更成本证据 |
| A-05 | **中** | `services/gateway/src/ordivon_gateway/upstream.py:166–186,264–319` 每个 Owner 用共享 HTTP pool，但新建 MCP SDK Client session 做每次 RPC | M02/M12：性能开销与跨请求状态设计有张力；不是简化为「每次重新创建 TCP pool」 | 先核实际调用场景和 SDK contract；**无时延对照不判失败、不改行为** |
| A-06 | **中** | `services/runtime/scripts/backup.py`、`restore.py`、`services/harness/src/.../sqlite_store.py` 等仍引用 SQLite；此前根仓库 dialect 审计观察 65 个多 Owner SQLite direct callsite、33 path，`NOT_CUT_OVER` | M05/M06：代码存在不能直接推出双写，但“全部 PG-only”也不成立 | 逐条分 LEGACY_READ、TEST_FIXTURE、ACTIVE_WRITE、UNKNOWN；只在明确无现实写入消费者时删旧 API |
| A-07 | **中** | `services/harness/evidence/browser-security` 中数对历史 JSON 完全相同；`domains/capital/tools/legacy_replay/.../packages.lock.json` 与 `quickfixn_1_14_1/.../packages.lock.json` 同字节 | M09：有重复存量；**内容相同不证明语义来源重复** | 必须先核研究引用/签名/复现义务及不同实验身份，之后才决定 consolidate/delete |
| A-08 | **中** | Distribution 30 文件；开放 <https://github.com/ordivon-org/ordivon/pull/1950> 覆盖 21 文件，另有 <https://github.com/ordivon-org/ordivon/pull/1940> 同类旧文档 | M12：若并行 Agent 再写这些源会形成无谓 merge/重复工作 | 复用既有 PR、不重做文件；#1950 最后查询 OPEN/mergeStateStatus=DIRTY（非已合并） |
| A-09 | **低** | `catalogs/capabilities/providers/*.md` 多处硬编码 `/root/projects/ordivon`，如 Distribution、Artifact、Runtime、Security | M08/M11：源定位与本机绝对路径混合，对非同路径仓库不可移植 | 优先改当前路径为相对 Git 路径，保留历史绝对位置作 frozen provenance；只清理本次确实误导的卡片 |
| A-11 | **低** | `apps/chaoxing-autosign/chaoxing_mvp/engine.py:4` 与 `ports.py:4` 两个未使用 `typing.Iterable`；原生 Ruff `F401` 提供源级反例 | M09/M12：无需保留未使用导入；不需要新抽象/测试 | 已在 Chaoxing 独立 PR #2025（95f6a49a）直接删掉，`ruff` exit0、现存 11 测试 PASS；不代表整个领域架构现代化完成 |
| A-10 | **审计边界** | `docs/architecture/CURRENT_ARCHITECTURE.md:1` 明示 Historical Snapshot；`services/harness/research/README.md` 是研究状态恢复根 | M09/M11：旧文件和大材料不能由文件年龄/无 import 就证明无活消费者 | 保留当前研究 Authority / Git 历史边界，按高影响消费者结论再定删除；非当前修补阻塞 |

**不存在充分证据的断言**：不能说全仓存在「必然循环依赖」「所有 SQLite 都是生产写者」「每条历史研究记录都是垃圾」「所有模块不符合 Clean Architecture」。上述均需具体动态/语言级读取证据，不能拿成熟项目名当结论。

## 4. 具体源码/运行检查与现代基线

- 精确 SourceCut：`git rev-parse HEAD` 为 `ef17d6879d12faa61fff3bb762b0d500d73c9113`；`INVENTORY.md` 收录全部 5,002 path 及 checksum/role。
- 现有边界机制：`tools/repo/check_owner_boundaries.py:16–27,85–106`、`tools/repo/dependency_contracts.toml`、`tools/repo/owners.toml`、`mise.toml`、`.github/workflows/ci.yml`。
- PyAST 机械解析已对被跟踪的 Python 文件巡检：本轮读取路径无 SyntaxError，**不等于代码业务正确**。
- 生产只读 Host `host.status`：观测到 `wire schemaVersion=3`、`authority.journalBackend=postgresql`、`authority.journalSchema=13`，不能把 README 历史 Schema 11 当目前生产真值。该 Host 响应不证明本地 Git HEAD 与运行安装 SHA 一致。
- Linux Runtime `runtime.describe`：实际节点 `linux-pg`，`schemaVersion=1`，local_linux `configured/available=true`，声明 `runtime_host_namespace_path_witness`，不证明每次 Job 外部语义成功。
- 既有 `mise run repo:ci` 在此前本次 SourceCut 的 Program 同源小改切片上退出 0，仓库机制检查和 **533 pytest passed**；严格说并非对现在审计产物的最后验收，最终重新执行验证详见 `BASELINE_AFTER_AUDIT.md`。
- Distribution 既有 `mise run verify` 退出码 0，证明静态源契约和 R7 fixture 当前有效；不证明 provider writes 成功。

## 5. 跨学科反证与误判案例

1. **数学/状态**：`ConsumerObserved=0` 不推出 `NoConsumer`，除非当前依赖图、存活根及来源读集观察完备。GC/模型检查的条件性定理不能直接作为任意生产删除许可。
2. **管理学**：如果为“改善 Owner 边界”而再创建 22nd Owner 或全局 Reviewer，就是让组织问题复制为第二套执行权威。
3. **Clean/Hexagonal**：核心有 PG import 并非自动失败；只有该模块属于独立 domain core，且依赖方向违背现有 contract 才是问题。模块化单体不是所有代码都必须分进 libs。
4. **Nx/Turbo**：TS import 限制和仓库全语言边界检查能力不同。无需引入 Nx；用当前 `dependency_contracts.toml` 和 Owner gate 维护已存在规则，不能以文档替代执行。
5. **Matt/ECC/Superpowers**：分别做 Standards、Spec、当前源码逆向和真实验证，不能用对 code smell 的好恶取代规范，也不能为用户已禁止的测试扩张增加新的例程。
6. **版本**：历史 Schema/PR/数据回执 != CURRENT。此报告只赋予 source-level 资格，当前安装与业务结果保持明确 UNKNOWN。

## 6. 与执行计划的连接

详见 `REFACTOR_PLAN.md`；优先修 A-01/A-02/A-03（三项已证实，不新增能力），A-04–A-07 按自然 Owner 避碰、在本轮留明确受限制的剩余问题；所有批次仅用已有原生校验和 Git 可回滚更改。Phase4 实际提交及 CI 差异以 `BASELINE_AFTER_AUDIT.md` 更新为准。
