# 01_Security_and_Permission: Agent 权限分级与命令启发式阻断

## 一、 工程思想：从“事后拦截”到“事前预判”

在 `claw-code` 的架构中，Agent 的工具调用逻辑遵循 **“防御式编程”** 的最高原则。

### 1. 权限分级模型 (Tiered Permission Model)
Agent 并非处于全开或全关的状态，而是通过四个颗粒度进行降级：
- **ReadOnly**: 仅允许观察（ls, cat, grep）。
- **WorkspaceWrite**: 仅允许修改项目目录文件。
- **Prompt**: 敏感操作必须由人类通过交互式 UI 确认。
- **DangerFullAccess**: 允许修改系统配置、执行网络请求等高危操作。

### 2. 启发式命令分类 (Heuristic Command Classification)
**核心思想**：Agent 在执行 Bash 命令前，会先对其进行语义层面的分类。系统并不信任 AI 发出的所有命令。
- 如果当前处于 `ReadOnly` 模式，系统会检查命令是否在“白名单”中（如 `cat` 是安全的，而 `cat > file.txt` 是不安全的）。
- 这种逻辑将“代码能力”与“执行风险”在分发层就进行了隔离。

---

## 二、 具体实现逻辑 (Technical Implementation)

### 1. 权限执行器 (PermissionEnforcer)
在 Rust 实现中，通过 `EnforcementResult` 枚举定义了两种明确的终态：
```rust
pub enum EnforcementResult {
    Allowed, // 允许执行
    Denied { // 拒绝执行，并附带详细原因
        tool: String,
        active_mode: String,
        required_mode: String,
        reason: String,
    },
}
```

### 2. Bash 指令的黑白名单过滤 (Regex Heuristics)
系统通过极其详尽的字符串过滤逻辑来判定一个命令是否为“只读”：
- **白名单常用指令**：`cat`, `head`, `tail`, `ls`, `grep`, `rg`, `jq`, `git log` 等。
- **高危标志位阻断**：
    - 检测重定向符号（`>` 或 `>>`）。
    - 检测原地修改标志（`--in-place` 或 `-i`）。
    - 检测交互式标志（`python -i` 或 `node` 进入 REPL）。

**代码示例 (逻辑伪码)**：
```rust
fn is_read_only_command(command: &str) -> bool {
    let first_token = command.split_whitespace().next().unwrap_or("");
    
    // 检查首个 Token 是否在安全工具列表
    let safe_tools = ["cat", "ls", "grep", "git status", ...];
    let is_safe_bin = safe_tools.contains(&first_token);

    // 二次指纹校验：即使指令安全，参数可能不安全
    let has_redirect = command.contains(" > ") || command.contains(" >> ");
    let has_inplace = command.contains("-i ") || command.contains("--in-place");

    is_safe_bin && !has_redirect && !has_inplace
}
```

### 3. 工作区边界校验 (Workspace Boundary)
在进行写操作前，系统会强制执行 `validate_workspace_boundary`：
- 将相对路径转换为规范化的绝对路径。
- 使用 `starts_with` 校验路径是否逸出了用户设定的 `workspace_root`。
- **防逃逸**：它会显式检查 `symlink_metadata`，防止 Agent 通过软链接跳转到系统盘敏感目录。

---

## 三、 对 Quant-Agent 的应用建议
1. **行情导出保护**：我们的 `WikiService` 在写入 K 线数据时，可以引入类似的“工作区边界校验”，防止 AI 通过注入文件名路径（如 `../../secrets.txt`）来破坏您的知识库。
2. **交易执行锁**：在执行实盘下单指令前，引入 `Prompt` 模式分级，强制人类用户在前端 Dashboard 进行二次确认。
