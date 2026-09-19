# Web Provider Routing Closeout — 2026-09-14

## Standing

This slice is **locally complete**. No additional provider, wrapper, scheduler, or browser abstraction is admitted merely for architectural completeness.

## Accepted composition

| Need | Provider | Current standing |
|---|---|---|
| Provider-native/API/MCP path | Native connector | caller-bound |
| Plain public retrieval | direct HTTP/fetch | available |
| Site-scale crawl/map/extract | Firecrawl | deferred; unavailable locally |
| Known deterministic browser flow | Microsoft `@playwright/cli` | available |
| Unknown/changing browser UI requiring adaptive action choice | Browser Use | available |
| Desktop GUI beyond browser semantics | Computer Use | caller-bound |

The semantic selection rule lives in `scripts/web_interaction_route.py` and `.agents/skills/web-provider-routing/SKILL.md`. Physical Playwright CLI/browser materialization is owned by Workstation v2 through `/root/tools/bin/playwright-cli-binding`; Microsoft Playwright continues to own browser/session/action semantics.

## Acceptance evidence

- Workstation v2 main: `91d68223f3c62dd74b54992eb8edb061fbbdbeb2`.
- Ordivon Next main: `5a47897f16e7931f79207b6690be141cc1d87339`.
- Workstation test suite: 76/76 passed before integration.
- Next test suite: 21/21 passed before integration.
- Real browser E2E passed: router selected Playwright, Workstation materialized the exact upstream config, Microsoft `@playwright/cli` executed `open -> snapshot -> fill -> click -> find -> close`, and the resulting DOM state contained `route-verified`.
- Adaptive browser intent continued to select Browser Use.
- Site-scale acquisition with Firecrawl unavailable returned `NO_ADMITTED_PROVIDER` rather than silently shrinking to curl or Browser Use.
- `AGENTS.md + web-provider-routing` prompt-only Agent context materialized to 7,139 UTF-8 bytes.
- Representative Campaign Birth bootstrap compiled to 7,680 / 16,384 bytes with no provider SEND.
- Canonical Skill digest: `sha256:65eb31084a86c467be046f45308de9a2f717d9e2e14dc87faa60fc716fa3e808`; project, local Agent, and Codex copies matched at closeout.

## Deliberately deferred / not blockers

### Firecrawl

Do not install or maintain Firecrawl until a real site-scale acquisition workload exists. Re-enter this slice only when there is an actual task whose required semantics include crawl/map/batch extract and the current router returns `NO_ADMITTED_PROVIDER`. At that point prefer the mature Firecrawl provider rather than implementing a private crawler.

### Computer Use

Computer Use remains caller/application-bound. It is not a missing local service. Re-enter only when a task genuinely crosses out of browser semantics into desktop GUI interaction and the active application exposes Computer Use.

### Native connector availability

Native connector availability remains caller/application/plugin/MCP-bound. It must not be inferred from static local documentation.

## Rejected expansions

- no Ordivon Playwright wrapper API;
- no private selector engine, browser lifecycle, trace model, or action registry;
- no Host tool router;
- no Harness planner for browser routing;
- no custom Skill classifier for prompt-only Birth;
- no Firecrawl install without a real workload;
- no fallback that pretends direct HTTP is site-scale crawling;
- no provider mechanical completion interpreted as owning-domain semantic success.

## Re-entry triggers

This slice should be reopened only if one of the following becomes true:

1. a real site-scale workload requires Firecrawl-class semantics;
2. the Workstation Playwright binding becomes unavailable or exact CLI/browser identity changes incompatibly;
3. Browser Use is no longer healthy for adaptive browser work;
4. a caller exposes Computer Use and a concrete desktop-GUI task requires it;
5. an upstream provider surface changes enough that the current routing contract becomes false;
6. prompt-only Agent context can no longer fit the carrier budget.

Absent one of those triggers, further work on this slice is negative-value architecture churn.
