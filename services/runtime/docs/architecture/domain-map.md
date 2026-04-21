# Domain Map

## Core Domains

- `market`: symbols, market snapshots, derived market state, signal inputs
- `portfolio`: holdings, exposures, weights, cost basis, aggregate portfolio views
- `trading`: trade intent, order preparation, execution lifecycle metadata
- `research`: investment theses, analysis artifacts, research conclusions
- `journal`: logs, post-trade reviews, review queues, lessons learned
- `strategy`: strategy definitions, rule packs, activation state, ownership metadata
- `risk`: domain-level risk concepts such as exposure, sizing, drawdown, limits
- `reporting`: report objects, summaries, exports, publication metadata
- `userprefs`: defaults, watchlists, personalization, output preferences

## Current Code Mapping

- `pfios/domain/analysis` maps primarily toward `domains/research`
- `pfios/domain/recommendation` maps primarily toward `domains/trading` and `domains/reporting`
- `pfios/domain/review`, `issue`, and `lessons` map primarily toward `domains/journal`
- `pfios/domain/audit` overlaps `governance/audit` and should be clarified during migration
- `pfios/domain/outcome` and `usage` likely split between `domains/` and `state/`

This mapping is directional, not final. Each move should be reviewed against the truth boundary rules.
