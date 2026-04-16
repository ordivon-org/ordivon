# 10_Prompt_Router: 自然语言轻量级路由引擎

## 一、工程思想：在 LLM 之前的"快速通道"

向 LLM 发送每一个提问都需要付出 Token 成本和延迟代价。`claw-code` 实现了一套**无需调用 LLM 的轻量级自然语言路由器**，在用户提问到达 AI 之前，先通过关键词评分自动预路由工具和命令。

### 1. 三字段联合评分
每个工具/命令都有三个描述字段：
- `name`：工具名（如 `BashTool`）
- `source_hint`：原始来源（如 `tools/bash.ts`）
- `responsibility`：职责描述（如 `executes bash commands in a sandbox`）

用户的提问会被 tokenize 成词集合，每个词匹配上述三个字段后累积得分。**得分越高，越有可能被调用**。

### 2. 命令优先于工具的语义设计
在结果排序中，`command`（拥有更高优先级语义的快捷操作）总是先于 `tool`（底层执行工具）出现在结果列表中。这模拟了人类操作系统的"命令 > 工具"抽象层次。

---

## 二、具体实现逻辑

### 1. Token 化 + 多字段联合评分
```python
def _score(tokens: set[str], module: PortingModule) -> int:
    haystacks = [
        module.name.lower(),         # 工具名
        module.source_hint.lower(),  # 文件路径提示
        module.responsibility.lower() # 语义描述
    ]
    score = 0
    for token in tokens:
        if any(token in haystack for haystack in haystacks):
            score += 1  # 每命中一个字段 +1 分
    return score
```

### 2. 分离的提示词预处理
```python
# 用户输入被标准化：大写→小写，/ 和 - 替换为空格
tokens = {t.lower() for t in prompt.replace('/', ' ').replace('-', ' ').split() if t}
```
这确保了 `BashTool`、`bash-tool`、`bash/tool` 在词分割后对"bash"这个词的命中是等价的。

### 3. 工具筛选模式（Simple Mode）
系统还提供了一个极简模式，只暴露最核心的三个工具：
```python
if simple_mode:
    tools = [m for m in tools if m.name in {'BashTool', 'FileReadTool', 'FileEditTool'}]
```
这在资源受限的场景（如嵌入式 Agent 或快速演示）中非常有用，让 Agent 聚焦于最基础的能力。

---

## 三、对 Quant-Agent 的应用建议

1. **意图预分发**：我们可以在 `chatPanel.ts` 中实现轻量级客户端路由。当用户输入"看一下 BTC 价格"时，前端直接调用行情 API 而不经过 AI；只有复杂分析请求才路由至 Hermes。
2. **交易命令快速通道**：为高频操作（如"平仓"、"显示持仓"）定义固定的 slash 命令（`/close`、`/positions`），跳过 AI 解析直接执行，降低延迟和成本。
3. **工具描述的语义化**：这个路由器的效果高度依赖 `responsibility` 字段的质量。未来我们为 Quant-Agent 扩展工具时，应为每个工具写清晰的职责描述——这既是给人类看的文档，也是给路由器用的搜索素材。
