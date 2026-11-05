# Network execution program R1

Date: 2026-11-05. This file is an immutable *source-bound acceptance/backlog DAG*, NOT a new task-state database or scheduler. Ordivon Host Work alone owns mutable task state; Git/PR owns source and release truth; Runtime owns execution truth; systemd, Podman, Gluetun, sing-box and Tailscale own installed/runtime effects.

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
