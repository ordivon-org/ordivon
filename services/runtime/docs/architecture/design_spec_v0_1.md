# PFIOS（Personal Financial Intelligence Operating System）总体设计说明书 v0.1

## 一、系统总目标

PFIOS 的目标是建立一个围绕个人金融判断、风险控制、执行记录、复盘沉淀、长期知识积累而运转的智能操作系统。其核心闭环为：
`Observe → Analyze → Govern → Express → Persist → Review → Learn`

## 二、顶层架构

1.  **Interface Layer** (界面层): Web / Dashboard
2.  **API Layer** (接口层): FastAPI / v1 Routes
3.  **Orchestration Layer** (编排层): Engine / Router / Context
4.  **Reasoning Layer** (推理层): LLM / Agent Runtime (Hermes)
5.  **Governance Layer** (治理层): Rules / Validators / Audit
6.  **Expression Layer** (表达层): Report Builder
7.  **Object & Knowledge Layer** (对象与知识层): Object Service / Wiki
8.  **Core & Persistence Layer** (核心与持久化层): Config / DB

## 三、目录结构设计 (核心摘要)

- `apps/api/`: 对外可见的 API 壳，解耦协议与业务逻辑。
- `services/`: 系统能力中台。
    - `orchestrator/`: 编排引擎，控制工作流。
    - `reasoning/`: 推理层，解耦 LLM 供应商。
    - `risk_engine/`: 治理层，独立的风控与审计。
    - `report_builder/`: 表达层，生成 Markdown 报告。
- `skills/`: 可复用的能力模块 (Ingestion, Analysis 等)。
- `policies/`: 宪法 (`constitution.md`) 与 机器规则 (`trading_limits.yaml`)。
- `wiki/`: 长期知识资产库。

## 四、核心分层哲学

1.  **推理 != 治理**: AI 负责产生想法，风控引擎负责拍板封堵。
2.  **表达 != 持久化**: 生成内容与写入对象是解耦的两个环节。
3.  **知识 != 技能**: Wiki 记录内容，Skills 定义动作。
4.  **真相权在 PFIOS**: 外部 Agent (如 Hermes) 的状态是暂时的，最终真相必须进入 PFIOS 的审计与对象层。

## 五、当前发展阶段

- **当前目标**: Step 8 - 真实推理引擎挂载。
- **后续目标**: Step 9 - Dashboard 对接；Step 10 - 复盘中台与检索增强。
