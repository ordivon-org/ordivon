# Ordivon Finance 目录与 Owner 审计 R1

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
3. **KEEP（仅差分测试）`accounting/sqlite_ledger.py`**：`tests/test_sqlite_ledger.py`、`tests/test_postgres_trace_refinement.py` 和历史 restart-smoke Runner 仍引用。它不是 PostgreSQL 的生产回退，不需要迁移旧 SQLite 运行数据。彻底删除时同步退休真实消费者并更新 taxonomy/census。
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
