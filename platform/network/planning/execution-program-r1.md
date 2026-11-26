# Network execution program R1

Date: 2026-11-05. This file is an immutable *source-bound acceptance/backlog DAG*, NOT a new task-state database or scheduler.
Currentness notice (2026-11-13): this is the November 5 historical obligation set,
NOT the current open-task count or production policy. In particular, the
Singapore-only/SG-JP historical notes below were superseded by the
non-Hong-Kong provider selector; multiple subsequent Network PRs also fulfilled
parts of the listed obligations. Use current Git/source, actual installed/loaded
effects, Host Work and independent consumer evidence before reopening any row. Ordivon Host Work alone owns mutable task state; Git/PR owns source and release truth; Runtime owns execution truth; systemd, Podman, Gluetun, sing-box and Tailscale own installed/runtime effects.

## Rules of composition

1. Existing R2.1 LEGO ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold) and the N01–N10 / NS2 planning/lego-plan-r1.json graph are reused. No new universal registry, VPN controller, scheduler, custom unit manager or cleanup framework.
2. Natural owners: Network generic DNS/transport; Gluetun physical ONE WireGuard identity; each Consumer its own destination policy; Workstation boot; Security credentials; Host task state; Runtime Jobs/Workspaces; Tailscale iOS client selection.
3. Distinguish SOURCE, CONFIGURED, INSTALLED, EXECUTED, CONSUMER, FORMAL and CURRENTNESS. Unknown evidence stays UNKNOWN, never DONE. Bind SourceCut, binary, installed config, exact consumer, observation time and positive AND negative receipts.
4. Native tools: Go Task, ShellCheck/pytest, sing-box, Gluetun, Podman Secrets/Quadlet, systemd, Blackbox/Prometheus, Tailscale, GitHub PR/CI/auto-merge and native Runtime workspace.close. First choose DELETE-CUSTOM → REUSE → COMPOSE. Keep required recovery input, not historical clutter.
5. WIP 3–5 bounded P0 work units; Host Work CAS and Task Space existing coordination own durable status/claims. This catalog lists obligations and dependencies, not live assignment.
6. Publish: latest origin/main → exact source PR → native owner CI and behavioral negative control → GitHub merged → installed SourceCut readback → independently observed consumer readiness → rollback or accept. No direct-vs-proxy claims from CONNECT200, curl35, container ACTIVE, or historical PASS alone.

## Already delivered (historical source references, not re-opened work)

PR #1507: natural Owner Taskfile (95 task API names); PR #1548: 7 owner-private variables migrated with 4 byte-exact Task dry-runs; PR #1508: Gluetun child-service reconciliation; PR #1527: native Surfshark SG/JP provider single session and Podman Secret; PR #1540: Codex CDN HTTPS/source verification; PR #1544: 7 unconsumed historical documents deleted. Twelve selected real consumer checks previously passed. Current iOS client traffic, full cold boot and all indirect bypasses are NOT proved.

## Dependency-bound work obligations


### NS2 — 出口、绕行、证据证明

| ID | Priority | Owner | Dependencies | Work | Acceptance |
|---|---|---|---|---|---|
| NS2-01 | P0 | Network/各Consumer | — | 逐进程/端口/DNS/代理/直连/公网源头收集真实路径图 | SOURCE/INSTALLED/EXECUTED/CONSUMER 各自关联 SHA、时间、未知边 |
| NS2-02 | P0 | Network Consumer Egress | NS2-01 | 扩展已有 sing-box 原生独立 upstream spy 至 Codex、Discord、Model Provider | 允许主机可达 spy，未知地址/错端口零转发，移除 reject 的反例可观测 |
| NS2-03 | P0 | Network Installed | NS2-02 | 在同一因果周期关联源码、安装态、loaded config、二进制与实际请求 | 配置/进程不一致则 UNKNOWN，禁止 source-only PASS 冒充运行态 |
| NS2-04 | P0 | Network DNS/Security | NS2-03 | 审计 DNS UDP/TCP/DoH、IPv4/IPv6、metrics/auth/packages/间接出口 | 源站独立正例及 no-forward 反例，不能以 CONNECT/curl35 代替 |
| NS2-05 | P0 | Network/Workstation | NS2-04 | 跨 Linux/WSL/Windows 反证直连、环境变量/进程继承及任意目标旁路 | 坏策略负控可证伪；未观测路径 UNKNOWN |
| NS2-06 | P1 | Network ProofGraph | NS2-03 | SourceCut、配置、验证器、观察时间、正负读集的增量证据失效 | 模拟变更使过期 PASS 退为 UNKNOWN |
| NS2-07 | P1 | Finance/Claude/Browser | NS2-02 | 分别覆盖 Finance 多出站、Chrome mixed、Claude 与 Chat Ingress 专属语义 | 不把不同策略错误标准化成单出站模型 |

### ARC — 模块、边界、命名

| ID | Priority | Owner | Dependencies | Work | Acceptance |
|---|---|---|---|---|---|
| ARC-01 | P0 | Network Source | NS2-01 | 形成 Owner→服务→导入→配置→权限→消费者图 | 真实调用与系统进程证据，不按目录名猜测 Owner |
| ARC-02 | P1 | Network Source | ARC-01 | 计算跨 Owner SCC、调用耦合、重复代理与隐含全局状态 | 按真实消费者闭包给每个需要拆分的 SCC 选迁移序列 |
| ARC-03 | P1 | Provider/Surfshark | ARC-02 | 分离唯一 Gluetun 物理隧道与静态灾备 Profile | 不启动第二个 WireGuard 身份，灾备消费者明示 |
| ARC-04 | P1 | Consumer Owners | ARC-02 | 各消费者独立管理域名授权、接口和 READY 合同 | 跨消费者权限没有意外共享，真实请求正负验证 |
| ARC-05 | P2 | Network Generic | ARC-02 | 根 Taskfile 只编排共享任务，私有变量/实现下沉自然 Owner | Go Task 原生接口，公共任务 dry-run 等价 |
| REP-01 | P1 | Network Source | ARC-01 | 扫描路径、Unit、Namespace、名称与 R0/R1/R2 旧标识 | 当前身份/消费者/重命名成本逐一记录 |
| REP-02 | P1 | Natural Owners | REP-01 | 整理目录命名、Taskfiles、脚本、README 和重复表示 | 使用正式命名且所有调用/安装引用同步 |
| REP-03 | P1 | Network LEGO | REP-01 | 统一 Provider/Policy/Binding/Evidence/Currentness 表征 | 自然 Owner 声明一致，UNKNOWN 不判 FALSE |
| REP-04 | P2 | Network Source | REP-02 | 退役已无消费者的别名、旧 shim、无意义分层 | 源/安装/运行/恢复四层验证零消费者 |
| REP-05 | P2 | Network Docs | REP-03 | 消除过期证据、无源文档和重复说明 | 只留当前消费或实际恢复资料 |

### RET — 必要性清理

| ID | Priority | Owner | Dependencies | Work | Acceptance |
|---|---|---|---|---|---|
| RET-01 | P1 | Network/Runtime | NS2-01 | 源码、工作树、Workspace、服务、DB、凭据、镜像、日志的消费者闭包 | 读/写/启动/恢复每种关系确认，未知不删 |
| RET-02 | P1 | Browserless/Surfshark | RET-01 | 审计 production-cutover/provider-switch/旧 Manifest/静态 Profiles | Gluetun 原生替代时删外层，有真实灾备消费则保留 |
| RET-03 | P1 | systemd/Network | RET-01 | 退役过期 units、netns、代理 socket 与旧目标 | 运行状态、enable 以及依赖链均无消费者 |
| RET-04 | P1 | Podman | RET-01 | 官方原生命令清理无用容器/镜像/缓存/overlay 残留 | 避免损坏共享 Podman store、仍用镜像与凭据 |
| RET-05 | P1 | Security/Provider | RET-01 | 老密钥和多余凭据去重、撤销、恢复来源验证 | 单身份有效且灾备可重建，不泄露私钥 |
| RET-06 | P1 | Runtime/Network | RET-01 | 无消费者 Workspace、worktree、临时诊断日志与工作数据退役 | Runtime workspace.close/Git 原生方式、活动 Agent 不受损 |
| RET-07 | P2 | Network Evidence | RET-01 | 历史证据和缓存清理、Git provenance 保留 | 无当前读取或恢复消费后删除 |
| RET-08 | P2 | Network Owner | RET-02 | 旧 shim/辅助 LEGO 删除后的独立消费者回归 | 选择 DELETE 而非无意义包装，但生产 readback 必须通过 |

### RES — Provider、DNS、启动与终端鲁棒性

| ID | Priority | Owner | Dependencies | Work | Acceptance |
|---|---|---|---|---|---|
| RES-01 | P0 | Gluetun | NS2-01 | 原生 Surfshark 健康、国家限定、秘钥生命周期与单会话 | ipinfo.io、单隧道和 12 消费者实测 |
| RES-02 | P0 | systemd | RES-01 | 子服务失败但 target Active 时恢复；健康不无谓重启 | 真实故障注入与适配器/出口收敛 |
| RES-03 | P0 | DNS Owner | NS2-04 | 重现 DoH 间歇故障、部分/全部上游失效、缓存与恢复 | DNS 真实查询、因果日志、明确 fail-close |
| RES-04 | P0 | Workstation | RES-02 | Windows 开机→WSL→systemd→Podman→Gluetun→Consumer 冷启动 | 真实新 boot epoch 与每层 SourceCut/出口确认 |
| RES-05 | P1 | Podman | RES-02 | 追查 volatile-containers.json 损坏和服务依赖失败 | 官方系统自愈、真实重现与修复，不直接改共享 store |
| RES-06 | P1 | Mobile Exit/systemd | RES-02 | 调查历史 Tailnet Exit 重启风暴 | 断线后恢复且 restart 计数有界 |
| RES-07 | P1 | Gluetun | RES-01 | 优化消费者合格节点池、目录更新与延迟策略 | 复用 Gluetun 原生选择，无自制百节点轮询 |
| RES-08 | P1 | Network Observability | RES-03 | 区分 DNS、Tunnel、TLS、Policy、Origin、Application 故障 | 现成 Blackbox/Prometheus/Journald 的独立证据 |
| DEV-01 | P0 | Windows Codex | NS2-03 | 核验旧/新 Codex 进程的真实代理环境与 TCP 出口 | 进程级请求可溯源，不以新 CLI Doctor 推断旧进程 |
| DEV-02 | P1 | Codex | DEV-01 | CDN、ChatGPT、API 的严格域名策略和 HTTPS 完整性 | 来源态+载入态与未知域名拒绝同时满足 |
| DEV-03 | P0 | Tailscale iPad/iPhone | RES-01 | 两台 iOS 设备分别选择已批准 Exit Node 并用 ipinfo.io 验证 | 每台有源 IP/DNS/出口读回，设备离线保留 UNKNOWN |
| DEV-04 | P1 | Tailscale/Network | DEV-03 | Wi-Fi/蜂窝切换、局域网例外、DNS、断连与回路 | 客户端实际消费及无泄漏/恢复路径 |
| DEV-05 | P1 | Workstation | RES-04 | 关闭 Surfshark GUI 自启动并使桌面网络经明确的进程级绑定 | 无 Windows 全局代理副作用或双隧道 |
| DEV-06 | P2 | Developer Egress | NS2-01 | gh、Build 与 Agent 本地 shell 显式代理/NO_PROXY 行为 | 有实际进程级出站正负观测 |

### LEGO — 形式化、复用和证据增量

| ID | Priority | Owner | Dependencies | Work | Acceptance |
|---|---|---|---|---|---|
| LEGO-01 | P1 | Network LEGO | ARC-01 | 现有 N01–N10 完成 R2.1 ell 契约、模型/验证器/实现三层区分 | 独立证明来源与消费者可用的自然接口 |
| LEGO-02 | P1 | Proof Owner | NS2-05 | Hoare/Assume-Guarantee/LTS/CEGAR，仅为真实难题构造模型 | 至少一被证伪错误假设与代码/安装层独立 |
| LEGO-03 | P1 | Network Verifier | NS2-02 | 复用独立 spy，修正过度保守的 CONNECT403 必要性 | 网络拒绝必须有独立上游零转发，不承认泛化 curl35 |
| LEGO-04 | P1 | ProofGraph | NS2-06 | 建立源码/安装/验证器/环境/消费者读集与失效关系 | 有限增量验证与全量结果有可复现对照 |
| LEGO-05 | P2 | Skills | LEGO-03 | 仅当重复工作确有消费者时注册辅助能力或思想型 LEGO | 其他 Agent 冷启动真实调用与验收 |
| LEGO-06 | P2 | Network Maintenance | LEGO-02 | 删除不贡献独立信息的特化测试/护栏 | 保留硬核反例，减少维护成本 |

### REL — 原生发布、证明与编排

| ID | Priority | Owner | Dependencies | Work | Acceptance |
|---|---|---|---|---|---|
| REL-01 | P0 | Network/GitHub | NS2-02 | 最新主线、原生 Taskfile/mise/pytest/sing-box、精确 PR diff | 通过真实 Owner CI，GitHub PR+检查合并才算已发布 |
| REL-02 | P1 | systemd/Network | REL-01 | 安装→原子切换→target 收敛→消费者→回退 | 源/安装字节一致，未相关进程不重启 |
| REL-03 | P1 | Host/Runtime | REL-01 | Host Work 唯一任务状态、Topic 协作、Runtime 执行事实 | 不重复 Work；P0 WIP 控制 3–5 |
| REL-04 | P1 | Workstation/Network | REL-02 | 冷启动与提交之后再次读取 installed/executed/consumer | 旧 PASS 不能冒充 CURRENT |

## Host Work owners for first wave (mutable state is not stored here)

- P0 NS2: work:ordivon:network-ns2-real-egress-proof-r1:20261105
- P0 Provider/DNS recovery: work:ordivon:network-provider-dns-recovery-r1:20261105
- P0 Windows Codex and iOS Tailnet consumers: work:ordivon:network-mobile-windows-egress-r1:20261105
- P1 natural Owner retirement: work:ordivon:network-owner-retirement-r1:20261105

## First batch (actual execution in this program)

1. NS2-01: inspect actual source/namespace/proxy/consumer topology. NS2-02: expand existing native sing-box loopback upstream spy to Codex, Discord and Model Provider; allow hosts must be observed, forbidden host/wrong port must cause ZERO upstream sends; a deliberately weakened temporary route must be caught.
2. RES-03: characterize real DoH fault signatures and origin difference, using existing DNS tests. No disruptive fault injection without native recovery evidence.
3. DEV-01 and DEV-03: collect per-process Windows Codex and per-device iPad/iPhone evidence when clients exist; server READY never proves desktop/mobile selection.
4. RET-01: source/install/consumer/recovery readset, then RET-02/RET-03/RET-04/RET-05/RET-06 native retirement only for zero-consumer leaves.
5. REL-01: exact current Git source tests task all:validate, mise run ci, mise run behavior, PR+CI. SOURCE proof is not INSTALLED or CONSUMER proof.

## Explicit live UNKNOWN

NS2 source graph still PROPOSED; all-consumer indirect egress bypass and independent no-forwarding are unproved. Historical Gluetun DoH partial failure remains unclosed. Current Windows/WSL full cold boot, old desktop Codex process route, and both iOS devices' selected Tailscale exit + ipinfo public IP are unproved. Do not upgrade any of these from source-only or current service ACTIVE to READY.

## R12 refinement — identity-bound native evidence and protocol adoption (2026-11-26)

Inherit Host Network Work@5, R11 #32719/#32730, N01–N10/NS2 and existing
natural owners. Host proposal #32755 is coordination, not release authority.
RFC 3386/8001/9912 shared risk groups motivate physical independence; RFC
9298/9484 motivate standards-based transport candidates. Two interfaces
sharing the same modem are not two independent physical failure domains.

| Scope | Change | Acceptance / remaining boundary |
| --- | --- | --- |
| P0 evidence | Replace global raw sample counting for the three correlated alerts with native per-job unique fresh binary recording and current evaluation checks | promtool positive, duplicate-role negative, missing/stale and invalid binary negative; preserve alert labels; no physical-cause assertion |
| P0 underlay | Measure independently provisioned physical WANs before claiming redundancy | independent origin observations and shared-risk inventory; no second WAN currently established |
| P0 recovery | Keep one physical provider and native lifecycle; health cannot authorize release | observed drift, bounded recovery, exact independent consumer; no automatic protocol cutover |
| P0 device | Issue #2105 per-device exit/DNS observation | physical device receipt, not server READY |
| P1 verification | R11 uv/mise native lock; source-bound promtool tests, independent consumer and fault injection | no new scheduler or custom monitoring engine; source != installed |
| P2 transport | compare mature standard HTTP/QUIC/MASQUE implementations in authorized isolated reference workloads | measured consumer compatibility, goodput, latency, resource cost; no provider or production selection from novelty |

R2.1 evidence LEGO: I raw per-job probe_success and evaluation clock;
O per-role unique fresh binary observation and existing alert states;
S native Prometheus group; pre source-declared five jobs and raw samples;
post each admitted role has exactly one raw series and a binary sample aged
under 90 seconds; alert aggregation requires every role and current recording
evaluation; inv missing/duplicate/stale/invalid is UNKNOWN, not failed or
healthy; eff source rules only; c native PromQL role aggregation (not a
measured runtime improvement); epsilon neither physical independence nor
causal root cause, monitoring classification is not mutation authority;
prov native RED job-01a214af-47de-73ed-974f-6df38b18e49c and original fixtures;
unfold role identity -> sample qualification -> recording -> group alert.
Source PR/CI, installed bytes, loaded rules and independent consumers remain
separate acceptance steps. No service restart or network effect in this work.

## R14 testing reform — native differential and combinatorial verification

Host proposal #32915 extends the R12 candidate PR #2831 and is independent of
R13 history parsing. Existing global TESTING_UPSTREAM_ADOPTION_R1 and Work@5
remain authoritative for task semantics. Reference: NIST SP 800-142 and native
Prometheus rule testing (https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules/).

| Priority | Logic | Native capability and closure |
| --- | --- | --- |
| P0 | Finite independent rule oracle | 243 exhaustive ternary states plus 5-state pair interactions in two contexts, 475 deduplicated vectors, 1425 alert checks; native promtool, not a second evaluator |
| P0 | Mutation evidence | actual old raw count, removed role uniqueness, wrong direct threshold; detect semantic mismatches, not just syntax/exit failures |
| P1 | Temporal and lifecycle model | preserve native stale/recovery regression; Hypothesis stateful/Z3 for unbounded trace inputs where useful |
| P1 | Test cost and retirement | changed property/readset selection, measured runtime, retain independent negative controls and consumer evidence; no count-based deletion |
| P1 | Reproducible carrier | reuse R11 uv/mise, keep native promtool mandatory in core:validate; generic CI native installation and exact protected CI remain separately qualified |
| P2 | Independent fault and consumer acceptance | native isolated netem/Toxiproxy and real OS/application witness; no live disruption or causal claim from model tests |

R2.1: I five named roles, five synthetic observation states and exact rules;
O independent expected/observed three-alert agreement; S temporary native test
fixture/TSDB; pre real promtool; post 243 ternary states and all pair projections
covered; inv missing/duplicate cannot impersonate distinct roles; eff isolated
test only; c measured 19.67s for 475 vectors (not a universal runtime SLA);
epsilon higher-order duplicate combinations and variable temporal traces not
exhausted, production not observed; prov matrix Job
job-01a214e3-6cd3-72f9-af54-0388db11aaaa and mutant Job
job-01a214e4-140a-7473-bd78-bd7537a698b9; unfold specification -> generated fixture
-> native engine -> comparison. Keep existing temporal fixtures. No new runtime
dependency, registry or verification service.


## R15 — Joint qualification and native test execution identity (2026-11-26)

Host #33060/#33067. Join existing R11–R14 exact candidates, retain both
native Task validation calls and the existing uv lock. RED: native
`PYTEST_ADDOPTS=--collect-only mise run ci` reports 543 collected but exits
zero (job-01a21506-4005-7711-ad46-6105aeabbc29). All four owner pytest
entrypoints now remove ambient pytest options/plugins, disable automatic
plugin discovery, and explicitly load the new test-only Hypothesis plugin
from the same locked dev dependency group. Interactive focused testing
remains available through direct uv/pytest invocations, not the qualification gate.

Use Hypothesis rule-based stateful testing for the 19-source-role graph,
with bounded deterministic sequences of omission, duplication, corruption,
repair, pool loss and reordering. Independent multiset oracle, native
API-shaped implementation input, no native network mutations. Shared
test-only fixture inputs extracted from the example tests; no new runner
or production dependency. R2.1 I source roles and generated operation
sequences; O native test outcomes or rejection; S bounded test state; pre
locked source and declared pytest plugins; post native selected obligations
executed without ambient selector suppression; inv independent role
multiplicity and identity, collection != execution; eff isolated testing;
c bounded examples and steps; epsilon no universal proof, no protection
against malicious source/environment outside the scoped selectors, no
production acceptance; prov exact job receipts; unfold locked uv -> native
pytest -> stateful oracle -> test evidence. The conflicting shared package
node-exporter lifecycle remains a cross-owner source contract, not an
authorization to change the active unit.


## R16 — Temporal coverage and historical evidence representation (2026-11-26)

Host #33104, inherits exact R15 joint candidate. RED native pipeline
accepted 32 correctly paired scrapes concentrated in 15.5 minutes as
evidence for a 116-minute window (job-01a2153d-8348-7056-9c7e-dfd7f1a060d5).
Extract pure `historical_observation.py`: full source labels, exact paired
timestamps, immutable paired values, per-role leading/trailing and
inter-sample gap checks, separate successful and failed latency summaries.
At least 12 paired samples and no silence over 45 seconds within the
eligible window (30s declared cadence) are required; this is a conservative
coverage policy, not an availability estimate or proof of independence.
Historical qualification becomes UNKNOWN for inadequate coverage;
existing success floor uses unrounded ratio. Existing legacy all-probe
latency ranking remains unchanged; stratified statistics are diagnostic.
No new runtime dependency; native bundle source inventory includes the
new module (9 files); no deployment or group-atomic install claim.
Native local API witness 3 roles x 60 paired samples with 30s max gap
job-01a2153f-6ff0-7383-ac92-e4e0c97241b3. Generated regular-grid missing
slot oracle and latency partition oracle use locked Hypothesis.
R2.1 I exact per-role series and time bounds; O paired evidence, coverage,
diagnostic summaries, historical standing or UNKNOWN; S ephemeral typed
samples; pre source cadence, labels, matching original coordinates;
post exact pairs and bounded gaps; inv no implied current consumer health,
causality or effect authority; eff read-only source/verification; c sorted
pairing O(n log n), linear gap scan; epsilon historical stationarity and
physical availability unproved; prov native job receipts; unfold native
raw -> identity/time pair -> coverage -> diagnostics -> existing advisory
consumer. Cross-owner exporter correction remains PR2867, reviewed
separately without live effects.


## R17 — Release consumer identity and integration convergence (2026-11-26)

Host #33182; Runtime release consumer specification #33163 and GitHub
owner finding #33171. Official #2822 owner shard passes; repository
mechanics fails on a historical uv version literal in the current owner
test. Preserve registration evidence and scope; verify the native task
route rather than a historical version string. Current source verification
must not reinterpret a historical proof as a toolchain constraint.

The recovery payload contains nine nonsecret files in one directory.
Existing native install sequentially writes these files, then separately
writes two systemd unit files, reloads systemd and restarts the timer.
Observed native-copy fault cuts 1..8 all produce mixed payloads; 0 and 9
are unmixed. This is a temporary-directory injected-command-failure witness,
not a real filesystem power-loss or live service experiment. Fresh byte
readback rejects all incomplete cuts, same-size/same-mtime corruption and
linked payload paths. It does not make publication atomic.

Target reusable release interface (Runtime/Artifact ownership, pending):
immutable staged generation + exact byte/mode manifest + retained roots;
serialized preimage CAS and one durable activation pointer; consumer pins
the generation before resolving sibling imports/config; independent readback
of actual generation consumption; rollback as a new fenced effect. Systemd
unit writes, reload, timer scheduling and actual process effects are separate
obligations and cannot be declared atomic with the pointer. No Network
installer or daemon replacement until a qualified upstream release consumer
contract exists. Reference Nix profiles and OSTree atomic generations.

R2.1 I declared payload and historical/current source coordinates; O
byte/path readback and native route evidence; S bounded temporary test
workspace; pre stable authorized source and declared directories; post
no metadata-cache false match and no linked payload; inv installed bytes
!= loaded generation != consumer acceptance; eff no live changes; c linear
bytes; epsilon no race-free filesystem proof, power-loss durability or
multi-file transaction claim; prov exact Host/Runtime receipts; unfold
source -> byte readback -> native verification -> release consumer.
Consolidate the four original Network drafts and R15/R16 into one review
candidate for official CI; retain original branch history and natural
owner review. Do not merge by bypassing protected checks.


## R18 — Native generation consumer and pure response boundary (2026-11-26)

Host #33243, Runtime Nix private-store qualification #33210, consumer
witness #33251. Retain existing R17 consolidation PR2877. Adopt Nix native
immutable store/profile/GC roots as preferred release substrate candidate,
not an additional Network-specific installer. Runtime must supply
serialized preimage CAS, root acquisition before physical launch, retained
generation path through native terminal, durable receipt and reconciliation;
systemd unit writes/reload are separately qualified effects.

Actual native_switch child path calls re-resolved the active link after
module load; RED job-01a21553-7996-7481-9c53-6f6642ff9f84 (one path and five
malformed selection cases). Resolve source once before sibling imports
and reuse for three child edges. This pins those paths only; a physical
generation launch and retention fence are mandatory to avoid startup races.
Extract pure native_selection.py: typed selected snapshot, canonical
existing selection semantics, strict nested shapes and redacted read-only
projection. Malformed GET response now UNKNOWN rather than AttributeError
(three RED job-01a21554-ee26-717f-b180-7ec87018cc41). No new policy or
provider effect. Existing bundle ten declared nonsecret files. Private
native Nix actual ten-byte-exact/read-only payload and both generation
CLI imports/help PASS job-01a21554-161b-718e-b10f-ce596a1f0bae; second
generation synthetic marker, no provider execution. Generated independent
schema/field projection tests 350 configured examples, native regression
51 PASS and existing Z3 model job-01a21555-5414-713b-9b4d-5894862e768e.
R2.1 I raw JSON shape, current pinned path, source manifest; O canonical
snapshot or explicit rejection, stable child path; S immutable per-process
identity; pre physical generation retained by Runtime; post no per-child
re-resolution, no arbitrary nested payload projection; inv observation !=
effect authorization; eff isolated tests only; c linear schema projection;
epsilon no startup-race or runtime-retention proof, no production policy
change or deployment; prov exact Runtime/Host receipts; unfold source
-> native store -> pinned consumer -> pure representation -> existing
native adapter. Keep native owner lock; no extra production dependency.


## R19 — Native release identity/currentness evidence (2026-11-26)

Host #33286; exact R18 donor. R17 PR2877 official 8/8 and native
GraphQL mergeQueueEntry QUEUED position7 at observation, not merged;
PR2867 remains independent. Runtime #33264/#33268 adopts Nix for
normalized read-only trees, existing exact-mode exchange for legacy
consumers, PG monotonic CAS plus native reader roots still pending.

Existing native bundle verification compared file bytes and selected
loaded-command/calendar substrings but did not qualify the manager's
fragment, drop-ins, load state or reload-needed state. Six false accepts
RED job-01a21566-74a6-710f-9dca-cac2a3d2234a. Separate pure source-side
release_unit_evidence.py; require exactly one of each native systemd
property (loaded, exact fragment, no drop-ins, no reload needed). No
activation changes or new service dependency. Both actual units' native
read-only property output passes job-01a21566-c910-75cc-b2be-12ae7d68f879;
this is manager identity evidence only, not deployed candidate byte
parity. Retain existing selected command/calendar checks, explicitly
consumerExecutionProved=false. No full effective configuration proof or
atomic observation across queries.

Regression tests cover both units, missing/duplicate/foreign metadata,
order invariance and actual native copy interruption at all 11 cuts of
the ten-file payload (9 mixed middle cuts). Persist the prior isolated
failure-cut demonstration as a reproducible regression; synthetic old
bytes never executed, no live effects or power-loss claim. Focused
33 PASS job-01a21567-1a43-753e-b3e9-618157b452be.
R2.1 I declared native unit fragment and manager response; O qualified
identity/currentness or explicit rejection; S none; pre stable trusted
manager and source; post complete unique exact properties; inv
installed bytes != loaded metadata != actual execution/consumption;
eff read-only tests/source only; c linear response; epsilon no
atomic observation, no deployment proof; prov actual Host/Runtime
receipts; unfold native manager observation -> pure projection ->
existing verification. Reuse native systemd, no replacement controller
or registry. Preserve in-flight protected R17 queue head.


## R20 — Native typed loaded configuration (2026-11-26)

Host #33332, R19 donor c32a630cdd; R17 #2877 native protected queue
position5 at observation, not merged. Runtime #33321 receipt snapshot
and reader-lifetime proof remain distinct from per-resource activation CAS.
Replace display-text substring acceptance with existing systemd D-Bus
native JSON property projection (busctl GetUnit, get-property only).
Require exact declared command tuple and exact single calendar rule,
native signatures and numeric coordinate shapes; runtime coordinates do
not prove execution. R19 native identity/currentness checks remain.
RED six synthetic false accepts job-01a2156f-7a62-76f6-bae0-31f41f575b6a;
native systemd 262.2 actual typed property 2/2 read-only PASS
job-01a2156f-d380-76d6-b61d-dee1cf51805f. No new production dependency
(the existing systemd distribution supplies busctl), no changed operational
policy, no activation, no new runtime registry. Separate GetUnit and
property reads do not prove atomic snapshots; exact selected command and
calendar are not full effective unit configuration.
R2.1 I declared expected tuple, native JSON; O qualified bounded configuration
projection or rejection; S none; pre trusted stable manager; post exact
signature, row count, selected static fields and coordinate types;
inv configuration != execution != consumer; eff read-only tests;
c bounded linear parsing; epsilon no whole-unit, live deployment,
concurrent change or startup proof; prov exact jobs; unfold native manager
-> pure projection -> existing verifier. Preserve pending R17 queue;
recompose R18-R20 once actual merge is observed.
Reference https://www.freedesktop.org/software/systemd/man/262/org.freedesktop.systemd1.html
and https://www.freedesktop.org/software/systemd/man/262/busctl.html.


## R21 — Active observation receipt refinement (2026-11-26)

Host #33402; exact R20 donor e8690babd3cb521c7e41dc60f0da62e94efd481f.
R17 PR2877 native GraphQL position2 AWAITING_CHECKS; do not reset
the protected queue. Runtime #33387 reports actual PG/Nix target CAS
prototype and producer/reader composition, not production ABI.

The parent previously consumed any stdout object containing standing
string, even after child exit failure or signal. Eleven false accepts RED
job-01a2157f-e879-7337-95cc-93f8fdaecb17. Extract pure
active_observation.py: shared producer kind/exit mapping, existing
standing/curl parser, strict receiving relation. Success requires exit0
plus matching kind, UTC-shaped coordinate, stable/running observation,
two exact business roles and true typed receipts, zero claimed standby;
NOT_QUALIFIED requires exit1 and coherent false business evidence.
Other existing explicit UNKNOWN/rejected standings retain exit1
semantics, malformed/contradictory observations map to UNKNOWN in the
parent. Reject duplicate/nonfinite JSON and nonfinite/negative timing;
no new geographic policy or operational effect. Native bundle eleven
nonsecret files; durable copy-fault tests now cover all 12 cuts.
Actual synthetic Python child writes success stdout then exits0/1 or
SIGKILL; receiver distinguishes native terminal and evidence. Generated
truth-table oracle, explicit negatives; 109 focused PASS
job-01a21580-b82f-7125-9cf3-c0dbbbad024c. Source-only; no provider calls.

R2.1 I child terminal code and JSON bytes, O bounded observation or
UNKNOWN, S none, pre trusted retained source generation; post exact
terminal/shape consistency, inv stdout != execution != consumer success;
eff pure and read-only tests; c linear JSON, epsilon no freshness,
origin authentication, complete effect or native endpoint proof from
structure alone; prov actual Runtime jobs; unfold producer -> native
terminal -> receiver -> existing orchestrator. No new production
dependency or scheduler. Further decomposition of orchestration,
freshness identity and full effect receipt remains distinct. Reference
https://docs.python.org/3/library/subprocess.html and
https://hypothesis.readthedocs.io/en/latest/tutorial/introduction.html.


## R22 — Native manager object identity and unambiguous representation

Host #33440; exact R21 consolidation head7c5ff9aa081ad53458f58c9d3d98aba90ee02322.
PR2899 official open auto-merge enabled; preserve its in-flight head.
Runtime #33413 independently pursuing positive native terminal evidence.
Native D-Bus reader previously accepted any matching path prefix and
ordinary JSON duplicate-field overwrite. Six RED cases
job-01a21588-7260-71a5-8774-a98e688e8620. Separate pure strict JSON
envelope, object path projection and canonical unit Id match; selected
property read uses the same observed object path. Reject ambiguous JSON
or foreign Id; no activation or operational policy change.
62 focused PASS and actual two native read-only selected properties
job-01a21588-ad6d-7222-923f-99591561e75e. I native manager responses;
O identity-bound property or explicit rejection; S none; pre trusted
stable manager; post canonical Id matches requested unit; inv property
readback != execution/consumption; eff source/tests/read-only; c linear
representation; epsilon no atomic multi-query observation, no production
deployment. Reuse native systemd and Python JSON hooks, no new production
dependency. External references systemd262
https://www.freedesktop.org/software/systemd/man/262/org.freedesktop.systemd1.html
and https://docs.python.org/3/library/json.html.
