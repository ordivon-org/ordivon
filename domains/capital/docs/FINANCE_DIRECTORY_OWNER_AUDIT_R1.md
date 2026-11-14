# Ordivon Finance 目录与 Owner 审计 R1（2026-11-07 历史快照；当前变更见下）

## 2026-11-14 Finance R3 Paper 收盘日历 Consumer 扩展

严格收盘时间之真实消费者图：
Markets exchange_calendars XNYS → Markets etf_eod_snapshot
(来源/权利/PIT声明与 EOD 收盘日校验)
→ Accounting PostgresPaperClose (重复同一日期事实、不可伪造类形状)
→ Risk paper_close_risk (相同快照与已提交日结账一致)
→ Portfolio paper_close_performance (净值/现金流匹配报告)。

此图不把 issuer source / historical PIT / adjusted total return
视为已认证。PostgresPaperClose 对纯历史 CALLER_SUPPLIED_MARKS
依然保留模拟效果但不产生市场来源证明；
正式终端前不实施真实交易授权。反证测试以节假日、
2025-11-28 提前收盘，以及 2026-04-02 夏令时误报为样本。
测试的独立 PG 是本轮新建的 127.0.0.1:55581 数据库，
数据库目录已在服务退出后删除，未动生产 PostgreSQL。
另增加完整一次 Markets → PostgresPaperClose → 本地 PG
read_committed_paper_close → Risk review_paper_close_risk →
Portfolio summarize_paper_period 真实消费者测试。
合成一份 SPY 买入和两日日结：1000000 USD cents 初始
账户，900000 保护金，最后 1000100 cents NAV，扣除
测试费用后期间增量 100 cents。它不是现实交易或真实报价。
测试要求 PG 物理 data_directory + 连接身份完全符合
caller-bound disposable 测试集群；未提供独立 sandbox
环境时自动跳过，不接触生产 PG。
同时旧核心导入第一次真正需要市场日历才加载 pandas 和
exchange_calendars，避免普通 PG imports 被研究库拖慢。
独立 CPython 3.15 进程一次性测量导入
ordivon_capital.accounting.postgres_paper_close：
改前 652.8 ms / 131576 KiB peak RSS，
改后 98.0 ms / 39780 KiB；无需市场日历的普通
Accounting 调用不再预加载 pandas/numpy。
这种单次进程峰值不能代表稳定的生产尾延迟、长期内存泄漏
或并发压力，正式性能测试仍需消费实际 Runtime 预算。
两类证据来自具体 native 测试和内存/启动延迟观测，
不是对未来负载、历史市场权利或 alpha 的证明。

## 2026-11-14 Markets 日期资格与真实 Research 消费者修补

本节是新证据，不重算下方 2026-11-07 历史快照的静态目录数量；
它不创建 Owner Agent、第二份市场时钟平台或新的投资引擎。

- External producer Cboe/OpenBB 的历史日线可能含虚假 XNYS
  2025-05-26 交易日；Windows 私有历史 SPY/QQQ/IWM 原始捕获
  SHA 与原 R3 实验源清单相同。对应真实消费者分别为
  adoption/r3_native/etf_qlib_consumer.py (Qlib TimeAdjuster/label)
  和 adoption/r3_native/riskfolio/etf_riskfolio_native.py
  (历史收益估计和 CVaR/方差)。
- Markets 自然 Owner 新增只读、有界的
  src/ordivon_capital/markets/equity_session_calendar.py，直接组合
  upstream exchange_calendars 4.13.2 XNYS，不自建节假日规则或时钟数据库。
  消费者必须在读取原始数据后、构造标签和风险收益前进行校验。
- Consumer graph: original publisher/byte receipt → Markets 日期轴
  → Qlib/TimeAdjuster 或 Riskfolio → Portfolio 只读模拟。
  日期形态正确只是一条必要条件，不产生额外 PIT、复权、
  外部授权或 Paper PG 财务能力。
- 当前实证：同版本五种 Qlib 持仓口径，原始 962 行 vs
  删除仅一个假交易日后的 961 行，模型/Portfolio 输出均相同，
  数据集摘要却不同；Riskfolio last-252-day 权重亦相同。
  另一个更早 Qlib 源码版本的 H1 预测曾改变，
  两者不能混成单个受控实验。
- 工程验收：同一自然 Owner 的 Source moduleMap / census
  同步登记；test_market_xnys_source_session_calendar.py
  覆盖假节假日、缺失及时间顺序等负控，默认 Capital CI 消费。
  真 Windows native 原始数据拒绝/校正后通过需与原生 SourceCut
  和正式 GitHub CI 分开确认。

## 2026-11-10 存量减法重审（Git 主线 ef17d6879d12faa61fff3bb762b0d500d73c9113）

此前 R1 的目录/行数与历史工具 KEEP 结论只代表 2026-11-07 SourceCut，不再是当前文件基线。全仓 5,002 文件结构清单及跨 Owner 评估在 `docs/architecture/audits/2026-11-10-brownfield/`；Finance 原始本轮基线为 399 文件。自然 Owner 七类仍不变。

本次证据：当前 `src/ordivon_capital/`、根 `mise.toml` 和实际 CLI 不直接导入 `tools/legacy_replay/` 或 `tools/tigerbeetle_0_17_9/`；`tests/test_legacy_replay_surface_isolation.py` 主要要求这些已隔离历史文件仍存在，`config/legacy_replay_surface_registry.json` 为同一历史路径登记。于是当前工作树同时退役这 21 份旧工具、1 份依赖 LEAN 回放的 Nautilus M6 旧入口、1 份存在性测试与 1 份历史注册表，旧代码通过 Git revision 可复现；不存在当前实盘交易或 PostgreSQL 状态的迁移。仍保留 `wave_b/fixtures/wave_a_target_portfolio.json` 的唯一已冻结回归身份和 `tests/test_wave_b_contract.py` 的现有静态合同验证。

当前会计实现为 `src/ordivon_capital/accounting/postgres_ledger.py`、`postgres_paper_close.py`；旧 SQLite 历史比较不得作为当前源码所有者事实。Nautilus rc4 / QuickFIX / JSONSchema 等其他独立差分候选暂未因本次删除决定被连带改变；源级直接引用和业务实际消费仍需分别审计。已消除不被当前入口引用的旧 `OKX_DEMO_EXTERNAL_EXECUTION_R1.md`，其历史版本保存在 Git。

## 2026-11-10 P0 补完：实际消费者状态及减法（SourceCut 3ad65a19003545878192d45a057c10f5a9e57ea1）

本次更新现有 Finance Owner 审计，不另建总控图或状态数据库。当前 SourceCut 是补丁前的 GitHub 主线；本表是源码、测试和隔离 PG 事实，不是生产安装或券商认证。

| 消费者线段 | 当前确切入口 / 验收 | 状态及边界 |
| --- | --- | --- |
| Mandate → Portfolio | portfolio/strategic_contribution.py、run-strategic-contribution-brief；Composition test_finance_contractual_execution_consumer.py | SOURCE_CONSUMED：给定现金、储备和权重可只读分配；真实目标/风险预算仍 UNKNOWN，配置 standing=UNSET |
| Markets → Research | markets/etf_eod_snapshot.py、research/pit_joint_forecast.py；test_pit_etf_eod_composition.py | TEST_CONSUMED：PIT 时间边界可复测，第三方来源真实性未认证 |
| Research → Portfolio | pit_joint_forecast.solve_pit_payload → multistage_policy.solve_multistage；test_pit_joint_forecast.py | SOURCE_CONSUMED / RESEARCH_ONLY，不形成实际交易订单 |
| Research → independent protocol | scripts/run-finance-lego、research/experiment_protocol.py；Composition test_finance_research_frozen_consumer.py | SOURCE_CONSUMED；前瞻经济有效性 UNKNOWN，不能产生 Broker 权限 |
| Portfolio → Risk → Governance | portfolio/portfolio_counterfactuals.py、risk/portfolio_risk.py、governance/policy_decision.py | SOURCE_CONSUMED；未登记预算不能产生风险授权 |
| Trading → external provider | trading/postgres_demo_intent.py、okx_demo_execution.py；test_postgres_demo_intent.py | PREPARED_NOT_ADMITTED；Demo/Live 写入均 NOT_ADMITTED，也不等于 ETF Paper |
| Markets + Paper fill → Accounting → Risk → Portfolio | accounting/postgres_paper_close.py → read_committed_paper_close → risk/paper_close_risk.py → portfolio/paper_close_performance.py | PG_TEST_CONSUMED：隔离 PG 18.6 收盘、重放、摘要、现金账本和绩效回读；外部市场真实来源未认证 |
| Performance → 再决策 | portfolio/paper_close_performance.py 有经济结果，无直接持续资产再配置消费者 | NOT_CONNECTED；报告存在不等于自动反馈闭环 |

Composition T01/T02 有源级消费者；T03/T04 为按需依赖，不能冒充已完成经济消费者；T05 是本次真实减法；T06 仅证明列出的 Paper PG 子链，不包括 Mandate 至券商的完整投资行为；T07 由 GitHub PR/CI 独立判定。

本批 RETIRE：scripts/run-crypto-public-shadow-r1 没有 CLI、服务或真实测试执行调用者。唯一当前代码引用来自 test_candidate_tool_surface_isolation.py 的文件存在/文本否定检查；全仓 brownfield INVENTORY.md 是以前 SourceCut 的静态目录快照。保留仍被引用的 R2 runner 和 R3 resilience runner，删除 R1 的虚假保留测试。历史可从 Git 恢复。

Paper 证据界限：新凭证将前驱完整回执的 SHA-256 绑定到本次回执，最新收盘与 ordivon_capital.accounts 的现金、应付、应收值对账；无前驱回执摘要的旧凭证仍仅有较弱的转换验证，不声称等效历史抗篡改性。单一数据库内无密钥摘要不防止特权攻击者协调修改多个字段。外部审计锚定和券商实盘核对不在本批范围。

**R1 以下表格与 KEEP 条目仅为原始历史观察**，不表示本轮继续保留已删除的旧工具。原生验证结果与合并状态见同批 Git PR 及全仓 `BASELINE_AFTER_AUDIT.md`，没有写成实盘/真实 Provider 认证。


审计基线：GitHub main `32f07fb387df8b20e1cb510a54fe4934064e0c08`（2026-11-07）。范围：`domains/capital/` 和 Finance Skills。这是静态源码及消费者审计，不是运行中生产服务、真实市场价格、券商清算或账户资产的认证。

## 最终目标与演化原则

Finance 是 Capital 内的智能投资研究和管理程序，不是第二个 Finance 包、交易引擎、Agent 平台或数据库。终点是：使用决策时实际可获得的信息，明确每月 1r 入金、经济效用、负债和融资合同，比较现金、被动 ETF、组合及借贷，产出可复现、可独立证伪的经济结论；若证据不足则报告 UNKNOWN/INSUFFICIENT_EVIDENCE。

执行顺序：DELETE 无消费者 → REUSE 现有自然 Owner → COMPOSE 已验证 LEGO → 最后才新开发。使用 PyPA 标准 `src/` 结构；按照 Martin Fowler Strangler Fig 原则逐一迁移消费者，不以目录美观为目的新建七个微服务、第二优化器或兼容壳。

## 实际源码：七个自然 Owner

本次读取到 Capital 387 个文件（不含虚拟环境和 Python 缓存），七个业务 Owner 共 63 个 Python 文件；另有根包 `__init__.py`。下表行数是静态近似值。

| Owner | 文件 / 行数 | 高聚合职责 |
|---|---:|---|
| `markets/` | 12 / 2,304 | ETF 日终/历史价格、公共市场流、可观察行情、来源和可用时点 |
| `research/` | 13 / 3,480 | PIT 联合收益分布、概率评分、实验冻结、独立经济重放和证据 |
| `portfolio/` | 9 / 2,637 | 定期入金、被动基准、CRRA 情景优化、Paper 情景及收益核算投影 |
| `risk/` | 9 / 1,421 | 尾部风险、依赖、暴露、券商报告的保证金和声明式清算 |
| `governance/` | 2 / 609 | 执行准入和政策判断，不能代替交易所回执 |
| `trading/` | 11 / 2,167 | 订单意图、私有账户现实、Demo 接口、FIX 投影与对账 |
| `accounting/` | 7 / 1,829 | PostgreSQL 账本、预留、模拟账户结算；不是另一份真实托管账 |

AST 显式跨 Owner 导入统计：Accounting→Markets(1)/Trading(1)；Portfolio→Accounting(1)/Governance(1)/Markets(2)/Risk(1)；Research→Portfolio(1)/Risk(4)；Risk→Accounting(1)/Governance(1)/Markets(1)。未见显式跨 Owner 循环导入，但该结果不能证明没有运行时耦合。

**结构决策：保留现有七个 Owner 和单一 `ordivon_capital` 包。** `research/pit_joint_forecast.py`（712 行）、`portfolio/multistage_policy.py`（676 行）应优先审查内部职责；没有真正独立的消费者与生命周期证据，就不为了减少行数机械拆文件。

## 顶层目录逐一审核

| 路径（文件数） | 用途 | 审计结论 |
|---|---|---|
| `src/`（64） | 七个业务 Owner 及根包 | KEEP，按真实消费者改进 |
| `config/`（28） | Owner census、政策、市场/执行配置 | KEEP；配置并非已部署状态 |
| `contracts/`（12） | 语义合同及历史 v1 回放约定 | KEEP 有消费者的合同，优先 v2 |
| `schema/`（3） | 数据格式定义 | KEEP 有消费者的 schema |
| `scripts/`（52） | 运行、研究、验证入口 | REUSE，避免重建 Finance CLI 平台 |
| `tests/`（97） | 源码验证、差分及恢复测试 | KEEP 有真实消费者的证据 |
| `formal/`（15） | Z3/Lean 等数学与精化证据 | KEEP 现金守恒、偿付、非前视核心性质 |
| `docs/`（原 19） | 人类使用、架构及历史文件 | CONSOLIDATE，删除无当前消费者的 Wave-A M1 指南 |
| `planning/`（1） | CA01–CA10 LEGO source contract | KEEP，不另建 LEGO registry |
| `examples/`（5） | 运行样例输入 | KEEP，作为 Human/Agent 验收入口 |
| `fixtures/`（4） | 固定测试数据 | KEEP 被消费的条目 |
| `evidence/`（21） | 验证与来源证据 | KEEP；历史 PASS 不能当成当前生产认证 |
| `artifacts/`（1） | 零字节 `.gitkeep` 占位 | KEEP，`.gitignore` 仍明确消费该目录约定 |
| `data-products/`（4） | Crypto Public Shadow 规范和验收 | KEEP 当前消费，不当成 ETF 原始数据 |
| `infra/`（2） | 可选基础设施、系统服务文件 | KEEP 必需消费者，不推断部署完成 |
| `destroyer/`（1） | false-green 回归语料 | KEEP 直到验证消费者退役 |
| `tools/`（50） | LEAN、Nautilus、QuickFIX、OPA 等独立候选验证 | ISOLATE，不当成默认生产引擎 |
| `wave_b/`（1） | 冻结 Wave-B 目标组合 | KEEP，旧 Runner 和测试仍消费 |

## 删除及不删除的依据

1. **DELETE `docs/WAVE_A_M1.md`**：它描述已经退休的 GLEIF/MLflow/equal-weight 构建路径；当前 Capital/Finance 测试、配置、代码和 Skill 没有对这个文档路径的直接引用。源代码之外的历史归档不由本次删除动作处理。
2. **KEEP `wave_b/fixtures/wave_a_target_portfolio.json`**：`tests/test_wave_b_contract.py`、Wave-B 回放工具和 `config/legacy_replay_surface_registry.json` 有真实引用。
3. **DELETE (Accounting SQLite 历史实现)**：移除旧 sqlite_ledger.py、旧 SQLite 专项测试、历史 R0-R5 runner 与重启 smoke；原 36 个两操作情景使用真实 PostgreSQL 及独立账务预期核验，不迁移旧行、不保留兼容后端。
4. **KEEP** 两个 SHA-256 完全相同的 `packages.lock.json`：分别属于 LEAN Wave-B 和 QuickFIX/n 的独立 .NET 项目构建边界，跨目录硬去重并不能让结构更好。
5. **KEEP `artifacts/.gitkeep`**：零字节且当前 `.gitignore` 保留这个工作目录；不是需要删除的运行时垃圾。
6. **没有触碰系统文件、账户数据、用户 Workspace 或其他 Agent 工作树。** 本次没有发现被 Git 跟踪的 `.venv`、`__pycache__` 缓存。

## 成熟能力型 LEGO 与思想型 LEGO

| 已有能力 | Human：解决的问题 | Agent：现有消费者入口 |
|---|---|---|
| CA01 / Markets | 价格何时真实可见，采用何种复权？ | `markets.etf_eod_snapshot`、`historical_close_snapshot` |
| CA02–03 / Risk | 联合尾部风险、敞口和保证金是什么？ | `risk.dependence_analysis`、`portfolio_risk`、`broker_margin` |
| CA04、CA09 / Portfolio | 每月 1r，什么资金配置有经济价值？ | `portfolio.passive_benchmark`、`strategic_contribution`、`multistage_policy` |
| CA08、CA10 / Research | 是否前视、过拟合、虚构利润？ | `research.pit_joint_forecast`、`experiment_protocol`、`independent_policy_replay` |
| CA05 / Governance | 是研究、Paper，还是可能产生外部效果？ | `governance.policy_decision` |
| CA06 / Trading | 订单到底成交、取消还是未知？ | `trading.execution_reconciliation` 和真实提供方回执 |
| CA07 / Accounting | 入金、负债、费用、模拟结算能否核对？ | `accounting.postgres_ledger`、`postgres_paper_close` |

**Human 使用路径：** 从真实投资目标、期限、每月 1r 和效用偏好开始；先核实来源、借贷和券商合同；先比较现金/被动 ETF/组合与净经济效用；只有在独立证据有增量价值时才考虑更复杂的优化模型或融资。不从 Wave-A 历史任务开始。

**Agent 使用路径：** 先看 `config/capital_domain_taxonomy.json`、`config/external_owner_census.json` 和 `planning/lego-plan-r1.json`。使用现有 `finance-paper-investment` Skill 做能力路由、`finance-experiment-review` 做实验冻结、`finance-pit-joint-forecast` 做 PIT。解析当前可见 Skill 的摘要，再运行真实源码/CLI；记录源码 revision、数据哈希、可用时间、经济合同、effects 和独立验证结论。Skill 文本不能代替实际执行证据。

**统一完成标准：** 在真实可审计数据上，由 Markets → Research → Portfolio(+Risk) → 独立证伪，完成现金、被动 ETF、组合、融资的可复现比较，生成明确经济结论或 INSUFFICIENT_EVIDENCE。复杂性不应以模块数量衡量。

## 成熟外部基线

- PyPA src layout：https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
- Martin Fowler, Strangler Fig：https://martinfowler.com/bliki/StranglerFigApplication.html
- 数值计算使用锁定版本 NumPy/SciPy/scikit-learn；形式化使用 Z3/Lean；持久化由 PostgreSQL Accounting Owner 负责，发布复用 GitHub CI / Merge Queue。

本文件是已由 README / Human Guide / Agent Skill 消费的单一目录审计结果，不是新增运行平台或第二套源码分类表。

## 文件级拆分增量：Portfolio 信息树（2026-11-07）

前述文件总数及 Owner 行数是首次审计快照 `32f07fb387df8b20e1cb510a54fe4934064e0c08` 的统计，不代表后续增量。实际复核发现 `portfolio/multistage_policy.py` 混合纯信息树校验与成熟求解器绑定，现将 `information_tree.py` 作为 Portfolio 内的**表示型基础 LEGO**，让它拥有唯一的类型、分支可观察性、概率、资金义务时点与融资合同检查；原 `multistage_policy.py` 只保留数值求解、LP 上界、结果与原 CLI。同步更新 `capital_domain_taxonomy.json` 的准确模块表及 `external_owner_census.json` 的来源映射。

这不是新金融 Owner、新 Solver、PIT 模型或兼容套件。旧研究消费者的类型身份仍相同，核心函数语义没有被重写。下一步只在真实消费者给出重构必要性时继续拆分 Research/Risk/Accounting；对历史回放文件仍遵循消费者可达性，不按名字激进误删。

## Accounting 逐文件退役（2026-11-07）

完成 Accounting SQLite 旧源码、test-only 差分后端及历史验收脚本的消费者穿透，删除不再需要的实现、重复测试和旧比较记录。同步更新 taxonomy、external-owner census、仓库 SQL dialect 约束、人类指南及现有 Agent Skill。原 36 个两操作轨迹保留为真实 PostgreSQL 测试，检查会计状态、超支、幂等、资金守恒。其环境必须是独立临时 PostgreSQL 数据库，不能接入生产财务库。
