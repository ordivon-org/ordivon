# 从探索到组合：写作与寓言创作 LEGO 调查 R1

日期：2026-10-25
状态：探索、源审计与候选职责建模；不代表已经开发或通过生产验收
本地源修订：/root/projects/ordivon @ 9d7311a73519447f0c20cba831043c8cd07909d9
当前隔离 Workspace：ws-chatgpt-20261025-fishing-fable-writing-lego-research-r1
真实消费者：本目录的《捞鱼者与造河人》十三章归档重录稿；原聊天消息是最初原文字词的权威
既有自然 Owner：Media/Studio 管表达与作品；Artifact 管交付契约；Web 管出版呈现；Git 管源代码与版本；Skill Catalog 只提供可解析的 Skill 文本；Runtime 管执行证据。不得另立权威数据库或创作流程服务。

## 0. 问题、结论与范围

问题不是“如何制造一个 Writing Agent”，而是：
> 不断拓宽创作可能性时，如何从有限且可信的材料中挑出真正值得表达的机制，将其组合成有因果、有角色、有读者体验的具体作品，并保持可替换、可验证与作者主权？

阶段性结论：
- 本地已有真实表达核心、Writing Profile、Matt 写作 Skill、ECC 文章 Skill、Creative Alpha、MDX 作品和消费者案例；
- 尚未得到本次故事“长篇虚构叙事创作→独立读者理解→语义/形式验收→出版”的完整证据；不得把“未验证”写成“仓库没有”。
- 最关键的缺口不是再增加创作工具数量，而是故事层（事件和因果）、话语层（如何告诉读者）、阅读层（读者如何重构）之间的契约、状态连续性以及真实消费者验收。
- Explore→Compose 不是简单两阶段瀑布，而是有证据和退出规则的映射：探索生成候选，组合要求接口、前提、效果和表达意图兼容；创作反馈会反过来打开新的探索分支。

范围：寓言/长篇虚构作为第一个压力测试，同时寻找可迁移到论文、技术文章、解释视频、教育叙事的抽象。暂不发布、不改已有生产基础设施、不造 Writing Engine、不创造全局评分。

## 1. 本地事实：真实路径、Skill、测试边界

### 1.1 已读取的本地 Ordivon 源

- capabilities/media/research/expression/creative-system.md：Studio 跨媒介 FRAME→BIND→EXPRESS→RENDER→AUDIT→DECIDE。显式反对第二套通用审美分数/媒体专属孤岛。
- capabilities/media/research/expression/profiles/writing.md：写作控制焦点、信息释放、语调、比喻、叙事距离；明确故事/论述所造成的暗含证据与因果误读，区分语义文本和真实阅读呈现。
- capabilities/media/docs/creative-capability-core.md：Creative Index 是可重建投影，不复制 owner-native 事实真源。
- capabilities/media/productions/browser-perception-note/story.mdx：真实案例证明构建通过≠读者首屏语义传达通过；此前已删除不适合写作媒介的帧率等伪共性字段。
- capabilities/media/productions/ordivon-book-v0/story.mdx：已存在关于有限认知、Reality≠Representation 的长文消费者。
- capabilities/media/src/ordivon_studio/creative_alpha.py 与 tests/test_creative_alpha.py：同一事实集合的不同排序、冻结对照与留出条件的局部实验；不能当作文学质量验证。
- .agents/skills/recursive-lego-calculus/SKILL.md：LEGO 是目标条件化、可替换的责任，不等于文件、Agent、Skill、Tool；最小字段 identity/responsibility/inputs/outputs/contract/acceptance。
- .agents/skills/method-router/SKILL.md：路由最少改变决策的方法，严禁无差别启用所有方法。
- .agents/skills/ck-design/SKILL.md：明确分离概念空间 C 与知识空间 K，审查 C→C、C→K、K→C、K→K。
- .agents/skills/compositional-contracts/SKILL.md：兼容的前提/保证、替换与组合闭包，而非同名模块即组合。
- .agents/skills/evolutionary-search/SKILL.md 和 exploration-policy/SKILL.md：适合可重复评估、反馈归因可行的多候选场景，不宜把文学评价降格成单一奖励。

### 1.2 已通过 Ordivon Skill Catalog 解析并读取的写作 Skill

| Skill ID | 职责 | 实际边界/危险误用 |
|---|---|---|
| matt-native/writing-fragments | explore：开放收集不规则原始材料、隐喻、碎片 | 不组织为文章；原生流程倾向逐步访谈 |
| matt-native/writing-beats | exploit：按 concept prerequisites/grounded 控制叙事节拍 | 主要针对文章按节拍互动编辑；不是完整人物/世界模型 |
| matt-native/writing-shape | exploit：素材→开头与逐段行文、针对论证目的剪裁 | 不负责原始素材发掘、发行，也不天然担保小说质量 |
| ecc-native/article-writing | 文章/长内容起草、结构、节奏、非虚构证据 | 不能把文章评价直接当寓言评价 |
| ecc-native/brand-voice | 有证据的风格样本→可复用 voice profile | 无样本不能编造“用户现有风格”；风格与作品事实应分离 |

说明：前三者的已读 SKILL.md 包含 disable-model-invocation:true，表明其特定交互模式不宜被偷偷宣称已经自动完整执行。本报告读的是 Skill 文本及其语义，不声称调用了完整交互会话。

### 1.3 已有生产链与仍属 UNKNOWN 的部分

已确认：存在原始文本、表达规范、Creative Index、局部实验测试、读者/浏览器呈现检查案例。
UNKNOWN：全篇人物弧线强约束是否有常规验证器；叙述视角连续性是否可自动消费；独立读者实测是否有此具体寓言的证据；跨书本长期修订是否完成消费者验收；最终出版是否在本次工作中执行。
不可将事实“源文件存在”和“Skill 解析成功”提升为“写作生产端到端 PASS”。

## 2. 外部成熟理论与可复用核

### A. 创作认知（explore/exploit）

1. Flower & Hayes (1981) / Hayes & Flower (1986) 的写作认知过程：计划、转译/表达、复核可以嵌套、迭代发生，并非一次性瀑布。可替代新造流程的基本递归框架。
   来源：https://doi.org/10.58680/ccc198115885 ; https://doi.org/10.1037/0003-066X.41.10.1106
2. Fauconnier & Turner (1998) Conceptual Integration Networks：不同心智空间选择性投射并产生涌现结构；寓言之“渔具—决策、河流—生态/社会、写作—制筐”属于候选概念融合实例，映射只保留相关关系，不复制一切属性。
   来源：https://onlinelibrary.wiley.com/doi/10.1207/s15516709cog2202_1
3. Ordivon 本地 C-K Design：真实已知 K 与待检概念 C 分离，允许没有既成答案的新故事形式。与一般 brainstorming 相比更明确规定知识洞与验证候选；不是小说标准。
4. 探索/利用（bandit 与进化搜索）：若多次独立作品或读者试验满足反馈归因，才考虑探索预算优化；单篇寓言不需要先有自动进化器。

### B. 叙事结构（story/discourse）

5. Cambridge Companion to Narrative Theory：区分故事层（被描绘的事件、事件之间的关系）与话语层（文本怎样揭示、安排这些事件），这是优先的最小表示，而不是给所有文字贴标签。
   来源：https://www.cambridge.org/core/books/cambridge-companion-to-narrative-theory/narrative-theorys-longue-duree/D746AC4DF357E6A0D6CB86B4CE3D360F
6. Cambridge Companion to Narrative：focalization（视角过滤）解释并非所有已知信息都应该告诉读者，且读者所见与世界事件状态不是同一个对象。
   来源：https://www.cambridge.org/core/books/abs/cambridge-companion-to-narrative/focalization/4292F5EB30ACFBB54BD1F8D4A920BED5
7. Cardona-Rivera 等 ICAPS 2024 Narrative Planning Survey：角色目标、行动、条件、因果链接与故事规划提供一组成熟可解释的形式化候选；故事情感和语言美感不能由符号规划单独证明。
   来源：https://ojs.aaai.org/index.php/ICAPS/article/view/31509
8. Mann & Thompson 的 Rhetorical Structure Theory：描述段落/篇章片段之间的论述功能关系，适合解释性寓言和议论文的结构检查；不必强迫所有小说完整转成 RST 树。
   参考原文：https://www.cs-135.org/wp-content/uploads/2019/11/Mann_Thompson_1988.pdf

### C. 读者、理解与效果

9. Zwaan 的 situation model 理论：读者会从文本中重构情境，而不只是记住词句；涉及人物、时空、目标、行动等的认知模型。
   来源：https://pubmed.ncbi.nlm.nih.gov/26088667/
10. Green & Brock (2000) 的 Narrative Transportation：情节沉浸、情感与注意力影响读者的理解与反应；可用作观察维度而非全能文学评分。
    来源：https://pubmed.ncbi.nlm.nih.gov/11079236/
11. LongStoryEval (ACL 2025)：对书本长度作品采用多维阅读评价，公开说明长篇作品评价的多个维度及自动评估局限。
    来源：https://aclanthology.org/2025.acl-long.799/

### D. 自动写作与持续性风险

12. EACL 2026 Story Generation Survey：系统梳理 57 篇研究，强调长篇的 coherence、character consistency、storyline diversity、plot controllability 仍是主要挑战。不能因为新模型一次能输出许多字就断言上述问题已经解决。
    来源：https://aclanthology.org/2026.eacl-srw.39/
13. ACL 2026 ConStory-Bench：2,000 个提示/多个场景，显式研究长篇 factual/temporal 等一致性缺陷，提供文本证据定位的检查思想。可借鉴 taxonomy 与证据链，不能照搬评分直接代替文学评判。
    来源：https://aclanthology.org/2026.findings-acl.410/
14. INLG 2024 Long Story Generation Challenge：联合机械指标与人类对一致性、语言、因果和重复的观察。
    来源：https://aclanthology.org/2024.inlg-genchal.4/
15. W3C PROV-O：跨系统记录来源/活动/产出关系的成熟来源表示；如果需要结构化 provenance，优先映射现有 owner 原件，不自造第二套 source graph。
    来源：https://www.w3.org/TR/prov-o/

证据边界：以上文献为方法或局部发现，不证明 Ordivon 已实现任何对应能力。成熟理论是可借鉴的机制，不是强制依赖列表。

## 3. 探索空间 C 与知识空间 K

### 3.1 K：当前可以站得住的东西

K1：十三章寓言已经有一份可消费重录归档稿，原聊天文本为首次完整公开文本。
K2：本地已有开放素材、写作节拍、文章塑形、风格与 Media 跨媒介认知方法。
K3：长文一致性、因果与读者体验不能从源码正确自动推论。
K4：作品里既有叙事，也有显性教学段落；文学质量是否被过度说教损坏，尚需独立读者验证。
K5：Media 已经反对重复权威和通用美学标量。

### 3.2 C0：让大体量、高概念密度的思想能够转为有体验的寓言

概念分叉（候选，不是决定）：
- 读者目的：理解一组抽象机制 / 体验人物的选择与改变 / 对既有目标产生质疑 / 感受无法简单量化的价值；
- 叙事形式：线性成长 / 多角色群像 / 同一事件多视角 / 环状回声 / 微型寓言串联；
- 信息释放：先讲道理再举例 / 先制造冲突后揭示 / 在伏笔和后果中隐含原则；
- 角色核心：阿澈观察者 / 铁山效率极大化 / 百策方法极大化 / 青禾交易协调 / 造河人系统边界 / 小渡表达与传播；
- 实践的最小试验：选取一个主题（如“工具不等于目标”），生成两种极不同的叙事方式，保留关键事件与人物前提，让不同读者在不看解释的条件下读后复述其理解与情感转折。

从 C 进入 K 的门槛：具体作品阅读/修改/消费者的证据，不是作者宣称或专家形容词。

## 4. 最小充分表示：只区分真正改变创作的对象

三层、两种证据足够作为初步 MSR：

1. **World/Story**：发生了什么、人物知道什么、想要什么、何种行为改变了何种状态；事件可有依赖边与时间界限。
2. **Discourse/Text**：读者依什么顺序遇到哪些事件与信念，叙述者允许透露哪些信息，章节/段落/词语如何实现。
3. **Reader/Encounter**：真实读者接收了哪些信息、形成何种解释、是否困惑或沉浸。

两种独立证据：
- source/provenance：作者原材料、版本、事实边界、外部引文；
- consumer observation：实际完整文本、修订 diff、读者反馈和最终显示效果。

不能把 World 真相、角色的信念和 Reader 的理解合并；不能把文学效果当成单一真值。所谓 story world graph 只是任务需要时的局部材料表示，不是永久全域本体。

## 5. 候选责任 LEGO：不是新增文件或服务清单

| 候选责任 | 输入→输出 | 首选现成消费者/机制 | 验收与限制 |
|---|---|---|---|
| L1 Intent Framing | 目标/读者/限制→创作意图 | Media FRAME；Matt/Creative Core | 是否有明确意图及不可接受的误导；作者/Owner 决定 |
| L2 Material Exploration | 现象/隐喻/研究→高多样性素材 | Matt writing-fragments、C-K | 材料可追溯；探索可停止；不强制全部采用 |
| L3 Conceptual Bridge | 抽象思想与现实对象→可叙事冲突/隐喻 | Conceptual Blending、Media writing profile | 映射边界明确；避免把隐喻误作科学事实 |
| L4 Narrative Causality | 人物目标+世界状态+事件→可解释事件链 | Narrative Planning / scene reasoning | 关键行为有动机、前提、结果；只做必要场景 |
| L5 Discourse Composition | 事件素材+叙述视角→分章/节拍/正文 | Matt writing-beats/shape、ECC article-writing | 概念先铺垫再使用；节奏真实服务体验 |
| L6 Continuity Checking | 世界状态+文本→不一致的证据位置 | ConStory taxonomy/检查思路、简单人工核对 | 对象/时间/事实冲突须附文本证据；不能以无冲突证明好故事 |
| L7 Reader Interpretation | 完整作品+读者任务→理解/误读/情感观察 | Media AUDIT，LongStoryEval/Transportation 的部分维度 | 人类或独立读者样本，分歧保留而不强行平均 |
| L8 Deliver & Learn | 通过验收的作品→发布形式/变更依据 | 现有 Media Production + Artifact + Web/Creative Index | owner-native，最终呈现实际读回，不复制真源 |

每个 LEGO 都只是“职责候选”。若某一次作品很短，不需要独立 L4/L6 就能自然正确完成，就不为它们立项。对一个真实长篇如果已有文学作者及编辑完整满足 L4/L5，也不重复实现。

## 6. 组合：由前提与保证而非固定工作流决定

组合不应该是八个必经步骤。真实关系是：

- FRAME 给探索提供读者和价值方向，但探索过程可能修改 FRAME；
- Material 具有来源约束，不因文学性而把假设升级成事实；
- Narrative 对象描述角色目标与事件变化，Discourse 可重新排序但不能无解释地破坏世界状态；
- Discourse 按读者已知概念控制信息释放；
- Reader Audit 可反向改变 World 假设、Discourse 节拍或整部作品意图；
- Deliver 必须从已确认语义工件出发，真正呈现和读回；
- 任何阶段都可以 NO-OP、退出、回到探索、删除无价值机制。

可形式化的最小接口义务：
A. event.preconditions 在 story-state 中成立后才能宣称其 action.effect；
B. temporal/identity/canon 冲突要报告文本位置、冲突类型和是否存在叙事上的有意不可靠视角；
C. 某个 concept 若被后续 beat 当作读者已知，则应由已定义的预设或更早节拍引入（不是所有文学文本都必须显性解释）；
D. 文本与读者意图的差异是评估信号，不是自动删除作品多义性；
E. 外部历史与引用事实受 provenance 管辖，但虚构世界事实不应误用真实新闻/学术校验器；
F. 变更前后应保留原始版本、修订理由与可观察后果；不以相同的“美感得分”替代独立判断。

## 7. 本篇寓言的具体消费者审计假设

文本中的真实可追踪物件：
- 旧竹筐：物理捕鱼工具→存续/替代责任→最后重用竹条（删除历史物件但保存有效功能）；
- 铁山巨网：局部高效→生态后果→拆分工具；
- “先看看脚下”：物理河岸风险→选择风险→行动前的立足点；
- 阿澈父亲的事故：风险识别的初始动机；
- 小渡写书：抽象 LEGO 的递归——创作本身也是目标/素材/组合/读者检验。

目前可以提出、但尚未独立确认的风险：
- 教学台词偏多，使人物像架构立场的代言人；
- 阿澈的发现多由师长口述，行动性/戏剧张力可能不足；
- 各章冲突的后果并非均有持久代价；
- 多角色的生活经验、利益、反应可能欠具体；
- “捕鱼→卖鱼→造河→写作”的概念过渡有时过于显性；
- 同一角色反复用问题答问题，语言声音可能趋同；
- 收束主旨过于明确，损害文学上合理的多解空间。

切勿在无独立读者证据时将这些假设提升为结论。

## 8. 研究完成条件与不做之事

研究阶段输出条件：
1. 真实作品已归档并有 digest；
2. 当前 owner、已有 Skill 与实际可消费源都指向可查路径；
3. 每个有价值的 LEGO 责任有输入/输出/前提/验收及复用方案；
4. 概念空间已筛选出下一个会改变决策的最小对照；
5. 未知项保持 UNKNOWN；
6. 不为输出漂亮地图而增加正式 Registry、Engine、Orchestrator 或假模型评委。

原则性下一实验建议（**尚未执行**）：保留同一人物与一场真实冲突的事实基础，写一个“寓言说理版”和一个“少说理、靠选择和代价推动版”；给几个不知 Ordivon 的读者匿名阅读，比较具体事件理解、角色可信度、误读和阅读意愿。应测的不是“哪篇得分最高”，而是两个表达机制各自的效应及限度。

决策：现在保留 Ordivon 现有 Media / Matt / ECC / C-K / narrative-planning / consumer-audit 的组合候选；继续检查证据缺口。**不创建新的长篇写作引擎，不声称创作质量已验证，不自动修改或发表用户作品。**
