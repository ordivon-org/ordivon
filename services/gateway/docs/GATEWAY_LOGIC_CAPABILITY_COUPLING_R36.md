# Gateway R36：Thought → Logic → Capability 与依赖边界审计

- 审计基线：正式安装 SourceCut `498ab3b10f11c2ca4f0eedd11c60a81ec406ae30`、Gateway `0.10.20`。
- 目标：以消费者实际问题而非文件名划分逻辑/能力；不增设第二套 Runtime/Host/Security 权威。
- 证据层次：生产 `system.describe` 是路由投影；安装 SourceCut 与源码、正式 Host 消息和 Native Runtime Job 分开核验；本 R36 源码变更仅是隔离候选，**不是已安装更新**。

## 一、第一性原理：八个问题、两类 Thought、具体 Capability

| 问题 | 正向 Thought（构造） | 逆向 Thought（反例） | Logic 表征/不变量 | Capability / 自然 Owner |
| --- | --- | --- | --- | --- |
| 能力是什么 | 需求→能力谓词 | 反证是否只是描述 | `routing.py`, `capability_projection.py`；路由键与能力名严格相等 | `capabilities/discovery.py`、Skills；用户任务 Owner |
| 谁承载 | 最小自然 Owner | 找不到/重复/过期 Owner | Route + Truth boundary | `service.py` 路由；Runtime/Host/Skills |
| 谁能调用 | 身份→对象→允许操作 | 伪造 Actor、错配 Principal/请求 | `ingress_identity`、Target、AuthZEN 决策绑定 | `security/*`；Security PDP，Owner 最终执行准入 |
| 协议如何变化 | 稳定 MCP ABI | SDK 重协商与旧 Schema 差异 | `owner_protocol.py`、`execution_refs.py` | `transport/upstream.py`；官方 MCP SDK |
| 效果如何执行 | 提交精确请求 | 回包丢失后重试导致双重效果 | `clientRequestId`、`operationRef` 精确绑定 | `execution/commands.py`；Runtime PG Job |
| 如何观察 | 取原请求/Job/Artifact | 超时不是未执行；observe 可派发 | Job 与 Attempt 不等价，OWNER Result ≠ Domain Success | `execution/observations.py`；Runtime |
| 如何处理 UNKNOWN | 谓词+证据+下一检验 | 相反证据/未观测/失败探测 | `runtime_status.py`、`readiness_inquiry.py`、`readiness_confirmation.py` | Owner status 只读观测；不新建效果 |
| 如何演进 | 精化、稳定公开契约 | 正反例、消费者回归、Source≠Installed | `mcp-surface.json`、`enforcement-surface.json`、形式化模型 | `tests/`、`formal/`、原安装流程 |

Thought LEGO 指导逻辑而不需要建立单独运行时服务：正向运用契约、信息隐藏与构造性推理；逆向运用反证、故障注入、差分验证、错误分类和最小阻断集。逻辑 LEGO 规定输入/输出、pre/post/inv、未观测的状态与自然 Owner；能力 LEGO 使用成熟 MCP SDK 和真实 Owner 执行对应行为。

## 二、真实模块图与依赖

- `mcp_server.py`：唯一向外注册 ABI，调用 Security 入口、薄 Service；不解析 Owner 业务真实状态。
- `service.py`：注入 Owner Caller 与 Route，向 discovery/host/execution/release 委托，不拥有工作状态。
- `logic/`：纯路由、Refs、Owner response 检验、Readiness 正反假设；`owner_protocol.py` 现在声明 OwnerCaller Port 与 OwnerCallError。
- `capabilities/`：发现、Host Work 协调、执行命令、观察和 Release 各自委托自然 Owner，不导入具体 MCP 传输。
- `security/`：Cloudflare/JWT 入口验证、Principal/Issuer、目标投影、PEP/AuthZEN、Owner credential 文件；授权来自 Security，不来自 capabilities 的用户字段。
- `transport/`：HTTP/MCP SDK Caller、连接池与错误编码；`owner_error_projection.py` 将已验证 Host domain-error 限定字段输出给客户端。

依赖方向：`mcp_server → security + service + transport`，`service → capabilities + logic`，`capabilities → logic.OwnerToolCaller`，`transport → logic + security.owner_identity`（仅现有上游连接凭据），**不得 `capabilities → transport` 或 `logic → security/transport/capabilities`**。

## 三、本轮拆解的真实反例

原路径：`security/owner_identity.py` 不只处理私有 credential，还构造 Host 错误输出；`capabilities/host/work.py` 从 Security 取得 MCP 错误展示函数。现役 Host 对超前游标返回 `CONFLICT`、`topic_resume_cursor_ahead` 和真实 TopicHigh；Gateway `structuredContent.error` 保留类型信息但公开文字只有 `owner tool returned error: host/topic.resume`。连接器只显示错误文字时，反例原因被压缩。

本轮候选：
1. `OwnerCallError` 类型移到 `logic/owner_protocol.py`，凭据仍在 Security。
2. `transport/owner_error_projection.py` 成为唯一 MCP `CallToolResult` 投影；对 Host 正确 v1 domain error、准确 Owner 身份，仅展示有限白名单的 code/reason/resourceKind/suggestedAction/evidenceBoundary/游标整数，不展示任意原始 prose；保留既有完整 `structuredContent` 兼容合同。
3. `mcp_server.py` 在 Host tools 注册时注入 Error Projector。 `capabilities/host/work.py` 接受函数参数而不导入 transport/security 的具体投影；业务调用保持原 Host Work 参数校验和 Owner 委托。
4. `formal/check_owner_status_contract.py` 将模拟 `runtime.describe` 的响应补上现有严格要求 `schemaVersion=1`，不放宽 `logic/runtime_status.py` 验证器。
5. 原有 `mcp-surface.json` 42 名称 / epoch17 / input ABI 完全不修改。新增测试正向确认 Host Domain 关键字段可见、逆向确认未认证字段不显示、其他 Owner 错误保持原样。

## 四、后续以真实反例为优先的最小拆解

P0：源码修补经 Gate 后，验证原生 MCP 调用 `topic.resume` 错误文字和结构化错误在真正 SDK/ChatGPT 连接路径均可见；无此验证不称 Installed 合格。
P1：按用户需求和服务调用事实审计 `transport/upstream.py` 的 SDK 模式分支、私有凭据读取、错误解码和连接管理，避免不必要的传输重实现。
P1：`capabilities/discovery.py` 的 Owner Status Probe（有副作用边界）与纯 Readiness 逻辑隔离；复用 `logic/runtime_status.py` 的严格契约，不能只检查选中目标而忽略矛盾兄弟目标。
P1：Release 与一般执行的授权、状态、效果认定保持分离。 `job.observe` 是具有可能触发派发的原生 Owner 工具，不应当被称为任意安全只读观测。
P2：继续按实际 SDK schema、Git/安装服务和用户消费来退役空壳路由与重复模块。Research 的组合发现不是科学任务已执行/已正确。

## 五、验收条件和已知证明范围

- `mise run gateway:verify`：本候选原有测试、Ruff、48 组 B01 Route 样本、100 组 B03 Status Pair/9 个 Inventory Case 通过。
- 仓库架构检查、`git diff --check`：复核并通过才能作为源码候选。
- `mise run gateway:formal:verify`：执行时因未找到符合锁文件 SHA 的 TLA+ JAR 退出；不能报告为模型 PASS/FAIL。
- `Git commit` ≠ `PR merge` ≠ `正式安装` ≠ `真实跨服务消费`。R36 本轮只签收实际完成阶段，不触碰现役 /opt release、Security token 或其他 Agent Workspace。
