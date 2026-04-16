# PFIOS Master Manual & Specification (v1.1)

> **"The intelligence is not in the model, but in the loop."**

本文件是 PFIOS (Personal Financial Intelligence Operating System) 的最高设计原则、当前状态与演化路线图的官方综合文档。

---

## 一、 系统定位与主说明书 (Manual)

### 1.1 系统本质
PFIOS 是一个围绕个人金融判断、风险控制、建议跟踪、复盘沉淀、知识积累而构建的智能操作系统。它通过将瞬时的推理（Reasoning）转化为持久的对象（Objects），实现投研能力的数字化积累。

### 1.2 核心使命
- **决策去情绪化**：通过治理层（Governance）拦截不符合纪律的直觉冲动。
- **经验资产化**：将每一次分析转化为可回溯、可审计、可复盘的 Wiki 资产。
- **系统自进化**：通过复盘闭环提取 Lesson，持续修正推理引擎与风控规则。

### 1.3 核心业务闭环
1. **分析闭环**：输入 -> 阶梯上下文 -> 推理 -> 风控拦截 -> 报告导出。
2. **建议闭环**：Action 过滤 -> Recommendation 对象 -> 采纳/忽略跟踪 -> 状态结转。
3. **复盘闭环**：结转对象 -> 自动骨架 -> 结构化 Lesson -> Wiki 知识回写。

---

## 二、 当前系统状态总览 (Current Status)

### 2.1 建设历程 (Step 1-11)
系统已完成从 0 到 1 的全框架搭建：
- [x] **Step 1-4**: 工程骨架、数据基座与分布式编排引擎。
- [x] **Step 5-7**: 标准化报告表达、风控审计层与 API 中台中继。
- [x] **Step 8**: 推理引擎驯化、质量回归系统与失效案例库。
- [x] **Step 9-10**: Web 控制台交互界面与建议/复盘业务闭环。
- [x] **Step 11**: 真实使用验证看板 (Validation Hub) 与稳定化。

### 2.2 核心能力清单
- **真实智力**：接入 Hermes 推理引擎，具备结构化解析与语义对齐能力。
- **治理刚性**：Allow/Warn/Block 三级风控逻辑，具备 Machine Discipline。
- **知识记忆**：DB + Wiki 双轨存储，支持全量审计追踪与报告回看。
- **业务闭环**：具备完整的建议生命周期管理与事后归因复盘能力。

### 2.3 当前限制
- 实时工具链（如宏观日历、研报抓取）尚未完全模块化。
- 复盘 Lesson 的自动规则提取目前仍需人为辅助确认。

---

## 三、 下一阶段路线图 (The Roadmap)

### 3.1 扩展优先级
1. **工具链增强**：接入社交情绪、宏观数据与多源新闻摄取。
2. **记忆深度化**：实现 Lesson -> Rule 的半自动转化，增强“历史相似案例”检索。
3. **绩效精细化**：建立 Recommendation 采纳后的真实表现归因分析系统。

### 3.2 演化原则
- **价值驱动**：优先实现能直接提升决策置信度的工具，不抢跑纯 UI 优化。
- **稳健迭代**：在核心闭环稳定运行 7-14 天的前提下，再开启下一层能力的扩展。

---
**Document Status**: Final Version (Updated 2026-04-17)
**Repository**: [zycxfyh/Personal-Financial-Intelligence-Operating-System](https://github.com/zycxfyh/Personal-Financial-Intelligence-Operating-System)
