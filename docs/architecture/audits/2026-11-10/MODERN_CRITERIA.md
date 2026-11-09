# MODERN_CRITERIA — 可检查的 2025–2026 现代化准则

**SourceCut** `ef17d6879d12faa61fff3bb762b0d500d73c9113`。本判定表接受各技术栈的等价成熟机制：**不要求把 Ordivon 改写成 Nx/Turborepo 或强制 apps 薄、packages 厚的统一模板**。只有确凿反向依赖才判违规；评分不替代证据。

## 12 项可检查项

| ID | 判定项 | PASS 需要的源码/执行见证 | 不符合/部分符合的典型证据 | 不适用时 |
| --- | --- | --- | --- | --- |
| M01 | 有限界上下文/责任内聚 | manifest Owner 和公开语义入口一致；包内变化原因一致 | 同一功能有两个权威模型；跨 Owner 直接写状态 | 无独立模块则 N/A |
| M02 | 六角/依赖方向 | 核心模型不直接依赖具体 OS/数据库/HTTP 适配；port + adapter 可定位 | 业务规则层直接 import PG/HTTP Client 或反向依赖应用入口 | 纯配置包标 N/A |
| M03 | 有执行力的边界 | repo-native boundary check / dependency contract + 现有 CI | 只在 README 写“禁止依赖”，规则未生效 | 不涉及代码依赖要说明 |
| M04 | Shared 模块复用质量 | 一个自然 Owner 持有事实，其他模块只读/调用公共契约 | 两份可写的状态/配置/复制算法，漂移或两套当前源 | 无共享逻辑可 PASS |
| M05 | 身份、Journal/CAS/不可变状态 | 状态身份/版本 CAS / schema 在本源 Owner 明确，失败结果不冒充 success | 双写、未带版本的并发修改、history 和 current 混用 | 无持久态不强制 CAS |
| M06 | schema/接口/实现一致性 | 同一 SourceCut 的类型和 schema 被真实当前代码加载；元数据有来源 | schemaVersion 不匹配、过期路径、同名两代 CLI | 文件无 schema 不强求 |
| M07 | 错误/恢复/外部效果边界 | 发生的物理效果与语义结果/回执分离，可恢复或明确 UNKNOWN | 抛异常当无副作用、盲重试、执行成功冒称领域成功 | 非效果型只观察纯函数 |
| M08 | 文件级组织/可理解性 | 人/Agent 从 README/AGENTS/manifest 到真实入口有无歧义路径 | 源码孤岛、长链跳转、循环技术层、不可信 Current README | 仅 asset 不按代码规则 |
| M09 | 死代码/重复/循环依赖 | 真实调用/配置/生产消费者/历史证据区分后无重复现行实现 | 可复现重复写权威、无任何调用且无恢复义务的旧包装 | 只出现相同哈希不算 FAIL |
| M10 | 既有原生验证与回归控制 | 现有 Owner `mise`/CI 能验证受影响真实旧行为 | 伪测试、从不执行的 checks 或过期固化通过字面 | 本轮绝不因此新增测试 |
| M11 | 文档、ADR、技能与当前性 | README 当前性与实际代码一致；必要重大决定可见；历史状态标历史 | READY_FOR_REAL_WORK 但执行入口已退役、假部署宣称 | 旧历史资料标 Historical 即可 |
| M12 | 变更成本、可替换性、回滚 | 修改局限自然 Owner；可独立 PR/revert；成熟 Provider 优先 | 牵连大量无关 Owner、二次审批/Registry、不得退役的脚手架 | 本次无部署不要求安装回滚 |

## 评级与误判防线

- **符合 (PASS)**：有明确 path+命令/事实支持具体准则；不代表整个系统无问题。
- **部分符合 (PARTIAL)**：既有正向机制成立但在观察的范围有缺口。
- **不符合 (FAIL)**：一项与既有要求相矛盾的**可复现源级/运行级反例**。
- **未知 (UNKNOWN)**：未证明的条件。以精确的补证据动作记录，不能当失败率分子或删除许可。
- **N/A**：该模块没有对应责任，例如纯观测资源不强制分层/Journal。
- 不把“无 README YAML frontmatter”机械判 FAIL；只有 Ordivon 现行契约要求时才算。
- 不把文件行数太大当 FAIL；它是需走调用关系确认的“审计优先线索”。
- 不把写了 `depConstraints` 就当自动 enforcement PASS；必须看到检查进入现有 CI。
- 不把文档自称 READY、某一时期证明 PASS、某次 branch CI SUCCESS 当成当前安装实例/外部效果。

## 成熟范式参考（读过的官方/高可靠来源）

- Nx module boundaries: https://nx.dev/docs/features/enforce-module-boundaries （JS/TS lint；全语言 Conformance 机制需按许可和当前项目适配，不能假设免费覆盖 Rust/Python）。
- Turborepo `turbo boundaries`：https://turborepo.dev/docs/reference/boundaries （实验性机制；不能代替 Runtime/Host 现有语言机制）。
- DDD bounded contexts: https://martinfowler.com/bliki/BoundedContext.html （按模型语言和边界，不按文件数）。
- AWS hexagonal architecture: https://docs.aws.amazon.com/prescriptive-guidance/latest/hexagonal-architectures/overview.html （核心向外、ports/adapters）。
- MADR: https://adr.github.io/madr/ （只记录可影响后续维护的重要决定，不为每个文件新增 ADR）。
- Superpowers executing-plans: https://github.com/obra/superpowers/blob/main/skills/executing-plans/SKILL.md （task small, expected vs actual, independent review）；本轮忽略新测试要求，严格服从用户冻结。
- Ordivon Skills：`matt-native/code-review` 双轴、`matt-native/domain-modeling`、`ecc-native/brownfield-retrospective` / `orch-refine-code`、`obra-superpowers/verification-before-completion`、`user-agents/recursive-lego-calculus` / `design-structure-matrix`。这些外部方法不是允许无限加门禁的根据。

## 用此准则判断一个文件的顺序

`真实入口/Owner → 实际 import/call/config/path witness → M01–M12 中相关维度 → 是否已有成熟替代 → 动作 DELETE / MERGE / REPAIR / KEEP / UNKNOWN`。对于非源/历史文件选择 M06/M09/M11/M12 即可，**不要求 12 项全部签字**；这是避免清理工作本身成为新官僚过程的关键。
