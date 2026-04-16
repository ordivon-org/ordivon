# PFIOS Master Manual & Specification (v1.1)

> **"The intelligence is not in the model, but in the loop."**

---

## 一、 PFIOS 到底是什么 (System Definition)

PFIOS (Personal Financial Intelligence Operating System) 不是普通的交易机器人，也不是一个简单的“会分析市场”的聊天助手。它更准确的定义是：**一个围绕个人金融判断、风险控制、建议跟踪、复盘沉淀、知识积累而构建的智能操作系统。**

它的核心使命不是追求“模型说得像不像分析师”，而是：
* **持续性**：能不能持续给出结构化的判断。
* **治理性**：能不能被严谨的治理规则（Governance）约束。
* **可审计性**：所有动作是否都留下了可追溯的审计痕迹。
* **资产化**：输出能否沉淀为持久的结构化对象（Objects）与知识。
* **进化能力**：能否通过复盘（Review）不断自我修正。
* **高可用性**：能否真正进入每日连续使用，而非一次性 Demo。

**核心逻辑链条**：  
Observe (观察) → Analyze (推理) → Govern (治理) → Express (表达) → Persist (持久化) → Track (追踪) → Review (复盘) → Learn (学习)

---

## 二、 整体架构总览 (System Architecture)

PFIOS 采用严格的分层架构设计，确保系统模块化与可演化性。

### 2.1 Interface Layer (界面层)
包含 Dashboard、Analyze 页面、Audits 治理中心、Reports 报告列表等。负责系统状态的可视化交互与操作发起，不承载业务逻辑。

### 2.2 API Layer (API 中台)
基于 FastAPI 构建，定义了 Pydantic 契约、路由装配（api/v1）与 Request/Response 协议，是前端与中台能力的通讯枢纽。

### 2.3 Orchestration Layer (编排引擎)
系统的“大脑总控”，包含 `engine.py`, `router.py`, `context_builder.py` 与 `state_manager.py`。负责决定 Workflow 路径、组织上下文数据、并串联推理、风控与持久化逻辑。

### 2.4 Reasoning Layer (推理智力层)
系统智力底座。包含推理模型契约、语义解析器（Parser）、Reasoning Service、Prompt 模板库。目前已实现从 Mock 到真实推理（Hermes）的升级，具备质量工程与回归治理能力。

### 2.5 Governance Layer (风控治理层)
PFIOS 的差异化核心。包含 `rules.py`, `validators.py` 与 `audit.py`。基于 Policy 与 Constitution 执行 Allow/Warn/Block 拦截，确保机器人的“纪律性”。

### 2.6 Expression Layer (报告表达层)
负责将结构化推理结果转化为标准化、可读性强的 Markdown 或 HTML 报告，实现了表达逻辑与推理逻辑的解耦。

### 2.7 Object & Knowledge Layer (对象知识层)
负责核心资产的持久化。包含了 Report, Recommendation, Review 等对象的生命周期管理。采用 DB (DuckDB) + Wiki (Markdown) 双写模式，将产出转化为长期知识资产。

### 2.8 Core & Persistence Layer (核心持久化层)
包括配置管理（Config）、数据库（DuckDB）、日志审计（JSONL）以及评测数据（Eval Runs/Baselines）。

---

## 三、 建设历程总回顾 (Step 1–11 Roadmap)

### Step 1: 骨架初始化
建立了工程根基，确立了 apps/services/policies/wiki 等核心目录结构。

### Step 2: 数据基座搭建
实现了 DuckDB 数据库初始化与核心 Schema 定义，确立了系统的存储锚点。

### Step 3: 对象沉淀与知识层落位
实现了 Object Service，打通了“DB 存事实，Wiki 存知识”的双沉淀逻辑。

### Step 4: 编排引擎去单体化
重构了 Engine 与 Router，实现了职责分离，为多工作流扩展打下基础。

### Step 5: 报告表达层
交付了标准化的报告生成器与模板系统，使系统具备了专业的“表达能力”。

### Step 6: 治理与审计
引入了双轨审计机制（DuckDB + JSONL），建立了基于机器纪律的风控拦截层。

### Step 7: API 重构
将中台能力装配化，通过 FastAPI 提供了标准的 Pydantic 契约服务。

### Step 8: 真实推理接入与驯化 (核心跳跃)
* **8.1/8.2**: 建立了语义契约解析器（Parser）与真实模型桥接（Hermes CLI Bridge）。
* **8.3/8.4**: 引入了五层上下文 Schema、Few-shot 模板及质量回归评测系统（Baseline/Diff Gate）。

### Step 9: 前端控制台 (Dashboard)
实现了 Dashboard、Analyze 页、Audits 页的全量对接，将工程系统转化为可操作、可回看、可监控的控制台。

### Step 10: 业务工作流闭环
实现了建议（Recommendation）与复盘（Review）的生命周期管理，确立了“分析->建议->复盘->学习”的完整价值闭环。

### Step 11: 真实使用验证与稳定化
建立了日快照式使用日志（Usage Log）、分级缺陷治理（Issue Triage）与 Validation Hub 看板，支持系统向“私有可用版”平稳过渡。

---

## 四、 核心业务主闭环 (The Master Loops)

### 3.1 分析闭环 (Analyze Loop)
信号捕获 → 上下文自动构建 → 真实推理 → 风险拦截审计 → 标准报告生成 → 对象持久化 → 前端回看。

### 3.2 建议/记录闭环 (Recommendation Loop)
分析结果生成 Recommendation → 用户采纳/忽略 (Adopt/Ignore) → 状态跟踪 (Tracking/Closed) → 进入复盘池。

### 3.3 复盘/进化闭环 (Review Loop)
已结转建议 → 自动生成复盘骨架 (Review Skeleton) → 录入实际结果与偏差 → 提炼结构化 Lesson → 写入系统知识库。

---

## 五、 文件夹结构与设计理念 (Directory Philosophy)

* **`apps/`**: 应用入口。回答“系统怎么被人用”。
* **`services/`**: 中台中枢。回答“系统的器官功能是什么”。
* **`policies/`**: 治理准则。回答“系统的底线和纪律是什么”。
* **`prompts/`**: 提示词管理。回答“系统如何更好地思考”。
* **`wiki/`**: 知识资产。回答“系统学到了什么”。
* **`data/`**: 运行时与评测数据。回答“系统表现如何，是否退化”。
* **`db/`**: 数据结构。回答“数据如何流转”。
* **`docs/`**: 设计意图。回答“系统为什么要这样设计”。
* **`scripts/`**: 工程辅助。回答“如何验证和维护系统”。

---

## 六、 下一阶段扩展路线图 (Future Roadmap)

### 6.1 更强的工具链 (Tools)
接入宏观日历、市场深度数据、社交情绪、研报自动化抓取，增强 Market Context 丰富度。

### 6.2 记忆与知识自动化 (Memory)
实现 Lesson 到具体逻辑规则（Rule/Prompt Case）的半自动转化，增强相似案例检索能力。

### 6.3 绩效归因分析 (Performance)
统计 Recommendation 采纳后的真实胜率、盈亏比，按 Market Regime 执行分段归因。

### 6.4 多模型与 runtime (Reasoning)
接入多 Provider (Claude/GPT/Olla/local)，实现 Fallback Routing 与交叉比对机制。

---

## 七、 准确定位与 GitHub 资产管理

**当前阶段定性**：一个完成核心框架建设、具备真实推理/治理/沉淀/看板能力，且通过初步稳定化验证的**个人金融决策中继站**。

* **仓库地址**: [zycxfyh/Personal-Financial-Intelligence-Operating-System](https://github.com/zycxfyh/Personal-Financial-Intelligence-Operating-System)
* **工程标准**: P0/P1 问题分级治理，Usage Log 跨天连续同步，回归评测底座全量保护。

---
**Document Status**: Final Version (Updated 2026-04-17)
**Maintenance**: Powered by Antigravity AI
