---
name: web-provider-routing
description: "Choose the thinnest currently admitted web/browser/desktop provider, then verify the resulting provider/domain state."
---

# Web Provider Routing

Use this skill when a task may require a connector/API, public-web acquisition, browser automation, adaptive browser control, or desktop GUI interaction.

## Selection law

Do not classify by keywords alone. Infer the task's actual interaction needs, then ask the local route profile for the thinnest admitted provider.

1. If an already-connected native connector/API/MCP tool directly satisfies the task, prefer it.
2. If the task only needs readable public content, prefer direct HTTP/fetch.
3. If the primary workload is web search/scrape/map/crawl/normalization at site scale, prefer Firecrawl **only when a real Firecrawl provider is currently available**.
4. If browser interaction is required and the flow/selectors/assertions are known, prefer an admitted Playwright/deterministic browser adapter.
5. If current page state must determine the next action, use Browser Use.
6. Use Computer Use only when required interaction crosses outside browser semantics.

Run the current local census before relying on a local provider:

```bash
python /root/projects/ordivon-next/scripts/web_interaction_route.py --census
```

For a route decision, translate the task into explicit facts rather than passing natural language to a classifier. Examples:

```bash
# Public read-only page
python /root/projects/ordivon-next/scripts/web_interaction_route.py

# Unknown/stateful browser UI
python /root/projects/ordivon-next/scripts/web_interaction_route.py \
  --requires-interaction --adaptive-browser-reasoning

# Known deterministic browser flow when the current application has admitted Playwright
python /root/projects/ordivon-next/scripts/web_interaction_route.py \
  --requires-interaction --deterministic-browser-flow --caller-available playwright

# Desktop interaction only when the current carrier actually provides Computer Use
python /root/projects/ordivon-next/scripts/web_interaction_route.py \
  --requires-interaction --requires-desktop-gui --caller-available computer_use
```

`caller-available` is evidence supplied by the current application/carrier. It cannot be used to invent local Browser Use or HTTP availability.

## Local Browser Use path

When the decision selects `browser_use` on this node, use the structured isolated adapter rather than arbitrary Browser Use Python:

```text
/opt/ordivon/agent-automation/current/scripts/browser_use_browserless.py
```

Keep one stable `--session-id` for the bounded task. Use `open -> observe -> click/input/scroll/back/tabs -> observe -> close`. Bind click/input to the observed index plus role and accessible name. Re-observe after meaningful state changes. `browser-agent-*` is the generic pool; never consume `chatgpt-carrier-11/12/13` for ordinary web tasks.

## Completion boundary

Provider success is narrow evidence only. After an action, verify the strongest relevant state available from the external provider/domain. Never convert a browser click, HTTP 200, crawl completion, Playwright assertion, or Computer Use action into domain completion without the task's actual acceptance evidence.

For a consequential ambiguous external effect, do not automatically try another provider or resend. Reconcile with owner-native idempotency/receipt/read-back semantics first.
