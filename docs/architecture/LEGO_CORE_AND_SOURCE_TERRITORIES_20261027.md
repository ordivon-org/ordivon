# LEGO 核心与全仓来源区域：调查、分类及归属缺口

日期：2026-10-27（Asia/Shanghai）
调查基线：`5448ee432dfd8dddc38f57fafa02c813b1fba08c`（已 fetch 的 main，PR #946 后）
性质：源码调查 + 可执行来源分类；不是全系统 LEGO 或证明验收。

## 本轮结论

上轮对 18 个既有分区内部的审计，不能推出 Ordivon 只有这些责任，也不能证明不存在其他必要 Owner。

应显式区分至少四种对象：

1. **语义责任与内容维护边界**：LEGO 核心、领域契约、具体模型等。
2. **仓库验证分区**：owners.toml 中有独立路径、原生验证任务的 18 个条目。
3. **来源导航区域**：代码、规范、方法、Profile、历史证据所在的位置。
4. **运行事实权威**：实际 Job/Attempt、Work、业务状态等，由对应系统提供。

本轮在已有 `owners.toml` 增加来源导航区域，扩展既有 `affected_owners.py` 重建精确 Git 切片的分类。没有新建 Registry、数学内核、服务或 Agent 管理层。18 个验证分区和原有验证选择规则保持不变。

## 并行候选整合后的独立来源边界（以下 18-owner 统计为历史基线）

以下旧 18 个 Owner、4,644 个 owner 匹配路径和 346 个 owner 外路径是 Git
SourceCut 5448ee432dfd8dddc38f57fafa02c813b1fba08c 的历史统计，
不能冒充整合后当前事实。

本轮为独立有消费者的两处责任注册真正的源码验证分区：
lego-core 对应原始 .agents/skills/recursive-lego-calculus/ 两个方法及数学参考文件；
formal 对应 tools/formal/ 九个成熟验证工具适配/原生反例文件。
源码分区由 18 增至 20；没有新增数学求解器、Agent Owner、全局注册中心或执行权威。

原有 lego-core-specification 与 formal-toolchain 的仅用于导航的 source_regions
在新机械 Owner 生效后已退役，避免双重来源类别。
剩下六个区域用于其他 Skills、Repo 跨域机械源、Research profiles、共享文档和根配置。
repo 普通 Owner 候选触发源测试路径虚假跨 Owner 依赖反例，现已撤回。
实际 Research 运行消费者证据不足，暂保留 SOURCE_NAVIGATION 而非验证 Owner。

新跨域有界契约：Media 写作 LEGO 研究案例的 claims.json
精确引用 .agents/skills/recursive-lego-calculus/SKILL.md；
复用 dependency_contracts.toml 的 PUBLIC_SOURCE_CONTRACT 记录及原生反例。
这只能确认为 SOURCE 来源，不是实际执行、数学证明或领域效果认证。

当前数值需从不可变 Git SourceCut 重建的 affected_owners.py
--classify-source-revision 输出核验；历史表格不等于候选的现在状态。

## 统计范围

使用 `git ls-files -z` 对照既有 Owner roots，得到：

| 基线对象 | 路径数 |
|---|---:|
| Git 跟踪路径 | 4,990 |
| 18 个 registered roots 匹配 | 4,644 |
| registered roots 外 | 346 |

这是路径统计，不是 LEGO 数量。Source history 原本另外承认 tools/repo 的机械区域，因此其 ROOT_UNOWNED 数量为 301；与 346 的不同来自投影范围，不是统计矛盾。

同一切片既有 R1 投影为 15 份载体、108 个规划节点、248 个唯一 source anchor 路径，其中 69 个被多个节点引用。多重证据引用不自动构成责任冲突；源码 anchor 数量也不是 LEGO 覆盖率。

## 已落实的来源区域

以下是 346 个原先不匹配验证 Owner 的路径在候选中的可重建归类。分类首次验证切片为 `ce1c87033f886ef6b6e51505c2966bb7efc47263`，保持基线路径集合；后续新增本文会增加一个架构文档路径。

| 来源导航区域 | 当前路径范围 | 基线路径数 |
|---|---|---:|
| lego-core-specification | .agents/skills/recursive-lego-calculus/ | 2 |
| agent-method-library | .agents/skills/，明确排除上面的核心目录 | 37 |
| repository-engineering | tools/repo/ | 45 |
| formal-toolchain | tools/formal/ | 9 |
| research-contract-profiles | meta/research/、profiles/research/、tests/catalogs/ | 16 |
| architecture-documentation | docs/architecture/ | 112 |
| migration-and-historical-records | docs/migration/、docs/retro/ | 115 |
| repository-configuration | .github/ 及明确列出的六个 root 配置文件 | 10 |

候选中基线 4,990 个路径的导航结果：4,644 个 REGISTERED_OWNER_SOURCE，346 个 DECLARED_SOURCE_REGION，0 UNASSIGNED、0 AMBIGUOUS。

**零未归类仅表示来源导航有位置，不表示每个文件属于已合格 LEGO，不表示历史文档有效，更不表示全系统已证明正确。** 未匹配的新路径仍返回 UNASSIGNED；不同区域同时匹配返回 AMBIGUOUS，不采用隐式优先级掩盖。

source_regions 只接受 name、description、literal paths 和显式 exclude。它不能声明 authority、verify_task、LEGO standing 或验收结果，不参与 CI 选择；现有 Owner 内部也不重复维护另一棵来源树。

## LEGO 核心应如何独立

**确认独立的内容责任：Recursive LEGO R2.1 的语义规范。** 当前 canonical source 已是独立两文件目录，但没有独立的内容归属表达，且被误认为 Next 私有 Skill 或 Skills 服务的一部分。本轮先给它独立来源区域并明确边界，未物理搬迁规范。

| 对象 | 内容与职责 | 实际载体与消费者 |
|---|---|---|
| LEGO 语义规范 | 问题/表示/契约/组合/替换/精化/验证资格的 R2.1 基线 | recursive-lego-calculus/SKILL.md 与 references/formal-model.md；跨 Owner 架构引用、Repo vocabulary/native witness 检查 |
| LEGO 方法入口 | 指导 Agent 分解、选择表示、寻找反例和演化 | 原 Skill；information-flow-analysis、minimum-sufficient-representation 等方法引用 |
| Composition 执行库 | 确定性 task-local 组合机械、接口兼容、证明义务绑定、successor 契约 | packages/composition；Next 多个生产脚本 import 公共 API |
| Formal 工具组 | 成熟证明器的来源绑定、调用与正负例验收 | tools/formal/verify.py、mise.toml、原生 proof 示例 |
| Owner-local 模型 | 某个实际系统或组合的不变量与转换 | Composition 的 Lego21OwnerBoundary.tla、Runtime 的 RuntimeDispatchR1.tla 等 |
| Repo 投影与检查 | 精确源码、声明布局、路径/图/来源一致性 | tools/repo/check_architecture_docs.py、source_history_legos.py |

不要把上述六项全部搬成“LEGO Runtime”。成熟证明器保留自己的数学内核；实际模型保留被描述责任的 Owner；Skills Bridge 负责发现/绑定/读取而非理论内容。

现有真实消费链包括：

- meta/next/pyproject.toml → packages/composition 公共包；
- research_artifact_gate_r3、web_security_gate_r3、cross_domain_binding_r3 等脚本 → Composition 公共接口；
- tools/repo/test_architecture_docs.py → 原 Skill / formal-model 精确路径；
- 架构文档 → formal-model digest；
- platform/skills/tests/test_recursive_lego_math_discovery.py → project-ordivon-next scope 下的标准 Skill 发现。

因此，物理搬迁必须迁移 Skill 包资源、发现来源/ID、路径引用和 digest 绑定，不能仅 git mv。若未来将规范搬到独立 specs/lego 区，必须只有一个 canonical definition，Skill 分发资源由明确构建过程绑定；这仍是候选，不是已实施。

## 其他 Owner 或责任域候选

| 责任 | 证据与判断 | 当前应如何放置 |
|---|---|---|
| Repo Engineering | 45 个文件；已有 RG 规划、SourceCut/Owner 检查、根 CI 和实际消费者 | 独立机械责任候选最强；当前已独立来源区域。不能把整个仓库 root 设成它的业务权威 |
| Formal Toolchain | 9 个文件；formal:verify 原生入口和成熟工具正负控 | 可作为可选工具组的机械分区候选。README 明确 opt-in，不能因分类成功而宣称已经运行 |
| Research Profiles | meta/research 12、profiles/research 3、contract test 1 | 作为共享 Profile/Schema 区；科学真理由 Study/独立项目掌握，不重建通用 Research Runtime |
| Agent Methods | 37 个非核心方法文件 | 与 Skills 分发服务分开；按实际方法/领域维护内容，不自动每个 Skill 一个 Owner |
| Knowledge | Next authorities/knowledge 及实际索引、provenance 消费 | 先作为 Next 内知识映射责任；不新建全局知识数据库 |
| Observability | Workstation observability、Ansible 与既有 Prometheus/Loki/Tempo/Grafana 消费 | Workstation 内部子责任；Network/领域观测保留自己的验收语义 |
| Workflow | Workstation 管部署，Artifact 管具体 workflow，Runtime/Host/Harness 各有不同状态 | 按具体持久对象和消费者归属，不用一个 Workflow Owner 重新拥有所有状态 |
| Data | Capital 数据、Artifact dataset、Preservation、Next task-local episode store | 分开记录领域数据、产物、保存和可重建分析投影，不据共同数据库技术强行合并 |
| Human/Life | Human 通用 Owner 已有明确退役记录；实际 human handoff 在 Harness；Life 无独立 tracked 实现入口证据 | 暴露为范围/能力证据缺口，不把生命周期命中当成 Life，不以未命中证明外部不存在 |

## 既有大分区的内部区域

路径多不等于一个巨大可执行 LEGO，也不意味着需要按子目录增加 Owner。

| 分区 | 基线路径数 | 本轮进一步分类的真实构成 |
|---|---:|---|
| Next | 1,016 | authorities359、evidence170、knowledge116、docs56、capabilities51、experiments51、domains50、migrations49、tests31、planning23、scripts19、experimental12、policies8、schemas7、data-products5及root文件 |
| Harness | 729 | tests168、evidence149、research101、scripts85、docs57、src54、evals40等 |
| Media | 582 | productions218、research170、docs25、src25、tests25、scripts21等；材料和研究不是能力模块数 |
| Artifact | 426 | format/provider/operation 的 build/verify/delivery 消费契约 |
| Runtime | 419 | research132、crates102、scripts57、docs30、planning16、formal14等 |
| Capital | 406 | market capture、descriptive research/risk、execution admission/reconciliation、accounting ledger |
| Workstation | 274 | providers58、workstation39、tests38、docs28、ansible20、scripts14、observability12、inventory10、tofu9、systemd6、n8n6等 |

其余 registered roots：Security173、Network158、Host98、Gateway83、Distribution69、Game51、Preservation47、Composition46、Skills38、Web27、Control Plugin2。

## 已暴露的问题及其位置

| 问题 | 真实位置/反例 | 状态 |
|---|---|---|
| LEGO 内容责任与分发责任混淆 | 规范在 .agents/skills，Next 消费却不拥有其源码位置，Skills 服务只是桥接 | 本轮独立来源归类；规范物理迁移未做 |
| 方法发现身份范围过窄 | 跨域规范仍以 project-ordivon-next scope 发现 | 已定位；迁移 discover ID 需要消费者兼容证据 |
| 可执行 Formal 入口没有 registered Owner 选择 | tools/formal/verify.py 和 mise.toml 变化在现有 convergence projection 为 REPOSITORY_ONLY | 已归区；保留 opt-in，未宣称 formal:verify 已执行 |
| Research 旧卡片与新 standing 冲突 | meta/next/capabilities/packages/research.md 仍描述较早 executable stack；SOURCE_MIGRATION_STANDING.md 和 profile 指向共享 profile-only | 已定位为当前性问题；未凭旧卡恢复实现 |
| Data 文档状态漂移 | package 卡 R5 与已有 R6 census；旧 deferred store 说明与 task-local episode store 并存 | 已定位；需区分分析投影与持久领域数据后再改 |
| root admission 的影响没有显式全选 | check_architecture_docs.py 本身变化未列在 CROSS_CUTTING_PATHS 的完整范围 | 已定位；不要简单把所有 tools 改为 all-owner |
| 分类可能虚假消除未知 | 未知路径/重叠规则 | 新分类保留 UNASSIGNED / AMBIGUOUS；没有宣称已实现 STALE_REFERENCE 或动态依赖分析 |
| 历史查询受 mutable manifest 污染 | CLI 启动时模块级 load_owners，当前损坏 TOML 阻断历史查询 | 独立review发现；真实 subprocess RED 后修复 lazy loading，并验证旧选择行为 |

## 可执行增量路径与验证

在仓库根目录运行既有命令：

```bash
python tools/repo/affected_owners.py --classify-source-revision <完整 Git commit>
```

输出绑定 sourceRevision、sourceTree、ownerManifestIdentity；每行含 path、sourceIdentity、verificationOwner、sourceRegion、classificationStanding、matchedRules。Git 路径按 NUL/surrogateescape 保留，包含换行或前导空白也不改写。历史切片只使用该切片的 manifest，不能用当前分类回填过去。

现有 --all / --changed-file / --base / --head 仍用于原生验证选择；分类模式不能与选择模式混用。Formal 工具被归区不代表验证被选中。

验证证据：

- 初始新增行为测试在实现前失败；随后通过。
- 真实 CLI 在当前 manifest 损坏时的反例先失败，修复后通过。
- 原生 affected-owner、convergence 和 source-history 回归通过。
- 两轮根 repo:ci 通过，包含 463 个 pytest 用例及其他原生 Git/SQL/Owner/发布检查。
- 独立 reviewer 检查分类与验证权分离、历史切片、路径身份、歧义和真实 CLI 反例。
- 未执行本轮 Formal 工具全集、生产切换或数据库迁移；不存在对应 PASS。

下一步优先明确 LEGO 核心规范内容维护边界和安全迁移，再收束 Research/Data 卡片当前性；依据具体变更消费者决定是否将 Repo/Formal 加为独立验证分区。不能用导航覆盖替代后续递归 LEGO 资格与契约覆盖。
