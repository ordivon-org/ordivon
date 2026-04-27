# Ordivon Prompt Patterns

Status: **DOCUMENTED**
Date: 2026-04-28
Wave: Docs-Lang-1
Tags: `prompt`, `pattern`, `template`, `runbook`

## 1. Ordivon Task Prompt v1 Template

Use this template for any IDE/AI task in the Ordivon project.

```markdown
# Ordivon Task Prompt v1

## 0. Current Stage
当前阶段：Wave X — Task Name
任务身份：[what this wave IS]

## 1. Purpose
本阶段要解决的问题：
为什么现在做：
它服务哪个 Ordivon 原则：

## 2. Scope
允许处理：
不处理：

## 3. Non-goals / Hard Boundaries
禁止：
- 不改 API
- 不改 ORM schema
- 不改 OpenAPI snapshot
- [project-specific constraints]
停止条件：
- 如果需要 ORM schema 变更，停止并报告。
- 如果 OpenAPI snapshot 出现大规模 diff，停止并报告。
- 如果发现 Core import Pack，停止并报告。

## 4. Truth Sources
必须先读取：
- 文件：
- 测试：
- 文档：
- 最近 commit/tag：

## 5. Assumption Map
当前假设：
A. [hypothesis]
B. [hypothesis]
请先验证这些假设是否成立。若不成立，停止并报告。

## 6. Risk Map
reject 级：[must-block risks]
escalate 级：[needs-human-judgment risks]
advisory：[record-but-don't-block risks]

## 7. Implementation Rules
最小修改原则：
不得越界：
不得重构：

## 8. Evidence / Receipt
完成后必须输出：
- 修改文件列表
- 测试命令与结果
- git diff --stat
- 是否改 API
- 是否改 ORM
- 是否改 OpenAPI snapshot
- 是否触发副作用
- 越界检查

## 9. Tests / Gates
必须运行：
- uv run pytest tests/unit -q --no-header
- uv run python scripts/check_architecture.py
可选运行：
- uv run pytest tests/integration -q --no-header

## 10. Review Questions
完成后回答：
1. 这个改动解决了什么真实问题？
2. 它是否新增了未来风险？
3. 它是否应该生成 CandidateRule？
4. 它是否需要 Policy promotion？
```

## 2. Audit Prompt Pattern

For read-only exploration. No code changes.

```markdown
当前阶段：Wave 0 — [Topic] Audit。
目标：只读审计。不实现，不清债，不改文件。

允许：
- 读取文件
- 搜索代码库
- 列出发现

禁止：
- 不改任何文件
- 不创建新文件
- 不运行修改命令

停止条件：
- 如果发现 blocking issue，停止，不修复，只报告。

输出：
- 关键发现列表
- 风险分级 (reject/escalate/advisory)
- 推荐的下一步行动
```

## 3. Fix Prompt Pattern

For repairing a single failing gate.

```markdown
当前阶段：[Wave] — [Bug/Issue] Fix。
目标：只修当前失败 gate。不顺手改周边。不做功能扩张。

允许：
- 修改失败 gate 相关的最小代码面
- 新增回归测试

禁止：
- 不做大重构
- 不改 API
- 不改 ORM schema（除非 bug 根源在此且别无选择）

停止条件：
- 如果修复需要扩大范围，停止并报告新的计划。

输出：
- 修复内容（1-2 句话）
- 修改文件列表
- 修复前/后测试结果
- git diff --stat
```

## 4. Feature Prompt Pattern

For adding a new capability.

```markdown
当前阶段：Wave X — [Feature Name]。
目标：[1 句话描述]

必须回答：
- 解决什么真实问题？
- 为什么不是文档/测试就够？
- 是否有 dogfood 路径？
- 是否会污染 Core？
- 是否需要新的 Receipt？

允许：
- [scope]

禁止：
- 不做 Policy promotion
- 不做大重构
- 不接 shell / MCP / IDE agent

停止条件：
- 如果发现需要 ORM schema 变更，停止并报告。
- 如果 Core 需要 import Pack 类型，停止并报告。

输出：
- 新增文件列表
- 修改文件列表
- 测试结果
- 是否改 API / ORM / OpenAPI
- dogfood 验证结果
```

## 5. Generalization Prompt Pattern

For extending a concept beyond its original domain.

```markdown
当前阶段：Wave X — [Generalization Name]。
目标：证明 Core 可以服务非 [original-domain] 场景。

核心约束：
- 不得通过复制 [original-domain] 语义泛化。
- 必须证明 Core 只消费协议。
- 必须至少有第二个 Pack 例子。

停止条件：
- 如果 Core 需要 import 新 Pack 的类型，停止并报告。

输出：
- 新 Pack 结构
- Core import 检查：必须为空
- 跨 Pack 验证结果
```

## 6. Dogfood Prompt Pattern

For running realistic validation.

```markdown
当前阶段：Wave X — [Pack/Domain] Dogfood。
目标：用 N 个模拟样本验证 [component] 的治理效果。

允许：
- 新增 dogfood 脚本
- 调用 Pack policy + RiskEngine
- 记录 expected / actual / reasons

禁止：
- 不真实修改文件
- 不接 shell / MCP / IDE agent
- 不创建 ExecutionRequest / ExecutionReceipt
- 不生成 CandidateRule
- 不自动 Policy promotion

输出：
- 每个 run 的 run_id, expected, actual, reasons, pass/fail
- 汇总 execute / reject / escalate 数量
- 0 errors / 0 real file writes / 0 side effects
```

## 7. Reflection / Philosophy Prompt Pattern

For synthesizing learnings into principles.

```markdown
当前阶段：[Label] — Reflection Synthesis。
目标：将近期实践提炼为 Ordivon 原则或语言规则。

步骤：
1. 先抽共识 — 多轮讨论的共同核心是什么？
2. 再找学科支撑 — 认知科学/系统论/控制论/组织学习对应点？
3. 再转成 Ordivon vocabulary — 用术语表表达
4. 再转成 prompt rule — 可操作的约束
5. 最后转成 checker/test/doc — 外化为可执行结构

输出：
- 原则陈述（1 句话）
- 对应的学科引用
- 对应的 Ordivon 术语
- 对应的 prompt rule
- 对应的外化建议
```

## 8. Required Evidence Block

Every task completion must include this block:

```markdown
## Evidence / Receipt

| 项目 | 结果 |
|------|------|
| 修改文件列表 | [files] |
| 新增文件列表 | [files] |
| unit tests | [N/N PASS] |
| integration tests | [N/N PASS] |
| architecture checker | [clean / violations] |
| 改 API？ | [是/否] |
| 改 ORM schema？ | [是/否] |
| 改 OpenAPI snapshot？ | [是/否] |
| 触发副作用？ | [是/否 — 说明] |
| 越界检查 | [通过 / 发现 X] |
| git diff --stat | [summary] |
| commit id | [hash] |
```

## 9. Stop Condition Block

Every prompt must include stop conditions:

```markdown
停止条件：
- 如果需要 ORM schema 变更，停止并报告。
- 如果 OpenAPI snapshot 出现大规模 diff，停止并报告。
- 如果发现 Core import Pack，停止并报告。
- 如果测试失败不是本阶段范围，停止并报告。
- 如果需要修改超过 N 个文件，停止并报告。
```

## 10. Example Prompt Skeleton

A concrete example using the template:

```markdown
# Ordivon Task Prompt v1

## 0. Current Stage
当前阶段：Wave E1 — Runtime Evidence Integrity Checker。
任务身份：新增只读静态 checker。不是 OpenTelemetry 大工程。

## 1. Purpose
问题：L9 Runtime 是 12 层中最弱层。
为什么：没有自动检查 runtime evidence 一致性。
原则：Receipt records evidence, not confidence.

## 2. Scope
允许：scripts/check_runtime_evidence.py + tests + doc.
不处理：OpenTelemetry tracing, live DB query.

## 3. Non-goals
禁止：
- 不改 API / ORM / OpenAPI snapshot
- 不接 shell / MCP / IDE agent
- 不做 Policy promotion
停止条件：
- 如果需要 ORM schema 变更，停止。
- 如果发现 Core import Pack，停止。

## 4. Truth Sources
文件：domains/execution_records/orm.py
     domains/finance_outcome/orm.py
     domains/journal/orm.py
     domains/candidate_rules/models.py
文档：docs/architecture/execution-request-receipt-spec.md

## 5. Assumptions
A. ORM model invariants are checkable statically.
B. Plan receipt spec exists and can be verified.
验证：跑一次 checker 看是否所有检查通过。

## 6. Risk Map
reject: 无。
escalate: 如发现 ORM 缺关键字段，报告，不自动修。
advisory: checker 本身是 CandidateRule。

## 7. Implementation Rules
最小修改：只加 checker + test + doc.
不重构执行的任何代码。

## 8. Evidence / Receipt
[see Section 8 template above]

## 9. Tests / Gates
必须：unit tests, integration tests, architecture checker.
可选：PG full regression.

## 10. Review Questions
1. 解决 L9 最弱层的问题。
2. 不新增风险 — 纯只读。
3. 不生成 CandidateRule — checker 本身是 advisory。
4. 不升级 Policy。
```
