# 05_MCP_LSP_Bridge: 协议桥接与跨应用能力扩展

## 一、 工程思想：协议即插件 (Separation of Protocols)

为什么 `claw-code`（和 Claude Code）如此强大？因为它不仅仅是在操作文件，它还在利用 **“外部协议”** 增强自己的大脑。

### 1. 技术栈无关的工具抽象
Agent 本身并不理解复杂的 LSP（语言服务器协议）或 MCP（模型上下文协议）握手过程。它只看到一组通用的“工具接口”。
- **桥接器模式 (Bridge Pattern)**：后端充当了翻译官，将 Agent 的“查找符号”意图转化为复杂的 JSON-RPC LSP 请求。
- **好处**：这种设计让 Agent 的核心逻辑非常轻量，所有的协议复杂性都被隔离在了 `runtime` 层的 Registry 中。

### 2. 构建开放生态 (The MCP Vision)
通过集成 MCP，Agent 可以瞬间拥有访问 Google Search、GitHub Issues、Slack 甚至各种实时数据源的能力，而无需为每个应用重写工具代码。

---

## 二、 具体实现逻辑 (Technical Implementation)

### 1. MCP 生命周期桥接 (McpToolRegistry)
在 `mcp_tool_bridge.rs` 中，系统维护了一个动态的 MCP 服务器池：
- **能力发现**：当一个新的 MCP 服务器连接时，Registry 会扫描它支持的所有工具和资源，并动态地将它们“映射”给 Agent 的 `execute_tool` 接口。
- **状态追踪**：它会追踪每条链路的 Auth 状态和 Disconnects。
- **精华逻辑**：系统实现了 `list_mcp_resources`，这让 Agent 能看到除了普通文件之外的“虚拟资源”（如外部 API 的返回结果）。

### 2. LSP 语言智能感知 (LspRegistry)
这是它超越通用 Agent 的关键。它通过 LSP 获取代码的深度静态分析数据：
- **`symbols`**：让 Agent 知道代码里定义了哪些类和方法，而不是只能暴力 grep。
- **`references`**：让 Agent 在修改方法命名时，能瞬间找到所有调用点。
- **`hover`**：获取类型定义和注释文档。
- **实现细节**：它在后台维护了一个特定语言服务器的 Client 实例，并通过 `registry.dispatch(action, path, line, character, query)` 将请求精准投送。

---

## 三、 对 Quant-Agent 的应用建议
1. **外部量化工具集成**：我们可以利用 MCP 协议，将您的 Quant-Agent 与 TradingView 的公开 API 或您自建的“因子计算器”连接。这意味着 AI 只要通过简单的 MCP 描述，就能学会调度复杂的外部行情处理工具。
2. **代码级策略审计**：利用 LSP 插件，AI 助手在检视您的量化策略代码时，将不再是凭空猜测，而是能准确识别出变量的作用域和类型冲突（例如：`open_price` 被错误地当成了 `volume` 处理）。
3. **插件式架构设计**：学习其“注册中心”模式。未来您可以像安装插件一样，给 Quant-Agent 增加一个“预测模型插件”或“套利监控插件”，而后端会自动完成工具挂载。
