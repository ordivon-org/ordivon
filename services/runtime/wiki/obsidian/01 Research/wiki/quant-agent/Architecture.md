# Quant Agent 架构要点

本项目已转为 OKX-first 架构：优先使用 OKX 原生 REST 直连，ccxt 作为兼容路径保留。

## OKX-first 目标

- 在 WSL 内通过 Windows `curl.exe` 复用宿主机网络路径
- 避免 `ccxt` 私有 API 初始化卡死导致整条链路不可用
- 将账户、执行、行情拆为可独立替换的 Adapter

## 关键模块

- `scripts/okx_private_rest.py`
  - 私有 REST 签名与请求
  - 账户同步、下单、撤单、订单查询
- `scripts/okx_market_data.py`
  - 公共行情入口（K 线、标的、order book）
- `scripts/account_adapters.py`
  - 账户快照统一入口与 OKX 规范化
- `scripts/exchange_adapters.py`
  - 交易与行情统一入口（脚本层调用）
- `scripts/pipeline_core.py`
  - 通用 schema / 时间工具
  - `create_ccxt_compat_client(...)` 作为兼容回退

## 典型流程

1. `sync_account.py` -> `account_adapters.fetch_account_snapshot`
2. `dispatch_execution.py` -> `exchange_adapters.place_order`
3. `sync_orders.py` -> `exchange_adapters.fetch_known_order`
4. `fetch_ohlcv.py` -> `exchange_adapters.create_market_data_adapter`

## 当前兼容策略

- OKX 账户同步：native-first
- OKX 执行下单：native-first
- OKX 行情拉取：native-first
- 其他交易所：暂保留 ccxt 作为兼容路径
