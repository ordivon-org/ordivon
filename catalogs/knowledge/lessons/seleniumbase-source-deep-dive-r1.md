# SeleniumBase Source Deep Dive R1

Date: 2026-09-17
Upstream: `seleniumbase/SeleniumBase`
Observed upstream HEAD: `52ceddcfbc466c937f88b322cfa69f11600b1e0a`
Scope: source-level study of browser lifetime vs control attachment lifetime, UC/CDP mode transitions, and late Playwright attachment. This is not a production anti-bot bypass runbook.

## 1. SeleniumBase models browser control as state, not as one permanent connection

Important source:

- `seleniumbase/undetected/__init__.py`
- `seleniumbase/core/browser_launcher.py`
- `seleniumbase/fixtures/shared_utils.py`
- `seleniumbase/core/sb_cdp.py`

The UC driver has explicit methods:

- `disconnect()` — stops the chromedriver service while the browser process remains;
- `connect()` — restarts the service and recreates the WebDriver session;
- `reconnect(timeout)` — disconnects, waits, restarts, and recreates the session;
- `is_connected()` / `_is_connected` — exposes connection state.

This is a major architectural distinction: **browser process lifetime and WebDriver attachment lifetime are separate state machines**.

## 2. CDP Mode is an explicit controller handoff

`uc_open_with_cdp_mode()` disconnects WebDriver, discovers the existing browser's remote-debugging endpoint, and starts the CDP driver against that same browser process.

`fixtures/shared_utils.is_cdp_swap_needed()` then redirects supported high-level calls to CDP methods while WebDriver remains disconnected.

The repository therefore has a formal controller transition of the shape:

`WEBDRIVER_ATTACHED -> WEBDRIVER_DISCONNECTED + CDP_ATTACHED`

with optional later transitions back to WebDriver.

For Ordivon this is stronger than a generic `browser running` flag. The exact control attachment at each phase is observable provenance and may change page-visible behavior.

## 3. Navigation and attachment are deliberately decoupled

`uc_open_with_reconnect()` and `uc_open_with_disconnect()` separate navigation from WebDriver connection state. In UC/CDP mode, a browser may navigate while WebDriver is absent and later be reattached.

This is structurally similar to pre-Browserless Ordivon:

`direct browser launch/navigation -> later automation attach`

The similarity does not prove identical anti-bot outcomes, but it establishes that `browser-first / controller-later` is a mature external architecture pattern rather than merely homemade glue.

## 4. SeleniumBase exposes a late-attach Playwright composition

`examples/cdp_mode/playwright/ReadMe.md` documents a composition where SeleniumBase/CDP owns an already-running Chrome session and Playwright later calls `connect_over_cdp()` against its remote-debugging endpoint.

The repository supports multiple controller compositions:

- UC/WebDriver -> disconnect -> CDP;
- Pure CDP with no WebDriver;
- CDP-owned browser -> Playwright `connect_over_cdp`;
- hybrid modes where WebDriver can be reconnected later.

This is highly relevant to Agent Birth because our current Browserless composition is different:

`Playwright -> Browserless /chromium -> Puppeteer launches browser`

while the old Ordivon path was closer to:

`browser launches independently -> later Playwright connect_over_cdp`.

## 5. Control transitions create both observability and correctness risk

The source and docs make it clear that reconnecting WebDriver is not behaviorally neutral. Separately, every transition can create mechanical risks:

- stale or recreated sessions;
- window-handle changes;
- extension tabs;
- control API availability changes;
- races during reconnect;
- commands that silently switch controller implementation.

Therefore a security experiment must test both:

1. page-observable/detector behavior;
2. automation correctness after each transition.

## 6. Required Ordivon attachment-state model

At minimum represent:

- `BROWSER_NATIVE_UNATTACHED`
- `CDP_CONTROLLER_ATTACHED`
- `PLAYWRIGHT_OVER_CDP_ATTACHED`
- `WEBDRIVER_ATTACHED`
- `WEBDRIVER_DISCONNECTED`
- `GUI_HUMAN_CONTROL`

These are controller states, not trust scores.

Each transition should be recorded with:

- monotonic timestamp;
- controller/provider identity;
- browser PID/process identity where available;
- remote-debugging endpoint identity/digest, not token-bearing URL;
- page/conversation coordinate;
- whether navigation occurred before/after the transition.

## 7. Required witness additions

- `browserProcessIdentity`
- `browserLaunchOwner`
- `webdriverServiceState`
- `cdpControllerState`
- `playwrightAttachmentState`
- `controlTransitions[]`
- `firstNavigationControlState`
- `effectControlState`
- `navigationInitiator`
- `attachLatencyMs`
- `reattachCount`
- `controllerBundleDigest`

This makes `ATTACHMENT_WINDOW` an explicit experiment dimension.

## 8. Experimental consequence for Agent Birth

A neutral A/B should hold browser build, network authority, profile class, target diagnostic page, and observation tooling constant while changing only controller timing:

- browser navigates before any automation controller attaches;
- controller attaches before first navigation;
- controller attaches after first navigation;
- controller detaches and reattaches.

The goal is attribution of observable differences, not defeating a protected production challenge.

## 9. What to absorb vs what not to copy

### Absorb

- browser lifetime separate from controller lifetime;
- explicit attachment-state machine;
- controller handoff and late attach as supported architecture;
- pure-CDP vs hybrid controller distinction;
- transition-specific regression tests.

### Do not absorb into Ordivon core

- site-specific CAPTCHA interaction methods;
- claims that one controller mode is permanently undetectable;
- SeleniumBase's patched driver as an irreplaceable correctness dependency.

If evaluated, SeleniumBase belongs behind a provider/experimental boundary.

## Sources

- Local clone of `https://github.com/seleniumbase/SeleniumBase`, HEAD `52ceddcfbc466c937f88b322cfa69f11600b1e0a`
- `seleniumbase/undetected/__init__.py`
- `seleniumbase/core/browser_launcher.py`
- `seleniumbase/fixtures/shared_utils.py`
- `seleniumbase/core/sb_cdp.py`
- `help_docs/uc_mode.md`
- `examples/cdp_mode/ReadMe.md`
- `examples/cdp_mode/playwright/ReadMe.md`
