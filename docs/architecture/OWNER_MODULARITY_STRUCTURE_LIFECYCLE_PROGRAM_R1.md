# Ordivon 存量逐文件审计与现代化减法重构 — 执行 SPEC R3

状态：2026-11-10 存量专项执行计划；沿用既有 Owner 改革方案，不新建治理权威。
审计锚点：Git origin/main 720146e6041e766d4c02d06ec5cef7776e7f36cf；每次编辑前复核最新主线及并行 PR。
协调：Host Space space:ordivon-whole-system-optimization-r1:20261002；
Topic topic:ordivon-whole-system:stock-file-by-file-modernization-20261110。
继承自本文件 R2 的历史工作分解；已执行的历史事务留在 Git、PR、Host/Runtime 原生记录，不在本文件重抄运行报告。

## 1. 本轮冻结范围与成功标准

这是存量改革，不是功能路线图。本轮不添加业务功能、测试文件/测试场景、消费者线路、通用框架、Agent/Skill 路由、Proof Registry、Schema 或新的跨 Owner 执行层。可以运行既有验证；仅因存量删改而修复原有引用、配置和自然 Owner 接口。不得为了使待删除骨架显得有价值而发明消费者或新测试。

目标是去掉未被真实需求支持的工作、减少实现与维护复杂度、恢复正确的抽象/Owner 边界，保留现有真正需要的能力及来源。实际结果必须是可检查的 Git 文件删除、合并、迁移、简化或缺陷修复，不把审计数量、模型形式或新增文档当作生产收益。

比较候选的次序：NO-OP（已有成熟能力满足）／DELETE → REUSE 现有自然 Owner 或成熟项目 → MERGE/COMPOSE → 最小 REPAIR。不要把重写当作默认项。UNKNOWN 不是 FALSE，但与当前具体操作无关的 UNKNOWN 不阻止其他合格任务。

完成判断：
- 删除后真实代码、CLI、发布配置、策略与数据消费者不再需要原对象；独有历史事实留在 Git 或其原生保存 Owner。
- 合并后只剩一份有权威的状态/协议实现，没有新别名、重复适配层或双写。
- 现有 SourceCut、Owner 配置和已运行服务的事实分别成立，原生验证不因本轮改动退化。
- 通过 GitHub 原生 PR/受保护主线；Merge 与安装不是同一状态。专项协调文件在工作完成后可以退役。

## 2. 现状：逐文件物理基线，不冒充语义审计

在基线提交上通过 Git ls-files 的完整清单，逐路径实际读取 4,998 个跟踪文件，共 123,167,707 字节（约 123.17 MB）；零符号链接。包含 Python 1,457、JSON 1,315、Markdown 849、Rust 131、TypeScript 89；全部上述 Python 文件通过当前本地 Python AST 解析，JSON 无解析错误。这不保证其他解释器/类型检查/运行时正确。

按根目录归集：services 1,405、capabilities 1,054、domains 784、platform 663、catalogs 532，其他 560。发现 23 组 byte-exact 重复、65 个成员，理论多余字节约 1,616,076；不同 Owner 的 Python 版本锁、LICENSE、素材与历史证据副本可能故意独立，不能据重复 Hash 自动删除。

行数/大小仅为排查导航：Harness run_continuity.py 3,186 行、loop.py 2,366 行、Runtime test_deploy_reclaim.py 5,155 行、Repo check_architecture_docs.py 2,524 行；Media 中有约 41.5 MB MKV 与 16.5 MB MP4。长度不是切分理由，大文件也不等于垃圾。各项还需读取实际调用图/职责/消费者才能给语义判定。

每个文件的机械身份来自 Git（repo identity / commit / path / blob）；不新增永久 File Registry。对重要源采用 Owner 源、运行时、数据库及服务读回；历史文档和来源的引用不是正在运行的消费者。

## 3. 采用的成熟理论及严格使用条件

| 理论／成熟项目 | 解决的具体问题 | 不能据此断言 |
| --- | --- | --- |
| Parnas 信息隐藏、DDD Bounded Context、Ports & Adapters | 按易变决策与状态权威分模块；识别需要一起变化的责任 | 同目录/高行数 = 模块缺陷 |
| MIT Design Structure Matrix / SCC、Bazel 反向依赖思想 | 从真实 import/call/config/effect/readset 找到耦合及迁移影响面 | 文字提及 = 活消费者；静态图完整 |
| Hoare、Assume–Guarantee、现有 Lean/Composition | 在同一端口、相同可观测域与合法前提下判断兼容替换及不变量 | 模型/SMT PASS = 已安装或真实效果 |
| Fowler Refactoring / Strangler、Git worktree | 先定位真实独立边界，再逐步替换/删掉多余实现，保持可恢复差异 | 另起新框架并永久双轨运行 |
| PostgreSQL 事务/约束、系统原生 systemd/Windows Job、Git | 回归自然权威：存储、进程、源码各自解决本职问题 | 一个存储/治理层统一承诺所有域 |
| Lean/TOC、价值流、Team Topologies、Deming PDSA | 优先解除交付瓶颈，限制跨 Owner 冲突，审计后采用反馈结果 | 以新增行数、门禁、文档量作为成果 |
| Matt Skills：to-spec、to-tickets、implement-spec、code-review | SPEC 固化决策；以有真实阻塞边的可合并纵向小票执行；源规范和代码标准独立复核 | 将外部 Issue/Agent 系统直接搬进 Ordivon |
| ECC：research-first、progressive loading、verification-loop | 先检索已有实现与当前来源，只加载相关方法，按现有命令验证 | 复制外部 Hooks、记忆/安全控制平面 |
| obra/Superpowers：worktrees、systematic debugging、verification-before-completion | 使用 Runtime 隔离工作树、具体差分验证、结果实际读回 | 每次修改都必须产出新测试或强制多 Agent 审批 |

方法入口已存在于 .agents/skills/{recursive-lego-calculus,project-kernel-decomposition,design-structure-matrix,systems-engineering,compositional-contracts,organizational-cybernetics,skill-supply-chain-audit,task-space-reentry}/SKILL.md。方法型 LEGO 是指导决策的可选工具，不把每份文件/Skill 自动登记为正式 LEGO。正式声明独立能力/思想 LEGO 时才使用完整 typed ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)；错误和成本 UNKNOWN 有具体范围。

外部一手参考：Parnas 1972 DOI 10.1145/361598.361623；Martin Fowler Strangler Fig 2024 https://martinfowler.com/bliki/StranglerFigApplication.html；Matt https://github.com/mattpocock/skills；ECC https://github.com/affaan-m/ECC；Superpowers https://github.com/obra/superpowers。外部 Skill 只采用适用方法，不安装未经独立供应链审核的执行包。

## 4. 真正逐文件审计：从文件到职责、再到价值

对 Git 跟踪的每一条路径按现有 tools/repo/owners.toml 动态归属自然 Owner；共享的 tools/docs/studies 则由其真实定义/调用者负责。每个文件以工作表中的一行或一次有来源的审计记录处理；不把表格变成新的长期权威。

对每一个代码/配置/文档/数据/测试/素材文件执行以下判断，允许按相同消费/来源集合批处理，而不是人工逐原子重复：
1. 取得精确 Git blob、用途、语言、来源，辨别生产源、测试、数据、生成物、历史证据与当前配置。
2. 打开内容，而不只用文件名猜功能；查导入/调用、命令、声明式依赖、打包、CI、启动、迁移、数据库及服务使用者。对可能的动态消费标成 scoped UNKNOWN。
3. 向外穿透到具体使用场景和维护中的 Owner；区分“被另一份无用材料引用”与真实 User/Service/Domain Value。
4. 反向审查是否由成熟的现存 Owner、操作系统、数据库、工具链或外部项目直接提供相同能力。若不必存在，优先删。
5. 对保留职责检查模块边界、环形依赖、重复状态、错误处理、幂等/恢复和变化共因。拒绝纯“超过 N 行就拆文件”的规则。
6. 给出 DELETE / MERGE / REUSE_NATIVE / REPAIR / KEEP / UNKNOWN_NARROW 之一，引用实际 SourceCut 与具体原因；严禁由静态零引用直接推出业务零消费者。
7. 在隔离工作区实施最小原生更改；如果只是写一份报告而原问题仍在，该工作不算完成。

历史 Git 版本和旧模型不必在当前活跃目录重复保存。真实消费者或独有证明尚在的内容由对应 Owner 保留；可再生的测试输出、重复源、已退役纯计划与过期 README 应尽量退出工作树。已合并旧 PR/无意义分支、Runtime Workspace 通过各自然 Owner 的原生操作清理，不为清理建立第二套数据库或工具。

## 5. Wave / Dependency DAG（只做存量）

| 阶段 | 输入及可并行 Owner | 本轮执行动作，不新增能力 | 完成证据 |
| --- | --- | --- | --- |
| S0 当前性与冲突 | Git main、52 个当时 OPEN PR、owners.toml、Host/Runtime Space | 冻结主线、列出实际文件清单与并行 PR 重叠；继续使用原生 Work/PR | 精确 SourceCut、候选文件与当前变更占用 |
| S1 Repo/Docs/Skills | tools/repo、docs、.agents、extensions | 归并重复入口、删除过时 Spec/已替换状态、简化低价值扫描/包装；不得与 #1940/#1950/#1999 等当前 PR 重叠 | 新增机制零；原生 repo/Skills 检查无退化 |
| S2 Runtime/Host/Harness/Gateway | services 的各自然 Owner | 盘点 PG/SQLite 并行代码、重复状态机、旧桥/脚本、巨型模块真实依赖；优先直接删已退役实现和过度包装 | 保持现有真实事务、恢复和运行入口；原生现有测试通过 |
| S3 Network/Security/Workstation | platform 各 Owner | 检查实际系统服务/配置是否复刻成熟底座；清除过期 Unit、重复代理、无消费者安装和历史别名 | 原生 provider/source/installed 读回；不增加新门禁或测试 |
| S4 Artifact/Media/Distribution/Preservation | capabilities 各 Owner | 按内容身份/交付/保存的权威边界裁剪生成物、重复元数据/验证器和过期包；不能按媒体文件大小盲删 | 实际作品、归档、目的地保持可用；删除真实冗余 |
| S5 Capital/Game/Apps/Data/Composition/Catalog | domains、apps、packages、catalogs | 删除无当前业务用途的原型、重复适配、研究边车，合并源决策，修补现有代码缺陷；保留独有历史证据 | 现有代码与平台入口不退化，角色边界更少更清楚 |
| S6 交付与收尾 | 每个实际修改 Owner、GitHub、Runtime | 仅调用现有验证及 GitHub Merge Queue；确认源变更、PR、原生安装事实后关闭相应 Workspace/Work | Git diff 删除/净缩减、既有检查、精确提交与状态收口 |

S1–S5 不是必须串行的项目阶段；按真实依赖图与 PR 修改冲突决定可执行前沿。约束理论用来找“哪项存量负担真正阻塞修改或运营”，不以全仓一次性完工为前置条件。每一项变更能独立回滚；同一 Owner 的不相关改动不强行合并一个超大 PR。

## 6. 每个候选必须接受的双轴、九问审计

审计轴 A：SPEC——这个东西是否还应该存在？能否删除或用成熟原生机制取代？现有职责/不变量/来源是否满足？
审计轴 B：Engineering Standards——代码是否违反现有 Owner 的模块边界、维护规范、事务/恢复/错误及发布标准？

九个可证伪问题：
1. 最终真实用户/业务价值与具体瓶颈是什么？没有此文件会损失什么？
2. 有什么数学/系统工程结论真正适用？前提是否成立，哪条不能移植？
3. LEGO 的十一坐标只用于真的独立责任了吗，是否把源码文件错当能力？
4. Matt/ECC/Superpowers 的相关 Skill 是按原义使用还是走形式？
5. 是否过于保守，把静态引用或不相干 UNKNOWN 当成永久保留/审批理由？
6. 是否只是调整名称、文档或自造检查器，没有改善存量代码/复杂度？
7. 问题表征是否抓住可变决策、Owner 权威、调用图和消费者，而非优化代理指标？
8. 外界成熟或本地已经具备什么？能否 DELETE/REUSE/MERGE，减少而非增长抽象数？
9. 真实修改 Diff、未破坏的现有入口、现有原生验证及已知反例是什么？

每个同行可返回 KEEP / REVISE / DELETE / UNKNOWN_NARROW 和 SourceCut/路径/反例。社会消息不是代码审查批准；不存在新审批层。实际危险效果只受原有自然 Owner 的授权与服务规则限制。

## 7. 首批需验证的具体库存候选

- apps/chaoxing-autosign 11 个文件：当前 README 自称 MVP skeleton；CLI 只运行 Fake Provider 与临时 SQLite，仓库外未找到 AutoSignEngine 或 MonitorRunner 的生产调用；目前仅原生仓库治理/测试索引、历史结构及导航引用。必须定点查是否有实际独立安装/服务消费者，若无则整体退役而非先修补无人使用的模拟引擎；当前 GitHub #1999 修改 tools/repo/test_affected_owners.py，且若干旧 PR 涉及 SQL dialect 检查，须避让并行文件编辑。独立 Windows Chaoxing read-only 工程不等于这套 Python MVP 的消费者。
- services/harness 核心长源：先区分状态与职责的真正变化共因，检查原生 PG 迁移 PR 和已删除旧桥，禁止因行数而拆文件。
- tools/repo 现有多个 >2,000 行验证/覆盖脚本：检查各自真实保护的不变量、重复验证任务与成熟标准工具替代，不用新增 Repo lint/Proof 体系。
- capabilities/media 中作品与证据占大部分仓库二进制字节；完整媒体源/最终作品可能都被真实发布或恢复消费者消费。优先删除中间可再生物，而不是按体积排序强删。
- 文档与既有 Agent Spec：既有 #1940/#1950/#1993 做存量去重，不发并行同义清理 PR；本文件自身改写而不是新增第五个行动计划。

## 8. 发布、冲突与退出

在每个自然 Owner 的当前目录下工作；以 Git 和 Runtime Workspace 作为隔离，先审冲突，再编辑，运行现有最小相关检查与已有完整原生检查，浏览差分，交给 GitHub PR 和 Merge Queue。**不新增测试**不等于可以把失败的现有检查写成 PASS；对于存在但环境不可运行的入口，报告有界事实，避免捏造成功。

SOURCE/CANDIDATE、MERGED、INSTALLED、LOADED、EXECUTED 与实际消费者接受保持不同证据边界。改动未合并只是 PR，未发布的删除没有生产完成效果。清理本次生成的临时工作区、过期分支和重复协调载体，历史由 Git 和自然 Owner 原生记录留存。

全局没有固定“必须所有 Owner 同时通过”的阻塞门；每个可执行模块完成最小改动和既有验证即交付。专项结束时，只有真实能力保留下来，冗余实现实际消失，本计划本身可以删除。
