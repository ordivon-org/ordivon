# 07_Recovery_Recipes: 故障自愈配方体系

## 一、工程思想：将"失败"视为已知的一等公民

大多数系统的错误处理是被动的：出错了打日志、抛异常。`claw-code` 的做法截然不同——**将 7 类已知故障场景提升为一等公民，为每一类都预定义结构化的"康复配方"**。

### 1. 失败的分类学（Failure Taxonomy）
不是所有错误都应该以相同方式处理：

| 故障类型 | 自愈步骤 | 升级策略 |
|---------|---------|---------|
| `TrustPromptUnresolved` | 自动接受信任提示 | 通知人类 |
| `StaleBranch` | Rebase → 重新构建 | 通知人类 |
| `McpHandshakeFailure` | 重试握手(5s超时) | **直接中止** |
| `PartialPluginStartup` | 重启插件 → 重握手 | 记录并继续 |
| `ProviderFailure` | 重启 Worker 进程 | 通知人类 |

**核心洞察**：不同故障有不同的"容忍度"——MCP 握手失败选择中止是因为继续执行会产生更危险的副作用（错乱的工具状态）；而部分插件启动失败则可以"记录并继续"，因为其影响是局部的。

### 2. 一次尝试原则（One-Shot Auto-Recovery）
所有配方的 `max_attempts = 1`。这不是懒惰，而是理性设计：
- 如果第一次自愈成功，无需人类介入。
- 如果第一次失败，**立即升级**而不是盲目重试——避免在错误路径上浪费时间甚至造成更大损害。

### 3. 升级策略分级（Escalation Policy）
- `AlertHuman`：通知人类，但系统继续运行其他任务。
- `LogAndContinue`：静默记录，系统以降级模式运行。
- `Abort`：彻底停止。用于无法在不确定状态下继续的情况。

---

## 二、具体实现逻辑

### 1. 结构化配方查找（recipe_for）
```rust
pub fn recipe_for(scenario: &FailureScenario) -> RecoveryRecipe {
    match scenario {
        FailureScenario::McpHandshakeFailure => RecoveryRecipe {
            steps: vec![RecoveryStep::RetryMcpHandshake { timeout: 5000 }],
            max_attempts: 1,
            escalation_policy: EscalationPolicy::Abort, // MCP失败直接中止
        },
        FailureScenario::PartialPluginStartup => RecoveryRecipe {
            steps: vec![
                RecoveryStep::RestartPlugin { name: "stalled" },
                RecoveryStep::RetryMcpHandshake { timeout: 3000 }, // 重启后再握手
            ],
            escalation_policy: EscalationPolicy::LogAndContinue, // 插件失败可降级
        },
        // ...
    }
}
```

### 2. 恢复事件追踪（RecoveryContext）
每次恢复尝试都发射结构化事件，可被外部监控捕获：
```rust
RecoveryEvent::RecoveryAttempted { scenario, recipe, result }
RecoveryEvent::RecoverySucceeded
RecoveryEvent::RecoveryFailed
RecoveryEvent::Escalated  // 触发升级策略
```
这意味着故障恢复本身是**可观测**的，可以接入告警系统或写入运维日志。

### 3. 部分成功的处理（PartialRecovery）
如果一个配方含多步骤，且中途某步失败：
- 返回 `PartialRecovery { recovered: [步骤1], remaining: [步骤2] }`
- 不是简单的成功/失败，而是精确记录走了多远

---

## 三、对 Quant-Agent 的应用建议

1. **API 熔断器升级**：我们目前对 DeepSeek API 超时的处理是简单地返回 `[System Fallback]`。可以引入类似的配方体系：
   - 第一次超时 → 自动重试一次（超时时间加倍）
   - 第二次超时 → `AlertHuman`（在 Dashboard 上显示醒目的 ⚠️ 警告）
   - 第三次超时 → 切换到备用模型（如本地 ollama）
2. **数据库断连恢复**：DuckDB 有时会因为文件锁而失败。我们可以为 `DB_CONNECTION_FAILED` 场景定义配方：重试5次 → 切换只读模式 → 通知用户。
3. **Wiki 写入失败保护**：Obsidian 文件有时会被编辑器锁定。`WikiService` 可以参考此模式，在 `IOError` 时先尝试 100ms 后重试，失败则写入临时缓冲区，不影响主链路。
