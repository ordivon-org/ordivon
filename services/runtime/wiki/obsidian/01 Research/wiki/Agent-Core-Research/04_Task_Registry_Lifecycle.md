# 04_Task_Registry_Lifecycle: 任务状态机与生命周期管理

## 一、 工程思想：状态解耦与后台化 (Stateful Decoupling)

在复杂的开发任务中，AI 常常需要执行耗时极长的命令（如编译整个项目或跑大型回测）。

### 1. 从“同步等待”到“注册中心”模式
传统的 Agent 往往是：发出命令 -> 等待结果 -> 下一步。
`claw-code` 采用了 **“任务注册中心 (Task Registry)”** 的异步思维：
- Agent 创建任务后，获得一个 `task_id`。
- Agent 可以转而去处理其他事情，或者周期性查询任务状态。
- **意义**：这让 Agent 具备了处理“并行任务”或“耗时守候任务”的雏形。

### 2. 原子状态的可追溯性
每一个任务都被赋予了明确的状态生命周期。这确保了当 Agent 崩溃或重启时，它能通过 Registry 重新找回进度。

---

## 二、 具体实现逻辑 (Technical Implementation)

### 1. 任务记录结构 (TaskRecord)
系统中定义了极其详尽的任务元数据：
```rust
pub struct TaskRecord {
    pub id: String,
    pub status: TaskStatus,
    pub command: String,
    pub output: String,      // 累积的标准输出
    pub exit_code: Option<i32>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub assigned_team: Option<String>,
}
```

### 2. 线程安全的注册表 (DashMap)
在 Rust 实现中，由于 API 是多线程并行的，系统使用了 `DashMap`（一种高性能的并发哈希表）来全局存储 `TaskRegistry`：
- **`create`**: 生成 ID 并存入 Map。
- **`append_output`**: 随着后台进程的运行，持续将 stdout/stderr 写入对应的记录，实现流式进度追踪。
- **`stop`**: 强制向后台进程发送 Terminate 信号。

### 3. 状态转化机 (State Machine)
任务状态严格遵循以下流转：
- `Created` -> `Running` -> `Completed` (Success/Failed)
- `Running` -> `Stopped` (User/Agent Interruption)

系统通过 `TaskUpdate` 工具接口，允许 Agent 显式地标记任务进度（例如：“已完成 50%”），这种元数据反馈对于长链路任务至关重要。

---

## 三、 对 Quant-Agent 的应用建议
1. **长时回测管理**：对于一次耗时 10 分钟的 BTC 历史回测，我们的 Agent 不应该傻等。我们可以引入此处的 `TaskRegistry`：
    - AI 发起回测请求 -> 返回 `task_id`。
    - 后端启动独立 Python 策略进程。
    - 后台进程通过 `append_output` 将当前的盈亏比、进度实时刷入 Registry。
    - 对话框里，AI 可以回一句：“回测正在后台运行，我会监控它并在完成后提醒您。”
2. **多进程同步锁**：学习其 `DashMap` 的并发思路，确保当多个 WebSocket 推送行情数据时，后端解析状态不会发生竞争。
