# External Candidate Funnel R1

## Rule

Gate 0 is the latest-stable language baseline: Python 3.14.7 and Rust 1.98.1 as of 2026-09-21.

Passing Gate 0 does not imply adoption. A candidate must still have an active exact contract, pass semantic/authority and executable correctness gates, and demonstrate a material advantage over the smallest credible local baseline.

## Current funnel

| Candidate | Language gate | Active exact contract | Current standing |
|---|---|---:|---|
| OpenBB 4.7.3 | PASS declared Python 3.14-capable range | No | no adoption; AGPL/deployment review only if a contract appears |
| PyPortfolioOpt 1.6.0 | PASS declared Python 3.14 | No | no adoption; future matrix must include SciPy 1.18.x HRP compatibility |
| Riskfolio-Lib 7.3.0 | PASS CPython 3.14 wheel evidence | No | no adoption; heavy dependency/supply-chain surface remains a gate |
| NautilusTrader | v2 upstream language matrix passes; individual versions differ | Yes | no version currently passes all gates |
| Qlib | FAIL, classifiers stop at Python 3.12 | No | rejected |
| RD-Agent | FAIL, tested evidence centers Python 3.10–3.11 | No | rejected |
| TradingAgents 0.5.0 | UNQUALIFIED for Python 3.14 | No | reference only |
| ai-hedge-fund 2.2.0 | UNQUALIFIED for Python 3.14 | No | reference only |

## Nautilus version split

The project name is not the qualification unit.

- rc4: old-language historical evidence.
- v1.231.0: latest-language compatible, but failed the exact DENY/risk-effect contract.
- rc5: current v2 challenger, but pre-release and not locally executable-qualified.

Therefore no Nautilus implementation is in the canonical core dependency graph after R1.

## Dependency consequence

The canonical environment no longer installs NautilusTrader merely to make import nautilus_trader succeed. Candidate-bound rc4 modules live under tools/nautilus_rc4, and the Market core src tree has no Nautilus import.

This is the intended funnel behavior: eliminate candidates early, keep only evidence, and spend integration cost only on a candidate with a live contract and a realistic chance of beating the local baseline.
