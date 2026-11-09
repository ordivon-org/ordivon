# Ordivon 2026 存量架构：源级审计报告

日期：2026-11-10。SourceCut: `ef17d6879d12faa61fff3bb762b0d500d73c9113`。

## 总体结论与约束

当前文件索引共有 5002 项，21 个原生 Owner 加 1 组根/研究文件；1460 个 Python 源文件 AST 均成功解析。单纯机械扫描和高 LOC 不能推出“坏架构”或“已可删除”。本报告逐 Owner 做的是**主要真实目录、核心模块与已验证问题**的审计；没有把 5002 份文件逐个进行运行环境与人工语义验收。本阶段不添加功能、测试、消费者线路或新架构框架。

### 已实际成立的局部边界

- `tools/repo/owners.toml` 定义 21 个 Owner；`tools/repo/check_owner_boundaries.py` 执行后返回 `valid`：2320 active files、31 个 seam、38 个跨 Owner 源引用。这不是跨语言/动态加载的全覆盖证明。
- Python 公共包 AST 导入扫描观察到 `studies/experimental-episodes` 消费 `ordivon_composition`、研究脚本消费 `ordivon_data`；没有发现这些当前 Python 顶层公共包间双向导入，但 shell/Rust/TypeScript/MCP 未因此获得循环无误证明。
- `apps/web/tsconfig.json` 已有 `strict`、`noUncheckedIndexedAccess`、`exactOptionalPropertyTypes`，并使用 pnpm 独立锁文件；`services/runtime/Cargo.toml` 使用 Rust workspace；不能按 JS 专有 Turborepo 目录经验改造全仓。
- `packages/data/README.md` 明确只读 DCAT/ODPS projection，不拥有数据仓库或 Research 真值；该边界有 `src/ordivon_data` 实现与真实研究调用。
- `README.md` 清楚区分 Runtime/Host/Harness 三个状态源，但 Runtime 子目录 Quickstart/漏洞报告路径与现在的 Git 项目相矛盾（见 H01/H02）。

## 核心文件问题（按重要程度）

| ID / 优先级 | 当前文件与确切反例 | 理论判断 | 修补动作 / 风险 |
| --- | --- | --- | --- |
| H01 高 | `services/runtime/docs/quickstart.md` 要求 `git clone https://github.com/zycxfyh/ordivon-runtime.git` 再 `cd ordivon-runtime`，但根 `README.md` 的 Primary 仓库是 `ordivon-org/ordivon`；`services/runtime/README.md:56,134,191` 和 `docs/authority.md:44` 仍把 Quickstart 当实际入口 | C10 文档/实现/当前发行信息漂移，真实 Agent/Human 导航被误导 | **本次原地修补**为主仓 clone 和 `cd ordivon/services/runtime`；不改脚本本身，旧独立发行历史保留 Git |
| H02 高 | `services/runtime/SECURITY.md` 和 `services/runtime/.github/ISSUE_TEMPLATE/config.yml` 仍指向旧个人仓库 security/advisories/new；根 `SECURITY.md` 当前收件地址为 `ordivon-org/ordivon` | C05/C10：实际安全报告权威不一致。给出更多流程口号不解决错误入口 | **本批修补**为已经被根政策使用的官方当前仓 URL；无需新权限/机制 |
| H03 高 | `services/harness/src/ordivon_harness/sqlite_store.py` 与 `postgres_store.py` 同时存在，已有 CLI/AgentRun 明确 PG-only；此前 Wheel 制品实际包含旧 SQLite 源 | C05/C07：历史/当前存储二重实现及安装暴露。但 `append_event` 相同语句不是事务/系统身份相等的证明 | 同其他 Agent 的 #1867 PG 退役协同，先核查测试/回放/安装消费者后整体退役；不创造第二套通用 store |
| H04 高 | `services/runtime/Cargo.toml:13` 的 `repository` URL 仍指旧个人独立项目；`rusqlite` 仍是 workspace 依赖。Runtime Linux/Windows PG 当前事实不同 | C05/C10：源发布元数据和消费者迁移有不一致风险 | #1937 现有 PR 修改同一 Cargo 文件，本批不抢占；由 Runtime Owner 依据实际 crate、Windows installed 和 source refs 处理 |
| H05 中 | `platform/workstation/scripts/host_historical_projection.py` / `platform/workstation/evidence/host-v1-*` 历史投影与 `tools/repo/check_sql_dialects.py` 引用互相保活 | C07/C12：历史强引用造成当前代码链保留，不是只重命名文件 | #2008 删除原生历史代码/证据并修旧消费者；但新增加的 422 行 Workstation SPEC 应复审是否又制造闲置计划 |
| H06 中 | `capabilities/distribution/evidence/r1-r10` 有冗余历史证据，但 `platform/workstation/scripts/accept-n8n-distribution-adapter-smoke.sh:6` 真读取 R7；`.gitleaksignore:47,52` 真保留 R5 锚点 | C12：只能删除已证明无独立消费者的部分 | #2007 已有独立整理；R7/R5/adapter 必须按当前业务消费保留 |
| H07 中 | `docs/architecture/AGENT_OUTCOME_CONSTRAINT_EXECUTION_SPEC_R1.md:76` 将替换前提集合写成 candidate ⊆ existing；`tools/formal/RecursiveLegoRefinement.lean:63-100` 需要 old assumption → new assumption | C06 数学契约方向错误，强化前置条件会丢旧合法输入；旧文档还将已合并 PR 记为 OPEN | 退役旧计划/沿现有 R2.1 概念保持正确精化；由 #2006 现有单一 Owner 计划及相应自然 Owner 负责 |
| H08 中 | `services/harness/scripts/playwright_browserless_chatgpt_submit.py` 与 `playwright_browserless_human_resume.py` 中同一种 pre-effect Receipt 写入逻辑重复 | C04/C07：不是 domain 级独立职责，完全同 Owner 同 Schema | 上一批本 Agent #2005 已改成复用：+1/-30、15 项既有测试 PASS；Merge Queue 待完成，不能当当前 main |
| H09 中 | `domains/capital/tools/legacy_replay/lean_wave_b` 与 `tools/nautilus_rc4/run-m6-differential` 看似历史代码；`config/legacy_replay_surface_registry.json` 与 `test_legacy_replay_surface_isolation.py` 真实读这些路径 | C08/C12：历史回放与证据源，不能凭 legacy 名字删除全部 | **KEEP** 旧实验工具，除非自然 Capital Owner 能改成更小的同等历史消费者，不替换成无证据的新实现 |
| H10 中 | `services/runtime/crates/ordivon-runtime-core/src/runtime/tests.rs` 10788 行、`pg_admission.rs` 3026 行、`services/harness/src/ordivon_harness/ordivon/run_continuity.py` 3186 行、`tools/repo/check_architecture_docs.py` 2524 行 | C01/C04 变更风险和导航成本很高，但大文件不是拆分充分条件 | 先做真实输入/输出与 DSM 变更聚类，沿一个不变量/公开接口执行可回滚原地收敛，不增通用模块 |
| H11 中 | `apps/web/src/store.ts` 810 行、`apps/web/src/app.ts` 721 行，实际包含 Fastify/Session/Web 当前语义 | C09 应审“app 是否过厚”，但移出其自身 session 事实可能违背最小 owner | Web Owner 证明数据域后再考虑拆分；当前仅风险线索，未证明违规 |
| H12 低 | `domains/game/examples/room-encounter/addons/dialogue_manager/` 里数千行 Godot 第三方/插件代码 | C08 现成成熟 Godot 插件不是 Ordivon 自造核心；全仓行数不能作为自研重复负担 | 保留/固定版本，只以现有游戏消费者的实际引用决定删减 |

### F13 / 源级 P1：多 Owner SQLite 迁移不是已完成的统一 PG 切换

按仓库已有 `tools/repo/check_sql_dialects.py`，在明确加载所需的 `pglast==8.6` 后，当前 SourceCut 观察到 **65 处 SQLite API 调用，分布在 33 条源码路径**，检查器给出 `PostgreSQL durable-owner migration standing=NOT_CUT_OVER`；同时 **Host 自己的活动源码是 PostgreSQL-only PASS**。说明不同 Owner 的真实切换速度不同，不可将 Host PG 当前权威、Linux Runtime PG 安装或某个 Harness CLI 的 PG-only 表述推广成“全仓已经完成 PostgreSQL 统一切换”。建议自然 Owner 从具体调用与安装消费者出发逐项处理，不统一重构所有锁文件或自行删除已经实际服务历史回放的 SQLite 接口。本检查器使用 `uv run --with pglast==8.6 python tools/repo/check_sql_dialects.py` 完整 PASS，`NOT_CUT_OVER` 是其监测到的架构状态，不是该 checker 的失败。

## 分 Owner 核查矩阵

这里的等级仅指**本次源级检查的成熟范式符合性**，不是生产系统整体认证。`待证` 的结论不得强行转成不符合。

| Owner（跟踪文件数） | 当前源级等级 | 已看真实路径与主要行动 |
| --- | --- | --- |
| Harness (731) | 部分符合 | `src/ordivon_harness/ordivon/run_continuity.py`、`postgres_store.py`/`sqlite_store.py`；历史二重 Store |
| Media (553) | 部分符合 | `src/ordivon_studio/`、`processing/`、`research/`；保留生产/研究独立归属 |
| Runtime (452) | 不符合 C10；其他部分 | `Cargo.toml`、`docs/quickstart.md`、`SECURITY.md`、`crates/ordivon-runtime-core/` |
| Artifact (425) | 部分符合 | `artifact_core/`、`artifact_verification/stage.py`、`scripts/artifact_verify.py`；#1974/#1994 Standing 并行 |
| Capital (399) | 部分符合 | `src/ordivon_capital/` 七个语义模块、`tools/legacy_replay`；不删唯一回放 |
| Game (387) | 部分符合 | `src/`、`examples/room-encounter/addons/`、`formal/`；区分平台插件 |
| Authorities (376) | 待证整体 | `records/`、`observations/`、`scripts/authority_catalog.py`，单次 git 跟踪不等于权威当前 |
| Workstation (265) | 部分符合 | `systemd/`、`postgresql/`、Host v1 历史投影见 #2008 |
| Network (236) | 部分符合 | `config/`、`consumers/`、`systemd/`，需要真实网络读回 |
| Security (162) | 部分符合 | `contracts/`、`policies/`、`formal/`，当前安装策略另需证明 |
| Host (117) | 部分符合 | `src/ordivon_host_v2/`、`migrations/versions/0013_unicode_substring_gin.py` |
| Gateway (107) | 部分符合 | `src/ordivon_gateway/mcp_server.py`、`owner_protocol.py`，RPC 当前安装时间界限另定 |
| Composition (86) | 部分符合 | `src/ordivon_composition/`、`formal/Lego21OwnerBoundary.tla` |
| Capabilities (77) | 待证整体 | `catalogs/capabilities/ele/studies.py`、`routing/`；另一 Agent 独立审计 |
| Preservation (46) | 部分符合 | `scripts/verify_source.py`、`artifacts/creative-preservation/`，恢复证据独立 |
| Skills (45) | 部分符合 | `extensions/chatgpt-skills-mcp/src/ordivon_skills/`；工具暴露不授予业务真值 |
| Web (35) | 部分符合 | `src/app.ts`、`src/store.ts`、`tsconfig.json` |
| Distribution (30) | 部分符合 | `scripts/test-structure.sh`、`evidence/`，见 #2007 |
| Data (19) | 部分符合 | `src/ordivon_data/`、`README.md`，只读跨 Owner 接口成立 |
| Chaoxing (11) | 待证 | `chaoxing_mvp/engine.py`，尚未检验真实外部登录效果 |
| Control Plugin (2) | 待证 | `extensions/ordivon-control-plane/`，只见轻声明不冒充已安装 |
| Root/studies (441) | 部分符合 | `tools/repo/check_owner_boundaries.py` 真实 PASS；`check_architecture_docs.py` 仍是大而耦合的机械审计热点 |

**审计停止线**：5002/5002 已追踪并建索引；跨 Owner 动态引用、全部 TS/Rust/GDScript 程序行为、每条生产部署与每个文件独立语义证明尚未完成。对这些范围只能报告具体 UNKNOWN，不报告“全部现代化符合”。
