# Browser Use Agent-Browser Kernel — extracted design lessons

Status: **REGISTERED / PROTOTYPE-READY**  
Registered: 2026-09-14

## One-sentence model

**Browser Use is an agent-browser adapter: it converts a live web page into a compact, actionable observation and maps model-selected browser actions back onto the real browser through CDP.**

## Why this matters

A browser automation library such as Playwright already knows how to click, type, navigate and inspect pages. Browser Use adds the missing layer needed by a general LLM agent:

- a bounded representation of what the browser currently offers;
- an action vocabulary the model can choose from;
- stable-enough short-lived references to interactive elements;
- an iterative observation/action loop;
- browser lifecycle handling suitable for long, dynamic tasks.

The important innovation is therefore not a new click primitive. It is the **agent-facing perception/action interface** between web state and model reasoning.

## Core mechanism 1: compress reality before reasoning

Do not send a complete browser implementation/DOM dump to the model if a smaller task-relevant representation is sufficient.

Browser Use combines information such as DOM structure, accessibility semantics, page snapshots and optional screenshots into a model-facing state containing URL/tabs/content and indexed interactive elements.

General lesson:

`raw environment -> task-relevant observation -> agent`

This reduces context size and makes tool selection more reliable.

## Core mechanism 2: expose affordances, not selectors

A coding agent should not need to synthesize CSS/XPath selectors for every unknown page interaction.

Instead expose current affordances such as:

```text
[3] Search input
[7] Submit button
[9] Product link
```

and actions such as:

```text
input(3, "query")
click(7)
```

The index is deliberately ephemeral. The page may re-render, so the correct loop is:

`observe -> act -> re-observe`

not:

`observe once -> execute a long blind action sequence`

## Core mechanism 3: structured state + vision are complementary

DOM/accessibility information is efficient and precise for ordinary web controls. Screenshots/coordinate actions are useful when visual layout or non-standard controls matter.

Prefer structured browser semantics first and add vision where it provides information unavailable or unreliable in DOM state.

This is usually more efficient than treating every web task as generic pixel-only computer use.

## Core mechanism 4: separate reasoning from browser execution

The agent loop should choose actions from schemas; the browser provider performs them.

```text
model decision
   ↓
action schema
   ↓
registry/handler
   ↓
browser session
   ↓
CDP/browser
```

Custom browser actions can be added to the registry without rewriting the model loop.

This mirrors the same tool-registry principle observed in Codex.

## Core mechanism 5: browser state is a session, not isolated HTTP calls

Web tasks often depend on:

- cookies/login state;
- tabs;
- local storage;
- downloads;
- navigation history;
- popups/dialogs;
- dynamic rendering.

Therefore browser automation needs an explicit session/profile boundary. Persistent profiles can reuse authentication, while task-specific profiles can isolate trust/state when necessary.

## Core mechanism 6: observation after effects

A successful browser command only establishes that an interaction was attempted/executed. It does not establish the intended page/business effect.

After consequential or state-changing actions:

1. re-read browser state;
2. inspect the relevant confirmation/state;
3. only then continue or claim success.

This is the browser-specific form of Ordivon's `execution success != semantic success` rule.

## Core mechanism 7: browser-specific lifecycle services belong in the provider

Downloads, popups, DOM refresh, screenshots, navigation readiness, browser crashes/reconnection and related concerns are mature browser-provider responsibilities.

Do not migrate these into a generic Ordivon operations/event subsystem. Ordivon should see Browser Use as one replaceable capability provider.

## Routing against adjacent tools

### HTTP/fetch

Use when the desired information is directly available without browser interaction or authenticated JS state.

### Playwright/Puppeteer/Selenium

Use when the page and intended flow are sufficiently known that deterministic selectors/actions/assertions are preferable, especially automated tests and stable production scripts.

### Browser Use

Use when the path through the site is uncertain or changing and model reasoning must choose interactions from current page state.

### Generic computer use

Use when the task crosses non-browser applications or requires whole-desktop GUI control that web semantics cannot represent.

### n8n

Use when the service exposes a stable API/integration and a deterministic workflow can avoid browser automation entirely.

A useful preference order is therefore:

`native API/connector -> deterministic HTTP/workflow -> deterministic browser script -> agentic browser -> generic GUI`

Move right only when the thinner/more deterministic representation cannot satisfy the real task.

## Security lesson: the browser is an adversarial environment

Unlike a local repository, webpages routinely contain content controlled by third parties. An agent can mistake webpage text for instructions.

Therefore:

- webpage content must remain data, not trusted authority;
- secrets should not be unnecessarily exposed to model context;
- credentials/session state should remain provider/profile-owned;
- restrict network/domains where useful but do not rely on a single URL filter as complete isolation;
- require stronger confirmation for financial, publishing, account or other consequential effects;
- keep version-specific browser security controls under review.

This threat model is materially stronger than ordinary deterministic browser testing.

## What Ordivon should not copy

- Browser Use's DOM extraction/serializer implementation;
- accessibility and interactive-element heuristics;
- Chrome/CDP target/session management;
- browser watchdog/event infrastructure;
- LLM provider abstraction;
- hosted browser/proxy/stealth infrastructure;
- loop detector/planner/judge implementation;
- browser-specific credential/profile synchronization mechanisms.

These are provider implementation details with significant maintenance cost.

## What Ordivon should retain as knowledge

1. **Represent environments for agents through bounded affordances, not raw state.**
2. **Use ephemeral action references and re-observe after changes.**
3. **Prefer structured semantics before pixels when the environment exposes them.**
4. **Separate agent reasoning/action schemas from provider execution.**
5. **Treat session state as natural provider-owned state.**
6. **Verify post-action reality rather than trusting tool success.**
7. **Route to the thinnest deterministic interface before escalating to browser agents.**
8. **Treat external web content as adversarial/untrusted instructions.**

## Minimal prototype

A prototype requires only:

```text
Chromium + CDP/Playwright
        ↓
DOM/accessibility snapshot
        ↓
interactive-element detector
        ↓
indexed browser-state serializer
        ↓
LLM + small browser action schema
        ↓
execute action
        ↓
re-observe
```

Five or six browser actions are sufficient to demonstrate the concept. Browser Use's value beyond this prototype is the accumulated production work around perception quality, browser lifecycle, robustness and scaling.

## Project-study acceptance

### One-sentence test

PASS: Browser Use adapts a real browser into an agent-readable observation and agent-executable action environment.

### Prototype test

PASS: the observation/action/session loop and transport boundary are explicit enough to implement a minimal prototype on top of Playwright/CDP.

## Verdict

**PASS — USE PROVIDER + EXTRACT PERCEPTION/ACTION DESIGN RULES.**

Further source study should be demand-driven around specific browser reliability, security, authentication or scaling problems.
