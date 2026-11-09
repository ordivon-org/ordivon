# Ordivon 存量架构与源码审计：范围与 SourceCut

- 日期：2026-11-10，Asia/Shanghai
- Git SourceCut：`ef17d6879d12faa61fff3bb762b0d500d73c9113`，仓库 https://github.com/ordivon-org/ordivon
- 来源：独立 Runtime Git Workspace，从 `/root/projects/ordivon` 读取；没有修改共享主检出。
- 现行长期 Owner 模块化工作计划：`docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md`，由其他 Agent 的 PR #2006 原地更新。本目录只是本次历史审计的交付工件，**不是另一个治理权威或新注册表**。

## 系统边界与责任

系统目标：在已有功能、接口、持久化语义、外部消费者与可恢复性不变的条件下，降低源码责任重复、维护成本和历史过期表征。必须遵循 DELETE → REUSE → COMPOSE → 原地 REPAIR，拒绝增量功能、测试体系、消费者线路、产品化、新的 Owner/Daemon/Policy 引擎。

| 事实类型 | 现行自然 Owner | 代码/真实入口 |
| --- | --- | --- |
| Workspace、Job、Attempt 和物理执行 | Runtime | `services/runtime/crates/ordivon-runtime-core/src/` |
| Work、Space、Topic、Message 协作连续性 | Host | `services/host/src/ordivon_host_v2/` |
| Agent Run、工具/模型调用、Journal/CAS 和 Agent 连续性 | Harness | `services/harness/src/ordivon_harness/` |
| 北向工具路由 | Gateway | `services/gateway/src/ordivon_gateway/` |
| 策略、身份、网络、OS 部署 | Security/Network/Workstation | `platform/` |
| 金融、媒体、游戏、Artifact、数据 | 对应自然 Owner | `domains/`、`capabilities/`、`packages/` |

根仓库只管理 Source/CI/依赖图机械事实；不得成为第二个 Domain/Runtime/Harness 语义状态源。`tools/repo/owners.toml` 有 21 个 Owner。

## Phase 与证据层级

- Phase 0：SourceCut、Owner、硬约束、10+ 条现代化可执行判据。
- Phase 1：全部 Git 跟踪文件的路径/类型/大小/内容哈希，明确入口、目录和未知消费者。
- Phase 2：语义边界/代码和配置审查，具体反例按阻塞/高/中/低分级。
- Phase 3：最小可回滚实施任务 DAG，优先删除已无独立消费者的链条。
- Phase 4：只做存量修改；使用**既有** Owner/Repo 验证和真实 GitHub PR。
- Phase 5：记录相对 SourceCut 的变化、原生验证和待决风险。

本批所有 5002 个文件均进入 `INVENTORY.md` 机械清单，**不能由此声称已经逐个验证了 5002 个文件的代码语义**。直接已读源码/入口消费者/本地验证 > README/设计声明；Git MERGED、真实安装、Runtime Job、领域效果各自独立。独立 Space 审计意见只提供反例，不授予完成权威。

## 回滚和外部盲区

采用 Git commit/受保护 PR。回滚使用当前主线校验后对合并 SHA 的 `git revert`；不 reset 共享分支、不清理其他 Agent 的 Workspace。动态 import、配置驱动、systemd 运行实例、外部服务、唯一历史回放证据可能不出现在静态 grep；对此记录具体 UNKNOWN，不把 UNKNOWN 当无消费者，也不因一个 UNKNOWN 保留整片已确认垃圾。
