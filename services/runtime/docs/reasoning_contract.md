# PFIOS 推理契约 (Reasoning Module Contract v1.0)

本契约定义了 PFIOS (Personal Financial Intelligence Operating System) 推理层的核心交付标准与行为边界。

## 1. 核心定位 (Core Positioning)
推理层是 PFIOS 的“投研智力子系统”，其职责是基于结构化的事实输出严谨、平衡的金融判断。
- **它不是最终决策者**：决策由治理层 (Governance Layer/RiskEngine) 负责。
- **它不是执行者**：执行由业务层/集成层负责。
- **它必须是可观测的**：所有推理路径必须可被治理与审计。

## 2. 行为准则 (Guiding Principles)
1. **证据平衡 (Evidence Balance)**：任何推断必须同时审视正向支持证据 (Evidence For) 与反向风险因素 (Evidence Against)。
2. **保守主义偏好 (Conservative Bias)**：在信息不完整或证据冲突时，模型必须显式降低置信度 (Confidence)，并优先建议“观察 (Observe)”或“规避 (Avoid)”。
3. **结构统一性 (Structural Consistency)**：输出必须严格遵守定义的 JSON Schema，禁止自由发挥。

## 3. 输出数据契约 (Data Contract)
推理层返回的 `ReasoningResult` 必须包含：
- `thesis`: 包含核心论点、发现集及量化的置信度。
- `action_plan`: 包含建议动作、仓位建议、止损/止盈阈值及“失效条件”。
- `risk_flags`: 对本次建议涉及的关键风险进行标签化描述。
- `next_steps`: 具体的后续跟踪步骤。

## 4. 故障分层与处理 (Error Layering)
- **Invocation Failure**: 基础设施层调用失败（超时、环境错误），系统抛出 `ReasoningInvocationError`。
- **Parse Failure**: 输出结构损坏，系统抛出 `ReasoningParseError` 并记录失败样本。
- **Cognitive Failure**: 内容合法但逻辑薄弱或过激。此类“失败”由 RiskEngine 通过评分与拦截机制处理，并在评估框架中扣分。

---
*Status: Established as of 2026-04-17*
