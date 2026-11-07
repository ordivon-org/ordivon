# Ordivon Capital｜1r 代数化投资控制与经济学优化规格 R1

> **数学规格及有限情景求解，不是投资建议、数据商预测、实盘交易、前瞻纸面盘或保证金永不触发的证明。**
> 本规格取代把 40% 回撤、历史最大跌幅加固定百分点、1.5×杠杆、固定利率、固定移动窗口当成普适金融定律的做法。早期 `unit_r_dca.py` 仅保留为明确假设的历史实验消费者，**不拥有统一风险模型的语义定义权**。

## 1. 核心数学结论：不存在仅由日K决定的唯一最优杠杆

有限历史日K `{P_t}` 仅是观察样本，它不包含唯一的未来条件概率分布 `Q_t`、融资利率 `r^b_t`、投资者效用 `u`、未来支出负债 `L^h_t` 或券商真实保证金制度 `M_t`。

因此，不存在一个对所有投资者和未来市场都成立的常数或函数 `leverage=f(MDD)`。最优投资是**条件性的**：给定偏好与可行性以后求解；参数仍未知时输出符号解族或风险—效用 Pareto 前沿。**禁止填入主观“安全”数字来制造唯一答案。**

这是一项可证明的不可识别性：相同的历史价格路径、不同的未来风险溢价或融资利率，可以给出相反的最优借款决策。

## 2. Financial State 与单位 1r

设月度贡献时点集合为 `\mathcal M`，每期新增本金 `f_t=\mathbf 1_{\{t\in\mathcal M\}}\cdot 1r`。这里 r 是可缩放资本单位，不是人民币或收益率。

状态 `S_t=(q_t,P_t,C_t,B_t,N_t,U_t,H_t,Z_t,\mathcal M_t)`，其中 q 是各 ETF 综合持仓单位、P 是相应价格、C 是现金、B 是融资本金与应计费用、Z 是观测市场状态与信贷条件，`\mathcal M_t` 是真实券商保证金规则。

账户净财富与交易后自融资恒等式：

`W_t=q_t^{\top}P_t+C_t-B_t`

`\sum_i a_{i,t}+C_t-B_t+K_t(\Delta a_t)=W_t^-+f_t`

其中 `a_i` 是风险资产美元等价值，以 r 为记账单位；`K` 是来自提供方或经过验证的交易成本函数，不允许假定为普适固定费率。

单位净值的新增本金会计：若期初有 `N_t` 个账户单位、每单位 `U_t>0`，注入 `f_t` 后新增份额 `\Delta N_t=f_t/U_t`，因此 `U_t^+=U_t^-`。新增本金不能构成当期投资收益。若需度量历史峰值回撤，使用这个不含入金的 `U_t`，不是日益变大的累计出资账户权益。

下一期在给定场景 `\omega` 的价值：

`W_{t+1}^-(\omega)=\sum_i a_{i,t}G_{i,t+1}(\omega)+C_tG^l_{t+1}(\omega)-B_tG^b_{t+1}(\omega)`

其中 `G_i=1+R_i`；现金和融资的复利增长因子均由相应行情/券商提供，**不设置普适固定融资利率**。交易成本在当期自融资式中已扣，不应二次扣除。

## 3. 真正的跨期优化：Bellman / Stochastic Control

投资期限 `T`、投资者风险偏好 `\gamma`、真实月度投入序列 `f_t=1r`、可用投资品种、未来负债以及外部资金的可质押性均为问题输入。

采用成熟 CRRA/isoelastic 效用族，而不是固定的“最大40%回撤”：

`u_\gamma(W)=\log W`（`\gamma=1`），否则
`u_\gamma(W)=\frac{W^{1-\gamma}-1}{1-\gamma}`，`\gamma>0, W>0`。

当条件未来收益分布已定义时：

`\pi^*=\arg\max_{\pi\in\mathcal A}\mathbb E_{Q}\left[u_\gamma(W_T^\pi)\mid\mathcal F_0\right]`

状态递推为：

`V_t(S_t)=\sup_{\pi_t\in\mathcal A_t(S_t)}\mathbb E_{Q_t}\left[V_{t+1}(S_{t+1})\mid S_t\right]`，
`V_T(S_T)=u_\gamma(W_T)`。

若市场分布存在可独立证实的不确定集合 `\mathfrak P_t`，可将条件期望替换为 `\inf_{Q\in\mathfrak P_t}\mathbb E_Q[\cdot]`。**集合必须有数据和检验来源，不能随意引入 Wasserstein 半径来证明稳健。**

这是完整的跨期问题规格；仓位随市场信号、融资制度和未完成定投期数内生变化。下面的 SciPy 单期求解器只是其中一个可证明凹性/凸可行域的计算子问题，**不能冒充整个 Bellman 系统已经被全局求解**。

## 4. Merton 理论给出的解析杠杆，而不是人为阈值

单资产理想化连续扩散：预期收益率 `\mu`，收益方差率 `\sigma^2>0`，可存入利率 `r_l`，借款利率 `r_b\ge r_l`，CRRA 系数 `\gamma>0`。

在无交易摩擦、无其他仓位约束、系数恒定时：

`L_\ell=(\mu-r_l)/(\gamma\sigma^2)`，
`L_b=(\mu-r_b)/(\gamma\sigma^2)`。

**允许持有现金、禁止卖空**的解析解：

`L^*=\begin{cases}
\max(0,L_\ell),&L_\ell\le1\\
1,&L_\ell>1\;\land\;L_b<1\\
L_b,&L_b\ge1.
\end{cases}`

这里的“1”是百分之百自有净资产的财务定义，不是人为设定的杠杆上限。实际可行解仍要加入券商初始/维持保证金、离散再平衡、交易成本和跳跃风险，且规则切换会破坏这个闭式解。

例如即便资产波动率较低，只要 `\mu\le r_b` 或 `\gamma\sigma^2` 足够大，也未必应当借款。不能由 `MDD_i<MDD_j` 推出 `L_i^*>L_j^*`。

## 5. 真实券商可行性：作为硬约束，而不是效用假设

对每种资产 `i` 从实际提供方读取**初始**保证金系数 `m^{0}_{i,t}`，以及各风险情景 `\omega` 的**维持**要求 `m^{maint}_{i,t+1}(\omega)`。

当期股权交易后 `W_t^+=W_t^-+f_t-K_t(\Delta a_t)`，应满足：

`\sum_i m^0_{i,t}\,a_{i,t}\le W_t^+`

给定未来价格/流动性/保证金变动的情景，还要检查：

`W_{t+1}^-(\omega)\ge\sum_i m^{maint}_{i,t+1}(\omega)\,a_{i,t}G_i(\omega)`。

如果真实券商要求更复杂的集中度、组合保证金或阶梯型规则，就必须直接使用它的准入函数，不能用简化线性模型替代真实规则。

**没有无条件“永不强平”的杠杆公式。** 若模型允许持有资产完全归零，且没有可兑现现金或外部担保，对任何正负债 `B_t>0`，最坏状态下一定有 `W_{t+1}^-<0`。因此不存在在这些假设下还能保证绝不强平的非零借款仓位。

数学模型能提供的是：在被明确接受、可核验的结果集合内保证合同可行；或在经过校准的随机模型下估计损失概率，不能将历史有限样本冒充无限未来证明。

## 6. 可实际求解的单期有限场景凸模型

令归一化的现有净权益为 `1r`，风险资产 `w_i\ge0`，现金 `c\ge0`，借款 `b\ge0`，已有仓位 `w_i^{old}`，交易额辅助变量 `h_i\ge|w_i-w_i^{old}|`，提供方成本率 `k_i\ge0`。

**资金预算：**

`\sum_i w_i+c-b+\sum_i k_i h_i=1`。

`s` 情景下净权益：

`W_s=\sum_i w_iG_{i,s}+cG_{\ell,s}-bG_{b,s}`。

输入有条件概率 `p_s>0,\sum_s p_s=1`、风险偏好 `\gamma`、券商系数 `m^0_i`、`m^{maint}_{i,s}` 和上述真实费用，求：

`\max_{w,c,b,h}\sum_s p_s u_\gamma(W_s)`

满足：

`\sum_i m_i^0w_i+\sum_i k_i h_i\le1`，

`W_s-\sum_i m^{maint}_{i,s}w_iG_{i,s}\ge0\quad\forall s`，

`W_s>0,\quad w,c,b,h\ge0`。

因为 `u_\gamma` 对正财富严格凹，`W_s` 是控制变量的仿射函数，且约束线性，故这是**凹效用最大化的凸可行优化问题**。具体实现用本地已有 SciPy HiGHS/SLSQP 数值求解，输出敞口、现金、债务、费用、情景权益和原始约束残差。它不会生成交易订单或写 Paper Ledger。

概率分布 `p_s`、利率、保证金要求或 `\gamma` 缺失时**不应该生成唯一优化建议**；系统必须报告输入未识别。有限场景数值可行也不证明场景之外安全。

## 7. “回撤”退回为被测量的风险结果，而不是强加的数字

定义不含入金的单位净值 `U_t`，历史最高 `H_t=\max_{s\le t}U_s`，实际回撤过程 `D_t=1-U_t/H_t`。

在不给定投资者损失容忍度时，不设置 `D_t\le40\%` 或其他自行指定的硬阈值。

应计算并展示整组不被支配的投资政策：

`\mathcal E=\mathrm{Pareto}\big(\mathbb E[u_\gamma(W_T)],\mathrm{CDaR}_{\alpha}(D),\Pr(\tau_{\mathrm{margin}}\le T),\mathrm{Cost}\big)`。

`\alpha` 也是 CDaR 统计定义中的分位参数，并非默认某个百分比。参数空间是需说明偏好/模型假设的连续变量；不必人为截断为几个候选数。不能仅从可用历史日K推导这些预期/概率量。

若需要唯一政策，必须由投资者真实偏好、未来确定性支出及券商规则等外生信息打破 Pareto 前沿上政策之间的偏序关系；缺乏这些信息时应输出不可比较的政策族。

## 8. 核心数学性质与证据

源级规格 → Z3 抽象数学等价 → Python/SciPy 数值精化及严格可行性读回 → 市场条件分布/券商合同真实性 → 跨期历史消费者 → 后续独立前瞻验证。

`AlgebraicCapitalR1.smt2` 证明：
1. 任意两资产与比例交易费的 `1r` 自融资/损益守恒；
2. 任意资产维持保证金合成恒等式；
3. 新入金仅增加账户份额、不改变单位净值；
4. 在资产预期增长不超过现金收益且风险厌恶为正时，扩散模型的正向最优风险敞口导数不可能为正；
5. 当所有风险资产可全损且存在借款/无现金时，无法保证每种状态均不触发资本亏空；
6. 构造非空真实违规模型反例。

Z3 证明的**实数抽象规格**不等于对 SciPy、Python 浮点、数据库或券商规则的通用证明。

## 9. 对 Human 与 Agent 的分离指导

### Human

- 明确投资期限、固定每月 `1r` 现金流及未来必须支付的负债。
- 若没有确定的风险效用参数 `\gamma`，先比较整条**有效前沿**，通过真实损失承受能力/无差异选择识别偏好，不要求人凭空填写百分比。
- 现金投资、满仓、允许融资必须在同一个样本信息时点及同一成本/制度下比较；别把“过去最大回撤小”当作唯一适合加杠杆的依据。
- 区分长期确定性收入的现值与券商可质押担保：未来每月 `1r` 不是今天可用于强平时即时补仓的现金。

### Agent

- 不再把既有 `unit_r_dca.py` 里的 40%、35%、固定利率和手动压力倍率解释为 canonical 策略。
- 调用 `merton_single_risky_crra` 之前，必须说明扩散假设、`\mu,\sigma^2,\gamma,r_l,r_b` 的真实来源；这是无限期连续模型的解析基线，不是可交易指令。
- 调用 `solve_one_period` 前，提供完整的 `Scenario` 联合收益/概率/维持保证金以及 `OnePeriodProblem` 的成本、旧仓位与 `\gamma`；不得用完整五年结果挑选未来时点的概率。
- 只读 Research，不直接调 Broker / Trading / Accounting 的带副作用接口。Missing evidence → UNKNOWN；no admissible portfolio → INFEASIBLE；数值残差与真实经济证明严格分离。
- 多期策略须继续使用成熟 Boyd/Cvxportfolio 的 model-predictive control、标准随机动态规划或已验收的 Ordivon 多期算法组合；不得把单期 SciPy 结果冒充全球最优跨期投资。
- 对代表性反例验证而不是无止境创建特化测试；真正交易商/市场提供方的副作用必须由实际消费者验证。

## 10. 对应成熟文献和能力复用

- Merton 1969：Lifetime Portfolio Selection under Uncertainty（跨期随机控制、CRRA 解）。
- Samuelson 1969：Lifetime Portfolio Selection by Dynamic Stochastic Programming。
- Grossman–Zhou 1993：Drawdown-constrained optimal investment（其 `\alpha` 是**外生偏好**，不是论文内生的最优 40%）。
- Rockafellar–Uryasev 2000：CVaR via convex optimization。
- Busseti–Ryu–Boyd 2016：Risk-Constrained Kelly（风险参数来自偏好，非任意固定概率）。
- Boyd et al. 2017：Multi-Period Trading via Convex Optimization；在投资中复用成熟数值优化/模型预测控制方法。
- Chekhlov–Uryasev–Zabarankin 2005：Conditional Drawdown-at-Risk，多场景回撤风险度量。

链接：
- https://web.stanford.edu/~boyd/papers/cvx_portfolio.html
- https://web.stanford.edu/~boyd/papers/kelly.html
- https://www.math.columbia.edu/~chekhlov/ChekhlovUryasevZabarankin--03-2004.pdf
- https://www.sfu.ca/~kkasa/Merton_69.pdf
- https://onlinelibrary.wiley.com/doi/10.1111/j.1467-9965.1993.tb00044.x
