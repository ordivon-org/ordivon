# Finance Pack Inventory

## Purpose

This inventory lists finance-specific files and directories that should not become core primitive owners.

## Immediate Candidates

- `orchestrator/context/context_builder.py`
- `orchestrator/context/market_context.py`
- `orchestrator/context/portfolio_context.py`
- `policies/trading_limits.yaml`
- `tools/market_data/README.md`
- `tools/news_data/README.md`
- `tools/broker/README.md`
- `domains/market/README.md`
- `domains/portfolio/README.md`
- `domains/trading/README.md`

## Later Candidate Areas

- finance-specific recommendation wording/rendering
- market/news/broker integrations when they gain executable logic
- finance policy overlays beyond the current minimal trading limits file

## First Staged Extraction Completed

- `packs/finance/context.py` now owns:
  - `MarketContext`
  - `PortfolioContext`
  - finance analysis context defaults
- `orchestrator/context/market_context.py` and `orchestrator/context/portfolio_context.py` are now compatibility shims
- `packs/finance/analyze_defaults.py` now owns symbol/timeframe-driven analyze capability defaults

## Wrong Placement To Avoid

- Do not treat this inventory as a migration script
- Do not mark execution/governance/runtime primitives as finance-pack candidates
- Do not move files just to satisfy this document
