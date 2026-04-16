# 03_File_Operations: 二进制防护与精密 IO 管理

## 一、 工程思想：零信任的文件交互 (Zero-Trust Content)

在 Agent 系统中，文件 I/O 不仅仅是磁盘读写，更是 **“上下文注入 (Context Injection)”**。

### 1. 保护 LLM 上下文 (Token Protection)
如果 Agent 错误地尝试读取一个 100MB 的日志文件或一个二进制可执行文件，会发生两件事：第一，上下文窗口被瞬间撑爆；第二，非 UTF-8 字符会导致令牌解析器崩溃。
`claw-code` 的核心思路是：**在数据到达 LLM 之前，必须经过“熔断器”和“扫描仪”。**

### 2. 变更的原子化与可视化 (Structured Diffing)
简单的 `write_file` 容易丢失历史信息。系统提倡通过 **“结构化补丁 (Structured Patching)”** 来返回结果。这不仅方便人类审计，也方便 Agent 验证自己的修改是否符合预期。

---

## 二、 具体实现逻辑 (Technical Implementation)

### 1. 二进制自动检测 (Magic NUL Sniffing)
系统并不依赖文件扩展名（扩展名极易伪造），而是采用直接扫描缓冲区内容的方法：
```rust
fn is_binary_file(path: &Path) -> io::Result<bool> {
    let mut file = fs::File::open(path)?;
    let mut buffer = [0u8; 8192]; // 采样前 8KB
    let bytes_read = file.read(&mut buffer)?;
    // 精华：检查内容是否包含 NUL (\0) 字节
    Ok(buffer[..bytes_read].contains(&0))
}
```
**原理**：只有二进制文件（图片、二进制包）才会频繁包含空字节，而标准的 UTF-8 文本文件极少出现这种字符。

### 2. 资源熔断器 (Resource Circuit Breaker)
为了防止过度开销，系统设定了强制边界：
- **`MAX_READ_SIZE`**: 10 MB。
- **`MAX_WRITE_SIZE`**: 10 MB。
如果超过此限制，工具会直接中断返回 Error，而不是尝试处理它。

### 3. 分窗口读取 (Windowed Reading)
为了应对大文件，它实现了 `TextFilePayload` 结构，支持 `offset` 和 `limit` 参数：
- LLM 可以请求读取文件的第 100 到 200 行。
- 回包中会附带 `totalLines` 元数据，让 Agent 知道该文件还有多少后续内容。

### 4. 结构化 Diff 生成 (make_patch)
在使用 `edit_file` 后，系统会生成符合 `diff` 格式的行差异描述：
- `-` 前缀代表删除，`+` 前缀代表新增。
- 即使是全量写入，系统也会尝试计算并返回 `structuredPatch`，让审计逻辑能清晰看到变更点。

---

## 三、 对 Quant-Agent 的应用建议
1. **行情数据库保护**：我们的 DuckDB 数据库文件属于二进制大文件。如果您在对话中问：“帮我看看 market.duckdb 里的内容”，后台必须自动识别出这是二进制并拒绝 `cat` 操作，而是提示 Agent 使用 SQL 查询接口。
2. **Wiki 大量内容自动同步**：目前的 `WikiService` 是全量追加。如果您的 Daily Log 在几个月后变得几万行，可以参考其 `offset/limit` 设计，在导出给 AI 分析时仅抓取“最近 50 次交互”，保护我们的上下文 Token 成本。
