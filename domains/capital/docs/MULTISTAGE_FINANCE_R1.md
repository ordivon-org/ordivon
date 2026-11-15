# Ordivon Capital / Portfolio — 多期 1r 随机控制的有限情景精化

**证据状态：CONDITIONAL_FINITE_TREE_OPTIMIZATION。** 所有收益概率、资产收益、借贷价格、风险厌恶偏好、交易成本及保证金制度必须由外部明确提供；此模块**不负责预测**，也**不接受实时交易或 Paper Ledger 写入**。它不是 23 年 ETF 历史回放的自动收益升级。历史日线不能自动识别未来条件分布。

本规格与 `ALGEBRAIC_FINANCE_POLICY_R1.md` 共同构成长期目标：从 CRRA/Merton 的单期解析特例出发，到 Bellman 跨期随机控制，再到可真实运行的**有限情景树凸子问题**。

## 1. 经济信息与每月 1r 现金流

一棵树 `\mathcal T=(\mathcal N,\mathcal E)` 中每个非终端节点 `n` 是一个可被参与者观察的信息历史。设 `a_{n,i}≥0` 为资产 `i` 的金额（r），`c_n≥0` 为现金，`b_n≥0` 为债务，`h_{n,i}≥|a_{n,i}-a_{\mathrm{parent},i}G_{\mathrm{parent},n,i}|` 是交易额上界。

场景枝 `e=(n,m)` 给出已经发生的资产总回报因子 `G_{e,i}≥0`、现金 `G^\ell_e>0`、借款 `G^b_e≥G^\ell_e` 和该枝路上的**真实来源**维持保证金系数 `m_{e,i}`，而不是研究者设的随机常数。

每个**非终端月度决策节点**都恰好新增 `1r`；所有终端叶节点均不新增、不得重新交易。这样长短路径终点不会暗含不同的本金；共同终端深度为 `T` 时，路径总外部贡献就是 `Tr`。

到达子节点 `m`、当月新资本到来**之前**的价值：

`W_m^-=\sum_i a_{n,i}G_{e,i}+c_nG^\ell_e-b_nG^b_e`。

先检查 `W_m^-≥\sum_i m_{e,i}a_{n,i}G_{e,i}`，**再**接纳新 `1r` 并执行新决策。每个节点的自融资平衡为：

`\sum_i a_{m,i}+c_m-b_m+ \sum_i k_{m,i}h_{m,i}=W_m^-+1r`

根节点相当于 `W_0^-=0`，并接收初始 `1r`。

初始保证金在所有月度决策节点按其当时的经纪合同计算：

`\sum_i m^{init}_{m,i}a_{m,i}≤\sum_i a_{m,i}+c_m-b_m`。

所有投资本金先按 1r 现金入账，再由自融资恒等式与交易成本抵消。没有事后价格发明、未来资金提前抵押、无效重置、计算中的隐藏入金或自定义强平例外。

## 2. 原始优化目标：跨期非预见 CRRA

叶节点 `\ell` 的概率由树上提供的**条件概率**沿路径相乘：

`p_\ell=\prod_{e\in\mathrm{path}(\ell)}p_e`，每组兄弟节点条件概率和为 1。

有对已观察历史的一个共同决策 `x_n=(a_n,c_n,b_n,h_n)`；对未来未知分支不能定义不同的当前 `x_n`。如果两个子分支有**完全相同的可观察到的收益、融资变化、保证金条件与公开信号**，却被当成两个可提前区别的决策节点，模型拒绝这个信息结构，防止隐含预知。

终点资产以**总回报调整后市值**估值（本模型不假设强制清仓或不存在的税收）：

`W_\ell=\sum_i a_{\mathrm{parent}(\ell),i}G_{\ell,i}
+c_{\mathrm{parent}(\ell)}G^\ell_\ell
-b_{\mathrm{parent}(\ell)}G^b_\ell`。

对 CRRA `u_\gamma(W)=\log W`（`\gamma=1`）或 `(W^{1-\gamma}-1)/(1-\gamma)`（`\gamma>0,\gamma\ne1`），优化：

`\boxed{\max_{x\in\mathcal F}\;\Phi_\gamma(x)=\sum_{\ell}p_\ell u_\gamma(W_\ell(x))}`。

效用系数 `\gamma` 由 Human 真实偏好提供，不从历史最佳回测结果里倒推。若未提供联合场景、概率、融资成本、券商合同或效用，返回 UNKNOWN/INCOMPLETE，不编造股票收益率和最优仓位。

## 2.1 终端负债的经济价值精化（资产负债管理）

将情景 l 的终点账户净权益 W_l 与其确实需要偿付的终端义务
L_l（同单位 r）严格分开，定义可支配余额 S_l=W_l-L_l。

在既有多期树凸优化中，以 sum_l p_l u_gamma(S_l) 作为目标，
并在每一个给定终端情景施加 S_l>0 的 CRRA 定义域约束。
L_l 由经济主体明确输入，不能通过价格日K、历史回撤或固定预算比例发明。
这些合同不改变每月1r的入金时点，不是交易成本，也不是券商认可的抵押品。
未来负债可以随终端状态改变，但状态揭示之前只允许共享一个决策。

代码在 `MultistageProblem` 中提供可选 `terminal_liabilities_r`，
若给出必须包含**全部**终端叶子的非负有限金额；若省略，
保持既有无负债研究行为。若原始全部持现金策略无力偿付，
复用已发布的 HiGHS LP 寻找严格正的终端盈余内点；
没有可行内点则报告 INFEASIBLE，不增加任意风险阈值、杠杆或虚构入金。

可行后沿用 SciPy/SLSQP 求解凹效用，再通过已发布的切超平面
HiGHS 独立计算全局效用值上界（对 `u(W-L)` 而不是 `u(W)`）。
结果分开报告 `terminalR`（总账户权益）、`obligationR`（负债）、
`disposableTerminalR`（可支配盈余）以及相应的期望值和确定性等价。
保留旧 `certainty_equivalent_terminal_r` 字段作为未扣负债的账户
总权益确定性等价；新增 `certainty_equivalent_disposable_r` 专门表示
偿付负债后的可支配财富确定性等价。不允许原字段出现静默语义漂移。
每个终点节点分别报告总财富、真实负债和净盈余。

这是**仅终点负债**的 ALM 有限模型；对投资期限内真实中途支出、收入
不确定性、信用担保、清算价格等，下一阶段必须将它们加入状态转移，
不可把这项功能谎称已求解全部生命周期负债。

成熟理论：Cornuejols & Tütüncü《Optimization Methods in Finance》
第18章 https://doi.org/10.1017/CBO9780511753886.019
及 Desmettre–Wahl–Zagst (2022) surplus optimization
https://doi.org/10.1007/s13385-021-00292-z 。

## 2.2 月度现金义务：区分“入金之后支付”与“入金之前到期”

终点负债不能替代投资期内的真实付款。现有非预见情景树增加
`node_outflow_after_contribution_r`，由经济合同明确给出每个非终端
信息节点 n 的已到期款项 D_n，额度单位依然为 r；没有默认支出额。
本接口严格采用以下时间语义：

市场回报及借款增长 → **先检查已有持仓保证金** →
该月外部 `1r` 实际到账 → 支付当期明确为到账后应付的
`D_n` → 交易费用与自融资再平衡。

因此每个当月决策节点的完整预算为：

    sum_i a_{n,i} + cash_n - debt_n + trade_cost_n
      = W_n^before + 1r - D_n.

这不是通过预设损失百分比决定杠杆，而是账户现金流守恒。
输入必须恰好覆盖全部非终端决策节点，未提供时视为模型**没有**
额外中期支出，而不是隐含已经支付了未输入的真实负债。
如果某个已观察分支的给定应付额不能在真实现金流和约束下
融资，模型返回 INFEASIBLE，绝不发明额外入金。
全部已知合同满足时复用当前 SciPy/HiGHS 的凹效用优化
和独立全局效用上界，原始 `terminal_liabilities_r` 可同时存在。

每个节点输出 `contributionR`、`outflowAfterContributionR`，
以及扣除付款后的 `postTradeEquityR`，方便 Human/Agent 检查
付款是否被误计入收益。

**严格限制**：不能把入金前或月中已经应付的负债挪到这个接口。
提前到期的债务、实际资产出售流动性、券商冻结或强制平仓，
需要更细的经济事件时钟和 Broker 合同消费；现阶段并未实现。
也不能用“未来还有多次1r”充当已经可支配的现金或保证金。

## 3. 为什么它是数学上成熟的凸优化，而非自制求解器

每一笔自融资、成交金额绝对值辅助变量、初始保证金和逐场景维持保证金都可以表达为**仿射等式/不等式**。形成凸可行多面体 `\mathcal F`，在 `W_\ell>0` 的域上：

`u'_\gamma(W)=W^{-\gamma}>0`，
`u''_\gamma(W)=-\gamma W^{-\gamma-1}<0`。

因此，`\Phi_\gamma(x)` 是 `x` 上的凹函数，求 `\max_{x\in\mathcal F}\Phi_\gamma(x)` 是在凸可行集上的凹效用最大化。**不需要通过试错固定 40% 回撤/35% 压力/1.5 倍杠杆来寻找解。**

本地实际能力仅进行**模型专属矩阵构造**；数值优化调用成熟 SciPy/SLSQP，初始解由**全部持现金**的逐节点自融资策略直接构造（无贷款、没有任何预测中的借款额度假定），不是自写黑箱优化算法。

独立的数学数值误差上界：对于数值可行解 `\hat x`，凹函数的切超平面恒有

`\Phi(x^*)≤\Phi(\hat x)+\nabla\Phi(\hat x)^\top(x^*-\hat x)`。

利用成熟 SciPy/HiGHS 线性规划，解

`z^*\in\arg\max_{z\in\mathcal F}\nabla\Phi(\hat x)^\top z`，

因此获得**全局效用值上界**：

`0≤\Phi(x^*)-\Phi(\hat x)
≤\nabla\Phi(\hat x)^\top(z^*-\hat x)`。

实现将这个 `gap` 与原始等式/不等式残差一起输出；仅可声称在所提供有限情景模型中得到数值可行候选及一个数学支持的最优值上界，**不得夸大为独立验证整个实际金融系统或全球无限期 Bellman 解**。

## 4. 这一步真实解决了什么？没解决什么？

- **已实现**：同一个节点只允许一份决策、下月 1r 现金流在下一月才进入、已完成逐枝融资利息与收益复利、按资产区分初始/维持保证金、绝对值换仓成本、CRRA 期末效用、跨多月再配置、独立 LP 全局效用上界。
- **不可在数学上凭空解决**：未来收益分布/状态概率的真实性；未来每月工资是否可靠；其他券商组合保证金非线性；极端非模型情景；真实市场流动性；实际资金交收；无限复杂度 Bellman 的全局优化；个人效用参数唯一识别。
- **真实交易效应**：本模块没有订单、券商下单、持仓落库、PG Paper Close 及正式结算能力。默认不触发任何经济副作用。
- **终端价值**：为最后一个月后的**市值**，不含不存在的末端强制清仓成本。若用户要可兑现税后财富，需明示真实清仓规则和税务状态，不能偷偷把估值视为已清算现金。
- **失效原则**：场景不全、概率和不为 1、来源不可信或数值求解残差过大，严格报告条件不满足；不把长期历史涨幅或合并的分叉误标成可靠预期收益。
- **计算复杂度**：显式随机树随着分叉数及月份数增长迅速膨胀。更长投资期限优先复用正式动态规划、分解法、场景削减、Boyd/Cvxportfolio MPC，不新造一套长期预测平台。

## 5. 已实现消费者接口

源码：`domains/capital/src/ordivon_capital/portfolio/multistage_policy.py`
输入：`MultistageProblem(gamma, nodes)` 和 `InformationNode`（含节点身份、月序、已观察边收益、条件概率、券商保证金及成交成本）。
调用：`solve_multistage(problem)`，无写入副作用。
输出：每个信息节点的风险资产/现金/债务/费用 r、每个终端路径的权益与概率、期望终值 r、CRRA 确定性等价终值 r、现金流笔数、**可行性残差与全局效用上界残差**。

**实际只读消费者，不新建执行平台：**

    cd domains/capital
    PYTHONPATH=src uv run --no-sync python -m ordivon_capital.portfolio.multistage_policy --input /path/to/authoritatively_supplied_tree.json

输入 JSON 顶层必须严格只有 `gamma` 与 `nodes`。每个 nodes 项是
`InformationNode` 的公开字段：`id`、`parent`、`t`、
`conditional_probability`、`risky_gross`、`cash_gross`、
`debt_gross`、`maintenance`、`initial_margin`、
`turnover_cost`、`terminal`、`observed_label`。
利率、概率、保证金与效用**不设政策默认值**；
没有来源核验的数据明确标注为
`CALLER_SUPPLIED_NOT_MARKET_ATTESTED`，经济效果状态明确为
`READ_ONLY_NO_BROKER_NO_PAPER_LEDGER`。
CLI 只写标准输出 JSON，无下单、账户读写、自动市场预测或数据库修改。


源级数学检验：`domains/capital/formal/MultistageOneRCashflowR1.smt2`，Z3 预期 **UNSAT×5、SAT×1**：
- 同根两枝分别新增 1r，正确资金守恒；
- 终端资产收益与借款收益分别进入财富；
- 后到账的 1r 不能追溯性纠正此前的保证金不足；
- SAT 反例显示错误实现若先注资再检查保证金会假阳性放行。

实际消费者验证：`domains/capital/tests/test_multistage_policy.py`，包括一个月时与已发布单期求解器的一致性、两个月现金收益解析基准、可观察分支各自交易、可能全损时拒绝无担保贷款、隐藏分支信息拒绝、债务成本不能凭空套利。

## 6. Human 与 Agent 使用指南

**Human：** 无需提交“你能容忍40%回撤吗”这种伪科学标准表格。明确投资期限、账户是否允许借贷、现金流是否为每月1r、真实不可延期支出/不再接受负债的经济偏好；效用未识别时比较连续风险效用参数族和 Pareto 前沿。不要将模型假定的债务额度当成账户获得的信用授权。过去最小回撤并不意味着未来最优利率/仓位。

**Agent：** 场景必须由 Capital/Markets 已核验来源或显式声明的研究假设供给；每个分支必须有同一市场时钟、可观察信息、价格总回报、现金/借款增长因子、保证金系数、费用及条件概率。每月 1r 入金在风险检查**之后**，所有终端贡献次数一致；主动阻断前视数据、不可观察分叉、未验证数字伪装成市场事实。数字 LP gap 是模型内数值证据，不是资产价格真实性或经济最优预测的外部证明。继续复用 canonical Risk/Portfolio/Research 与现有 Harness，不增加独立平台，也不调用实盘或正式 Paper Ledger。

## 7. 成熟理论来源

- Ruszczyński & Shapiro, *Lectures on Stochastic Programming*, 2009, Chapter 3: information histories and nonanticipativity. https://epubs.siam.org/doi/book/10.1137/1.9780898718751
- Boyd et al., *Multi-Period Trading via Convex Optimization*, 2017: transaction costs, portfolio constraints, MPC. https://stanford.edu/~boyd/papers/cvx_portfolio.html
- Skaf & Boyd, *Multi-Period Portfolio Optimization with Constraints and Transaction Costs*, 2009: dynamic programming approximations. https://stanford.edu/~boyd/papers/dyn_port_opt.html
- Cvxportfolio official MultiPeriodOptimization manual: https://www.cvxportfolio.com/en/stable/optimization_policies.html
- Merton (1969), Samuelson (1969): CRRA / lifetime portfolio decisions.
\n### 鍒拌揪鏃剁偣闆舵潈鐩婄殑缁忔祹鍚堟硶鎬n
鍦ㄦ棤鍊熸涓斾笉娆犵淮鎸佷繚璇侀噾鐨勬儏鏅腑锛屾姇璧勮€呭彲浠ュ皢褰撴湀1r鍏ㄩ儴鐢ㄤ簬
鐪熷疄鏀嚭锛屼娇娆℃湀鏂拌祫閲戝埌璐?*涔嬪墠**鐨勮处鎴锋潈鐩婃伆濂戒负闆躲€俓n瀹冨苟涓嶆槸璐熷€猴紝涔熶笉搴旇鏁板€煎唴鐐规潯浠惰涓哄繀鐒跺己鍒跺钩浠撱€俓n
鎵€鏈変腑闂存湀鑺傜偣鍙姹?W^- >= 0 涓旀弧瓒崇湡瀹炵淮鎸佷繚璇侀噾 W^- >= M銆俓n鍙缁堢 CRRA 鍙敮閰嶄綑棰?W_T-L_T 瑕佹眰涓ユ牸姝ｇ殑鏁堢敤瀹氫箟鍩熴€俓n鍙鐐规悳绱€丼LSQP 鍘熷绾︽潫鍜岀嫭绔?HiGHS 鍒囪秴骞抽潰鏈€浼樺€间笂鐣孿n鍏ㄩ儴閲囩敤鐩稿悓鍙鍩燂紝閬垮厤鑷埗鈥滃畨鍏?epsilon鈥濆彉鎴愮粡娴庤鍒欍€俓n
## PIT-to-Portfolio direct read-only consumer

The existing Research point-in-time joint forecaster now has an opt-in
`--solve` flag, so no Agent needs to create a second JSON bridge or duplicate
the SciPy optimizer. It consumes only published price vintages at the stated
decision time, preserving cross-ETF joint monthly outcomes and explicit
economic input (CRRA gamma, cash/debt rates, cost and broker margins).

Run from `domains/capital`:
    PYTHONPATH=src uv run --no-sync python -m ordivon_capital.research.pit_joint_forecast --input request.json --solve

The old evidence-only request (without --solve) remains backward compatible.
`conditional_allocation` is conditional on `forecast_evidence` and the caller's
economic contract. It is NOT a market-verified optimal policy, not a claimed
real-world probability distribution and never authorizes a live trade.
A future-published vintage cannot change the frozen earlier solution.
The original research experiment review remains responsible for independent
prospective proper-scoring and subsequent economic out-of-sample evidence.


## PIT 鏉′欢姒傜巼鐨勪弗鏍奸厤瀵硅瘉浼紙涓嶆槸鏀剁泭鐜囨楠岋級

Research 宸叉湁 `prequential_energy_evaluation`銆佸鍙橀噺 Energy Score 鍜孿nVariogram Score銆傛柊鍑芥暟 `compare_pit_prequential_forecasts` 鍦?*鐩稿悓鐨?*
淇℃伅鎴鏃堕棿銆佸悓涓€鏈熺粨鏋滀笌鍚庣画璇勪及鏃堕棿涓婏紝瀵筡n`empirical` 涓?`lagged_knn` 杩涜閰嶅锛歕n
    d_t = EnergyScore(candidate_t, realized_t) - EnergyScore(baseline_t, realized_t)

杈撳嚭鍐荤粨棰勬祴鍝堝笇銆侀€愭湀 d_t銆佸潎鍊煎強鐩稿悓鏁版嵁涓婄殑 Variogram
宸銆傛鍊间唬琛ㄥ€欓€夋鐜囬娴嬫崯澶辨洿澶э紝璐熷€间唬琛ㄦ洿灏忋€俓n涓嶅厑璁告贩鐢ㄤ袱妯″瀷涓嶅悓鐨勬牱鏈垨鏈潵鎵嶅彂甯冪殑浠锋牸淇銆俓n
杩欏彧鏄潯浠舵鐜囨ā鍨嬬殑**鎻忚堪鎬?*鏍锋湰澶栬瘉鎹紝涓嶇洿鎺ヤ骇鐢熸姇璧勬敹鐩婏紝
涓嶈嚜琛屽绉扮粺璁℃樉钁椼€傝嫢瑕佹楠岄暱鏈熼娴嬪噯纭€у樊寮傦紝椤婚噰鐢ㄦ垚鐔焅nDiebold鈥揗ariano 鏃跺簭鐩稿叧璇樊鎺ㄦ柇锛涜嫢涓嶆柇灏濊瘯澶氫釜妯″瀷锛岃繕椤籠n浣跨敤鎴愮啛澶氶噸妯″瀷姣旇緝锛堝 Hansen SPA锛夈€傛病鏈夊彲鏍搁獙鐨勮冻澶熸牱鏈琝n鍜屽畬鏁寸爺绌堕娉ㄥ唽锛屼笉缂栭€犱换浣?p 鍊兼垨鏈€浼樻潬鏉嗙粨璁恒€俓n
鐞嗚锛欸neiting鈥揜aftery, Strictly Proper Scoring Rules (2007);
Diebold鈥揗ariano, Comparing Predictive Accuracy (1995);
Hansen, Superior Predictive Ability (2005).


## Broker segment margin and declared liquidation evidence (Risk owner)

The financial truth boundary is the broker's timestamped *account segment*
report plus actual recorded cash, shares, debt and sale fills.
For each broker segment s:

    ExcessLiquidity_s = ProviderRecognizedEquity_s - MaintenanceRequirement_s

For IBKR, securities use equity with loan value (EWL); commodities
use net liquidation value (NLV). Do not sum independent segment cushions
to declare a breached segment safe. A negative difference denotes a
maintenance breach; it is not proof that the broker has already sold.

The canonical Capital/Risk facade exposes two read-only operations:
* `assess_provider_margin_segments`: provider, timestamp and exact per-segment
  observed equity, initial margin and maintenance requirement, allowing
  negative broker equity and no hardcoded house margin or loss limit.
* `replay_declared_long_liquidation`: retrospective same-currency
  long-only share/cash/debt conservation. It consumes explicit share
  quantities, a fixed reference mark, actual fill price/quantity, fee,
  debt repayment, and the actual pre/post broker maintenance requirements.
  It does not decide which assets the broker must sell or when.

For initial quantity q_i, mark p_i, sold share amount s_i, fill price f_i,
cash c, loan b, fee F and debt paydown d, the account transitions obey

    E_before = sum_i(q_i * p_i) + c - b
    c_after  = c + sum_i(s_i * f_i) - F - d
    b_after  = b - d
    E_after  = sum_i((q_i - s_i) * p_i) + c_after - b_after

and exact conservation:

    E_after - E_before = sum_i[s_i * (f_i - p_i)] - F.

Debt repayment does not create equity. Bad fills and fees reduce equity.
Liquidating every share need not eliminate an unpaid loan. Broker post-fill
maintenance must be supplied; do not silently estimate house-margin changes.

Provider-observed margin equity is NOT generally the same as the simplified
marked account equity used in the share-sale calculation. The two are
separate independent evidence layers. If real provider values or fills
are unavailable, return UNKNOWN rather than treating the research
simulation as a live margin account or backdating future 1r deposits.

Formal proof: `mise run //domains/capital:verify:formal:broker-liquidation`.
Z3 checks exact accounting and a counterexample for residual debt, not
live provider code, unpredictable market fills, intraday mark changes,
interest accrual, taxes, collateral segregation or broker order selection.
The Portfolio optimizer's no-margin-breach constraints are not a complete
endogenous liquidation and recovery control process.

External mature references:
- IBKR Excess Liquidity https://www.interactivebrokers.com/campus/glossary-terms/current-excess-liquidity/
- IBKR real-time liquidation https://www.interactivebrokers.co.uk/en/trading/marginRequirements/margin3.php
- LEAN Buying Power https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/buying-power
- LEAN Margin Call https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/margin-calls

## 信息树合同和优化求解的源码边界（2026-11-07）

- **表示与验证 Owner**：`src/ordivon_capital/portfolio/information_tree.py` 的 `InformationNode`、`MultistageProblem`、`validate_information_tree` 是纯 Python 基础 LEGO。它验证有唯一根节点、层级与月度连续性、分支条件概率之和、可观察分支的非预知性、融资/保证金参数、逐节点现金支出和逐叶负债；不依赖 NumPy/SciPy，也不执行优化。
- **求解 Owner**：`src/ordivon_capital/portfolio/multistage_policy.py` 仍是唯一 `solve_multistage` 与 `python -m` 入口；先消费信息树合同，再用锁定的 SciPy SLSQP 和 HiGHS 作有限情景数值优化。当前 Research/PIT 继续使用原有 `multistage_policy.InformationNode/MultistageProblem` 导入；该导入是对同一类型对象的重导出，而非第二套定义。
- **Human**：先识别每个节点的真实可观察信息、每月 1r 入金时间、当期应付负债和提供方融资合同，再选择是否求解。若市场发布时点、概率或券商合同未得到外部验证，不能把语义合同通过误写成真实可投资策略。
- **Agent**：用 `from ordivon_capital.portfolio.information_tree import validate_information_tree` 作无优化器副作用的合同准入，再沿用 `ordivon_capital.portfolio.multistage_policy.solve_multistage`。分别记录合同验证、数值可行性及数值最优性上界；不要将 SciPy 成功、`ValidatedInformationTree` 或任何形式化抽象误报为真实价格/券商资格证据。
- **成熟机制**：标准 PyPA `src/` 分层和 NumPy/SciPy 优化接口；参见 https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/ 和 https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html 。不新建平台、Solver、数据库或 Skill。

## Markets → Research PIT：历史交易日不等于实际可用时间

Finance Research 的 `market_capture_to_pit_vintages` 不新增行情数据库或第二套解析器；它直接调用 Markets 已有的 `historical_close_snapshot.admit_adjusted_close_csv`，验证输入 CSV 原始字节的 SHA-256、列身份、交易日期与价格结构。

**关键时间合同：** 调用者分别提供最后交易日 `last_session`、该交易日真实收盘瞬间 `last_session_close_at`，以及本次文件实际取得瞬间 `captured_at`。两个时间必须有时区；最后收盘瞬间的美东日期应等于 `last_session`，且 `captured_at >= last_session_close_at`。调用者仍必须独立证明交易日历和真实捕获时间；函数不能从今日下载的历史价格推断过去何时发布。

研究对象 `PriceVintage.published_at` 使用本次 `captured_at` 作为**保守的已知时间界限**，不声称它等于供应商最初发布时间。即使 CSV 包含五年前的收盘价，本次下载的整个版本也不能用于 `t < captured_at` 的历史决策。需要严格历史 PIT 回测时，必须取得当时确实归档的不同版本以及对应时间来源证据。

**Human：** 使用先前已有的 Markets CSV 入库合同，提供原始字节、准确 SHA-256、证券列表、首末日与两个独立时间，再用现有 Research `empirical_joint_forecast` 和 `prequential_energy_evaluation` 进行只读研究。调后收盘价不是可执行成交报价，也不能直接等同于真实含分红税费的总回报。

**Agent：** 保存原始文件摘要和 `SECONDARY_VENDOR_NOT_ATTESTED` 状态；数据来源认证、企业行动、分红口径、券商规则和现实经济回报仍是独立的 UNKNOWN。与 `research/prospective_validation` 联合使用时，先按捕获时间决定可见信息，再检查冻结实验之后的日历候选，不得用历史回填日期代替真实捕获。

参考：ALFRED 对 historical vintages 的区分，OpenBB 的 unadjusted / splits_only / splits_and_dividends 价格口径，以及 NYSE 官方交易时段与提前收市日历。
