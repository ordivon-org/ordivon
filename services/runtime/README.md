# PFIOS: Personal Financial Intelligence Operating System

> **"From Engineering Skeleton to Evolutionary Intelligence."**

---
📑 **[PFIOS Master Manual & Specification](./docs/PFIOS_MASTER_MANUAL.md)** (系统总说明书 / 当前状态 / 演化路线图)
---

PFIOS (Personal Financial Intelligence Operating System) 是一个围绕个人金融判断、风险控制、建议跟踪、复盘沉淀、知识积累而构建的智能操作系统。

## 1. 系统核心定位
PFIOS 不是简单的交易机器人，而是您的**数字智能投研中台**。它旨在将碎片化的市场观察转化为结构化的判断，并通过严谨的治理层（Governance）与审计层（Audit），确保每一个决策都可追溯、可对账、可进化。

## 2. 核心架构 (Layered Architecture)
系统采用模块化的分层设计，确保各组件职责边界清晰：
- **Interface Layer**: 基于 Next.js 的现代化 Dashboard 与分析控制台。
- **API Layer**: 标准化的 FastAPI 接口，连接前端与中台能力。
- **Orchestration Layer**: 系统的编排中枢，管理推理、风险与存储的生命周期。
- **Reasoning Layer**: 智力引擎，接入真实推理模型（Hermes）并执行语义解析。
- **Governance Layer**: 治理核心，基于 Constitution 与 Policy 执行合规检查。
- **Object & Knowledge Layer**: 知识沉淀层，DB (DuckDB) + Wiki (Markdown) 双轨存储。

## 3. 主要闭环流 (The Loops)
- **分析闭环**: 问题输入 -> 推理 -> 风控拦截 -> 标准化报告导出。
- **建议闭环**: 分析策略 -> Recommendation 对象 -> 采纳/忽略跟踪 -> 生命周期结转。
- **复盘闭环**: 结转建议 -> 自动复盘骨架 -> 结构化 Lesson 提炼 -> Wiki 知识回写。

## 4. GitHub 仓库与工程管理
- **仓库地址**: [zycxfyh/Personal-Financial-Intelligence-Operating-System](https://github.com/zycxfyh/Personal-Financial-Intelligence-Operating-System)
- **分支策略**: 采用 `main` 分支作为生产级里程碑。
- **工程标准**:
  - 全量 DuckDB 映射：`db/pfios_main.duckdb`
  - 自动化回归：`data/evals/` 下的基准测试集
  - 治理审计：`data/logs/audit/` 双轨留痕

## 5. 项目结构
```text
.
├── apps/               # 应用入口 (Web/API)
├── services/           # 核心能力 (调度/推理/风控/报告)
├── policies/           # 治理宪法与规则
├── wiki/               # Obsidian 知识沉淀库
├── data/               # 运行时数据与评测集
└── docs/               # 架构设计与推理契约
```

---
**Current Status**: Step 11 - `Private Usable Version`. 系统已具备在真实环境中连续运行的稳定性。
