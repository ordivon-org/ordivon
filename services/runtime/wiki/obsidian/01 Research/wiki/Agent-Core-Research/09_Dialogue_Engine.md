# 09_Dialogue_Engine: Agent 的对话引擎与元认知设计

## 一、工程思想：Agent 需要"自知"——知道自己还剩多少"油"

大多数 Agent 框架让 LLM 尽情运行，直到 API 报错才知道超出限制。`claw-code` 的 `QueryEnginePort` 在每一轮对话后都会**主动计算并核查自己的预算消耗**，这是一种 Agent 的"元认知"设计。

### 1. 双保险预算机制
系统设置了两道独立的安全阀：
- **`max_turns`（轮数保险）**：无论如何，超过 N 轮就停止递进。
- **`max_budget_tokens`（Token 保险）**：预测下一轮的 Token 消耗，如果超额则提前刹车。

这两道保险独立触发，互不依赖，确保不会有任何意外导致无限消耗。

### 2. 流式事件协议（Streaming Event Protocol）
对话的每个阶段都被映射为独立的事件，而不是一个整体响应。这是现代 Agent UI 的标准范式，让前端能实时呈现 Agent 的"思考过程"：

```
message_start    → 会话开始，携带 session_id 和 prompt
command_match    → 识别到了哪些命令（可能同时触发多个）
tool_match       → 匹配到了哪些工具
permission_denial → 哪些工具因权限被阻断
message_delta    → 流式输出内容（流式 token 渐进展示）
message_stop     → 终止，携带用量统计和停止原因
```

---

## 二、具体实现逻辑

### 1. 预算自检机制
```python
# 每轮提交后，预测累计 token 消耗
projected_usage = self.total_usage.add_turn(prompt, output)

# 如果预测下轮将超出预算 → 提前停止
if projected_usage.input_tokens + projected_usage.output_tokens > self.config.max_budget_tokens:
    stop_reason = 'max_budget_reached'
```

### 2. 多重停止原因的精确建模
```python
stop_reason: str  # 有三种明确值：
# 'completed'          - 正常完成
# 'max_turns_reached'  - 超过轮数上限
# 'max_budget_reached' - Token 预算耗尽
```
这种精确建模让调用者（前端或上层逻辑）能根据停止原因采取不同的动作——比如预算耗尽时允许用户选择"继续"（扩充预算）或"放弃"。

### 3. Transcript（成绩单）与 Session（会话）的分离
```python
# transcript_store: 记录完整的对话原文，用于人类审阅和 wiki 同步
# mutable_messages: 维护发往 LLM 的滑动窗口，用于上下文控制
```
两者独立维护：`transcript` 是永久记录（不会被压缩丢弃），`messages` 是发给 AI 的工作窗口（会被压缩管理）。

---

## 三、对 Quant-Agent 的应用建议

1. **聊天面板升级**：我们的 `chatPanel.ts` 目前只显示最终回复。可以重构为流式事件消费模式：
   - 先显示 `⚙ 正在获取市场数据...`（当 tool_match 触发时）
   - 再显示 `⚠ 权限检查...`（当 permission 事件触发时）
   - 最后流式展示 AI 回复文字
   这会极大提升用户体验，让用户感知到 AI 正在"做事"而不是无响应地加载。
2. **Token 成本 Dashboard 面板**：借用 `message_stop` 的 `usage` 字段，在系统日志面板中显示每次对话消耗的 Token 数和估算人民币费用（DeepSeek-chat ≈ ¥0.001/1K tokens）。
3. **预算告警机制**：在 `api_server.py` 中积累当日总 `token` 消耗，当超过阈值（如 50万 tokens/日）时，在 Dashboard 上触发红色告警。
