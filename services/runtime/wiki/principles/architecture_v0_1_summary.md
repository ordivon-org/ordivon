# PFIOS 总体设计规范 v0.1 - 核心架构总结

## 1. 系统愿景 (The Vision)
PFIOS 是一个**治理驱动型**的个人金融智能操作系统。它的核心价值在于将 AI 的智力（Reasoning）置于严格的人类原则约束（Governance）之下，并将其产生的每一项成果转化为长期知识资产（Knowledge）。

## 2. 核心闭环 (OODA-L Loop)
系统运转遵循以下完整闭环：
- **Observe (观测)**：通过 Ingestion 技能获取市场与账户原始数据。
- **Analyze (分析)**：Reasoning 层进行深度结构化思考。
- **Govern (治理)**：Risk Engine 基于 Constitution（宪法）执行准入过滤。
- **Express (表达)**：Report Builder 将结论转化为人类可读的报告。
- **Persist (持久化)**：Object Service 将结果存入 DB 与 Wiki。
- **Review (复盘)**：通过 Performance Engine 定期评估决策效果。
- **Learn (学习)**：将复盘结论沉淀为新的原则或技能，实现自我进化。

## 3. 分层架构规范 (Layered Architecture)

| 层级 | 名称 | 核心职责 |
| :--- | :--- | :--- |
| **L1** | **Interface** | Web Dashboard / API 入口 |
| **L2** | **Orchestration** | 工作流逻辑控制、上下文聚合 |
| **L3** | **Reasoning** | 解耦的 AI 推理能力 (Hermes/OpenAI) |
| **L4** | **Governance** | 原则执行、安全性审计 (ALLOW/WARN/BLOCK) |
| **L5** | **Expression** | 报告模版渲染、Markdown 生成 |
| **L6** | **Object & Knowledge** | 结构化对象存储 (DB) 与 知识百科 (Wiki) |
| **L7** | **Core** | 系统配置、数据库底层、日志 |

## 4. 核心设计原则 (Design Principles)
- **推理与治理分离**：AI 可以“异想天开”，但治理层必须“守口如瓶”。
- **表达与持久化解耦**：怎么说（报告）和怎么存（对象）是两个独立的逻辑。
- **知识与技能并重**：Wiki 存储静态经验，Skills 定义动态能力。
- **系统权威性**：所有外部 Agent 的中间态均不可信，系统最终真相必须源于 PFIOS 的审计轨迹。
