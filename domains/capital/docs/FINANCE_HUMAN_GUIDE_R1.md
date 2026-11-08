# Ordivon Finance — Human 操作指南（R1）

**Directory audit and Human/Agent roles:** [Finance Owner / LEGO audited guide](FINANCE_DIRECTORY_OWNER_AUDIT_R1.md). Use the existing natural Owners instead of recreating the retired Wave-A pipeline.

> 多阶段情景树优化与严格非预见性说明：
> `MULTISTAGE_FINANCE_R1.md`。这个成熟随机规划子问题在所有
> 价格/融资/效用分布均由调用者或真实提供方给定时才有条件最优解，
> 未知分布不应被默认猜测，也不意味着允许交易。

> 研究模型最新口径：`ALGEBRAIC_FINANCE_POLICY_R1.md`。每月 `1r`
> 为标准化外部入金；不能仅从历史最大回撤、任意 40%/35% 数字
> 推导普适的最优杠杆。早期 `UNIT_R_DCA_LONG_HISTORY_R1.md` 中的
> 回撤门槛、假设年化融资与额外压力缓冲都只是历史情景参数，
> 不是经济学模型的默认值。优先查看由效用、融资合同和联合收益
> 概率分布决定的代数可行政策族。


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
| CA07 · DurableCapitalReservationLedger | 预留、释放和最终入账如何保持一致？ | Accounting 唯一 PostgreSQL 账本，真实 PG 重启、并发和 36 条会计合同轨迹；无 SQLite 后备数据库 |
| CA08 · ProspectiveStrategyEvidenceValidation | 研究结果是否发生在冻结假设之后？ | Research 的前瞻有效性检验 |
| CA09 · StrategicContributionOnlyAllocation | 如何保留现金并分配新资金？ | Portfolio 的贡献式分配 CLI（下面可立即运行） |
| CA10 · FrozenExperimentProtocolReview | 研究方案是否先冻结、再观察结果？ | Research 的 `run-finance-lego` 与现有研究 Skill |

对 Agent 来说，正确流程是**先选择用户问题，再沿自然 Owner 调用已有 LEGO**；对 Human 来说，先确认经济目标、数据来源和可承受的回撤，然后再解释结果。CA01—CA10 之外新并入的 Paper 模块仍由其自然 Owner 管理，不因为尚未获得连续 CA 编号就“不可使用”。


### Risk 的形式化性质与实际实现

对 CA03 暴露账本，现有 Lean 证明 `net`、`gross` 在任意有限整数
头寸列表上的组合律，并证明 `|net| ≤ gross`。在仓库根目录运行
`mise run //domains/capital:verify:formal:risk-exposure` 检查模型；
再运行 `mise run //domains/capital:verify` 检查实际 Python 消费者。
两者不可混为一谈：Python `Decimal`、因子加载、外部账户真实性与
真实投资结果尚无相应实现精化证明，详见
`domains/capital/formal/RiskExposureBound.md`。

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

如要检查这类比较的底层**数学转移契约**，在 `domains/capital` 运行
`mise run verify:formal:passive-benchmark`。证明范围及具体的 Human/Agent
证据使用规则见 `formal/README.md`：五个 `unsat` 与一个 `sat` 证明
两期精确实数模型的性质，并不等于真实 Python/市场收益已被证明。
另可运行 `mise run verify:formal:passive-general`，用 Lean 检查**任意有限
期数**下的现金流累计、相同条件下的结果一致性和费用后非负性等
精确有理数模型定理；再用 `mise run verify` 检查真实 Python `Decimal`
在多期、舍入、异常值下的消费者行为。任意期数的模型证明不等于
Python 实现已获得形式化精化证明，更不等于真实行情可投资。

此外，累计外部现金流与市场估值是两个不同的数值口径：前者不允许默默舍入，
后者允许 `Decimal` 的有限精度计算，但一笔现金注入造成的舍入误差
上界必须不超过该笔投入的 `1e-12`。否则程序拒绝生成对照报告，不能
将拒绝误读为现金已经损失。

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

### 每日结算前：先读取原有账户的最新已结算日期

```sh
cd domains/capital
# 需预先设置专用的 ORDIVON_CAPITAL_PAPER_PG_DSN
scripts/run-capability-python -m ordivon_capital.accounting.postgres_paper_close \
  --account PAPER_ACCOUNT --read-latest
```

这是 **只读 PostgreSQL 查询**，不创建账户，不重新拨入起始虚拟本金，不生成任何今日收盘价。
返回 `COMMITTED_PAPER_HEAD` 才表示存在可验证的本地模拟日结回执；
`NO_COMMITTED_PAPER_CLOSE` 仅表示已初始化的 Paper 数据库里该账户为空。
缺失数据库、密码或结算表则报错，而不是自动声称余额为零。查询会核对
同一数据库快照中的原始请求摘要、回执的行情声明和前一条摘要；
它**不独立证明**行情是某个交易所当天发布的，也不以账面 NAV 代替收益率。
没有新、完整、可核验的合格收盘价就报告 `NOT_SETTLED`，不要重置本金或伪造结算。

**Paper 提交与读取隔离验证**（数据库内核精化，不是行情真实性证明）：
Accounting 已使用 PostgreSQL `SERIALIZABLE` 写事务，最新/历史日结读者
使用 `REPEATABLE READ READ ONLY`。新增的真实数据库反例位于
`tests/test_paper_head_readback.py`，覆盖三种情况：

- 写入现金账与回执、尚未提交时，其他消费者不能看见半完成日结；
  已建立的只读快照在另一个事务提交新日期后仍看见原日结。
- 两个针对相同 `account_key + session` 的不同请求同时写入时，只允许一个
  提交；另一笔不能覆盖已承诺请求。
- 在 SQL 写入完成、事务提交前实际终止该 PostgreSQL 后端时，未提交数据
  回滚；旧日结仍可读取，随后新的完整重试能够提交并被读回。

在已配置且确认**可以销毁**的独立 `ordivon_paper` 测试数据库中：
`ORDIVON_CAPITAL_PAPER_PG_TEST_DSN=... uv run --group test pytest -q
tests/test_paper_head_readback.py`。测试会写入随机模拟账户，
其中一项还会终止**它自己的**数据库写入会话；绝不可把生产 DSN 用作测试 DSN。
如果未提供测试 DSN，相关测试会标记为 `SKIP`，不能视为通过真实 PG 验证。
这些反例证明 Paper 数据库内部的原子可见与恢复边界，不能证明 Git 产品元数据、
外部 Parquet 文件与 PostgreSQL 已经获得跨系统原子事务或业务时点数据可信性。

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

### Paper 日报：新增本金与投资盈亏分开

对两个已经提交的连续 Paper 收据，可读取 PostgreSQL 并生成只读简报：

```sh
cd domains/capital
scripts/run-capability-python -m ordivon_capital.portfolio.paper_close_performance \
  --account PAPER_ACCOUNT --session YYYY-MM-DD --previous-session YYYY-MM-DD \
  --snapshot /private/etf-raw-marks.json \
  --binding /private/operator-market-binding.json
```

沿用上节的专用数据库 DSN、账户和行情占位符。简报复用 Accounting 的
净值及 Risk 的核对；投资盈亏为「本期净值 − 前期净值 − 本期新增本金」。
收益率假设新增本金在期初可用；它不是时间加权收益或内部收益率，
首份收据不评收益。JSON 中的 `accountingPersistenceReverified=true`
只表示已完成原生 PostgreSQL 回读，不证明外部行情来源真实。

Agent 可直接调用 `summarize_paper_period`，或用
`--current-receipt` / `--previous-receipt` 提交文件；文件模式的持久化
核验标志保持 false。必须保留前驱摘要链、Markets 原始价绑定、
Risk 状态及精确收益小数字符串；不要从此简报推导下单权限。

### 形式化与实际结算：目前验证到哪里？

Finance 已有原生 Lean 模型 `formal/PaperCloseAmounts.lean`，可以运行
`mise run //domains/capital:verify:paper-amounts`。其整数规格证明：
清算已经计入的应付和应收款不会凭空改变同一市场价格下的 NAV；
结算当日收到的卖出款不会同时增加**当日新买单可用预算**；
在结算额不超过原负债时，剩余应收应付款仍非负。
这不是对 Python、PostgreSQL 或真实交易所行为的自动证明。

Human 应把「数学模型成立」「代码有可观察的对应行为」
「数据库真正提交和读回」「提供商数据可信」看作四种不同证据。
Agent 需要在实际操作中同时检查源码、`test_paper_close.py`
消费者行为和 Paper PostgreSQL 回读；没有实际回读时不能标为已验收。
现阶段模型到实现之间不存在机器验证的全面精化证明。

### 研究参数的精确身份与冻结

`fingerprint-policy` 会将研究策略的资产权重、基准费用率按**精确十进制数值**生成
`configDigest`，而不是将它们先截断为默认 28 位有效数字。
例如 `0.5` 与 `0.50` 在数学上等价，指向相同策略；
但在第 40 位小数上不同的两个权重不能再使用相同研究预注册身份。
冻结前应保存实际生成的策略摘要、源码版本与配置来源；更新源码后不能
将历史冻结收据直接视作由新版算法签发，更不能用事后变更的参数
改写研究结果。这个身份检查并不独立证明时间戳或市场数据真实。

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

## 多期策略的先验合同检查（2026-11-07）

Finance Portfolio 的月度信息树现在由独立的 `portfolio/information_tree.py` 验证。人类使用时先明确：每月 1r 入金时点、当时真正可观察的分支、所有资产条件概率、逐期现金支出、最终负债以及提供方提供的保证金与融资合同。仅当数据、合同和效用足够完整，才用现有 `portfolio/multistage_policy.py` 进行数值优化，且仍为只读研究结果。

这次拆分不新增任何交易入口、账本或 API。详细数学接口及 Agent 调用见 [多期模型与信息树合同](MULTISTAGE_FINANCE_R1.md)；对应的源码与已退役文件审计见 [Finance Owner/LEGO 审计](FINANCE_DIRECTORY_OWNER_AUDIT_R1.md)。

## PostgreSQL 会计唯一入口与人类操作（2026-11-07）

Finance 的持久化账本由 Accounting 的 PostgresAccountingLedger 负责。对于每月入金、预留、消费、释放和 Paper 结算，先核实真实资金合同、命名空间和 PostgreSQL 连接；研究模型输出不等于账本回执。测试应当使用专用、可销毁的 PostgreSQL 数据库，环境变量为 ORDIVON_CAPITAL_PG_TEST_DSN，绝不把测试运行到生产金融数据库。

旧 SQLite 引擎、R0-R5 脚本和差分测试已退役。36 条两操作情景直接对真实 PostgreSQL 和独立账务预期进行比较，无需迁移旧 SQLite 数据。Human 可从 scripts/run-nonlive-capital-effect-matrix 了解模拟资金效果；这仍需要显式 PG DSN，且不构成外部交易授权。Agent 的操作顺序见现有 finance-paper-investment Skill。

## Prospective Validation：日期对齐与真实数据证据

`research/prospective_validation.py` 只负责一项纯计算：在冻结的决策时点与交易所时区下，找出所有必需资产**共同拥有、严格晚于决策日**的候选交易日期。它不接触行情原始响应，也无法核实首次观测时间、数据发布时间、使用许可和企业行动。

**Human：** `postDecisionSessionDatesAligned=true` 只说明日历条件满足；`POST_DECISION_DATES_ALIGNED_SOURCE_UNVERIFIED` 不是“样本外数据已经可用”。当前返回的 `postDecisionHoldoutAvailable=false` 是刻意保留的证据边界。不可把回填日期或尚未发生的日期当成真实的未来收益观察。

**Agent：** 先固定 `decision_boundary` 与 `session_timezone`，调用已有 Research 日历算子得到 `alignedCommonSessionDates`；再到现有 Markets 与 Research Owner 核验原始来源摘要、首次观测/发布时间、企业行动和真实评价时点。上述证据缺失时保持 UNKNOWN，不得宣称 PIT 验证、OOS 评价完成、经济优越性或实盘交易权限。禁止再建时间数据目录、专用证明服务或第二套研究执行器。
