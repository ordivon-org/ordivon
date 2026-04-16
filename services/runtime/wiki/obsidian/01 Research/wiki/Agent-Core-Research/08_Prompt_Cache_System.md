# 08_Prompt_Cache_System: LLM 请求指纹与缓存可观测性

## 一、工程思想：让每一分 Token 开销都可见可溯

LLM API 的费用是无形的——你看不到钱是从哪里漏走的。`claw-code` 构建了一套完整的**请求指纹体系**，让缓存命中/失效变得完全透明可观测。

### 1. 请求的四维指纹
每个发向 Anthropic API 的请求，都被分解为四个独立的哈希签名：
- **model_hash**：使用的模型名称
- **system_hash**：系统提示词
- **tools_hash**：工具定义（包括所有工具的 schema）
- **messages_hash**：对话历史

任何一个维度发生变化，系统都能精确知道**是什么导致了缓存中断**，而不是笼统地说"缓存 miss 了"。

### 2. "预期中断"与"异常失效"的区别
这是本模块最精髓的设计：
- **预期中断（Expected）**：你改了系统提示词，当然缓存会失效，这是正常的。
- **异常失效（Unexpected）**：请求的四个指纹完全没变，但缓存读取的 Token 数量却骤降 2000+——这说明 Anthropic 服务端的缓存在你不知情的情况下失效了，这是需要警惕的成本泄漏。
  
区分两者，让运维人员能专注于追查"真正的缓存不稳定"，而不被正常的缓存更新行为淹没。

---

## 二、具体实现逻辑

### 1. FNV 哈希签名（快速、无加密开销）
```rust
// FNV-1a 哈希，专为短字符串设计，速度远快于 SHA256
const FNV_OFFSET_BASIS: u64 = 0xcbf29ce484222325;
const FNV_PRIME: u64 = 0x00000100000001b3;

fn stable_hash_bytes(bytes: &[u8]) -> u64 {
    let mut hash = FNV_OFFSET_BASIS;
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}
```
每个请求的四个组成部分（model / system / tools / messages）被分别序列化为 JSON 再进行哈希，得到四个 `u64` 签名。

### 2. 缓存中断检测逻辑（detect_cache_break）
```rust
// 核心判断：如果 token 下降超过阈值（默认 2000），才触发中断分析
let token_drop = previous.cache_read_input_tokens - current.cache_read_input_tokens;
if token_drop < config.cache_break_min_drop { return None; }

// 检查四个指纹，确定中断原因
if previous.system_hash != current.system_hash { reasons.push("system prompt changed"); }
if previous.tools_hash != current.tools_hash  { reasons.push("tool definitions changed"); }

// 如果没有找到任何原因 → 这是异常失效
let unexpected = reasons.is_empty() && elapsed < prompt_ttl;
```

### 3. 磁盘级缓存层（Completion Cache）
除了 Anthropic 服务端的 prompt cache，系统还在本地磁盘上实现了一层请求响应缓存：
- 请求完整签名 → HASH → `~/.claude/cache/prompt-cache/{session}/{hash}.json`
- TTL: completion 缓存 30秒，prompt state 缓存 5分钟
- 版本控制：缓存条目包含 `fingerprint_version`，升级后自动淘汰旧格式

---

## 三、对 Quant-Agent 的应用建议

1. **DeepSeek API 成本追踪**：我们目前对 API 调用费用一无所知。可以参考此设计，在 `api_server.py` 中记录每次调用的 `input_tokens` 和 `output_tokens`，并在 Dashboard 上展示当日累计成本。
2. **系统提示词缓存优化**：我们每次调用 Hermes 时都会重新发送完整的市场上下文（K 线数据）。可以在上下文不变时（价格在一定范围内未发生显著变化）复用上一次的上下文，节约 Token 消耗。
3. **K 线数据的哈希签名**：借用其四维指纹思想，我们可以对 BTC/ETH 的多周期 K 线数据实现哈希缓存：`hash(BTC-15m-latest) + hash(ETH-1h-latest)` → 如果与上次相同，则跳过重新生成上下文，复用已有的分析结论。
