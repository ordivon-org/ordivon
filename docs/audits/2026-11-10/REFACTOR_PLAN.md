# 存量重构任务图：执行与回滚

目标仅为整理、归并、修补已有责任。没有新功能、测试扩展、消费者线路或新 Owner 注册表。长期架构程序为 `docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md`；本文件是本批一次性任务实施证据。

## 依赖 DAG

`P0 SourceCut/真实消费者 → P1 有界问题与证伪 → P2 删除/复用/原地修补 → P3 现有 Owner 验证 → P4 PR/受保护 Git 主线集成 → P5 状态读回和旧 Carrier 退役`。

不能越过 P1 仅按文件名/代码量删除，也不因文档中预期动作而声称 P4/P5 已实现。

| Work | 前置 / 操作 / 验收 | 风险与回滚 |
| --- | --- | --- |
| T01 本批 | `services/runtime/docs/quickstart.md` 现行 clone 改为 `ordivon-org/ordivon.git` 并进入 `ordivon/services/runtime`；跑原生 docs checker | 真实 README/authority 入口已指向该 Quickstart；Git revert 可还原；历史 standalone 史不改 |
| T02 本批 | `services/runtime/SECURITY.md`、`services/runtime/.github/ISSUE_TEMPLATE/config.yml` 私密漏洞报告 URL 与根 `SECURITY.md` 对齐；跑已有 docs checker | 不创建报告通道；只替换旧个人 URL；SourceCut 可回滚 |
| T03 已分派 | #2006 原地收敛当前 Owner 全仓架构总纲，别创建第 N 份替代 SPEC | 数学前提要遵循 R2.1 Lean 的 old → new assumption；由该 Owner PR 集成 |
| T04 已分派 | #2007 Distribution 清理历史文件，保留 R5/R7 真实消费者 | 现有 n8n script、gitleaks path 证明保留边界；不重复分支 |
| T05 已分派 | #2008 Workstation 退役旧 Host v1 投影和其 root checker 强引用 | 检查 422 行新增临时 SPEC 的独立消费者，防止以清理之名增加文档维护 |
| T06 已分派 | #2005 Harness 复用 Browserless 同一 pre-effect Receipt 写入 | 15 项旧测试 PASS；完整队列结果只在 PG DSN 缺失前阶段通过，受保护 CI 决定合并 |
| T07 后续 | Harness SQLite 文件与 PG-only 实现之间的历史安装/测试/动态引用闭包 | 与 #1867 协调，避免以单个重复方法替代为全局通用 Store |
| T08 后续 | Runtime Cargo 旧 repo 元数据、Windows/PG/SQLite 事实 | #1937 触及 `Cargo.toml`，等现有 Owner PR，不能基于 Linux PG 独断 Windows |
| T09 后续 | 长文件如 `pg_admission.rs`、`run_continuity.py`、`tools/repo/check_architecture_docs.py` 的真实责任聚类与 deep-module 抽象 | 先用 DSM/接口/调用读回再拆，反对单纯按 LOC 决定重构 |
| T10 长期 | 在真实 PR 末报告**被删除的责任**、减少维护触点、保留消费者、唯一未解 UNKNOWN | Git/Host/Runtime/Owner 原生状态是验收，非本临时文件 |

## 一批的标准执行片段（Superpowers / Matt / ECC 思想）

精确 `SourceCut + Owner + file + consumer + falsifier` → 先执行已有的最小 native checker → 只编辑已列路径 → 读 `git diff --check` 与现有 Owner native verification 输出 → 原生 PR/merge queue → 向 Space handoff `state / completed / pending / evidence pointer / next`。此处的 method 不能代替授权，更不能要求新增其他测试体系。

每一批独立检查：①理论/A-G 是否正确②是否复用成熟方法③是否仍在修表面④是否因过保守阻止独立部分⑤是否破坏独立合法消费者⑥是否无声地增加了耦合或新注册表。

Git 回滚采用该批实际合并提交的 `git revert`；不要 `reset --hard` 共享主检出、操作其他 Agent 的未完成 Workspace 或删除生产数据库行。不得将 `OPEN`、`CI_PASS`、`MERGED`、`INSTALLED`、`CONSUMED` 混为一谈。
