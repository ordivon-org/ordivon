# Runtime Workspace 生命周期与 Agent 结果约束 — 实施规格

> SourceCut: `3b43977e682d8c7668f6371ffd998c7821e4312a` (GitHub origin/main, 2026-11-09)。Owner: Runtime。状态：SOURCE SPEC；不等同于合并、安装或消费者验收。

## 1. Problem Statement

Runtime 的 Linux 生产 Workspace 回收已使用 PG 原生 `ordivon-runtime-pg-reclaim`、每小时 systemd timer 和 4h 最小年龄，但已安装的关键脚本未被当前源树声明；仓库 `packaging/systemd/ordivon-runtime-lifecycle.service` 仍指向旧 SQLite 回收入口。现行安装脚本要求“曾有成功 Job”“HEAD 已被 origin/main 包含”“目录 ctime 未刷新”，导致零 Job、终态失败、有效持久分支与元数据变化的临时 Workspace 可能无限堆积。

更广泛的问题是 Agent 通过文字规则自我解释成功，现有测试主要约束误删，却未严格约束最终回收、真实部署和消费者结果。一个过度保守的 Agent 因此能通过增加拒绝条件获得表面正确性。

## 2. Solution and ownership

以可复用的 **行为合同 + 独立反例 + 单条生产入口 + 实际消费者回读** 替代新的 Agent 框架或 Registry。

- Git 是源码持久性的权威；物理 Workspace 可删除，必要工作必须先锚定可保留的 Git 引用或 Artifact。
- Runtime Registry 是 Job/Attempt 和当前 Workspace 活动的权威；Linux PG 操作从 PG readback 获取事实；不得依赖旧 SQLite。
- systemd/cgroup 与 Windows SCM/Job Object 是物理进程的权威。
- Host/Domain 负责 Task 意义。Runtime 的 `consumerReleased` 是调用者声明，不得把它宣传为“已独立验证全部 Host 消费者”。
- 4h 是默认工作区闲置窗口，不是等待成功 Job 的条件，也不是 Linux ctime。
- 使用现有 `workspace.get`/`workspace.close` 作为回收最后的原子所有权边界；复用现有 Runtime 发布清单及 `runtime:verify`。
- Windows PG/SQLite 是独立迁移，在真实 Windows PG cutover 前不删除当前 SQLite Registry。
- 不新增 Workflow engine、Task/Job 数据库、审批层、通用 Policy DSL 或大规模独立 Agent Skills。

## 3. Behavior contract

定义 `t_last = max(t_workspace_created, t_latest_job_activity)`；若无 Job，则 `t_last = t_workspace_created`。在有权威时间、无活跃 Job、无独立消费租约且 `now >= t_last + 4h` 时，允许进入回收候选阶段。必须读取、再次检查并经 Runtime 原生 Close 成功后才报告回收完成。

**必需性质**
- S1: Active/Held Job、可观测进程持有或仍有效的消费关系，不能被 GC 关闭。
- S2: 有未提交源码修改但无持久替代者，默认不强制关闭。
- S3: Git HEAD 的源码持久性以可保留 Git refs/明确已发布提交或 Artifact 判断；不能等同于“已合并 main”。工作树自身 ref 不算持久副本。
- S4: Replay、响应丢失、MCP 断连、PG 不可用、证据不完备不能被转换为 `closed`。
- L1: 零 Job 的干净、无消费者、足龄 Workspace 必须可进入回收。
- L2: 失败、取消、lost 等已有终态证据不得单独形成永久保留理由；但遗留外部副作用为 UNKNOWN，不声明业务成功。
- L3: 目录 ctime 或无关文件元数据变化不能无限延长生命周期。
- L4: 当回收循环有公平机会且依赖可用，满足条件的 Workspace 最终必须关闭。
- D1: 生产脚本、Service/Timer、发布清单和依赖工具必须来自可审计 Git SourceCut，且安装后能回读字节 digest。
- G1: 更改模型生成的报告、计划、测试不能单独改变上述合同；CI 必须在 Owner 原生测试中验证 S/L 双向性质。

**当前实现限制（不得隐藏）**：未建立跨 Host 的显式 Workspace consumer lease 之前，普通 `workspace.get` 只观察 Runtime 自身当前 Job；无法机械证明所有潜在 Host 后续引用不存在。4h 可回收是经过用户选择的本地临时 Workspace 政策，而非全系统无未来消费者定理。新增正式租约需要 Host→Runtime 的真实协议消费者与独立测试，不应以任意猜测引用代替。

## 4. User stories

1. 作为工程 Agent，我能执行工作并依赖 Git/Artifact 保存结果，而不手工维护临时工作区。
2. 作为 Linux Runtime 操作者，我能看到当前 PG-native 回收实现来自哪个提交及发布清单。
3. 作为工作区创建者，我打开一个完全无 Job 的工作区后，即使忘记关闭，超过 4h 且无消费者仍可回收。
4. 作为失败任务使用者，我不会因某次终态失败而无限保留整个 Workspace。
5. 作为并行 Agent，我的活跃 Job 和实际进程引用不会被回收器越权删除。
6. 作为分支作者，我的成果在持久 Git 引用中保留后可以释放临时物理工作树，即使尚未合并 main。
7. 作为发布操作者，我能从 Git 生成与已安装 Linux 生命周期配置一致的版本化产物，并读回验证。
8. 作为低能力 Agent，我无法让一个永不回收的方案通过行为合同，只靠形式上的“没有误删”验收。
9. 作为 Windows 用户，我的仍在写入的 SQLite Registry 不会因 Linux PG 切换而被误删。

## 5. Acceptance seams (prefer existing)

- **Public operator CLI**: `ordivon-runtime-pg-reclaim` 的只读/应用入口。测试零 Job、失败终态、活跃 Job、已锚定未合并 HEAD、ctime 漂移、空/错误 PG 观察。
- **Runtime MCP**: `workspace.get` → `workspace.close`，不使用直接磁盘删除，接受 `expectedSourceStateDigest`。
- **Release**: `ordivon-runtime-deploy` 的正式 Artifact manifest 与 systemd packaging 来源。校验每项安装产物与 Git 内容一致。
- **CI**: 现有 Owner-native Mise 验证，测试红→绿→复现失败，并检查改变测试文件后的证据。

## 6. Non-goals

不做 Windows PG 生产切换，不重建 Runtime scheduler，不新建全局 LEGO 注册器，不把 Agent Prompt 评分当成物理验收，不强制删除已有活动 Workspace；不为本任务复制 Matt/ECC/Superpowers 的整个 Skill 树。

## 7. References and prior art

- Matt Pocock: `to-spec`, `to-tickets`, `tdd`, `code-review`，基于真实接口的 tracer-bullet 和双轴 review。
- ECC: `verification-loop`（Build/Type/Lint/Test/Security/Diff）；`continuous-learning` v1 已弃用，不使用。
- Superpowers: `writing-plans`, `executing-plans`, `verification-before-completion`。
- 本地权威：`AGENTS.md`、`services/runtime/AGENTS.md`、`tools/repo/owners.toml`、`mise.toml`、`formal/WorkspaceConsumerCloseR1.tla`。
