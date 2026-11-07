# Ordivon Finance — Human 操作指南（R1）

**入口定位**：Finance 是 Ordivon Capital 的投资研究与模拟投资能力组合，不是独立交易机器人或独立 Agent Runtime。当前源码在 `domains/capital/`；所有示例均以仓库根目录为工作目录。首次体验先执行下方的无账户、只读示例；修改源码或验收工程变更时才运行 `mise run //domains/capital:verify`。无需为一个简单示例先跑全仓测试。

## 1. 我能用它做什么？

| 需求 | 对应自然 Owner / 现有模块 | 当前实际能力 | 不等于什么 |
|---|---|---|---|
| 查询、整理 ETF 收盘行情和历史版本 | Markets · `etf_eod_snapshot.py`, `historical_close_snapshot.py` | 有来源与时间边界的行情快照准入 | 自动获取全市场真实、实时的价格 |
| 将新存款分配给长期目标资产 | Portfolio · `strategic_contribution.py` | 给定持仓、市值与目标比例，计算**只买不卖**的计划 | 投资建议、实际订单或可信行情 |
| 比较主动策略与相同现金流的被动指数 | Portfolio · `passive_benchmark.py` | 纯函数、现金流与费用口径匹配的描述性对照 | 真实预测、税务计算或交易执行 |
| 用已冻结的历史行情重放模拟策略 | Portfolio · `paper_investment.py` | 生成逐日模拟净值、回撤和基准差异 | 真实订单成交、可复现的未来 Alpha |
| 检查行情新旧版本是否改变历史结论 | Portfolio · `paper_vintage.py` | 同覆盖期间的价格版本敏感度比较 | 对未来表现的预测 |
| 保存模拟持仓、应收应付和日结 | Accounting · `paper_close.py`, `postgres_paper_close.py` | Paper 专属 PostgreSQL 的模拟账务与日结收据 | 实盘经纪商资金、自动行情授权 |
| 冻结假设、评价研究与独立反证 | Research · `experiment_protocol.py`, `investment_candidate.py` | 研究预提交、样本外与经济证据审查 | 已证明策略收益、实际资本授权 |
| 度量风险、决定是否允许效果 | Risk / Governance / Trading | 已有边界化度量、策略规则与执行可行性检查 | 自动下单的默认授权 |

这些模块分别归属 Markets、Portfolio、Research、Risk、Governance、Accounting、Trading 七个已有源码 Owner。**Human 先选择目的，Agent 再选择经过验证的最小 LEGO；不能反过来因为存在某个模块就自动授予它资金权限。**


### 源码 LEGO 索引：CA01—CA10 的实际消费者是什么？

下表指的是当前 `planning/lego-plan-r1.json` 内**已有的源级合同**（全部标记为 IMPLEMENTED），而不是声称所有外部工具、形式化证明或真实市场接入都完成。每项是否能用于某个结果，仍由该源的实际证据决定。

| LEGO | Human 应该问什么 | Agent 应该调用/验证的自然消费者 |
|---|---|---|
| CA01 · PublicMarketSnapshotQualification | 行情是公开、及时、可合法使用的吗？ | Markets 的公开行情准入；不读取私有账户 |
| CA02 · FactorProxyDependenceMeasurement | 这些因子是不是高度相关？ | Risk 的相关性/依赖测量；不得推断因果收益 |
| CA03 · PortfolioExposureLedger | 我的真实或模拟敞口是什么？ | Risk 的暴露账本投影；避免重复累加因子 |
| CA04 · PortfolioCounterfactualComposition | 如果调整仓位，组合会发生什么变化？ | Portfolio 的情景推演，再交独立 Risk 约束 |
| CA05 · NonLiveExecutionPolicyAdmission | 本次操作仅允许模拟，还是有额外效果？ | Governance 的 NON_LIVE 准入；拒绝越权执行 |
| CA06 · AmbiguousExecutionReconciliation | 某笔订单状态到底确认了吗？ | Trading 的提供方观测核对；证据不足为 UNKNOWN |
| CA07 · DurableCapitalReservationLedger | 预留、释放和最终入账如何保持一致？ | Accounting 的持久交易/预约模型；旧 SQLite 为迁移对照，不是新首选 |
| CA08 · ProspectiveStrategyEvidenceValidation | 研究结果是否发生在冻结假设之后？ | Research 的前瞻有效性检验 |
| CA09 · StrategicContributionOnlyAllocation | 如何保留现金并分配新资金？ | Portfolio 的贡献式分配 CLI（下面可立即运行） |
| CA10 · FrozenExperimentProtocolReview | 研究方案是否先冻结、再观察结果？ | Research 的 `run-finance-lego` 与现有研究 Skill |

对 Agent 来说，正确流程是**先选择用户问题，再沿自然 Owner 调用已有 LEGO**；对 Human 来说，先确认经济目标、数据来源和可承受的回撤，然后再解释结果。CA01—CA10 之外新并入的 Paper 模块仍由其自然 Owner 管理，不因为尚未获得连续 CA 编号就“不可使用”。


## 2. 立即可复现：给长期投资账户规划一笔虚拟新增资金

这是最简单的无账户、无数据库、无网络金融效果的起步任务：

```sh
domains/capital/scripts/run-strategic-contribution-brief \
  < domains/capital/examples/strategic_contribution_r1.json
```

样例以**美分（USD minor units）**为单位：已有现金 50000（$500）、保护储备 30000（$300），计划投入 10000（$100），已有 INDEX_CORE 80000（$800）、BOND_CORE 20000（$200），目标比例 60%/40%。

当前源码实跑输出：`allocationsMinor.BOND_CORE=10000`、`allocationsMinor.INDEX_CORE=0`、`cashAfterMinor=40000`，同时明确 `executionAuthorized=false`、`riskStanding=NOT_EVALUATED`、`dataStanding=CALLER_SUPPLIED_UNATTESTED`。这只是按已提供的目标和市值计算贡献缺口，不能反向证明这些目标、估值或投入时间合理。

你可以在样例的**副本**中改为自己的虚拟组合与目标比例，再运行相同入口；不要在公开仓库保存个人账户余额或 API 凭据。

## 3. 三条实际工作路径

### A. Investment Mode：长期资本配置

1. 先明确投资期限、必要储备、可投入资金、基准与最大可承受回撤；这些由 Human 决定。
2. 在虚拟账户上跑上面的 Contribution 方案，检查现金保护不变量与分配结果。
3. 需要衡量策略是否优于简单指数时，使用现有 `portfolio.passive_benchmark`。输入需包含同一现金流、每期税费/成本假设与时点；详见 `docs/FINANCE_INVESTMENT_MODE_R2.md`。
4. 结论只允许是比较结果及其限定条件，不允许把“样例回测上涨”写成“建议买入”。

### 同一现金流的被动基准：一个不用行情账户的算例

从仓库根目录进入 Capital 责任目录执行：

```sh
cd domains/capital
scripts/run-capability-python \
  -m ordivon_capital.portfolio.passive_benchmark \
  --input examples/passive_benchmark_first_run_r1.json
```

这个原生运行器会将执行目录切换到 `domains/capital`；
因此输入路径须相对于 Capital 根目录，不能直接把仓库根相对路径
传给 `--input`。

这个独立的合成算例让策略与基准都从 $1,000 开始，并在两个
假想收益期间各于**期初**投入 $100。它明确建模不同的每期收益、
费用比例和固定手续费，不请求行情 API。累计投入 $1,200；
在该固定输入下，策略期末财富为 $1,192.10672，基准为
$1,214.44400448，相差 −$22.33728448。这个差值是描述性的，
没有数据真实性认证、统计显著性或实际投资建议的含义。

使用真实数据时必须单独证明资产价格来源、公司行为调整、各期
现金流、费用和可获得时间；不能将回测样例转为可信的样本外收益。

### B. Research Mode：建立可反证的研究

现有 Agent Skill `.agents/skills/finance-experiment-review/SKILL.md` 是正式流程说明，入口是：

```sh
domains/capital/scripts/run-finance-lego --help
# 以下命令读取分别准备好的规范 JSON，不存在默认市场数据
domains/capital/scripts/run-finance-lego fingerprint-policy < policy.json
domains/capital/scripts/run-finance-lego freeze-experiment < plan.json
domains/capital/scripts/run-finance-lego assess-holdout < review.json
```

冻结点、数据可获得时间、试验次数、源码/配置摘要与未来样本必须可区分。缺少独立证据是 `UNKNOWN`；不能为了获得 PASS 用未来数据补写历史计划。策略和被动指数应使用相同资本、市场数据和费用口径。

### C. Paper Lab：重放、模拟账本与每日结算

**第一级（纯历史模拟，易复现）**：`paper_investment.py` 的现有接口要求明确提供历史价格文件，且请求中有对应源码指纹；只读历史来源不构成数据商真实性认证。

```sh
domains/capital/scripts/run-paper-etf-replay-r1 \
  --request examples/paper_fixed_mix_etf_20261106.json \
  --source /path/to/verified/daily_adjclose.csv \
  --output /private/path/paper-replay-receipt.json
```

脚本参数中的相对路径从 `domains/capital` 解析，外部文件可用绝对路径。
上面的 `--source` 是**占位符**：必须先独立取得与请求摘要一致的授权数据，否则程序应拒绝。仓库示例文件并未自带真实数据；不要臆造“今天收益”。输出为 `RETROSPECTIVE_PAPER_REPLAY_NO_FORWARD_EDGE_CLAIM`，不等于实盘盈利或独立市场源验证。 可选的 --output 使用一次性原子创建的本地模拟收据：相同请求可复用既有文件，不同策略或数据版本不能覆盖已有路径；应选择新的收据路径。

**第二级（有状态的模拟日结）**：仅在 Paper 专用 PostgreSQL 数据库 `ordivon_paper` 中使用 Accounting 的原生日结入口。配置 `ORDIVON_CAPITAL_PAPER_PG_DSN` 指向 Paper 专属角色，再提交已经明确交易所日期和持仓来源的 session：

```sh
domains/capital/scripts/run-capability-python \
  -m ordivon_capital.accounting.postgres_paper_close \
  --account cash --input /private/path/session.json
```

如果有已经得到 Markets 准入的 ETF 日终快照，必须**成对**传入 `--market-snapshot snapshot.json --market-binding binding.json`；不能仅靠添加标志绕过行情资格，也不能把上一次价格悄悄当成今天价格。输入和收据格式以 `domains/capital/README.md` 的 Paper accounting 部分为准。

Paper 日结会改变**模拟数据库**的状态，但不会调用真实经纪商。重复提交相同已关闭时段应获得原收据，改变同一已关闭时段的内容应被拒绝。模拟买卖的清算日期、费用和企业行为存在明确的已实现范围；无真实行情时，日结事实必须标为未知或缺失。

### Paper 账本到 Risk：检查已承诺的模拟账户

如果已经由 Accounting 在**专用** `ordivon_paper` PostgreSQL 数据库
完成一个 Paper 日结，Risk 可沿现有只读消费者核对已提交日结与
Markets 独立准入的原始未复权收盘价，而不从复权历史柱子猜测成交：

```sh
cd domains/capital
scripts/run-capability-python -m ordivon_capital.risk.paper_close_risk \
  --account PAPER_ACCOUNT --session YYYY-MM-DD \
  --snapshot /private/etf-raw-marks.json \
  --binding /private/operator-market-binding.json
```

此处四个大写/私有路径都是占位符，不是可直接用于某位用户的默认
账户或市场数据。实际运行需要已存在的 Paper 收据、可用的
`ORDIVON_CAPITAL_PAPER_PG_DSN` 和外部独立来源证据。
`--receipt` 离线模式只能读取自行提交的收据文件，**不能证明**它
确实已经入账。NAV 口径是现金减未结应付款、加未结应收款与
按有效行情计价的持仓；未结卖出应收款不是可立即投入的自由现金。
目前 Principal 风险预算输入标为 `UNSET`，Risk 不能因此宣称
风险限额已满足。Agent 专项操作说明在
`.agents/skills/finance-paper-risk-review/SKILL.md`，真实资格由
Accounting/Markets/Risk 原生消费者给出。

历史尾部风险如果单独计算 VaR / ES，应使用现有 Risk 的 `historical_expected_shortfall`，并按 [Portfolio Risk Monitoring](PORTFOLIO_RISK_MONITORING_R1.md) 理解其经验分布与尾部概率口径。尤其不要把“超过阈值的样本直接平均”误认为指定置信度的 ES；它不能替代未来风险预测或风险预算。

## 4. 如何阅读结果？

- **`READ_ONLY_PROJECTION`**：只是数学投影。它不证明行情真实或组合风险合格。
- **`SIMULATION_ONLY`**：只有虚拟资金效果；不代表券商成交。
- **`UNKNOWN` / `NOT_EVALUATED`**：没有相应资格或证据，不是失败也不是“默认通过”。
- **`REJECTED`**：输入、证据、资金约束或源码合同不满足；先修复信息而不是放宽阈值。
- **`capitalAuthority=NONE`、`executionAuthorized=false`**：从研究结果不能推出资本转移权限。
- **收益率**：注意区别交易收益、净值变化和外部入金。未处理外部现金流时，不能把净值增加直接当投资利润；需要 GIPS 一致的时间加权或正确标注的现金流调整口径。

## 5. Human 与 Agent 的职责差异

**Human 决定**：投入目标、时间范围、储备现金、可承受风险、何时退出以及是否有适用的法律/经纪账户约束。需要人工确认的不是每次计算，而是这些不可由统计模型取代的经济偏好。

**Agent 执行**：寻找已实现的原生入口、检查数据使用权与可获得时间、构建研究假设、产生可重放实验、比较被动基准、寻找反例、输出带来源与未知项的结论。Agent 不应该以自信的市场故事取代原始数据。

**当前缺口**：具有时间保证的实时行情采集、自动交易所节假日日结调度、企业行为完整处理、源独立认证和实盘账户对账不可从上述例子中推定已经完成。Finance 能跑一个历史 replay，和生产环境每天可靠地结算，是两项不同的验收。

## 6. 开发者与 Agent 快速定位

- 源码责任目录：`domains/capital/config/capital_domain_taxonomy.json`。
- R2.1 可组合 LEGO：`domains/capital/planning/lego-plan-r1.json`。
- 源码能力与成熟外部 Owner：`domains/capital/config/external_owner_census.json`。
- Agent 研究 Skill：`.agents/skills/finance-experiment-review/SKILL.md`。
- Agent 投资/Paper Skill：`.agents/skills/finance-paper-investment/SKILL.md`。
- Agent 专项模拟账本 Risk：`.agents/skills/finance-paper-risk-review/SKILL.md`。
- 本地验证：`mise run //domains/capital:verify`；全仓库发布验证：`mise run repo:ci`。
- 理论来源：QuantConnect LEAN Algorithm Framework（分离资产选择、组合、风控与执行）、CFA Institute GIPS（现金流对收益的影响）、Agent Skills 开放格式（按需加载知识，不重复做 Agent Runtime）。

投资结果、研究证据和金融效果分别由原有 Portfolio / Research / Accounting 与平台自然 Owner 管理；新增流程首先使用 `DELETE-CUSTOM → REUSE → COMPOSE`，不创建第二套记账、回测、权限或注册系统。
