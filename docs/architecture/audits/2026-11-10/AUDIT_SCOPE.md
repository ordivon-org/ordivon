# AUDIT_SCOPE — Ordivon 2026-11-10 存量现代化（冻结观察基线）

**SourceCut**：Git `origin/main = ef17d6879d12faa61fff3bb762b0d500d73c9113`（本地通过 `git fetch origin main` 验证）。生产检出路径 `/root/projects/ordivon` 的 `main=93780417c71600873a0847f02c17d094f2416082`，相对 `origin/main` **1 ahead / 140 behind**（历史观测，不宜用于新 PR）。当前审计独立 Workspace 为 `ws-gpt6-20261110-full-brownfield-phases-r1`。所有发现需带本次 SHA，后续需要重验证才能用于新日期或部署。

## 用户硬约束

只审计并整理存量代码/目录/文档/配置/接口、行为保持的内部重构、已知缺陷的最小修补。**不新增功能、新测试和测试框架、不创造消费者线路、不推产品增量、不新建平行治理/Registry/Agent**。所有修改在独立 Git Workspace 内完成，可通过 `git revert` 或独立 PR 回退；未经证据不做物理生产删改。

**阶段和退出定义**：Phase0 锁边界（本文件和 MODERN_CRITERIA）；Phase1 逐文件机械枚举及真实树；Phase2 按每 Owner/模块判定符合性（PASS/PARTIAL/FAIL/UNKNOWN）且给路径/问题/风险；Phase3 写具体任务顺序、命令、回滚方案；Phase4 执行至少一项确认可逆的现存修改并跑原生验证；Phase5 固化新基线和未完成原因。每阶段真实完成后继续下阶段，不设人为审查阻塞，但跨 Owner 高风险问题必须有相关事实。

## 当前自然 Owner 与源码范围

权威映射为 `tools/repo/owners.toml` 的 21 个 `[[owners]]`；真实源路径包括：

`catalogs/authorities`, `catalogs/capabilities`, `packages/composition`, `extensions/ordivon-control-plane`, `services/runtime`, `services/host`, `services/harness`, `services/gateway`, `extensions/chatgpt-skills-mcp`, `platform/security`, `platform/workstation`, `platform/network`, `capabilities/artifact`, `capabilities/distribution`, `capabilities/media`, `capabilities/preservation`, `domains/game`, `domains/capital`, `packages/data`, `apps/web`, `apps/chaoxing-autosign`。

**Computing 不是此 SourceCut 下独立的 `computing/` Owner**。计算、组合、形式化、研究的真实职责分别落在 `packages/composition`、`packages/data`、`tools/formal`、`studies/` 和各领域/Owner，不能因用户提到 Computing 就新增 Owner。非 Owner 源区域为 `docs`、`tools/repo`、`tools/formal`、`profiles`、`studies`、`.github`、`.agents` 等；需纳入清点但不能私自获得业务事实权威。

## 应尊重的现有运行边界

- Host owns Work/Task continuity、Actor、Space/Topic/Message、Journal/CAS、Schema/Alembic。
- Runtime owns Workspace/Job/Attempt/Runner、真实物理执行及恢复证据。
- Harness owns bounded Agent Run 的认知/工具/Provider 连续性；不能被误写为 Runtime Job 或 Host Task Owner。
- Gateway owns northbound routing/authorization mediation，不能把路由配置冒充服务可用性。
- Security、Network、Workstation、Skills、Artifact、Media、Capital 等各自存储/效果/身份/研究的本源独立。一个依赖说明可以形成调用边，不能成为另一个 Owner 的最终事实权威。

实际安装 SourceCut、PostgreSQL schema 版本、生产 Job/消息与 HTTP/GitHub 外部效果 **不由本次 Git 跟踪文件盘点证明**，除非另有精确生产观测证据。README 的 `schema_version` 仅是文档/契约版本，不等于 PG schema 版本。

## 原生审计与发布入口

`git ls-files -z`（全量机械枚举）、`git log -- <path>`（历史）、`git grep`/AST（潜在调用）、`tools/repo/owners.toml`（Owner）、`tools/repo/dependency_contracts.toml`、`tools/repo/check_owner_boundaries.py`、`mise.toml`、`.github/workflows/ci.yml`（现有规范检查）及 Owner-local `mise run <owner>:verify`。不能为本轮再编写新的 lint/CI、数据库或测试。

## 已存在并行工作，先避碰

`#2013` 为既有全仓 Program R3 Draft PR；`#1950` 对旧 Distribution 30 文件中的 21 个文件及其他 Owner 有待合并清理；`#1940` 等也涉及跨 Owner 历史文档。任何改动都要检查 `gh pr view --json files`，未合并 PR 的文件禁止重复改动。本次六份审计文档是用户指定的一次性工件，不能代替 #2013 的现有 Program 权威，也不变成永久维护数据库。

## 审计证据等级与限制

- **A**：本轮原生 Git/语言解析/Owner verification/CI 运行，带 SHA、命令和退出码。
- **B**：具体文件、行号和静态引用，能支持有边界的架构结论。
- **C**：README/历史证据/第三方基准，能指导追问但不能证明本机部署。
- **UNKNOWN**：尚无实际运行消费者/动态加载/安装证据，不偷换成 FAIL 或“可删”。

审计覆盖的含义必须区分：**枚举所有文件**、**自动规则扫描每个文件**、**人工深审一部分文件/模块**。不得声称 5,002 个文件全部经过完整逐行语义审计，除非确有逐行日志与覆盖证明。
