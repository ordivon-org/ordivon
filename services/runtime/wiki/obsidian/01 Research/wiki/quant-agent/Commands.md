# Quant Agent 常用命令

本页记录当前可用的日常运维与交易入口，优先使用 `just` 与 Hermes CLI。

## 进入项目

```bash
cd /home/dev/projects/quant-agent
direnv allow
```

当前标准入口已恢复可用：

```bash
cd /home/dev/projects/quant-agent
direnv allow
direnv exec . just test
```

## Just 命令（推荐）

```bash
just doctor
just test
just account
just health
just status
just check-shadow
just show-blockers
just reconcile
just cleanup-prepared
just pause-trading
just resume-trading
just sync-account
just hermes-account
just hermes-status
just hermes-health
just hermes-sync
```

## 脚本入口（需要 qpython）

```bash
./bin/qpython scripts/account_summary.py
./bin/qpython scripts/account_health.py
./bin/qpython scripts/system_status.py --check shadow --json
./bin/qpython scripts/show_blockers.py --json
./bin/qpython scripts/reconcile_state.py --json
./bin/qpython scripts/cleanup_prepared.py --json
./bin/qpython scripts/pause_trading.py --reason operator_check --json
./bin/qpython scripts/resume_trading.py --json
./bin/qpython scripts/sync_account.py --json
./bin/qpython scripts/sync_orders.py
./bin/qpython scripts/open_position.py --symbol BTC/USDT:USDT --side long
./bin/qpython scripts/close_position.py --symbol BTC/USDT:USDT
./bin/qpython scripts/cancel_order.py --order-request-id ord_xxx
./bin/qpython scripts/fetch_ohlcv.py --help
```

## Hermes CLI（项目内）

```bash
hermes quant status
hermes quant health
hermes quant doctor
hermes quant status --json
hermes quant account-sync
hermes quant open --symbol BTC/USDT:USDT --side long --mode dry_run --entry-price 70000
hermes quant close --symbol BTC/USDT:USDT --mode dry_run
hermes quant cancel --order-request-id ord_xxx
hermes quant sync-orders
```

## 环境变量（OKX）

```bash
OKX_API_KEY=...
OKX_SECRET_KEY=...
OKX_PASSPHRASE=...
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```
