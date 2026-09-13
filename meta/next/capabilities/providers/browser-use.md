# Provider: Browser Use

Status: **AVAILABLE / PROTOTYPE-READY / USE WHEN AGENTIC BROWSER CONTROL IS REQUIRED**
Role: agent-facing browser interaction provider built on browser/CDP primitives.

## Observed local installation — 2026-09-14

- Browser Use installed as an isolated `uv tool`, upgraded to `browser-use 0.13.10`;
- Browser Use Skill installed for Codex at `~/.codex/skills/browser-use/SKILL.md`;
- the same Skill is also available through the generic Agent Skills location `~/.agents/skills/browser-use/SKILL.md`;
- local `PATH` already resolves `browser-use` from `~/.local/bin`;
- Browser Use Python API was verified by launching an existing Playwright Chromium, creating a real browser page, and reading back the expected title/URL without an LLM or external website;
- default Browser Use extension download was disabled for this smoke test because current network access stalled the optional uBlock Lite fetch; this does not block core BrowserSession/CDP operation;
- the upstream `browser-use install` helper currently falls back to Ubuntu `apt-get` dependency installation on this Arch WSL host, so Ordivon should reuse existing Chromium/Playwright or another native browser instead of treating that helper as authoritative for this machine.

## One-sentence understanding

**Browser Use turns a live browser into an agent-friendly environment by compressing page state into indexed interactive elements plus optional vision, exposing a small action registry, and repeatedly re-observing the page after model-selected actions.**

## When Ordivon should route work here

Prefer Browser Use when the work requires:

- interactive web navigation where the exact path/selectors are not known in advance;
- agent adaptation to changing page structure;
- a logged-in browser session/profile;
- JavaScript-rendered applications;
- multi-step form/site interaction;
- browser tasks that are easier to express as a goal than as a deterministic script;
- an existing coding agent such as Codex that needs browser control through CLI/Skill/MCP.

Prefer thinner or more deterministic providers first when appropriate:

1. **HTTP/API/fetch** for public/read-only data when no interaction is required;
2. **Playwright/Puppeteer/Selenium** for known, repeatable browser flows and tests where selectors/assertions should be deterministic;
3. **Browser Use** when browser navigation/action selection itself requires agent reasoning;
4. **generic Computer Use** when the task spans desktop applications or non-browser GUI surfaces.

Browser Use and Playwright can share/control the same Chromium instance through CDP; they are complementary rather than mutually exclusive.

## Core primitives

### Browser session / profile

A BrowserSession owns or connects to a real browser through CDP and tracks tabs/targets, browser state, downloads, popups, screenshots, storage/profile state and related lifecycle events.

Profiles provide persistent cookies/local storage/login state when needed.

### Agent-facing browser state

Raw browser state is transformed into a bounded observation for the model. The useful state includes roughly:

- current URL/title;
- open tabs;
- visible page information;
- DOM/accessibility-derived interactive elements;
- stable step-local numeric indices for actionable elements;
- optional screenshot/vision context;
- recent action/history state.

The key abstraction is that the model does not need to reason directly over a complete browser DOM or write selectors for every step.

### Interactive element indexing

Browser Use identifies likely interactive elements using DOM attributes, semantic/accessibility roles, browser snapshot information and other heuristics, then exposes them as indexed elements.

This produces an action interface such as:

`[12] <button>Submit</button>`

followed by:

`click(index=12)`

Indices are observations of current state, not durable external identifiers; re-observe after meaningful page changes.

### Action registry

Browser operations are normalized as registered actions/tools with schemas and handlers, for example:

- navigate;
- click;
- input/type;
- scroll;
- back;
- tab operations;
- screenshot;
- extract/read;
- upload/select/keys and other browser-specific operations.

Custom actions can be added without changing the agent loop.

### Agent loop

The essential loop is:

```text
task + history + browser state
        ↓
       model
        ↓
 browser action(s)
        ↓
 action registry
        ↓
 BrowserSession / CDP
        ↓
   live browser
        ↓
 re-observe state
        └──────────────> model
```

The system should re-observe after actions rather than assuming a click/input produced the intended result.

### Event/watchdog layer

Browser Use coordinates browser lifecycle concerns such as DOM updates, screenshots, downloads, dialogs/popups, navigation/security checks and browser reconnection through event/watchdog services.

This is operational robustness around the browser session, not a new Ordivon event framework.

## Security / authority boundary

Web content is untrusted input and may contain prompt injection. Browser automation may also carry authenticated sessions and sensitive information.

Use defense in depth:

- scope browser profiles/sessions to the task when practical;
- prefer existing authenticated profiles/storage state over injecting raw passwords;
- keep secrets out of model context when the provider supports execution-time placeholder substitution;
- restrict domains/network where useful;
- keep host/tool/network permissions independently constrained;
- re-confirm consequential actions and target state where the task has external consequences;
- do not treat Browser Use domain allowlists alone as a complete security boundary.

Recent Browser Use security reports have demonstrated navigation-scheme/domain-restriction bypass classes, reinforcing the need for independent host/network/security controls and current-version review before relying on these controls for sensitive automation.

## Ordivon boundary

Browser Use owns:

- browser session/profile mechanics;
- browser-state extraction/serialization;
- browser action schemas and execution;
- browser-specific operational robustness.

Ordivon owns only:

- deciding that agentic browser interaction is the right provider;
- task framing/constraints;
- composition with other capabilities;
- domain-level acceptance and verification.

Do not copy Browser Use's DOM serializer, CDP session manager, action registry or browser watchdog framework into Ordivon.

## Prototype recipe

A minimal Browser Use-like prototype can be built with:

1. launch or connect to Chromium through Playwright/CDP;
2. read URL/title/tabs and obtain a DOM + accessibility snapshot;
3. identify likely interactive elements and assign current-state numeric indices;
4. optionally capture a screenshot;
5. serialize a compact browser state for a model;
6. expose a small action schema: `navigate`, `click(index)`, `input(index,text)`, `scroll`, `back`, `tabs`;
7. dispatch the model-selected action to Playwright/CDP;
8. wait for relevant page settling and re-observe;
9. repeat until the task's explicit acceptance state is observed;
10. add profile persistence, download/popup handling and security constraints only as required.

This is enough to reproduce the architectural idea. A production system benefits from Browser Use's mature DOM heuristics, browser lifecycle handling, model prompting, loop detection and hosted browser infrastructure; Ordivon should consume those rather than rebuild them.

## Prototype readiness gate

**PASS.** The observation representation, action space, browser transport, agent loop and provider boundaries are explicit enough to implement a minimal working prototype.
