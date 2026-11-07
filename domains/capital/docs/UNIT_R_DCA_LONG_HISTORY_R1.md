# Ordivon Capital / Research：1r 定投 × 长历史 × 回撤约束

> **历史固定参数实验，不是统一优化策略。** 文中的 40%、35%、
> 10个百分点、历史加固定缓冲和假设融资利率均为研究情景选值，
> 并无经济理论证明它们普适最优。统一 1r 代数规格请见
> `ALGEBRAIC_FINANCE_POLICY_R1.md`。不得把历史回放终值写成
> 已求得的全局最优利润，或把历史未强平当作未来保证。


## 范围

只读历史投资研究（HISTORICAL_REPLAY_ONLY）。不属于实盘、前瞻模拟盘或 Paper Accounting；不创建交易订单、不修改任何持仓/结算账本。

**每月 1r** 是标准化资金单位，与人民币、汇率、年收益率及风险倍数均无关。累计 N 次入金为 N r。投资绩效必须同时报告出资时点匹配的 XIRR、剔除入金影响的单位净值最大回撤；不能将期末盈利直接除以总出资冒充年化收益。

来源：2026-11-07 下载的 Yahoo Finance 日线历史，截止交易日 2026-11-06。6只 ETF 共同日历 2003-05-01—2026-11-06 共 5,919 根日 K，逐资产 SHA256 存档。Yahoo 是二级数据商，来源身份未逐条得到交易所独立认证。各 ETF 上市之前不存在 ETF 历史数据，不得拼接成历史可交易轨迹。

## 数学表示与会计不变量

状态：q 为 ETF 综合份额，p 为分红调整价格，c 为现金，b 为借款，E = q*p + c - b 为账户净资产（r）。
月度首个可用交易日收盘前，必须先用当日日 K 最低价检查既有持仓维持保证金；之后才可在当日收盘追加1r和重平衡。每次交易成本 = 0.001 × 交易名义金额；借款按真实日历天数及情景固定融资年利率复利计息。假设可交易任意小数份额，现金不计息。
外部入金不构成投资收益；调仓费用和利息则计入流量调整后的 U_t。H_t 是 U_t 的历史峰值。

静态保证金解析式，假设初始权益=1r、杠杆w≥1，跌幅d，维持保证金比例m：

    E_after = 1 - w*d
    gross_after = w*(1-d)
    headroom = E_after - m*gross_after
             = 1 - w*(m+(1-m)*d)
    w <= 1/(m+(1-m)*d)

Z3 模型验证该代数恒等式、静态合法案例和违约见证。这不是对实际券商保证金、Python 代码、分红及未来跳空的完整证明。

## 无前视风险估计

每次重平衡严格使用当日之前756根每日调整收盘价，从 Capital Risk 的现有 historical_expected_shortfall 算子取得历史21交易日重叠收益的 97.5% ES；计算过去756日峰谷最大回撤（MDD）。风险情景：

    d* = min(0.95, max(0.35, MDD_756+0.10, 1.25*ES_97.5(21-session loss)))

维持保证金压力假设 45%，可用理论杠杆余量的80%；初始保证金要求50%。最终敞口允许小于1，剩余资金保留现金。

    w_margin = min(2, 1+0.8*(1/(0.45+0.55*d*)-1))
    w_risk   = min(w_margin, delta/d*)
    F_{t-1}  = (1-delta)*H_{t-1}
    cushion  = max(0, 1-F_{t-1}/U_{t-1})
    w_CPPI   = min(w_margin, cushion/d*)

w_CPPI 复用 Grossman-Zhou / Black-Perold 的峰值保护及 CPPI 思想，实际只是离散月度再平衡的近似，不是连续无跳空的硬保证；当缺少缓冲时自动转为现金，可能在熊市后错过反弹。

五项预先声明策略：基准始终1倍；Margin Cap 不超过1.5倍且受压力保证金限制；Risk Budget 使用30%或40%的压力损失预算；Peak Cushion 使用40%峰值损失预算；Crisis Memory 将之前所有有效日 K 的历史最大回撤（加5个百分点）纳入40%压力预算，不能因为756日窗口滚动便遗忘2000年科技泡沫或2008年金融危机。Crisis Memory 使用每只ETF的完整上市后历史，不受RSP在2003年才上市的共同起点限制；信号仍严格排除当前和未来日线。

在完整可用历史中 QQQ（2000-03-27 至 2002-10-09）观察到最大回撤约82.96%；SMH（2000-06-21 至 2008-11-20）约85.92%。保留历史极端记忆通常显著减少仓位，也可能导致长期财富终值下降。Crisis Memory 不等于 CPPI，有限调仓下最大实现回撤仍可能突破名义预算；不能称作严格回撤保证。
实际历史维持保证金检测为40%，额外运行45%敏感性；融资情景利率 3%、7%、12%。这些利率不是已独立验证的历史券商真实融资价格。

## 月度调仓：Research 内的独立计算单元

回放调用 `research.unit_r_dca.solve_turnover_adjusted_exposure`，不再在
月度循环中嵌入两套交易费用算法。假设按实际调仓名义金额的
`turnover_cost` 收费，费用是投资损失，不是外部入金。

给定调仓前权益 `E`、旧名义敞口 `G0`、目标敞口/净权益倍数 `w`、
交易费率 `f`，新名义敞口 `G` 与新权益 `P` 必须满足：

    P = E-f*abs(G-G0)
    G = w*P
    增持 (w*E>=G0): G=w*(E+f*G0)/(1+w*f)
    减持 (w*E< G0): G=w*(E-f*G0)/(1-w*f)

如果 `E<=f*G0`，全额平仓成本已耗尽权益，计算器明确拒绝该
交易输入。模拟现金和借款按 `G,P` 分割，仍满足 `G+cash-debt=P`。

`formal/UnitRRebalanceConservationR1.smt2` 使用已有的 Z3 QF_NRA
验证买卖两分支固定点、分支方向、正权益、初始保证金、现金/负债
恒等式：7 UNSAT 与 2 SAT。`formal/UnitRMarginBoundR1.smt2`
已有的静态保证金模型继续保持 2 UNSAT 与 1 SAT，二者均进入
Finance 原生 `mise run verify`，UNKNOWN/超时不能算作通过。

**Human：**运行 `mise run verify:formal:unit-r-margin`、
`mise run verify:formal:unit-r-rebalance` 与完整 `mise run verify`。
**Agent：**通过现有 `finance-experiment-review` Skill，明确分开
精确实数数学模型、Python float 实现证据、独立行情来源、历史回放
与券商执行权限。这里不包含完整的 float 形式化精化证明、交易滑点、
前瞻损失上界或真实券商强平行为。

## Human 与 Agent 分离指导

Human：采用相同日K、同样的每月1r现金流、相同融资/费用假设比较 IWM/SPY/QQQ/SMH/DIA/RSP。重点查看2006年、2007年高位入场、2017年和2021年四个历史起点。优先比较最大回撤、XIRR与保证金事件，再比较期末r，而不是简单把杠杆加满。

Agent：每次读取完整数据哈希、起止交易日和调整价规则；验证信号只消耗严格早于当日的日K。不填造缺失价；新钱不能拯救入金前的保证金不足。如果触发 MARGIN_BREACH，不能用后来价格回升补写有利的清算结果。严禁触发券商交易 API、模拟持仓入账或修改 Capital Accounting Paper Ledger；研究数据与真实连续持仓应分层。

## 验证入口

    cd domains/capital
    PYTHONPATH=src uv run --no-sync python -m pytest -q tests/test_unit_r_dca.py
    cd ../../tools/formal
    mise run verify:formal:unit-r-margin
    mise run verify:formal:unit-r-rebalance

第一个模型预期 2 UNSAT / 1 SAT，第二个模型为 7 UNSAT / 2 SAT。

真实历史只读消费示例：

    cd domains/capital
    PYTHONPATH=src uv run --no-sync python -m ordivon_capital.research.unit_r_dca --source-dir /var/lib/ordivon/capital/research/etf-unit-r-longhistory-20261107 --output /var/lib/ordivon/capital/research/etf-unit-r-longhistory-20261107/results_7pct.json

不将验证成功夸大为历史市场数据真实性证明、未来损失概率证明或发布完成证明。

## 外界成熟理论

- Grossman & Zhou (1993): https://doi.org/10.1111/j.1467-9965.1993.tb00044.x
- Black & Perold (1992): https://doi.org/10.1016/0165-1889(92)90043-E
- Rockafellar & Uryasev (2000): https://doi.org/10.21314/jor.2000.038
- Bailey et al. (2017): https://doi.org/10.21314/JCF.2016.322
- Yahoo 调整价格说明: https://in.help.yahoo.com/kb/adjusted-close-sln28256.html
- 美国 SEC 保证金说明: https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-29
