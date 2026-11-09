# 2026-11-10 Ordivon 存量审计：已完成基线与剩余问题

**冻结基线**：`ef17d6879d12faa61fff3bb762b0d500d73c9113`；21 Owners + repo/studies。所有 5002 个当前跟踪路径均记录于 `INVENTORY.md`。这是完整机械清单，不是全部文件均已源码精化验证。

| 阶段 | 本批完成的事项 |
| --- | --- |
| Phase 0 | Git SourceCut、用户 Freeze、Owner Manifest、Nx/Turbo/Matt/ECC/Superpowers/R2.1 判据定稿 |
| Phase 1 | 5002 个文件路径/字节/sha12 和 Owner 分类；1460 Python AST 解析成功；21 Owner 实际目录与模块热点盘点 |
| Phase 2 | 12 条带路径/反例的源级问题、22 个 Owner/root 组的有界成熟度与风险报告；源码边界 checker 起点有效 |
| Phase 3 | 依赖任务 T01–T10、独立 Owner 与 PR 分工、现有验证与回滚约束 |
| Phase 4 | 本批仅修 Runtime 当前 Quickstart 与原仓安全报告 URL；Harness #2005、Distribution #2007、Workstation #2008 的物理删减在各自独立 PR |
| Phase 5 | 以本次 Git PR 的真实 diff/验证/合并状态作交付依据；本快照只用于历史比较，不替代现行当前 Owner 入口 |

## 本次原生验证的精确结果

- `python3 tools/repo/check_owner_boundaries.py`：PASS，报告 2320 active files、31 seams、38 refs。
- `python3 tools/repo/check_architecture_docs.py`：PASS，`architecture documentation drift check passed`。
- `cd services/runtime && python3 scripts/check_docs.py`：PASS，`documentation contract: valid`。
- `uv run --with pglast==8.6 python tools/repo/check_sql_dialects.py`：PASS；PostgreSQL 18.6 pglast 解析四个 SQL 载体，SQLite 3.54.1 in-memory 与 osquery 5.23.1 原生检查 PASS。其遗留观测为 65 处跨 Owner SQLite 调用/33 条路径，`NOT_CUT_OVER`。
- **环境诊断不属于代码失败**：第一次直接执行 `python3 tools/repo/check_sql_dialects.py` 因缺 `pglast` 导致全命令退出非零；按根 `mise.toml:64,81` 的原生 `uv --with pglast==8.6` 使用已存在的依赖约束后通过，没有添加测试或安装第二套平台工具。
- `git diff --check` / 受保护 PR 检查需在最终提交与 SourceCut 对齐后重新观察。

## 不增加平台复杂度

本批不创建运行服务、LEGO 注册表、测试套件、消费者 API 或新工作流。本目录的 6 份 `.md` 文件是用户明确要求的**一次性冻结审计输出**；未来可在 Git 历史中完整查到，不应被提升为与当前 Owner README/AGENTS/`owners.toml` 竞争的真值源。

## 真实验证与待决

- 起点 `python3 tools/repo/check_owner_boundaries.py`：`valid`（2320 active files，31 seams）。
- 本批修改需要读 `git diff --check`、`tools/repo/check_architecture_docs.py`、Runtime 现有 docs checker 的实际结果；未运行或环境障碍不能自动填 PASS。
- 相关已存在 #2005 的聚焦 15 项 Harness 测试 PASS；Harness 完整 Queue 最后 Wheel/Host-free PG 因未提供 `HARNESS_PG_TEST_DSN` 而未得到整体 PASS。
- #2006/#2007/#2008/#1937 和主线部署状态随时间变化；本文件写入不构成这些 PR 已合并、代码已安装或外部消费成功的证明。
- 未解决的主要职责：Harness SQLite→PG 的唯一状态权威、Runtime Windows/PG 源与安装、关键大模块的实际变更耦合、历史文件的动态/外部/回放消费者。
- 完成的定义：真实消费者能力不回退，当前 Owner 原生验收/必要安装读回通过，误导性当前文档/重复责任减少，且使用受保护 Git 合并。做不到这些的项保持精确 `UNKNOWN`。

## Space Handoff

当前 SourceCut: `ef17d6879d12faa61fff3bb762b0d500d73c9113`。本次变更：Runtime 当前入口/漏洞报告 URL、冻结文件和模块清单。自然 Owner：Runtime 文档/Repo 一次性审计输出；其他 Owner 独立 PR 按上文链接。待决：GitHub 受保护 CI/Merge Queue、安装验收，以及 H03/H04/H10 后续自然 Owner 处理。回滚：精确 Git revert，不触碰共享主检出与历史生产状态。
