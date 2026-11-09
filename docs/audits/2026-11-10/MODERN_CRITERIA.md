# 现代架构审计标准（可检查、可反驳、非 Nx/Turbo 安装要求）

标准结论为 符合 / 部分符合 / 不符合 / 待证。只有源代码或真实消费者/运行证据才能支持符合；单纯存在 ADR、Skill、LEAN 模型或一个绿色测试不足以宣称整层符合。

| ID | 具体审计问题 | 主要证据路径及反例 |
| --- | --- | --- |
| C01 | 领域/功能职责是否高内聚，而非让一个概念跨越多个任意技术层？ | Owner README、`src/` 与 public API、调用者；DDD bounded context |
| C02 | 模块边界是否真正可执行，不只写在文档？ | `tools/repo/owners.toml`、`check_owner_boundaries.py`、原生 CI |
| C03 | Ports/Adapters 是否遵守依赖反转，Domain 不依赖 Adapter 的私有实现？ | public imports、CLI、Rust crates 与跨 Owner 引用 |
| C04 | 模块接口是否足够深，还是纯包装层造成更多文件/胶水？ | Matt `improve-codebase-architecture` deletion test 和修改时调用链 |
| C05 | 状态、Journal/CAS、Evidence、Identity、Effect 是否有单一当前权威？ | Host/Runtime/Harness、DSN、PG migration、Receipt 来源 |
| C06 | Schema/Contract/Provenance 是否与当前实现和真实消费者同步？ | schema、migration、release、校验器、实际读回 |
| C07 | 是否存在真实循环依赖、重复职责、双写、隐式全局状态？ | Python AST、TS import、Cargo graph、部署文件、效果边界 |
| C08 | 是否复用成熟外部机制，而非对同一接口自造私有系统？ | Git/systemd/PG/OPA/Cargo/uv/pnpm/Godot/FFmpeg |
| C09 | App 与库的职责是否合理？App 是否包揽了本该在领域 Owner 的知识？ | `apps/web/src/app.ts`、`store.ts`、领域 APIs；不照搬纯 JS 目录 |
| C10 | README、ADR、Quickstart、Security/Source 链接是否描述真实而非历史？ | Root/Owner README、`services/runtime/docs/quickstart.md`、`SECURITY.md` |
| C11 | Owner 构建、锁文件、发布与验证是否独立、真实和可重放？ | `mise.toml`、Rust/uv/pnpm 锁文件、GitHub checks |
| C12 | 删除旧文件是否基于真正的消费者闭包；历史唯一证据是否保留？ | Git blob/sourcecut、当前调用/安装/外部消费者、Owner readback |

## 采用但不照搬的成熟工程方法

- Nx 项目 tag+依赖约束可自动执行模块边界；Ordivon 的 Rust/Python/Godot/TS 混合仓库已经有 Owner checker，不安装 Nx Enterprise 作为另一套权威。
- Turborepo 用 package manager workspace/exports/lockfile 把 JavaScript package 作为独立单位；不能把此布局强加给 Cargo、uv、PG 和 systemd。
- Matt Pocock：domain-modeling 统一领域词汇，improve-codebase-architecture 只推荐 deletion test 确实收敛复杂度的深模块，grill 只在存在真实决策歧义时使用。
- Superpowers：writing-plans → executing-plans、systematic-debugging、verification-before-completion，但本轮禁止新增测试，只重跑当前 Owner 验证。
- ECC：research-first、选择性 hooks/rules/Skills、跨会话证据连续；这些理念应由现有 Git/Runtime/Host/CI 承担，不重做一套执行器。
- Parnas information hiding、Hexagonal Ports/Adapters、DDD bounded context、A/G refinement、DSM 的共同要求是**维护稳定职责与行为替换前提**，而不是增加文件。

官方与原作者出处（2026-11-10 检索）：
- https://nx.dev/docs/features/enforce-module-boundaries
- https://turborepo.dev/docs/crafting-your-repository/structuring-a-repository
- https://github.com/mattpocock/skills/blob/main/docs/engineering/improve-codebase-architecture.md
- https://github.com/mattpocock/skills/blob/main/docs/engineering/domain-modeling.md
- https://github.com/obra/superpowers/blob/main/skills/executing-plans/SKILL.md
- https://github.com/affaan-m/ECC
- 本地权威：`.agents/skills/recursive-lego-calculus/SKILL.md`、`tools/formal/RecursiveLegoRefinement.lean`。
