# Finance R2｜经济因果链与逻辑/能力 LEGO 的源码边界（2026-11-20）

> SourceCut: 2026-11-20 本地 origin/main `c343558e2ee1ba7c8194b62c23fa6e68be84098c`。本文件记录独立 Workspace 的候选重构，不代表已合并或已部署；以 Git/真实测试/PG/市场提供方各自的事实权威为准。

## 目标—现实—变化

**目标：** 在有限资金、明确入金、投资期限、现金需求及独立风险预算下，先证明数据的决策时可得性，再以可复验的实验评估现金、被动 ETF、研究型策略及其真实可实现净收益。Paper 是模拟账务，不是券商账户；真正市场、订单与资金效果只能由各自权威证实。

**现实：** `src/ordivon_capital/` 有 Markets、Research、Portfolio、Risk、Governance、Trading、Accounting 七个自然 Owner，`config/capital_domain_taxonomy.json` 精确登记 62 个可导入业务模块。当前 `config/execution_policy.json` 为 `NON_LIVE`。独立审计检测到 Portfolio/Risk 的 CLI 直接导入 Accounting PG，以及 Research→Portfolio、Trading→Accounting、Accounting→Markets/Trading 等跨域边。并非所有边都错误；Accounting 提交前的市场/交易资格复核具有信任边界价值，不可仅为消除循环而删除。

**本轮变化：** 将 Paper Contribution、Performance、Risk 的 PostgreSQL/文件/Market 读入与 CLI 解释从业务模块剥离至现有 `scripts/applications/`，使 Portfolio 和 Risk 的计算函数不再持有对应的 Accounting CLI 读入路径。原有模块的纯计算 API 与测试保留，真实 CLI 消费者同步迁移，不创建第八个业务 Owner、额外 ORM、OMS 或财务账本。

## 思想 LEGO：正向与逆向

| 思想 | 正向问题 | 最强逆向反证 |
| --- | --- | --- |
| 因果/PIT | 在决策时是否已经可见？ | 未来标签、发布日期、调整价、时区或训练窗口泄漏 |
| 统计与科学证伪 | 预测是否优于被动基线？ | 偶然选择、重复调参、非样本外验证和区间不匹配 |
| 优化与控制 | 在预算约束下何种配置可执行？ | 校准不充分、整数股/费用/滑点/现金/保证金不可行 |
| 风险与生存 | 何种损失无法承受？ | CVaR、相关性、流动性、融资和极端情景失效 |
| 会计守恒 | 经济效果如何进入现金、仓位与 NAV？ | 未成交记账、重复成交、跨账户混合、修正/撤销缺失 |
| 信息隐藏 | 谁拥有本类事实和最终责任？ | CLI/报告/研究模型变成第二真相源 |

## 逻辑 LEGO：不同的对象必须保持类型与语义分离

信息链：

```text
MarketObservation -> QualifiedVintage -> ResearchHypothesis
                  -> ForecastWithHorizon -> ValidatedEconomicEstimate
                  -> Mandate -> PortfolioTarget -> FeasibleOrderIntent
                  -> ExecutionEvent -> ReconciledFill -> LedgerEntry
                  -> PaperClose / CustodyTruth -> NAV -> EconomicEvaluation
```

预测值不是年化期望收益，目标权重不是订单，模拟撮合不是券商成交，测试 PG 回执不是现实资产。每一条晋级边须显式声明资产、价格口径、决策时间、可得时间、持有区间、现金流、账户、货币、资金与效果资格。任何缺失字段均保留 `UNKNOWN` 或拒绝晋级，而非默认成功或默认为零。

| 逻辑模块 | 输入 → 输出 | 前置条件/核心不变量 | 能力归属 |
| --- | --- | --- | --- |
| 事实资格 | Provider 捕获 → 时间资格数据 | 时区/交易日/来源、公司行动、availableAt、权利明确 | Markets + OpenBB/日历 |
| 研究资格 | 冻结数据/标签 → 假设/验证报告 | 训练/验证/测试隔离，label/score 列与 horizon 一致 | Research + Qlib/MLflow |
| 经济目标 | 人类目标/现金流/负债 → 经济合同 | 利率、入金、融资、风险偏好没有凭空默认值 | Portfolio |
| 组合优化 | 合格经济估计与约束 → 目标组合 | 预算、整数手、费用、可交易性必须可求解 | Portfolio + PyPortfolioOpt/Riskfolio |
| 风险测量 | 暴露/尾部场景 → 风险报告 | 风险度量与政策授权不同；未配置的预算不得自动放行 | Risk |
| 资格决策 | 风险报告/政策/委托 → Admission | 必须明确 NON_LIVE/模拟/真实效果边界 | Governance |
| 交易与对账 | 合格 Intent/原生事件 → Fill 事实 | account/instrument/order/trade/partial-fill/cancel/correction 不混淆 | Trading + NautilusTrader |
| 账务核对 | Fill/现金流/mark → Ledger/NAV | 现金守恒、幂等性、账户隔离、结算状态、PG 事务 | Accounting + PostgreSQL |
| 应用组合 | 各域受限 API → CLI/报告 | 仅编排，不产生新的业务事实或外部金融授权 | 现有 scripts/applications |

## 模块边界与第一批精确文件改造

| 操作 | 原路径或消费者 | 新位置/处理 |
| --- | --- | --- |
| SPLIT | `portfolio/paper_contribution_plan.py` 的参数解析、PG HEAD 读取、文件解析和 CLI | `scripts/applications/paper_contribution.py`；保留纯贡献计算和 Markdown 投影 |
| SPLIT | `portfolio/paper_close_performance.py` 的 CLI、PG readback、输入解析 | `scripts/applications/paper_performance.py`；保留现金流匹配及 Risk/NAV 核验 |
| SPLIT | `risk/paper_close_risk.py` 的 CLI、PG readback、文件解析 | `scripts/applications/paper_risk.py`；保留 Risk 核验和预算状态 |
| MIGRATE | 现有三组 CLI 真实测试、Finance Human Guide、Paper Risk Skill | 调用新的 script entry，未保留双实现兼容层 |
| KEEP | `accounting/postgres_paper_close.py` 及其 Markets/Trading 校验 | 事务提交边界的独立重复核验，禁止因目录规范化而移除 |
| KEEP | `trading/nautilus_paper_bridge.py` | 目前为模拟报告→PaperSession 限定 ACL；native event 不能直接升为券商成交 |
| NEXT | `research/pit_joint_forecast.py:solve_pit_payload` | 研究到组合求解的应用编排候选；需迁移真实消费者及 `--solve` CLI 后再删除 |
| NEXT | `accounting/paper_simulation_run.py` | 跨 Governance/Portfolio/PG 的应用组合候选；应先核准 score、horizon、账户和 PG 事务资格 |

此处分层刻意使用已经存在的 `scripts/` 作为组合入口；未引入新的 `ordivon_capital.application` 包，避免第八个 Owner 的分类歧义。业务域核心函数不反向调用脚本。

## 验收边界

1. 源码静态边界：三处被拆出的业务模块不再导入 `accounting.postgres_paper_close`；新 CLI 是唯一有该 PG readback 的展示入口；保留两个已有条件：Markets 数据来源资格、Accounting 持久化资格。模块分层测试保证此边不会回归。
2. 真实消费者：针对 `test_paper_contribution_plan.py`、`test_paper_close_performance.py`、`test_paper_close_risk.py`、`test_capital_domain_taxonomy.py` 运行真实 Python pytest，CLI 通过 `PYTHONPATH=src` 启动。独立 PostgreSQL 的测试在没有 `ORDIVON_CAPITAL_PAPER_PG_TEST_DSN` 时会跳过，不得当作已验证生产读写。
3. 合规范围：未进行任何实盘订单、账户/券商写入、生产 PG 操作；任何历史 Market EOD/Cboe 回填都不自动证明 PIT、分红复权或可交易收益。当前 NON_LIVE 约束继续有效。
4. 发布：工作树里编译/测试成功不意味着主线合并、已安装服务或当前真实经济消费者切换成功，必须由独立 PR/CI/SourceCut 与运行事实证明。

## 后续最高杠杆的工作顺序

**P0** 预测时间合同和可实现收益（score、label、availableAt、close→next-open、分红/复权）→ 账户/成交/账务守恒的真实负控；**P1** Research→Portfolio 的求解编排剥离，Accounting Paper 模拟跨域入口剥离，原生框架消费者与回执精化；**P2** 历史候选、无消费者脚本、重复注册/锁文件按真实消费者删减。不要先制造新框架或扩大模拟交易权限。

外部成熟实现参考：OpenBB V5 标准数据模型、Qlib 工作流/Recorder、MLflow tracking、PyPortfolioOpt 组合目标、Riskfolio 风险优化、NautilusTrader 原生交易引擎及 Ports-and-Adapters 体系。