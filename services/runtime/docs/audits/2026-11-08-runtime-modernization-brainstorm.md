---
schema_version: 1
id: runtime.modernization-audit-2026-11-08
title: Runtime Modernization Evidence and Brainstorm
type: reference
profile: engineering
lifecycle: active
source_role: canonical
visibility: internal
owners:
  - ordivon-runtime
audience:
  - operator
  - builder
  - agent
updated: 2026-11-08
summary: Source-grounded modernization defects, OS-native replacements, dynamic resource scheduling options, formal obligations, and release gates.
evidence_status: observed
readiness: REVIEW
applies_to:
  - ordivon-runtime
related:
  - runtime.operations
  - runtime.recovery
  - runtime.model
---

# Runtime 现代化审计与头脑风暴 — 2026-11-08

## 判定范围与证据等级

本文件是一次可消费的 Owner 审计，不是新框架规格，也不是已经发布的系统现状。源目录：隔离 Workspace `ws-gpt6-runtime-pg-boundary-20261107-r1`，以 `6de375a567a6` 为基础，有尚未提交的 Runtime 修复。此文件中的源码观察针对该工作区的文件；**生产运行态**仅由连接的 Linux/Windows Runtime 查询证实。严禁把源分支、模型、证明 Harness 或测试修改称为已部署。

证据等级：**OBSERVED**（源码/连接节点直接核验）、**INFERRED**（从代码逻辑推导，待物理复现）、**CANDIDATE**（有成熟外界依据，但尚未验证适合 Ordivon）。凡涉及物理资源、内存、PSI 或 cgroup 的当前数字，由于 Linux 普通执行池阻塞而**没有获取**，绝不推断硬件空闲。

## 当前最强的反例：固定并发与失联的取消

- OBSERVED: `crates/ordivon-runtime-mcp/src/pg_main.rs` 的 `ExecutionContext.global_limit=4`（约第 44 行）**硬编码**；`runtime/pg_runtime/node_query.rs` 的 `globalExecutionLimit=4`（约第 27 行）又单独**硬编码**。更改一处不能同步实际准入与能力描述。
- OBSERVED: `pg_admission.rs` 约第 374–380 行使用 PostgreSQL 活动预留计数：`workspace_count >= 1 || global_count >= global_limit` 时拒绝。既无 CPU/内存/IO/PSI 作为输入，也未对不同 Job 按资源需求加权。
- OBSERVED: `pg_admission.rs` 使用全局固定 advisory transaction lock `79245017` 串行化包括容量在内的准入；此锁是正确性工具，但扩容后可能成为热点，应测量而非盲删。
- OBSERVED: Linux 节点 `globalExecutionLimit=4`；四个先前已经取消的 Job 所属 Attempt 均仍为 `stopping`，`concurrency_reservations=active`，`mechanicallyConverged=false`。本轮再次分别请求精确 Job 取消：三个仍 `stopping`，一个 `REGISTRY_UNAVAILABLE: native stop not confirmed`。新 `workspace.exec` 在持久化前返回 `CONCURRENCY_LIMIT / not_started`。
- OBSERVED: `runtime/platform/linux.rs` 已通过 systemd `KillMode=control-group`、`TimeoutStopSec=2s`、`SendSIGKILL=yes` 让内核负责进程组终止，不需要新的 PID walker。
- OBSERVED: 原 `job.cancel` 使用异步 `systemctl --no-block stop`；`reconcile` 优先要求 `result.json`。Runner 提前被终止而未留下 Result，或原生身份无法被可靠确认时，可形成永久占用。
- OBSERVED: 当前可访问的 Linux 执行工具本身属于受这四个 PG 预留约束的普通 Job 池。没有从已连接接口获得独立 root/systemd 管理 Shell。因此**没有证据可以宣布四个原生 cgroup 已成功强制停止或四条 PG 预留已释放**。授予管理员权限不等于已实现可到达的独立 OS 管理通道。
- OBSERVED: 当前 Windows 原生 launcher 已有 Windows Job Object 原语；Windows R6 Registry 仍使用活动 SQLite 文件，不能将启动中的 PostgreSQL 服务当作 Windows PG-only 证据。

### 原生终止目标的准确身份（未物理核验 Unit 是否仍存在）

| Job / Owner | Attempt（对应代码生成的候选 systemd Unit 为 ordivon-pg-{Attempt}.service） | PG 现状 |
|---|---|---|
| Security | `attempt-01a1b62b-82f0-76d2-855b-d4a9c2966620` | stopping / active |
| Finance Updater | `attempt-01a1b608-afed-7220-a4fe-d9cf42fc9be4` | stopping / active |
| Finance Differential | `attempt-01a1b5fe-27ce-7677-99e2-5848c52425f1` | stopping / active |
| Data | `attempt-01a1b678-3665-7756-b27c-fc00220bc402` | stopping / active |

严禁按 `ordivon-*` 进程名通配杀服务。通过系统管理入口查询这些精确 Unit 的 `LoadState`、`ActiveState`、`Job`、`InvocationID`、`ControlGroup` 和原生 cgroup 事件；若精确 Unit 尚在并已确定身份，交给 systemd 停止／终止；再让 Runtime 的现有 PG 终态事务对账。原生进程不存在只足以证明物理容量可回收；**不能倒推出任意外部副作用失败或成功**。

## 头脑风暴：已确认的现代化欠账（OBSERVED）

| # | 范围 | 确认的欠账 | 首选成熟替代／收敛方向 |
|---|---|---|---|
| O01 | Admission | 服务入口和能力 API 两处硬编码 4 | 删除常量双写；单一资源能力投影 |
| O02 | Admission | 按 Job 数而非资源向量准入 | CPU、memory、IO、pids、磁盘与外部设备的请求／分配／实际利用 |
| O03 | Workspace | `workspace_count >= 1` 使只读且独立任务也被阻塞 | 资源调度与 Git 写租约分离，允许无冲突并行读取 |
| O04 | Admission | 满额立即 `Capacity` 拒绝且未建立 durable pending queue | 已接受但未启动的队列、按资源可用自动唤醒；不要把队列占用当内核进程 |
| O05 | Liveness | 停止意图已经写入，Runner 结果缺失可卡死 | systemd/cgroup 原生终止见证 → PG 原子释放，效果未知保留 UNKNOWN |
| O06 | Control plane | 运维和修复命令依赖被堵死的普通执行容量 | 独立原生管理入口，systemd/SCM 服务管理；不要实现第二套调度器 |
| O07 | Reactivity | `runtime/pg_runtime/job.rs` 的 Observe 重连数据库、50ms sleep 轮询 | systemd D-Bus／cgroup.events 与 PG LISTEN/NOTIFY 唤醒；观察超时只作为上界 |
| O08 | DB | 所有准入共享固定 advisory xact lock | 保留事务 CAS 语义；评估短事务、分区租约及负载热点，先证明再改 |
| O09 | State | Job 的物理是否运行、PG reservation 和语义效果易混为一个数值 | PhysicalAllocation 与 ExecutionOutcome 观测分离，单一 Registry 真相 |
| O10 | Projection | `node_query.rs` `resultAvailable` 由 `finishedAt` 推导 | 只有实际 Runner Result Artifact 存在时才报告可读，LOST 有单独原生证据 |
| O11 | Error | PG 专用操作曾依赖 SQLite Engine 通用错误映射 | 已在隔离源码拆成通用与 SQLite-only，但尚未发布 |
| O12 | Rust crates | MCP 对 Core 强制 `transactional-runtime`；PG feature 仍编进 `rusqlite` | 抽出 storage-neutral Core；PG-only 编译依赖图验收后再删旧后端 |
| O13 | Monolith | `pg_admission.rs` 约 2,795 行，混合 SQL、事务、状态、验证、测试 | 按 schema/admission/cancellation/terminal/readback 真实职责拆分 |
| O14 | Monolith | `runtime/engine.rs`、`runtime/windows.rs` 等巨型旧引擎与 PG 路径并存 | 最终消费者优先；旧路径退役，PG 专属实现不再跨旧 Engine 引用 |
| O15 | Module boundary | `pg_runtime` 多处 `use super::*`，内部依赖未显式声明 | 用局部明确 imports、输入／输出契约和窄 trait，而非名字上的模块化 |
| O16 | Source truth | Linux 节点 ID `linux-pg`、固定 capabilities、最大 30min／4MiB 在入口静态编码 | 实际 installed provider 的单一能力投影，任务级预算与宿主上限分离 |
| O17 | Scheduling | 每个 Job 只有独立 timeout 和资源上限，没有已确认的资源请求/预留模型 | Kubernetes requests/limits 的区分；systemd 负责强制执行，PG 只记分配 |
| O18 | Feedback | 准入不读取内核 PSI、memory.events、CPU/IO 压力 | 内核 PSI 事件与少量可信容量反馈，而非固定并发数字 |
| O19 | Loopback API | 旧 PG server 被描述为 opt-in Linux-only 且 `structuredReleaseConfigured=false` | 从测试 vertical 收敛为正式可发布服务，原生 release receipts |
| O20 | Windows | Windows Job Object 成熟，但 Registry 仍有活动 SQLite 消费者 | 原生 Windows PG writer/readback/recovery 接受后彻底退役 SQLite |
| O21 | Source docs | 一些旧 SQLite parity / Windows-first 形式模型不再是当前发布前提 | 标记历史而不是继续作为现行阻碍，更新消费者 |
| O22 | Formal boundary | 源码拥有 Kani harness 但尚未实际运行，不能证明系统已修复 | 真实 Kani/TLC 与 OS/PG 物理验收证据相连，空白就填 UNKNOWN |
| O23 | Physical observation | 旧 helper 对消失的 cgroup 接口返回 `false`（可能与已观测到 `populated=0` 混淆） | 增加显式 `Option<bool>` 的可用性表征；缺失的 cgroup 事实不自动变成 0 |
| O24 | Lifecycle | systemd 使用 transient Unit 自动卸载（`CollectMode=inactive`），结果文件可能缺失 | 以启动身份、systemd 事件和 PG evidence 形成发布可检查的对账契约 |

## 尚需现网测量的候选（CANDIDATE，不伪装成已发现的 BUG）

| # | 能力 | 适用条件／成熟实现 | 验证项 |
|---|---|---|---|
| C01 | Capacity-aware admission | Linux cgroup v2、systemd MemoryHigh/CPUWeight/TasksMax、Windows Job Object | 真实资源容量与进程压力 |
| C02 | Pressure-aware feedback | Linux PSI：/proc/pressure/{cpu,memory,io}、cgroup PSI triggers | 精确启动／退出压力下的误杀率和吞吐 |
| C03 | Workload class | Kueue 队列＋可借配额思想；CPU-heavy/IO-bound/long-lived/interactive | 同类 Job 延迟、公平性和资源利用 |
| C04 | Multi-resource fairness | Dominant Resource Fairness（DRF）或 Weighted Fair Queueing | 不同 Owner 之间是否饥饿及相互干扰 |
| C05 | Adaptive concurrency | Envoy gradient / Netflix concurrency-limits 对服务请求限流 | 单机 Job 是异构长任务，不能直接复制 HTTP RTT 公式 |
| C06 | Native queue | PostgreSQL `FOR UPDATE SKIP LOCKED`（竞争队列）、LISTEN/NOTIFY（通知仅为 hint） | 消息丢失、进程重启和 exactly-once 误解 |
| C07 | Supervisor events | systemd D-Bus、cgroup.events/poll，Windows SCM/Job completion | 停止事务、systemd 自行卸载和重启跨越的事件丢失 |
| C08 | Restart and watchdog | systemd Restart=、WatchdogSec=、sd_notify，Windows Service Recovery | 管理服务不能自封持久存活；恢复时 PG authority 唯一 |
| C09 | Elastic priority / preemption | Kubernetes PriorityClass/Preemption、Nomad 排程 | 只对可恢复任务启用；不预设业务副作用可重试 |
| C10 | Resource borrowing | Kueue cohort borrowing / weighted pools | 空闲时允许任意 Owner 使用、负载时按权重回收 |
| C11 | Dynamic CPU scheduling | cpu.weight 优先，cpu.max 有明确必要时设 | 非必要硬限 CPUQuota 易导致欠利用 |
| C12 | Dynamic memory | memory.high 压力控制，memory.max 防 OOM 传播 | 工作负载尺寸变化、回收风暴、OOM 成本 |
| C13 | I/O and disk | io.weight/io.max、free bytes/inodes、artifact budget | 磁盘 IO 饱和但 CPU 空闲时的调度质量 |
| C14 | PID/FD exhaustion | pids.current/max、RLIMIT_NOFILE、systemd TasksMax | 外部 fork 量与进程句柄泄漏 |
| C15 | GPU/device claims | Kubernetes DRA 思路，仅存在真实 GPU 消费者时 | 设备独占／共享和内存不可抢占 |
| C16 | Heterogeneous nodes | Nomad feasible→ranking、node health/capability advert | Linux/Windows 不可互换；物理 target 必须匹配 |
| C17 | Autoscale | 只有存在多个节点／云实例消费者时引入 | 别为单机 Runtime 安装完整 Kubernetes |
| C18 | Capacity observability | OpenTelemetry metrics/trace：排队、调度、系统压力、实际利用率 | 每个采样都可映射 Job/Attempt/cgroup ID |
| C19 | Operator recovery CLI | systemctl、systemd-run、journalctl、psql、Windows sc/Job Object | Native-first；禁止写第二套进程树 manager |
| C20 | Workspace source isolation | Git worktree、文件锁/租约、只读 snapshot、可选 overlayfs | Workspace 写冲突与 Job 数应分开 |
| C21 | Artifact lifecycle | systemd State/CacheDirectory 与 tmpfiles、Git worktree remove | 确认所有消费者不可达才删除 |
| C22 | Release management | 现有 GitHub merge queue / CI / receipted release，A/B provider 硬证据 | installed image 与 source commit 精确匹配 |
| C23 | Explicit provenance | 按 LLVM/Rust digest、Rust toolchain lock、Git commit、源依赖闭包记录 | 不重复保存对系统无用的临时数据 |
| C24 | Runtime-only control traffic | Admin 操作独立于 ordinary admitted Job cap | 控制面被普通 Job 塞满时仍可停止、查询和恢复 |

## 推荐的最小现代目标表示：不用新增 Runtime 大框架

1. `Job`：用户期望与唯一请求身份；可处于 `pending/admitted/running/terminal`，不是一个内核进程。
2. `Attempt`：特定提供者、源快照和一次物理执行事实；不能对不透明副作用自动重放。
3. `Allocation`：按 CPU、memory、IO、pids 等资源和原生 cgroup/Job Object 绑定的实际分配；受内核观测而不是固定 Job 数约束。
4. `WorkspaceLease`：只保护确实互相冲突的文件效果，不作为全局任务数量限制。
5. `Scheduler`：从已接纳的 durable waiting queue 按资源可行性、Owner 公平权重和压力反馈派发；底层仍调用 systemd/Windows Job Object。
6. `Reconciler`：后台与交互入口共享一套执行结果/资源释放逻辑，但自身不受普通任务容量阻塞。
7. `Artifact`：可独立读取的原生停止与 Runner 证据；PG 终态、预留释放和 Metadata 在一个事务中提交。

**唯一剩余需要自研的东西应是 Ordivon 语义映射与薄适配器**：哪些 Job 可以放在哪个原生 Node、持久请求如何关联物理身份、外部效果不确定时怎样表达。OS 资源管理、PG 事务、Git 管理、队列基础算子、形式化验证都优先复用成熟实现。

### 推荐的释放／准入不变量（不是“永久 4 槽位”）

- 每一个物理运行任务具有准确的 systemd Unit 或 Windows Job Object 归属。Kernel 实际占用与 PG 表分离；无运行进程时，不能无限持有物理容量。
- Pending Job 不占用实际 CPU/RAM/PID。可以大量排队，但队列大小、数据库写入和磁盘资源仍由已有系统容量决定。
- 不允许通过资源可用性判断推导外部业务效果成功或失败。
- 如果某类任务的资源需求信息不充分，可以以 cgroup 实际压力渐进探索，而不是“一个 Job 固定一个槽位”。
- 满载只降低新的启动速率，**不关闭**取消、停止、观测、修复和发布管理入口。
- 允许 idle Owner 的资源借给其他 Owner；高优先级抢占只作用于证明可中断/可恢复的任务。
- CPU 空闲不代表内存、I/O、磁盘、GPU 空闲；也不代表外部 API 限额空闲。
- 资源请求/预算变化不得改变历史 Job 的 idempotency identity 或无证据地多派发 Attempt。

## 形式化与消费者证据矩阵

| 契约 | 最适合的成熟验证 | 必须保留的实际消费验证 |
|---|---|---|
| 同一 Attempt 至多一次物理派发 | Runtime 已有 TLA+/TLC、PG CAS | 真实 PG + Runner |
| 资源保守性：已分配资源不能超出可用份额 | TLA+/Quint 状态模型、SMT/线性约束 | cgroup/Windows 物理压力 |
| 取消不存在的 cgroup 不得伪造成功 | Kani 纯分类器、Hoare 前置条件 | systemd Unit/cgroup.events 回读 |
| 单条原生终止证据不能证明业务成功 | 类型/契约 + Kani | Artifact 与领域消费检查 |
| PG terminal + reservation + artifact 原子性 | PG SERIALIZABLE CAS、TLA 抽象 | PostgreSQL 18 真实事务/恢复 |
| 动态公平调度无长期饥饿 | DRF 数学性质、TLA temporal fairness | 不同 Owner 并发负载场景 |
| 可抢占/可恢复任务不得重复外部不透明副作用 | 效果模型、状态机、operation identity | 真实 native runner + domain receipt |
| 安装/升级后不混旧 writer 或 schema | 版本契约、精化检查 | Windows/Linux 实机部署与重启 |

**不得删除物理验收来伪造完成度**。纯数学函数证明不会证明内核路径及数据库身份；相反，重复的样例单元测试可以在其属性被执行过的形式化证明、实现精化、消费者验收完整覆盖之后删掉。

## 执行排序与实际验收条件

**P0.A — 控制面解耦并处理四个卡死预留：** 从普通 Job 池外的 OS 管理入口用精确 Unit/Invocation 身份确认系统状态；停止剩余原生进程组；在同一个 PG 原子终态路径中释放物理 reservation。要求 4 个历史 Attempt 的新状态有真实 kernel + PG 证据。**目前尚未成功。**

**P0.B — 删除固定 4 与每 Workspace=1 的容量语义：** 先分开 Pending 和 Running，把资源数量及 cgroup 可用份额作为输入，保存 resource allocation 的真实消费；工作树写租约独立维护。不能直接放开无限派发造成全机 OOM。

**P0.C — PG-only 源码：** 清除 MCP Cargo 中 `transactional-runtime` 的强制 feature，让 PG 路径不再链接 `rusqlite`；Win Native PG 切换后清理旧 SQLite 活动数据。

**P1 — 事件驱动调度与恢复：** 用原生 systemd/cgroup 事件 + PostgreSQL 通知代替 50ms 轮询；必要时引入按资源向量/Owner 权重的成熟公平调度模型。

**P1 — 管理面与发布：** 管理通道与普通 Job 的容量互不依赖；候选发布遵守已有 CI/GitHub merge queue 和实际安装回执。

**P2 — 理论与高级优化：** 经过实测才决定是否需要 DRF、Gradient2、GPU DRA、跨节点 Placement、弹性抢占；不要为一个 Linux+Windows 的小型系统照搬完整 Kubernetes/Nomad 控制面。

## 成熟参考源（复用思想和 API，不复制无关整体平台）

- Linux cgroup v2: https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html
- Linux PSI: https://docs.kernel.org/accounting/psi.html
- systemd resources: https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html
- systemd D-Bus: https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.systemd1.html
- Windows Job Object: https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects
- Kubernetes node-pressure and preemption: https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/
- Nomad scheduling: https://developer.hashicorp.com/nomad/docs/concepts/scheduling/how-scheduling-works
- Kueue: https://kueue.sigs.k8s.io/docs/concepts/
- Dominant Resource Fairness: https://www2.eecs.berkeley.edu/Pubs/TechRpts/2011/EECS-2011-18.html
- Netflix concurrency-limits: https://github.com/Netflix/concurrency-limits
- Envoy adaptive concurrency: https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/adaptive_concurrency_filter.html
- Tokio Semaphore: https://docs.rs/tokio/latest/tokio/sync/struct.Semaphore.html
- PostgreSQL SKIP LOCKED: https://www.postgresql.org/docs/current/sql-select.html
- Kani verification: https://model-checking.github.io/kani/

## 本轮操作回执

- 已实际使用连接的 Linux Runtime 对上述四个精确 Job 再发起取消；三项仍停止中，一项 native stop 未确认。**未强行修改 PG 数据**。
- 已用 Runtime 源码工具修正隔离分支的 cgroup 观测模型：新 `cgroup_population` 返回 `Option<bool>`，缺失的接口返回 UNKNOWN；旧 API 保持兼容；PG 新的停止决策器使用 Option，Kani 模型的 None 分支因此具有实际消费者。**源码写入成功，但尚未编译、测试、合并或部署**。
- 由于四个历史 Job 持续占据 PG 准入计数，新的 Linux `workspace.exec` 仍被拒绝。这不是当前已确认的 OS 资源瓶颈。
- 此文档仅反映本轮源码与接口证据；请在新原生管理入口可用、真实机内核观测取得后更新验收，不把计划候选标记为已安装。

## 数学化容量与调度契约草案（尚未实现）

**状态分离**：

- `QueueEntry(j)` 是已确认收到的工作请求，不属于物理资源消耗。
- `Allocation(j,n,t)` 是 Job 对节点 n 的一次具体物理资源占用，由 cgroup/Job Object 绑定；只有这种活动执行参与容量决策。
- `Observation(n,t)` 是系统在 t 时刻对 CPU、memory、IO、pids、磁盘及 PSI 的有作用域测量。缺失值是 UNKNOWN，不得补 0。
- `WorkspaceLease(j)` 只记录共享文件树上的互斥作用域；它不是任务执行的并发配额。
- `ExternalEffect(j)` 的已知/未知与 OS 进程占用无必然等价关系。

对于可比资源 i 的每个节点 n，在时刻 t 用 `C[n,i,t]` 表示可分配资源，`A[j,n,i,t]` 表示任务的获准分配量：只在资源确实声明了不可超额分配的语义时，才要求 `sum_j A[j,n,i,t] <= C[n,i,t]`。CPU time shares、内存 `memory.high` 等可借用/弹性资源不应伪装成固定不可超额容量，交由内核权重、压力反馈和高水位回收策略处理。实际 CPU／IO／内存耗用是观测值，不是 Job 数字。

**Owner 公平性**可参考加权 DRF：`dominant_share(owner) = max_i allocated(owner,i)/allocatable(node,i)`。当不同 Owner 同时排队时，优先帮助较低支配份额的 Owner；只有存在真实资源竞争时才执行公平性控制，允许其他 Owner 使用空闲资源。对没有资源估计的新任务，从小额可回收试运行和 PSI 反馈开始，不盲目假装资源需求已知。

**安全与活性（应进入现有 TLA+/Quint 验证体系，而不是新 DSL）：**

1. `G(PhysicalAttemptRunning -> BoundAllocationExists)`：实际运行的 Attempt 必须有对应的原生 cgroup/Job Object 分配身份。
2. `G(ReservationReleased -> KernelQuiescenceWitness || ValidIndependentTerminalWitness)`：不能靠单纯计时或任务名称释放仍在活动的物理资源。
3. `G(ExternalOutcomeUnknown -> !ClaimsSemanticSuccess)`：内核终止不构成外部业务效果成功证明。
4. `G((CancelIntent && NativeQuiescent && QualifiedEvidence && DurableStoreAvailable) -> F ReservationReleased)`：在对账服务有公平执行机会的假设下，资源最终回收；不能把“普通执行池有空槽”放入这个前提，否则正好重现本次死锁。
5. `G(PendingJob -> !ConsumesPhysicalAllocation)`：排队中的任务不占用进程分配量，其排队数据库与磁盘消耗由独立资源界限约束。

**增量验证顺序**：首先证明上述资源生命周期／公平性状态机不出现无端容量泄漏或饥饿；其次使用 Kani 验证 Rust 纯决策与资源向量的守恒/边界；再次使用真实 PostgreSQL 测试事务并发、Crash/restart CAS；最后在 Linux PSI+systemd 与 Windows Job Object 的真实压力任务下验证。没有实际观测不能标记证明通过。

**控制回路的稳定性**：动态调度不等于频繁改变一个并发上限；以资源压力变化为反馈，启动率和驱逐决策需考虑任务运行时间与资源重分配的滞后性。对 CPU/IO 的吞吐优先用内核权重治理，对内存实际压力采用非破坏性回收优先；只能中断已证明可恢复的批处理工作。必须用真实负载识别振荡风险，不自行发明没有消费者需求的 PID 算法。

**近期执行结论**：此草案优于把硬编码 `4` 改为一个更大的常数，但仍是 Specification/Candidate，并非已发布 Resource Scheduler。


## Implementation follow-through — 2026-11-08

The first implementation slice addresses O05/O06/O07/O10: exact native-stop
reconciliation, a cancellation recovery path outside ordinary Job admission,
kernel-backed observation wakeups, and honest Result availability. It preserves
the existing PG epoch and terminal transaction. A prior staged no-result fix was
insufficient on this machine because systemd had already removed all four bound
cgroups. Explicit removal evidence now distinguishes this case from UNKNOWN.
Kani production-classifier verification, strict Clippy and seven disposable
PG/systemd tests passed, including recovery after the client stops observing.
Production rollout and exact four-Job readback are recorded separately.

O01/O02/O03/O04 (resource admission, Workspace access contracts and persistent
queue scheduling), Owner fairness and Windows native PG cutover are not claimed
implemented by this slice. Their designs must distinguish resource requests from
hard limits, preserve exact idempotency and dispatch fencing, and prove actual
consumer behavior before replacing the existing capacity gates.


## Resource scheduler implementation follow-up, 2026-11-08

The prior first-batch status for fixed global/per-Workspace count gates is superseded in branch `fix/runtime-native-recovery-20261108`: count-based admission is removed from the Linux PG path. Durable pending Jobs, atomic resource allocations, native pressure observations, Workspace access conflicts, scoped source commitments and daemon scheduling are implemented. See the runtime/operator guide for the actual contract and verification bounds. Deployment qualification and exact commit/binary receipts accompany the installed release; source presence alone is not installation evidence. Windows PG-only cutover, heterogeneous cross-node placement, weighted owners, preemption and replacement of the advisory transaction lock are not claimed by this scheduler change.
