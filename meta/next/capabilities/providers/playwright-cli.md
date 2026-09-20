# Provider: Microsoft Playwright CLI

Status: **AVAILABLE / USE FOR DETERMINISTIC BROWSER FLOWS**
Role: mature browser automation and inspection provider for known, repeatable web interaction.

## Current local standing — 2026-09-14

- upstream provider: Microsoft `@playwright/cli` `0.1.18`;
- exact CLI entrypoint is registered by Workstation v2 rather than copied into Ordivon;
- current Chromium is supplied by Workstation's existing Playwright browser binding;
- `/root/tools/bin/playwright-cli-binding profile|materialize` only resolves node-local CLI/browser/config facts;
- callers invoke Microsoft `playwright-cli` directly for browser actions;
- a real `open -> snapshot -> click -> snapshot/find -> close` flow passed against the bound Chromium.

The local CLI package and browser cache have different bundled revision expectations, so Workstation materializes an upstream-native config with the exact current `executablePath`. Because the current WSL execution user is root, the config also sets Playwright's own `chromiumSandbox=false` launch option. These are physical launch facts, not new Ordivon browser semantics.

## Route work here when

Use Playwright when:

- selectors, assertions, and control flow are known or intentionally deterministic;
- browser regression/smoke/accessibility checks should be repeatable;
- the task needs exact click/fill/navigation/screenshot/network/trace operations without an Agent choosing each next action from an unknown UI;
- a project or application can define the browser flow explicitly.

Use thinner or different providers when:

- public content is readable without browser interaction -> direct HTTP/fetch;
- site-scale acquisition/normalization is the primary object -> Firecrawl when actually available;
- the next browser action must be chosen adaptively from changing/unknown state -> Browser Use;
- interaction leaves browser semantics -> Computer Use.

## Authority boundary

Playwright owns browser/session/action semantics and its own command surface. Workstation v2 owns only exact node-local CLI/browser materialization and launch binding. Runtime owns physical execution evidence when Runtime is used. The task/domain owns why the browser operation is needed and whether the resulting state satisfies acceptance.

Do not copy Playwright's selector engine, browser lifecycle, trace model, test runner, MCP surface, or CLI action registry into Ordivon.
