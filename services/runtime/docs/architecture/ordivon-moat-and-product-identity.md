# Ordivon — Moat and Product Identity

> 宪法注释层：解释 Ordivon 是什么、什么不可丢、护城河在哪。
> 目标读者：未来的 AI 协作者、外部评估者、以及会被市场噪音干扰的我们自己。

---

## 1. Ordivon 的主产物不是 PV

**PV / Ordivon Verify 是第一个可外化产品 wedge，不是 Ordivon 全系统本体。**

更高一层的定义是：

> Ordivon 首先是创造者的伴生治理系统；PV、Alpha、作品展示、社区和商业化都只是外部化路径。

伴生治理宪法见：

```
docs/architecture/ordivon-companion-governance-constitution.md
```

澄清关系：

| 问 | 答 |
|---|---|
| Ordivon 的主产物是什么？ | 一个伴生治理操作系统——让人的意图、约束、决策、行动、证据、结果、复盘和规则更新形成闭环 |
| Ordivon Verify 是什么？ | 第一个 surface layer 产品——最窄、最清晰、最容易外部理解的价值入口 |
| 关系 | Linux ≠ Ubuntu；Kubernetes ≠ kubectl；Ordivon ≠ Ordivon Verify |

Ordivon Verify 解决的具体问题：

- AI 说 done，能不能信？
- receipt 是否诚实？
- debt 是否隐藏？
- gate 是否被削弱？
- docs 是否还是 current truth？
- READY 是否被误当 authorization？

这些问题极其重要，但它们只是 Ordivon 治理语义在 verification 领域的一次实例化。

---

## 2. Ordivon 的核心对象

不是交易，不是文档，不是 CLI。

核心对象是：

> **AI / agent / 人类共同产生的行动，如何被治理。**

展开成治理回路：

```
谁提出？       → Intent
谁验证？       → Evaluation
谁授权？       → Authority
谁执行？       → Plan / Execution
证据在哪里？   → Receipt
债务在哪里？   → Debt
边界在哪里？   → Gate
真相源在哪里？ → Current Truth (registry)
失败如何处理？ → Review / Feedback
完成如何证明？ → Receipt + Checker
规则如何升级？ → CandidateRule → Policy
```

这才是 Ordivon。其他都是这个回路在不同领域、不同层的投影。

---

## 3. 不可割舍的七类资产

### A. Evidence / Authority 分离

第一性原理之一。

```
checker output    → evidence, not authority
receipt           → evidence, not review
ledger            → evidence, not execution authority
READY             → evidence, not authorization
CandidateRule     → proposal, not Policy
```

如果丢掉这个分离，Ordivon 降为普通 CI / automation tool。

### B. Receipt / Debt / Gate 三件套

最小治理机械结构。

| 组件 | 作用 | 缺失后果 |
|------|------|----------|
| Receipt | 声明做了什么 | 没有声明对象，验证无锚点 |
| Debt | 记录没解决什么 | 隐藏失败，积累未注册风险 |
| Gate | 定义什么必须通过 | 失去边界，越权无检测 |

Ordivon Verify 之所以能成立，正是因为这三件套成立。

### C. BLOCKED / DEGRADED / READY 状态代数

不是简单状态码，是对"信任程度"的产品化表达。

| 状态 | 语义 | 可跨领域使用 |
|------|------|-------------|
| BLOCKED | 有硬失败，不能 claim complete | Finance: trade plan blocked; Coding: PR blocked; Research: claim blocked |
| DEGRADED | 无硬失败，但治理不完整，需 review | 诚实状态——承认尚未完备 |
| READY | 选定检查通过，但不授权执行 | 最容易被误读的状态——必须保留 disclaimer |

### D. Human / Agent / CI 三方可读性

Governance layer 的独特性：必须同时服务三方。

| 读者 | 界面 | 缺失后果 |
|------|------|----------|
| Human reviewer | human trust report, docs, landing | 变成纯机器工具 |
| AI agent | SKILL.md, JSON report, skill policy | agent 无法理解治理规则 |
| CI / automation | exit codes, JSON, gate manifest, fixtures | 无法机器化执行 |

如果只给人看 → 文档工具。
如果只给机器看 → checker。
三方都能读 → governance layer。

### E. Dogfood-first 生成方式

不是偏好，是方法论护城河。

```
先自用    → 在真实项目中验证必要性
再抽象    → 提取跨领域的稳定语义
再机器化  → 把语义变成 checker / gate / receipt
再外化    → 把机器化结构变成 public wedge / Pack
```

反向路径（先营销→包装→找需求）会产出无法机器化验证的口号。

DG 从发现 receipt contradiction 中诞生。
PV 从 Ruff preview misclassification 中诞生。
7P 从 paper-without-live 中诞生。

### F. Private Core + Public Wedge 策略

当前阶段不可割舍。

Ordivon 主仓库包含太多内部演化轨迹、dogfood 判例、finance 细节、Core 草稿。不适合裸开。

路线：

```
Private Core (Ordivon repo)
  → Curated Public Verify Wedge (PV line)
    → Open schemas / CLI / skill / examples
      → Enterprise / hosted / advanced packs (later)
```

### G. New AI Context / Onboarding 机制

与普通软件项目的根本区别之一。

必须保证：

- 新 AI 读 root docs 后不会迷路
- 不会把历史当 current truth
- 不会把 Phase 8 当 active
- 不会把 CandidateRule 当 Policy
- 不会把 READY 当 authorization

机制：AGENTS.md header + current-phase-boundaries + agent-output-contract + stage summits + New AI Context Check per phase。

---

## 4. 什么不是不可割舍的

| 资产 | 态度 | 原因 |
|------|------|------|
| CLI 具体实现 | 可重构 | 语义（read-only / trust report / 状态代数）是核心，实现可变 |
| Python 语言 | 可替换 | 核心可 Rust，surface 可 Python，UI 可 TS |
| Finance 领域 | 可代理 | 高压测试场，不是系统身份；它验证出的原则才是核心 |
| 当前文档数量 | 可演化 | 31 个 registered docs 是证据，不是永恒形态 |
| Public release 时机 | 可延后 | 关键是 curated extraction / secret audit / private core protection 做到位 |

---

## 5. 护城河五层叠加

### Layer 1 — 实践生成的治理语义

> 很多人可以说"AI needs governance"，但很少有人能通过真实项目证明为什么 READY 不能是 authorization、为什么 DEGRADED 是诚实状态、为什么 tool limitation 不能误判为对象缺陷。

语义来自实践，不是口号。

### Layer 2 — 机器可执行的反自欺结构

哲学如果不能机器化，就容易变成口号。

已机器化的结构：

- document registry checker
- verification debt checker
- receipt integrity checker
- gate manifest checker
- baseline integrity
- trust report
- fixtures (BLOCKED / DEGRADED / READY)

别人可以复制"不要自欺"这句话。要复制一套会阻止自己 overclaim 的系统，难得多。

### Layer 3 — Core / Pack / Adapter 分层能力

随着系统扩大，真正杀死项目的不是功能少，而是语义边界混乱。

```
Core    = 不变量（从不 import Pack）
Pack    = 领域治理（imports Core）
Adapter = 外部连接边界（has capability declaration + local safety guard）
Surface = 使用界面
Evidence = 留凭
Authority = 授权
```

### Layer 4 — Dogfood evidence compounding

每个阶段都留下：receipt + ledger + checker + test + stage summit + New AI Context Check。

这会产生复利。阶段越多，治理判例越丰富。这些判例类似法律系统中的 case law。别人短期很难复制。

### Layer 5 — Agent-native governance positioning

Ordivon 不是 agent、不是 MCP、不是普通 CI、不是 SaaS dashboard。

它是：**验证 agent work 是否可信的治理层**。

agent 越多，Ordivon 的需求越强。这是一个更底层、更耐久的位置。

---

## 6. 单句核心护城河

如果只能选一个：

> Ordivon 的护城河，是把"系统不自欺"的治理哲学，通过真实 dogfood 沉淀为稳定语义，再通过 checker / ledger / receipt / gate / pack / surface 变成机器可执行约束的能力。

拆开：

| 组件 | 缺失后果 |
|------|----------|
| 治理哲学 | 没有方向，变成纯技术项目 |
| 真实 dogfood | 没有判例，语义来自臆测 |
| 机器可执行 | 没有约束力，变成文档规范 |
| 语义稳定 | 没有可迁移性，每次重来 |

四者叠加才是护城河。少任何一个都不够。

---

## 7. 两个必须避免的误判

### 误判一：PV 就是 Ordivon

不对。PV 是第一个外化产品 wedge。把 Ordivon 降维成 PV，会失去 Core / Pack / Adapter 的长期潜力。

### 误判二：Ordivon 的护城河只是理念

不对。理念会被复制。真正护城河是：

> 理念 × dogfood × checker × semantic boundary × product wedge × accumulated evidence

---

## 8. 三线产品规划

### 第一产品线：Ordivon Verify

当前最成熟。AI-generated work verification。面向 agent PR / receipt / debt / gates / docs / CI。状态：v0 prototype / private beta candidate。

### 第二产品线：Ordivon Packs

领域治理产品化：

- Coding Governance Pack
- Document Governance Pack
- Research Evidence Pack
- MCP Tool Governance Pack
- Compliance Evidence Pack
- Finance Decision Pack

### 第三产品线：Ordivon Core / Enterprise

更长期的 multi-repo governance、hosted evidence dashboard、audit trail、policy lifecycle、enterprise packs、cross-agent governance。

当前不要急着做。

---

## 9. PV 在护城河中的位置

PV 是护城河的第一根"外部长出来的枝条"。

它证明：

- Ordivon 的哲学可以变成 CLI
- Ordivon 的治理可以变成 trust report
- Ordivon 的状态语义可以被外部 fixture 验证
- Ordivon 的规则可以被 agent 读懂
- Ordivon 的边界可以被 CI 表达
- Ordivon 的 public wedge 可以不泄露 private core

但真正支撑它的是：DG Pack + 7P dogfood + Core semantics + Post-DG hygiene + agent-output-contract + receipt/debt/gate machinery。

---

## 10. 一句话回答所有

> Ordivon 的核心不是 Verify。
> Verify 是第一个外化窗口。
> Ordivon 的核心是：让 AI-agent 时代的行动、声明、证据、授权和复盘变得可治理。

---

*Created: 2026-05-01, post PV-N1 closure*
*Author: Ordivon creator + AI agent*
*Status: living document — evolves with each dogfood cycle*
