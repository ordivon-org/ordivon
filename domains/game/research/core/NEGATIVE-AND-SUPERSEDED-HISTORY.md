---
schema_version: 1
id: game.research.core.negative-superseded-history
title: Ordivon Game — Negative / Superseded History
profile: research
lifecycle: active
source_role: canonical-navigation
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
---
# Ordivon Game — Negative / Superseded History

Negative results and superseded handoffs are retained for provenance. They do not become current authority merely because their evidence still exists in Git history.

## Cancelled historical GDF3 — Game Feel / Feedback / Sensorimotor Coupling

Historical commit:

```text
042e34d  research(game): open GDF3 game feel foundations
```

Durable negative-history ref:

```text
refs/heads/research/history/game-feel-gdf3-cancelled
```

At that commit, the branch introduced a Game Feel version of:

```text
docs/GAME_DEEP_FOUNDATIONS_GDF3_A.md
evidence/gdf3-a/game-feel-falsifiers.json
evidence/gdf3-a/term-target-matrix.json
scripts/gdf3-a/*
```

That branch was opened prematurely and is **cancelled / noncanonical**. The current path `docs/GAME_DEEP_FOUNDATIONS_GDF3_A.md` belongs to the later canonical Authoritative Case Determination lineage and must not be confused with the historical Game Feel file at `042e34d`.

## Superseded next-route ordering

The old Game Feel / Time / Space / Strategy handoff ordering was explicitly demoted from roadmap status in:

- [GDF2 Closeout](../../docs/GAME_DEEP_FOUNDATIONS_GDF2_CLOSEOUT.md)

The unbiased whole-Game coverage search then replaced inherited ordering with evidence-driven route selection:

- [Game Deep Foundations Domain Coverage Search](../../docs/GAME_DEEP_FOUNDATIONS_DOMAIN_COVERAGE_SEARCH.md)

## Historical guards

```text
Cancelled Game Feel GDF3 != current GDF3
Superseded residual ordering != roadmap
Negative evidence != disposable evidence
History retention != current semantic authority
```
