# Quant Agent 当前状态

更新日期：2026-04-13

## 总体结论

quant-agent 已完成 OKX 私有与公共 API 的稳定直连，核心交易、账户与行情链路可在 WSL 环境下正常运行。ccxt 仍保留为兼容路径，但不再是默认入口。

本轮仓库级收尾已完成：

- root-owned 工作树污染已处理到不再阻塞仓库开发
- journal / status / execution / report 输出已改为 profile 驱动路径
- 测试输出与真实工作树已解耦
- shadow readiness 已改为按 `shadow_allowed_symbols` 判定
- 当前仓库级回归结果：`52 passed`
- `/nix/store` ownership 漂移已修复，标准 `direnv` 入口恢复可用

## 已可用能力

- 账户同步：balances / positions / open_orders 可拉取并入库
- 账户诊断：健康检查、摘要输出、失败 fallback
- 执行链路：开仓、平仓、撤单、订单同步
- 行情链路：OKX K 线与基础行情数据拉取
- 生命周期与复盘：订单与持仓事件链路已落库
- Hermes CLI：可通过 `hermes quant ...` 执行操作与诊断

## 架构定位

- OKX-first：优先走原生 REST（Windows `curl.exe` 在 WSL 内执行）
- 兼容层：`pipeline_core.create_ccxt_compat_client(...)` 作为回退路径
- Adapter 化：账户、执行、行情均由统一入口适配
- 输出目录已统一解析：`pipeline_core` 负责 `reports_root` / `executions` / `journals` / `status` / `quantstats`
- readiness 语义已拆分：
  - 全局市场健康继续保留
  - shadow 检查只按允许的 rehearsal symbol 判定
  - live 检查继续保持更严格的全局约束

## 关键数据表

- `account_sync_runs`
- `account_balances`
- `account_positions`
- `account_open_orders`
- `position_states`
- `position_lifecycles`
- `position_events`
- `order_requests`
- `order_events`

## 已知限制

- WSL 内 `ccxt` 的私有 API 仍可能受网络路径影响，不作为默认路径
- DuckDB 并发写入可能出现锁冲突，已加 retry 但仍建议顺序执行
- 当前 OKX 直连依赖 Windows `curl.exe`，对宿主机网络路径有依赖

## 当前运维结论

- `shadow`：当前可用
- `live`：仍按策略关闭，且继续受全局 market-data health 约束
- 当前推荐 rehearsal symbol：`ETH/USDT:USDT`
- 当前全局异常仍会记录 `BTC/USDT:USDT:stale_market_data`，但不会再误阻断 ETH-only shadow check
- 标准项目入口已恢复：
  - `direnv exec . just test`
  - `direnv exec . just sync-account`
  - `direnv exec . ./bin/qpython scripts/system_status.py --check shadow --json`

## 快速入口

详见 [[01 Research/wiki/quant-agent/Commands]]。
