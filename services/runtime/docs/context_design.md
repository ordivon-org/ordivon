# PFIOS 上下文分层设计 (Context Substrate Design v1.0)

本设计定义了推理引擎输入数据的分层标准，旨在通过高密度的认知感应点，消除 AI 的“真空幻觉”。

## 1. 五层上下文模型 (The 5-Layer Model)

### A. 查询层 (Query Context)
- **目标**：锁定当前分析的“原子任务”。
- **字段**：`user_query`, `symbol`, `timeframe`, `analysis_goal` (如 "breakout_validation")。
- **约束**：不允许模糊的全局性提问。

### B. 市场层 (Market Context)
- **目标**：提供当前行情事实与宏观 Regime。
- **核心组件**：
    - **Price Summary**: OHLCV 状态与近期波动范围。
    - **Regime Hint**: 当前市场性质 (Bull/Bear/Sideways, High/Low Vol)。
    - **Event Context**: 即将发生的宏观事件或最近重大新闻摘要。
    - **Physical Sensations**: 压缩后的最近 10 条 `observations`。

### C. 组合层 (Portfolio Context)
- **目标**：建立“利益相关”感。
- **字段**：`has_existing_position`, `current_exposure_pct`, `unrealized_pnl_state`, `portfolio_risk_level`。
- **原则**：只提供与当前标的相关联的风险敞口，不暴露全量隐私账本。

### D. 记忆层 (Memory Context)
- **目标**：基于历史教训进行关联。
- **源数据**：`ai_reviews` (仅限同标的或同策略)。
- **逻辑**：仅提取 1) 最相似的一条历史案例，2) 最近一次失败教训，3) 相关的经验法则 (Rule of Thumb)。

### E. 治理提示层 (Governance Hint Context)
- **目标**：提醒模型系统性格（而非命令其执行规则）。
- **包含内容**：
    - **行为风格**：平衡分析、保守倾向。
    - **防范清单**：不得过度推测、不得在证据冲突时强给大模型方向。

## 2. 数据密度与性能 (Density & Performance)
- **总长度限制**：必须控制在推理底座上下文窗口的 30% 以内，预留 70% 空间给模型思考。
- **刷新频率**：随 Orchestrator 启动实时构建。

---
*Status: Approved for Step 8.3 Implementation*
