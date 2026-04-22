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
- `packs/finance/analyze_profile.py` now owns the finance analyze request/profile defaults used by API and workflow entrypoints
- `packs/finance/analyze_surface.ts` now owns the finance front-end analyze option/default surface consumed by command-center and analyze workspace UI
- `packs/finance/policy.py` now owns finance trading-limits overlay refs
- `packs/finance/tool_refs.py` now owns finance tool namespace refs for market/news/broker wiring

## Wrong Placement To Avoid

- Do not treat this inventory as a migration script
- Do not mark execution/governance/runtime primitives as finance-pack candidates
- Do not move files just to satisfy this document
