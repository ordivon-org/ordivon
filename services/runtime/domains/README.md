# Domains

`domains/` holds business meaning for the Capability Layer. It is where business semantics live when they are deeper than a single user-facing capability.

## Intended Subdomains

- `market/`: market data semantics, market events, derived market views
- `portfolio/`: positions, holdings, exposures, allocation semantics
- `trading/`: execution preparation, order intent, trade lifecycle semantics
- `research/`: analysis artifacts that remain business-level, not raw wiki storage
- `journal/`: trading journal and review-centered business semantics
- `strategy/`: strategy rules, lifecycle, activation, and metadata
- `risk/`: domain-facing risk concepts that are distinct from governance enforcement
- `reporting/`: report domain semantics and export-ready report objects
- `userprefs/`: user operating preferences and default behaviors

## Rules

- Organize by business object, not by framework.
- Keep transport concerns in `apps/`.
- Keep user-facing feature packaging in `capabilities/`.
- Keep final policy enforcement in `governance/`.
- Keep persistence plumbing in `state/`.
