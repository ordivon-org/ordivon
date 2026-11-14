# Ordivon Finance Golden Road R1

**Scope: executable, non-live, bounded and falsifiable.** Current source of
truth: domains/capital. The seven existing domains own actual capabilities:
Markets, Research, Portfolio, Governance, Trading, Accounting and Risk.
There is no new OMS, second accounting ledger, broker mapping, or Agent owner.

## Economic objective and hard bounds

The Paper Investment Lab uses **USD $10,000 virtual starting cash**,
**USD $9,000 protected reserve** and a **maximum USD $1,000 simulated sleeve**.
One original Qlib-selected ETF is simulated for 5 or 20 holding sessions.
The experiment is NOT a real account, investment recommendation, historical
point-in-time market study, proven alpha or live authorization.

## End-to-end production-consumer graph

    Human: objective, reserve and allowed virtual capital
      -> Markets: capturedAt, availability, provenance, rights/PIT state
      -> Research: frozen study and actual Qlib OOS prediction snapshot
      -> Portfolio: existing strategic-contribution capital planner
      -> Governance: existing installed NON_LIVE execution policy
      -> Trading: original native Nautilus BacktestNode fills and order events
      -> Paper bridge: native-account-scoped event IDs, prices, fees, timestamps
      -> Accounting: EXISTING PG SERIALIZABLE Paper close per session
      -> Accounting independent read-latest committed receipt
      -> Risk / Portfolio performance, ONLY IF separate Markets snapshots
         and price/rights/time evidence are actually admitted
      -> Research: passive baseline, OOS independent falsification and report

A simulation mandate is only a caller-declared **Paper portfolio label** and
read-only Portfolio budget; it does NOT authenticate a customer or grant
live PortfolioIntent. Each distinct source / mandate has its own
run-specific r3sim_... PG account. The same portfolio label does **not**
create a canonical persistent multi-run portfolio aggregate.

## 2026-11-14 Markets ETF 日终资格与 PG 消费者精化

此前 Qlib/Riskfolio 已拒绝 2025-05-26 非 XNYS 历史会话，但
Accounting 所用的 Markets ETF EOD 快照仍可能接受任意
operator-declared 的会话日期和假收盘时刻。这会令模拟账户的
EOD close 被错误地投影为有效交易所收盘；源摘要正确并不能
证明会话日期或时刻正确。

当前 Markets etf_eod_snapshot.admit_etf_eod_snapshot 在继续原有
来源摘要、交易时点、原始 USD 收盘、使用权声明和公司行动声明
检查的同时，调用现有 equity_session_calendar 的
require_xnys_eod_session_closes。它直接复用已锁定的
exchange-calendars XNYS 历史会话、夏令时和提前收盘规则；
不开发第二日历/业务时间服务。Accounting
PostgresPaperClose.close_session 对传入的快照类型再次调用
同一自然 Markets 校验：Python dataclass 的形状不是授权或
日历正确性证明。缺日、假节假日、DST 时刻错误和提前收盘时间
错误一律在财务写入前拒绝。原测试专用 CALLER_SUPPLIED_MARKS
仍仅为模拟输入，Risk/Portfolio 不允许把它自动升级为
OPERATOR_BOUND_MARKS 或真实行情来源。

源经济边界必须保持清楚：Cboe/OpenBB 的日线接口只公开
OHLCV 字段，未提供该接口所保证的股息总回报调节类型；
2026 年 QQQ/IWM 的实际分红在各基金原始发行方公开可查，
必须独立取得分红和公司行动才能比较税费后总财富。
具体发行方反例（均为公开发行方记录，非本模型的已认证
历史 first-observed 行情）：Invesco QQQ 在 2026-09-21
除息，单份分配 USD 0.75143，支付日 2026-10-08；
iShares IWM 在 2026-09-15 除息，单份分配
USD 0.750436，支付日 2026-09-18。这两个事件都在
原 Qlib 2025-10 至 2026-10 的回顾性 OOS 时间轴内。
只用行情 open/close 计算的跨除息持仓收益，不能在没有
股息/复权核验时自动成为总回报；应由自然 Markets 来源层
重新取得发行方公司行动和实际可用时点，再委托既有
Research/Portfolio/Accounting 经济消费者，而不是在报告
里静默补算。是否以及如何调整原 Cboe OHLC 在该 SourceCut
依旧 UNKNOWN，禁止由网页上的一个股息日期推定完整
现金收益或投资策略 Alpha。

来源参考：
- https://docs.openbb.co/odp/python/reference/cboe/equity/historical
- https://www.invesco.com/us/en/financial-products/etfs/invesco-qqq-trust-series-1.html
- https://www.ishares.com/us/products/239710/iwm-ishares-russell-2000-etf

无官方已验证的复权、历史 first-observed、数据许可与客户
授权时，研究结果仍仅 retrospective；不能把模拟的 $88/$73
相对 SPY 差额当作真实 Alpha 或推送到真实交易。
真正的 Paper PG / Risk / Portfolio 验收可以只使用独立
临时数据库 + 合成来源声明，绝不重用生产账户。
原生验收和性能观测细节见 Finance R3 源审计回执，
不是以本段文字代替测试。

## 2026-11-14：发行方现金分配与 Research 持仓价格标签

**真实消费者问题：** OpenBB Cboe ETF OHLCV 日线接口没有明确的
分红/拆分调价参数；Qlib R3 H5/H20 研究标签是 T+1 OPEN →
T+H+1 OPEN 的价格比率，并不自然成为含现金分配的总回报。
两个行情端点的 close 相等，也不能证明原始价格复权语义、
来源独立性、数据许可或历史首次可知时间。

**唯一自然 Research 只读消费者：**
ordivon_capital.research.etf_distribution_label_audit。
输入仅包括冻结 CSV 面板、完整 XNYS 交易日网格和单独存放的
私有发行方事件观察 JSON。重用已安装 Mature
exchange-calendars 校验日历，检测
entry_session < exDate <= exit_session
的潜在分红暴露，不重复任何 Portfolio 收益、Accounting
应收款或交易引擎。所有 issuer 事件来自本次人工观察，
并非历史版本的独立时间认证，状态始终
OBSERVED_ISSUER_EVENT_EXPOSURE_NOT_TOTAL_RETURN。

本轮来源：私有
finance/market-daily/capture-20261114-r3/daily_close_panel_20261113.csv
sha256=a1daef34db81615b4ab26ada498ed2d7121833a42cc974303357aeb006cd2e59，
以及私有
finance/issuer-events-diagnostic-20261114-r1/issuer_distribution_observed.json。
发行方公开原始页面：
- QQQ：https://www.invesco.com/us/en/financial-products/etfs/invesco-qqq-trust-series-1.html
- IWM：https://www.ishares.com/us/products/239710/iwm-ishares-russell-2000-etf
- SPY：https://www.ssga.com/us/en/individual/resources/documents/etf-dividend-distributions

2025-10-01 至 2026-10-29 的所有可评价**假设决策日期**
（非 Qlib 真实选股与成交）：

| 研究窗口 | 完整标签候选 | QQQ 跨已观察除息 | IWM 跨已观察除息 | SPY 跨已观察除息的下界 |
| --- | ---: | ---: | ---: | ---: |
| H5 T+H+1 OPEN | 272 | 20 | 20 | 5 |
| H20 T+H+1 OPEN | 262 | 80 | 80 | 20 |

QQQ、IWM 各核实四项季度事件；SPY 仅核实 2026-09-18
一个事件，故 SPY 不是完整事件统计。没有观察到事件，
**不意味着已经证明没有任何发行方事件**。需要独立
来源历史发表时点、股息/拆分、调价语义、税费及权利
才能真正做总收益回测。

Agent 只读使用：

    cd domains/capital
    PYTHONPATH=src uv run --locked --group test python -m ordivon_capital.research.etf_distribution_label_audit --panel /private/panel.csv --observed-events /private/issuer_events.json --expected-panel-sha256 ACTUAL_64_HEX --decision-first 2025-10-01 --decision-last 2026-10-29 --holding-sessions 20

现有 Consumer Graph：
Markets XNYS / 来源字节 →
Research Qlib 冻结 H5/H20 价格标签 →
Research issuer-date label audit →
只有在独立取得合格复权、历史可知性与使用许可后，才允许
交给既有 Portfolio passive_benchmark / Research
investment_candidate 真正经济对照及 Accounting/Risk。
未认证前绝不回填 Qlib 已冻结输出、改写 Paper NAV、
声称 Alpha 或启动资金/真实账户。应继续使用成熟 Skill
finance-experiment-review 中 freeze/holdout/source 原则，
不建立新的 Corporate Actions Bookkeeper。

## 2026-11-14：Paper 账本不能把股票卖出应收冒充基金分红

本轮核对原生 PaperSession/PaperValuation 和
PostgresPaperClose 源码：Accounting 的 receivable_minor
仅承载 pending_sales、sale_settlement_dates 等真实卖出交割
应收，并不表示 ETF 除息后、派付日前存在独立的
dividend receivable 账目。Markets ETF EOD 的
admit_etf_eod_snapshot 要求 corporateActions.events 为
空，任何要求分红或拆分现金效果的输入都会在来源层
被拒绝；不应把 dividend 塞进 PaperSell settlement。

所以应先核对已经上市 ETF 原始公司行动、历史发表时点、
股东权益、record/payable date、券商税务口径、数据使用权
和分红是否已经包含在历史复权收盘价中，再由现有自然
Accounting Owner 决定是否需要添加新的事件类型。
本轮只复用旧的禁止 corporateAction 事件契约，
给 DIVIDEND 添加了原生负例，不修改 PG 账本、
不产生第二套现金收益计算，也不授权真实账户。

## 2026-11-14 R6：不要跨 Qlib 实验偷换 H20 实际选股

研究实验的真实身份至少包含：模型及预测哈希、
source digest / first-observed、hold_sessions、完整
决策样本、exit_price_kind（CLOSE / NEXT_OPEN）、标签
经济事件、数据源调整口径、挑选策略和费用约定。

R7 真实 H20 CLOSE 模型记录的 IWM 13/13 属于
T+H CLOSE 退出；R9 重新训练的 H20 NEXT_OPEN
属于 T+H+1 OPEN 退出。不能因为都叫 H20，就把旧
IWM 13/13 直接用于新 NEXT_OPEN 模型分红统计。
本轮原生 Portfolio 在 private frozen OHLC 上对
纯「13 次固定 IWM」重新计算，H20 CLOSE 相对 SPY
约负 USD 35.67（吻合旧 R7 报告），H20 NEXT_OPEN
约负 USD 25.98（与新 R9 的真实模型
NEXT_OPEN 报告正 USD 73.16 不同）。因此撤回此前
「H20 NEXT_OPEN 模型 4/13 次选中 IWM 跨分红」断言：
那个 4/13 仅是预设全选 IWM 的**条件性场景**，
实际 NEXT_OPEN 模型应恢复对应原始 Qlib prediction
与完整 SourceCut 后再判断。

原有 Research 日期消费者对所有候选日期窗口的
QQQ/IWM 除息相交检查仍可重复，不产生资本权威。
不要重写错误历史、继承不匹配的 benchmark 回执或
基于错误标签选择所谓获利资产。详见
adoption/r3_native/RESEARCH_HOLDING_HORIZON_OOS.md。

## 2026-11-14：HILO 原生数据形状质量

即使日期符合官方 XNYS、历史来源字节 SHA 正确，
同一条 OHLCV 行仍可能内部矛盾；由 (high-low)/close
构造 Qlib HILO 特征因此没有可复核的单一真实价格语义。
已存在的 OpenBB/Cboe 私有来源中：
QQQ 2026-05-20 的 high 比 close 低 USD 0.02；
IWM 2023-06-05 的 high 比 open 低 USD 0.55。
相比长期研究框架的系统性来源风险，这只涉及当前
SPY/QQQ/IWM 各 971 行中两条，但 IWM 发生在训练数据，
QQQ 发生在测试数据。不能为了保护历史回测排名而偷偷
增加 high、剪裁 close 或让 Pandas 填补这些字段。
另一个公开历史报价页面显示 QQQ 同日 high 为 713.15，
不等于已取得具 PIT/许可证明的原始报价替换证据。

复用现有 Pandas/NumPy 与 Markets 自然来源资格函数
equity_ohlcv_shape.require_ohlcv_shape_for_hilo：
高/低必须包住开盘和收盘，价格有限且大于零，
成交量有限且非负；否则报明确的
OHLC_BOUNDS_INVALID_FOR_HILO，在 Qlib HILO 生成前
拒绝后续新模型运行。这个契约不能将旧模型神奇变成
clean HILO，也不验证数据供应商首次可知时间。历史
模型结果只作为不可信原始 SourceCut 的描述性敏感性报告；
重新获取完整且可复验的原始 BAR 证据或预先定义一个
独立的非 HILO 研究家族后才能进行新比较。无私人
行情字节提交 Git，无真实账户/券商影响。

## Golden commands

### 1. Start without any database or broker

From repo root:

    domains/capital/scripts/run-strategic-contribution-brief \
      < domains/capital/examples/strategic_contribution_r1.json

Require executionAuthorized=false, dataStanding=CALLER_SUPPLIED_UNATTESTED
and riskStanding=NOT_EVALUATED. Do not infer an executable order from a plan.

### 2. Check current Governance nonlive admission

From domains/capital:

    scripts/run-capability-python \
      -m ordivon_capital.governance.policy_decision \
      --repo . --config config/execution_policy.json --mode non-live

Require NON_LIVE_POLICY_ALLOWED, allowExternalWrite=false and
externalFinancialWritesAllowed=false. This comes from the repository's
installed configuration and external-write input, not user JSON.

### 3. Actually run the research and native model

The existing Qlib test producer must yield the exact:
  - native_study_result.json
  - qlib_test_predictions.csv

The existing qualification producer at
adoption/r3_native/tests/probe_native_buy_hold_exit.py must genuinely use
the pinned Qlib study with frozen historical Cboe/OpenBB capture and
NautilusTrader BacktestNode to yield:
  - native_holding_result.json (true original native fill claims)
  - paper_sessions.json (co-produced Paper daily account transitions)

The producer needs its existing ORDIVON_FINANCE_R3_* environment and
non-live optional toolchain. It is **a qualification probe, not a
production scheduler**, and test score interventions are never original
Qlib predictions. The prior 2025-10 market history was collected in
2026-11; it is NOT certified as historically knowable in 2025-10.

### 4. Declare a small Paper-only investment envelope

Keep a PRIVATE file called paper-mandate.json, replacing SPY with the
actually model-selected ETF when necessary. All money is in USD cents:

    {
      "schemaVersion": 1,
      "kind": "ordivon.finance.portfolio.paper-simulation-mandate",
      "portfolioRef": "paper-lab-r3",
      "lane": "NON_LIVE",
      "externalFinancialWritesAllowed": false,
      "maxHorizonSessions": 20,
      "allocationRequest": {
        "schemaVersion": 1,
        "kind": "ordivon.finance.portfolio.strategic-contribution-request",
        "currency": "USD",
        "cashMinor": 1000000,
        "protectedReserveMinor": 900000,
        "contributionMinor": 100000,
        "holdingsMinor": {"SPY": 0},
        "targetWeightsBps": {"SPY": 10000}
      }
    }

The contributionMinor=100000 value is a **read-only $1,000 simulation
allocation ceiling**; it does NOT deposit another $1,000 to PG.
The Portfolio component verifies allocation/exposure budgets and
reserves; the Governance component independently verifies NON_LIVE.
Wrong instrument, reserve, horizon, real-execution lane, buy beyond sleeve
or a non-Paper account label must be refused BEFORE the first PG write.

### 5. Close a real simulation batch in a dedicated PostgreSQL

From domains/capital:

    export ORDIVON_CAPITAL_PAPER_PG_DSN='host=127.0.0.1 port=PAPER_PORT user=PAPER_ROLE dbname=ordivon_paper connect_timeout=4'
    scripts/run-capability-python -m ordivon_capital.accounting.paper_simulation_run \
      --study /private/research/native_study_result.json \
      --predictions /private/research/qlib_test_predictions.csv \
      --native /private/nonlive/native_holding_result.json \
      --sessions /private/nonlive/paper_sessions.json \
      --mandate /private/finance/paper-mandate.json

Do NOT commit connection secrets or private files. Database name is
required to be ordivon_paper; no real broker API is involved.
Require portfolioMandateStanding=SIMULATION_ONLY_PORTFOLIO_PLAN_BOUND,
simulationEvidence.nonlive_policy_standing=NON_LIVE_POLICY_ALLOWED,
protectedMinor=900000, brokerEffects=0,
realAccountMappingAuthorized=false, historicalPITQualified=false.

Legacy calls without --mandate still work as UNBOUND simulation replays,
but they do not fulfill this portfolio-scoped Golden Road.

### 6. Read the independently committed PG account head

    scripts/run-capability-python \
      -m ordivon_capital.accounting.postgres_paper_close \
      --account r3sim_FULL_KEY_FROM_PREVIOUS_OUTPUT --read-latest

Require COMMITTED_PAPER_HEAD and match account, mandate, simulation source
and valuation against the original response. The receipt still contains
caller-supplied marks, not independent market-price certification.

Every day is already an EXISTING serializable PG transaction, but the
multi-day batch is NOT atomic. To recover a committed prefix, rerun with
the exact same four artifacts AND same mandate; never silently replace
already-posted source or rewrite an existing Paper account.

### 7. Use independent Risk, benchmarks and Research only when qualified

Risk paper_close_risk and Portfolio paper_close_performance require separately
admitted Markets ETF EOD snapshots and rights/currentness, whereas these
native test closes carry CALLER_SUPPLIED_MARKS. Their stronger claims remain
BLOCKED for this raw experiment; never hand-author false market evidence.
The same-flow passive benchmark, fee/slippage/tax assumptions, OOS sample
size, actual Research precommitment and drawdown/tail risk are the next
independent scientific consumers. Positive simulated cash is NOT alpha.

The simulation account SIM-001 and derived r3sim_... accounts cannot
authorize trading.postgres_demo_intent, OKX, Binance, a live account or a
PortfolioIntent with external financial write effects.

## Engineering falsification and release acceptance

From domains/capital:

    mise run verify
    mise run verify:nonlive:nautilus
    mise run formal:paper

Verify the code on REAL isolated PostgreSQL18, not source-only fixtures:
H5/SPY 8 sessions and $10,005.17; H20/IWM 23 and $10,002.30; zero-entry H5
8 and $10,000; reserve $9,000 each. Assert wrong-ETF portfolio mandate,
changed reserve, false external write and wrong native fill price/fee/ID
are refused before PG; physically stop/restart and replay; interrupt after
four committed days then finish eight; independently read the PG latest
receipt and ensure it still reports non-PIT caller-supplied marks.

Measured 2026-11-13: the scoped run batch first wrote 55 original daily
closes across five virtual run accounts. Tests added extra fixture accounts;
a sixth deliberately interrupted scoped run was restored. The disposable
test cluster ended with 94 real rows in 14 virtual/testing accounts.
These are NOT real customers or production deployments. The existing Z3
Paper model is only an abstract mathematical proof; it is not a formal
proof of the whole Python and PG implementation.

Release code through GitHub Required CI, CodeQL and native Merge Queue,
then independently verify main's complete Capital Git tree. Keep peer
review standing UNKNOWN until an actual other participant checks that
exact source. Delete disposable test clusters and regenerable worktrees
only after Git/source/receipts are safely retained.

## Next-important work, in order

P0: Markets qualified PIT/rightful data -> Risk and Portfolio performance
real consumer acceptance, with no fabricated metadata.
P0: Independent adversarial review of current exact main SourceCut.
P1: Research net-of-fees, matched cash-flow passive benchmark and OOS
sample qualification; state UNKNOWN if no decisive increment.
P1: Persistent multi-run virtual portfolio aggregation ONLY when real
downstream consumers require it; current portfolioRef is not that owner.
P2: Scheduling via existing Harness/Runtime; never add a custom agent
worker or trading runner without a proven consumer and resource budget.
External broker finance writes remain NOT_ADMITTED.


## 2026-11-14 R6：研究经济消费者新的精确输入合约

已有 Qlib 测试经济消费者
adoption/r3_native/tests/probe_qlib_paper_horizon.py
现在拒绝与研究报告预测、Parquet 标签、三个 ETF
原始市场数据 SHA 不匹配的快照，并检查 H1/H5/H20
正确的 CLOSE/NEXT_OPEN 经济标签定义。其输出包含
native_study_identity，供 Agent 审查实际所消费的
预测字节、数据集与价格来源；变更一个文件不能仍然
借用旧模型名字继续计算。因此历史旧报告可保留，
新模型才有资格重新生成自己的结果，不用另写
Qlib/Portfolio 计算引擎。

私有 issuer-events-diagnostic-20261114-r6 中增加 SPY
2025-12、2026-03、2026-06 的有限事件观察，
当前三个 ETF 各观察到4个季度事件，但美版发行方
历史 XLSX 未单独认证，全部返回 SOURCE_UNVERIFIED/
PIT_UNKNOWN；现金敏感性脚本调用既有 Portfolio
cashflow-matched comparator。美国 SPY（NYSE Arca）
与同 ISIN 的新加坡 SPY 交易单位（SGX）存在
2026-06-18 vs 2026-06-17 不同当地 ex-date，
绝不能互用。同一基金不等于同一市场除息时间。

H20 CLOSE 固定 13 次 IWM 的旧比较 -35.67 USD，
与观察现金相加后的条件比较约 -36.68 USD；
H20 NEXT_OPEN 假设固定 13 次 IWM 的价格比较
-25.98 USD，条件现金 -26.93 USD。这些都是
历史价格/条件现金情景，不是新 R9 NEXT_OPEN
Qlib 模型重放，不是已认证的总回报，
更不提供实盘/PG 影响。
