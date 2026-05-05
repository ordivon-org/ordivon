---
gate_id: trading_discipline_fixtures
display_name: Trading Discipline Fixtures
layer: L5B
hardness: hard
purpose: Validate trading discipline intake fixtures — thesis quality, stop_loss, risk ratios, behavioral checks
protects_against: "Invalid intake fixtures, missing required fields, emotional risk bypass, revenge trade fixture gaps"
profiles: ['full']
timeout: 30
tags: [finance, trading-discipline, fixtures, intake]
---

# Trading Discipline Fixtures Checker

## Purpose

Validates that trading discipline test fixtures are well-formed.
Each fixture is a JSON decision intake payload that goes through
the Finance Pack's TradingDisciplinePolicy gates.

## Governed Objects

Test fixtures in `tests/unit/finance/` and `tests/fixtures/` that
exercise the trading discipline policy (thesis quality, risk ratios,
emotional state, revenge trade, chasing detection).
