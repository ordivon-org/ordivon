# REFACTOR_PLAN — Ordivon Phase3 逐项执行契约（存量 Only）

**SourceCut**：`ef17d6879d12faa61fff3bb762b0d500d73c9113`。**Goal**：在保持现有执行结果与权限边界不变的前提下，修复已证实的 Owner/Capability 当前性漂移和最小源码冗余，并产出六份可回滚的审计文件。**Stack**：Rust/Python/TypeScript/Markdown、Git、Mise、已有 pytest/ruff/CI、现有 GitHub Merge Queue。**Spec**：`AUDIT_SCOPE.md`、`MODERN_CRITERIA.md`、`AUDIT_REPORT.md`。

**全局硬约束**：用户明确禁止新功能、测试体系扩张、消费者线路及产品增量。Superpowers writing-plans 和 ECC brownfield/orch-refine 中“添加 failing tests”不是本次许可；只运行现有验证。改动采用 Matt Standards×Spec 两条独立审查轴。能通过成熟 Provider 或 Git 的事实直接替代，禁止添加二级抽象或自制验收系统。每个任务以一条可独立撤销的提交/PR 为界，不能先误改共享 main。

## DAG 与真实源文件

`T0 → T1 → T2 → T3 → T4 → T5`，其中 T2、T3 可在不同自然 Owner 无冲突情况下并行。若同一文件已在其他 PR 的 diff 中，直接对已有 PR 补修而不是再建竞争分支。当前 `#2013` 持有架构 Program，`#1950` 持有 21 个 Distribution 历史文件；因此两个任务必须绕开该重叠。

### T0 — 审计事实冻结（已完成）

**文件**：`tools/repo/owners.toml`、`AGENTS.md`、各 Owner `README.md`、`mise.toml`、`.github/workflows/ci.yml`。**消费**：所有后续任务通过 SourceCut/文件位置复用，非新的持久注册表。

- [x] `git fetch origin main && git rev-parse origin/main`，确认 ef17d6879d12...
- [x] `git ls-files -z` 全量 5,002 path + size/role/sha/schema 快照，输出 `INVENTORY.md`。
- [x] `tomllib.loads(... owners.toml)["owners"]` 证实 **21** 个 Owner，并在独立原生 source scan 中定位遗漏 Data。
- [x] 读取真实 `capabilities/distribution/README.md:37–53` 和当前 Catalog 描述，对比 Current/Retired；同时检查 #1950 和 #2013 当前 PR 文件集。
- [x] 形成 12 项有证据要求的成熟标准 `MODERN_CRITERIA.md` 和双轴问题清单 `AUDIT_REPORT.md`。

### T1 — 修 Catalog 当前能力语义：不恢复被退役的服务（高优先）

**Owner**：Capability Catalog，`catalogs/capabilities`。
**文件**：
- 修改：`catalogs/capabilities/providers/distribution-v2.md:3–14`（当前/历史身份）
- 修改：`catalogs/capabilities/packages/distribution.md:25–36`（历史资格≠活跃内置 admission）
- **不修改** `capabilities/distribution/README.md`（#1950 已占）、`capabilities/distribution/evidence/r7-*.json`（Workstation 使用）、`catalogs/capabilities/packages/INDEX.md` 的 `READY_FOR_REAL_WORK`（该标签在 `packages/README.md` 定义为广义启动能力而非生产服务已安装）。

**接口保持**：Capabilities 名/卡片/路径不变；只是把过期「现行审批入口 exists」改成「历史观察已发生、当前 Owner 为源 fixture/provider-native route，无运行 admission 服务」。修改不创造新抽象或新的权限流程。

- [ ] 读取该两张卡及 Owner README，给出单一“历史/现行”证据表。
- [ ] 将 Provider card 中 current approval/Temporal status 改为历史范围；将固定绝对路径改为相对仓库 Owner，仍保留 standalone SourceCut 历史身份。
- [ ] 将 Package card 的 standalone qualification 标为历史，不再给 Agent 暗示活跃原生审批；保留 provider-native real delivery 的任务能力。
- [ ] **执行现有验证**：`mise run capability-catalog:verify`，`git diff --check`，`git diff --name-status`。期望退出 0；没有新测试。
- [ ] 新建独立分支提交 `docs(catalog): distinguish retired distribution approval from native delivery`；推送 PR，验证受保护 GitHub 检查（否则只称 SOURCE）。

**反例**：若另一活跃组件确实通过 Distribution 自带审批服务写入，应给 MCP/脚本/部署文件而不是历史文字；这样的真实证明要求修订本任务，不可从“字符串不存在”推出生产关闭。**回滚**：`git revert <catalog-fix-commit>`。

### T2 — 修既有全仓 Program 的 Owner 漏登（高优先）

**自然权威** `tools/repo/owners.toml` **已登记 Data**；不得反向删 Data 代码迁就不准确的 Program。**文件**：`docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md`，且**在已有 Draft PR #2013 的对应分支上补改**；不得另建含相同文件的竞争 PR。

- [ ] 读取源 manifest 21 Owner；确认 `packages/data/AGENTS.md`、`README.md`、`mise.toml` 是真源。
- [ ] 在 Program「20 个自然 Owner」改为 **21**；不重排 O01–O20，末尾追加 **O21 Data — packages/data** 的职责/原生验证 `data:verify`；去除误导的 owner-count 陈述。
- [ ] 使用现有 `python3 tools/repo/check_architecture_docs.py`、`mise run repo:ci`、`git diff --check` 验证；不得添加专门的新断言。
- [ ] 提交到 **#2013 现有分支**，推动原有 GitHub CI/同行审阅；若 PR 基线变化导致冲突，复用原 PR 的现有源路径处理，不默默另开新源文件。

**回滚**：现有分支中对新增该行的单独 commit 可 `git revert`；未碰本地 main。**数学限制**：\(\text{OwnersManifest}=21\) 是当前 SourceCut 的有限计数，未来应从 manifest 获取，不能让另一份手写表产生比自然源更高的真值级别。

### T3 — 直接删除两项无用的代码依赖（低风险存量代码修补）

**Owner**：Chaoxing（与源模型/SQLite Ledger 完全分离），文件：
- `apps/chaoxing-autosign/chaoxing_mvp/engine.py:4` — 删除未使用的 `typing.Iterable`，不改其余代码；
- `apps/chaoxing-autosign/chaoxing_mvp/ports.py:4` — 同上。

原生 `ruff check --select F401,F841` 曾在这两行给出确定的 F401 反例。选择纯 import 减法，不改 `ActivityLedger`、状态机、真实签到流；不用增加新测试。

- [ ] 修复精确 import 仅保留实际使用的名字。
- [ ] `ruff check --select F401,F841 apps/chaoxing-autosign/chaoxing_mvp` → 期望 exit0；
- [ ] `mise run chaoxing:verify` 或现有 Owner 原生验证命令 → 期望 exit0；
- [ ] `git diff --check` 且只有两个原始文件出现差异；
- [ ] 独立 Chaoxing PR 提交，CI 按现有 gate 验证；不修改其他 Owner。
- [ ] 反证是否这些导入实际用于运行时动态 `__all__`/annotation API，若有直接保持原状。

**回滚**：单一 `git revert`；该项属于小而确凿的 Code Hygiene，不能宣传为架构核心已完成。

### T4 — 审计工件作为一次性 source-cut 附件提交（本轮要求）

**文件目录**：`docs/architecture/audits/2026-11-10/`，精确六份：
`AUDIT_SCOPE.md`, `MODERN_CRITERIA.md`, `INVENTORY.md`, `AUDIT_REPORT.md`, `REFACTOR_PLAN.md`, `BASELINE_AFTER_AUDIT.md`。这是用户指定工件，不建立新配置 schema、lint、Agent Service 或持久 Ledger。

- [ ] 逐文件目录树在初始 SourceCut 下完整枚举；角色字段必须声明机械启发式。
- [ ] 21 模块与 12 项 criteria 逐一有 PASS/PARTIAL/FAIL/UNKNOWN/N/A 及具体重要证据，严禁报“所有 5002 文件逐行审完”。
- [ ] 给每个高优先 issue 文件/行号/动作/风险，明确 #1950、#2013 的并行避碰。
- [ ] 现有 `git diff --check`、`python3 tools/repo/check_architecture_docs.py`、`mise run repo:retirement:verify` 和 `mise run repo:ci`；按实际退出码记录。
- [ ] 独立 docs-only PR 与两个 Owner 修复 PR 分离，交由现有 Merge Queue；没有编译性源修改，仍需真实 GitHub required checks。

### T5 — Phase5 固化与完整交付

**输出**：`BASELINE_AFTER_AUDIT.md`。记录 SourceCut、实际已修改文件、commit/PR、native verify、GitHub Required、peer verdict、尚未处理/未能证明的范围以及可逆性。不能写「改完=成功」；source-only, CI, MERGED, INSTALLED 和 CONSUMED 分级，不用历史消息充作生产验收。

- [ ] `git status --short`、`git diff --check`；最后一次检查时间和退出码。
- [ ] 对 T1–T3 相应独立 PR 的精确状态做 fresh `gh pr view`，禁止把队列中或 Draft 当 merged。
- [ ] 从已有 Whole-System Optimization Space 读取/发布 `STATUS / COMPLETED / EVIDENCE / BLOCKED / NEXT` handoff，同行没有回复即 `PEER_UNKNOWN`，不能伪造。
- [ ] 如果 #2013 或 #1950 尚未合并，在基线中明确待合并，不把其他 Agent 的工作重复拷入本审计 PR。
- [ ] 不创建额外的每周/每天审计任务；本次文件只作 source-cut 冻结材料，未来以 Git/Owner/Host Work 保持事实权威。
