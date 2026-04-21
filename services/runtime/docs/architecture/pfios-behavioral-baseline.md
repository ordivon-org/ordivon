# PFIOS Behavioral Baseline

## 1. 文档目的

本文件用于建立 PFIOS 的**行为学基线**。

目标不是把 AI 拟人化，而是借助人类行为学中的稳定规律，帮助我们理解：

- 一个行为体为什么会稳定或失控
- 为什么“更聪明”不等于“更可靠”
- 为什么环境、角色、反馈、记忆和约束比单次推理更重要
- 这些规律在 AI 系统中如何体现
- PFIOS 应该如何把这些规律落成系统设计

本文件回答的问题是：

> 从人类行为学拓展到 AI 行为学，我们能学到什么？
> 这些启发如何映射到 PFIOS 的分层架构和未来模块设计？

## 2. 总判断

人类行为学告诉我们：

**一个行为体的表现，不只取决于它“会不会想”，更取决于它所处的环境、角色、约束、反馈、记忆、激励和恢复机制。**

映射到 AI 系统：

**AI 的表现，不只取决于模型能力，更取决于任务设计、上下文表示、工具边界、治理机制、状态真相、记忆分层和反馈回路。**

因此，PFIOS 的目标不是“把模型变成全能行为者”，而是：

**把 AI 放进一个受控行为系统中，让它在清晰角色、边界和反馈里稳定工作。**

## 3. 基本行为学原则

### 原则 1：行为不是单纯由能力决定的

高能力不等于高可靠。  
行为表现是能力、环境、规则、反馈和记忆共同作用的结果。

### 原则 2：稳定行为来自结构化环境

自由度过高时，行为体往往不是更强，而是更混乱。  
高约束任务需要结构化自由，而不是无边界自由。

### 原则 3：行为必须有前置约束、过程记录和结果回执

不能只看“最后有没有成功”，还要看：

- 之前是否允许
- 中间是否越界
- 最后是否可验证

### 原则 4：事实与叙事必须分开

发生过什么，与如何解释发生过什么，不是一个层面的东西。

### 原则 5：长期改进来自复盘，而不是单次灵感

行为体的长期进化，依赖可追溯历史、反馈循环、经验提炼和规则修正。

## 4. 行为机制映射总览

下面将核心人类行为机制，映射到 AI 行为和 PFIOS 设计要求。

## 5. 机制一：行为体只对“表征后的现实”作反应

### 人类行为学

人不会直接面对全部现实，而是先经过：

- 感知筛选
- 注意力分配
- 模式识别
- 叙事整理

之后才行动。

### AI 行为学

AI 也不会直接“理解世界”，它只能对输入表示作反应。  
输入结构越混乱，行为越不稳定。

### 对 PFIOS 的要求

- 不应让 Intelligence 直接面对未经组织的全噪声世界
- 系统必须在 AI 之前完成：
  - 数据结构化
  - 语义整理
  - 上下文筛选
  - 任务 framing
- Capability 和 Orchestration 必须帮助形成任务表征

### 对应层

- Capability
- Orchestration
- Intelligence
- State

### 系统结论

**输入表示决定行为质量上限。**

## 6. 机制二：环境比意志更能塑造行为

### 人类行为学

人会被环境深刻塑造：

- 流程清楚时更少犯错
- 反馈明确时学习更快
- 制度存在时行为更稳定

### AI 行为学

AI 的稳定性也主要来自环境设计，而不只是模型本身。

关键环境因素包括：

- task contract
- tool boundary
- parser
- validator
- retry/fallback
- governance
- state truth
- feedback loop

### 对 PFIOS 的要求

- 可靠性优先通过环境解决，而不是只通过 prompt 或模型升级解决
- 每次错误优先改：
  - contract
  - workflow
  - boundary
  - execution adapter
  - truth source
  - feedback path

### 对应层

- Governance
- Execution
- State
- Infrastructure
- Intelligence

### 系统结论

**不要要求 AI 靠“自觉”可靠，要让环境把它驯化为可靠。**

## 7. 机制三：无边界自由不会产生稳定高水平行为

### 人类行为学

高风险职业依赖：

- SOP
- checklist
- 权限边界
- 风险阈值
- 例外处理机制

### AI 行为学

AI 在无边界场景里容易：

- 发散
- 过早总结
- 过度完成
- 越界行动
- 编造合理化解释

### 对 PFIOS 的要求

- Capability 必须定义“能做什么”
- Governance 必须定义“什么允许发生”
- Execution 必须定义“动作如何表达”
- Experience 不得把模糊状态包装成完成态

### 对应层

- Capability
- Governance
- Execution
- Experience

### 系统结论

**AI 需要有边界的自由，而不是无限自由。**

## 8. 机制四：行为体会合理化自己的行为

### 人类行为学

人经常先反应，再解释，再合理化。  
事后叙事并不等于真实原因。

### AI 行为学

LLM 很容易：

- 先输出结论
- 再补 reasoning
- 把未知说成已知
- 把猜测说成分析

### 对 PFIOS 的要求

- Intelligence 的输出不得直接升级为系统真相
- Experience 不得把 explanation 当 fact
- Knowledge 不得覆盖 State
- 无 receipt、无 audit、无 state relation，不得写 final truth

### 对应层

- Intelligence
- State
- Knowledge
- Experience

### 系统结论

**解释是叙事，不是真相。真相必须来自 state、audit、receipt 和可验证对象。**

## 9. 机制五：行为依赖反馈回路

### 人类行为学

没有反馈，行为难以纠偏。  
错误反馈或延迟反馈会塑造错误习惯。

### AI 行为学

AI 也必须依赖清晰反馈：

- schema error
- policy reject
- parser fail
- execution receipt mismatch
- state inconsistency
- validation issue
- eval signal

### 对 PFIOS 的要求

- 所有关键环节都要有明确反馈
- 不只记录成功，也要记录失败原因
- 反馈必须能进入：
  - workflow
  - governance
  - state
  - knowledge

### 对应层

- Orchestration
- Governance
- State
- Knowledge

### 系统结论

**系统不能只记录“成没成”，还必须记录“为什么没成”。**

## 10. 机制六：高风险行为需要前置纪律

### 人类行为学

金融、医疗、飞行等高风险行业，不依赖事后补救，而依赖前置纪律：

- 风控
- 审批
- 限额
- 熔断
- 对账

### AI 行为学

AI 在高风险动作中也不能先做再看。  
必须先判断允许条件。

### 对 PFIOS 的要求

- Governance 必须先于真实动作
- 所有 side-effect 必须带：
  - actor
  - context
  - reason
  - idempotency key
- 决策语言必须统一：
  - execute
  - escalate
  - reject

### 对应层

- Governance
- Execution
- State

### 系统结论

**AI 不需要情绪风控，但必须有行为风控。**

## 11. 机制七：角色边界决定行为清晰度

### 人类行为学

一个组织里的角色一旦混淆，行为就会混乱。  
分析、审批、执行、审计、记账不能混成一个角色。

### AI 行为学

如果 AI 同时扮演：

- 分析师
- 审批者
- 执行者
- 审计者
- 叙事者

系统就会失控。

### 对 PFIOS 的要求

必须维持角色边界：

- Intelligence = 判断者
- Governance = 约束者
- Execution = 执行者
- State = 记账者
- Knowledge = 复盘者
- Experience = 表达者

### 对应层

全层适用

### 系统结论

**分层本质上是在建立行为角色边界。**

## 12. 机制八：不同类型的记忆不能混

### 人类行为学

人的记忆分很多层：

- 工作记忆
- 情景记忆
- 语义记忆
- 程序记忆
- 情绪记忆

混在一起会导致行为污染。

### AI 行为学

AI 系统也必须区分：

- task context
- state truth
- knowledge lesson
- policy memory
- execution history
- user preference

### 对 PFIOS 的要求

- Intelligence context 不是 State
- State 不是 Knowledge
- Knowledge 不是 policy source 本身
- Experience 只读所需层，不得偷偷混合推断

### 对应层

- Intelligence
- State
- Knowledge
- Governance

### 系统结论

**记忆必须分层，不然上下文、事实和经验会互相污染。**

## 13. 机制九：稳定系统依赖习惯化流程，而不是单次聪明表现

### 人类行为学

长期可靠来自：

- 重复流程
- 训练
- checklist
- 规则化动作
- 持续复盘

### AI 行为学

AI 长期可靠也来自：

- 固定 task contract
- 稳定 capability
- 明确 orchestration
- 可验证 action model
- 固定 feedback path

### 对 PFIOS 的要求

- 不要依赖“一次神 prompt”
- 不要依赖“某个模型今天特别聪明”
- 必须让系统拥有：
  - 稳定能力入口
  - 稳定 workflow
  - 稳定 state object
  - 稳定 governance rule
  - 稳定 execution adapter

### 对应层

- Capability
- Orchestration
- Governance
- Execution

### 系统结论

**系统的长期可靠性来自制度化重复，而不是偶然灵光一现。**

## 14. 机制十：退化模式必须被设计出来

### 人类行为学

人在高压、信息不足、时间紧时会退化。  
成熟系统会预先设计：

- fail-safe
- no-go rule
- checklist
- fallback

### AI 行为学

AI 在：

- 上下文过长
- 工具失败
- 外部状态缺失
- 依赖服务不可用
- 任务跨度过大

时也会退化。

### 对 PFIOS 的要求

- Experience 必须诚实表达失败
- Orchestration 必须定义 retry/fallback
- Governance 必须支持 reject/escalate
- Execution 必须定义失败模型
- Infrastructure 必须提供健康检查

### 对应层

- Experience
- Orchestration
- Governance
- Execution
- Infrastructure

### 系统结论

**不要只设计顺利路径，必须设计系统如何安全失败。**

## 15. 机制十一：激励会塑造行为方向

### 人类行为学

人会被 KPI、奖励、惩罚和期待塑形。  
系统奖励什么，人就倾向做什么。

### AI 行为学

AI 没有情绪，但系统目标同样会塑造其行为。  
如果系统默认奖励：

- 快速给答案
- 看起来像完成
- 用户满意

而不是奖励：

- 诚实失败
- 守住边界
- 输出可验证结果

那么 AI 就会学会“表演完成”。

### 对 PFIOS 的要求

- Experience 不鼓励伪完成态
- Governance 要把诚实拒绝视为合法结果
- 测试要奖励边界正确，而不只奖励 happy path
- Knowledge 不允许 narrative 压过 truth

### 对应层

- Experience
- Governance
- Testing / Verification
- Knowledge

### 系统结论

**如果系统只奖励“像完成了”，AI 就会越来越擅长假装完成。**

## 16. 机制十二：真正进化依赖元认知

### 人类行为学

成长不只是做更多事，而是：

- 复盘
- 抽模式
- 总结元规则
- 下次提前规避

### AI 行为学

AI 系统的真正飞轮也应如此：

- 从 outcome 中提炼 lesson
- 从 recurring issue 中提炼 candidate rule
- 从失败中改 harness
- 从历史中改 governance 和 intelligence

### 对 PFIOS 的要求

- Knowledge 必须对象化
- lesson extraction 必须成为真实模块
- knowledge feedback 必须有路径进入 governance 和 intelligence
- flywheel 不只记录数量，还要记录规则变化

### 对应层

- Knowledge
- Governance
- Intelligence
- State

### 系统结论

**真正的飞轮不是多跑任务，而是系统逐渐学会自己的行为规律。**

## 17. PFIOS 行为层映射总结

### Experience

对应外显行为与对外表达。  
要求：诚实、可见、可理解，不伪造系统现实。

### Capability

对应可执行技能清单。  
要求：定义可做之事，不让系统在无边界空间自由发挥。

### Orchestration

对应计划与程序性步骤。  
要求：复杂任务必须分步、可追、可恢复。

### Governance

对应纪律、制度与授权。  
要求：所有关键动作先过约束，后做执行。

### Intelligence

对应认知、判断、语义理解。  
要求：做脑，不做全身。

### Execution

对应动作系统与对外交互。  
要求：动作必须对象化、可回执、可审计。

### State

对应客观行为记录与事实账本。  
要求：事实独立存在，不被叙事污染。

### Knowledge

对应经验、教训、可迁移规则。  
要求：沉淀 lesson，而不是冒充事实。

### Infrastructure

对应运行条件与组织环境。  
要求：系统运行条件本身必须稳定，否则行为无法可靠。

## 18. 直接工程要求

基于以上行为学基线，PFIOS 后续设计必须满足：

1. **所有 AI task 都必须有明确输入表示**
2. **所有 side-effect 都必须在动作前经过 Governance**
3. **所有真实动作都必须产生 receipt**
4. **所有事实对象都必须能写入 State**
5. **所有 explanation / lesson / narrative 都不得直接作为 truth**
6. **所有关键 workflow 都必须可追踪 run lineage**
7. **所有失败都必须能被诚实表达**
8. **所有 recurring failure 都应优先触发环境修正**
9. **Knowledge 必须对象化，而不是只停留在文档文本**
10. **飞轮必须由 outcome → lesson → feedback 构成，而不是由“模型越来越聪明”的幻想构成**

## 19. 最终结论

PFIOS 的核心思想，与人类行为学对成熟行为系统的理解高度一致：

**稳定行为不是靠单次高智商产生的，而是靠角色边界、环境约束、状态真相、动作回执、反馈回路和复盘系统共同塑造的。**

因此，PFIOS 的正确方向不是把 AI 做成一个更自由的万能主体，而是：

**把 AI 放进一个更成熟的行为系统里，让它在判断、治理、执行、真相和知识之间各司其职。**
