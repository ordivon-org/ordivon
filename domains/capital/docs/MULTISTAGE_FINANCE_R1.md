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
