# FlareSolverr Source Deep Dive R1

Date: 2026-09-17
Upstream: `FlareSolverr/FlareSolverr`
Observed upstream HEAD: `fe5e1e8cea10a68952e2eadd40401e973aa3b44f`
Observed package version: `3.5.2`
Scope: source-level study of drift detection, browser/session lifecycle, and failure attribution. This is not a production challenge-bypass runbook.

## 1. Architecture

FlareSolverr is a small service wrapping a Selenium-family browser control stack:

`HTTP API -> flaresolverr_service.py -> SessionsStorage -> utils.get_webdriver() -> vendored undetected_chromedriver -> Chromium/Chrome`

Important source:

- `src/flaresolverr_service.py`
- `src/sessions.py`
- `src/utils.py`
- `src/undetected_chromedriver/*`

The repository vendors its own `undetected_chromedriver` implementation instead of relying only on an external package. Selenium itself is pinned (`4.47.0` in the observed tree). Therefore the meaningful provider identity is a version bundle, not just `FlareSolverr 3.5.2`.

## 2. Challenge recognition is a detector state machine

The service does not have privileged Cloudflare state. It infers page state from page-visible observations such as:

- known challenge/access-denied titles;
- known CSS selectors;
- element disappearance/staleness;
- navigation/redirect behavior;
- cookies collected after the page stabilizes.

This is a crucial research lesson: the adapter's **detector can drift independently of the protected site's actual policy**. A timeout can mean at least:

1. the security provider changed policy;
2. the security provider changed challenge UI/DOM;
3. the detector's title/selector vocabulary became stale;
4. the browser/control layer changed behavior;
5. network/IP state changed;
6. the challenge is still present but represented differently;
7. the adapter itself has a timing/resource failure.

Therefore `challenge_timeout` must never be treated as a single root cause.

## 3. Browser lifecycle and detector lifecycle are coupled but distinct

`utils.get_webdriver()` constructs a browser/control stack and `SessionsStorage` optionally retains it across requests. Sessions are idempotently keyed and can be expired/recreated by TTL.

This gives two orthogonal state axes:

- browser/session identity and age;
- detector/challenge state.

For Ordivon, profile/session lifetime must therefore be part of every browser-security witness. A failure after a long-lived session and the same failure on a fresh session are different experiments.

## 4. The launcher is a bundled control-layer fork

The observed source launches via vendored `undetected_chromedriver` with a set of Chrome arguments and a headed/Xvfb strategy on Linux rather than relying solely on normal headless mode. The project also maintains its own patched-driver lifecycle.

The transferable point is not the particular stealth settings. It is that a mature anti-detection adapter often becomes a **multi-component compatibility bundle**:

- browser build/package;
- browser driver;
- patched control layer;
- Selenium version;
- launch configuration;
- detector logic;
- session/cookie model.

Ordivon should digest/version this bundle as one experimental provenance object.

## 5. The source itself demonstrates detector-induced side effects

The service may enable CDP Network instrumentation for resource filtering, navigates/reloads around cookie application, observes titles/selectors, and waits on DOM state changes. These actions change timing and protocol/control state.

Therefore an anti-bot adapter cannot be evaluated only by whether the final page loads. Instrumentation itself can change the browser's observable behavior. This reinforces the need for a native-browser negative control and a minimal-control baseline.

## 6. Why FlareSolverr is valuable as a drift sensor

The code contains many hard-coded challenge recognizers. That makes it fragile, but also makes public regressions highly informative:

- when titles/selectors change, challenge recognition regresses;
- when browser/Selenium/driver compatibility changes, control behavior regresses;
- when session/cookie timing changes, returned state regresses;
- when protected-site policy changes, the same recognizers may remain intact while outcomes change.

Its release/issue stream can therefore act as an external ecosystem signal for Ordivon Security, provided we reproduce any claim in an authorized neutral lab before attribution.

## 7. Required Ordivon failure taxonomy

At minimum separate:

- `DETECTOR_DOM_DRIFT`
- `DETECTOR_SEMANTIC_DRIFT`
- `CONTROL_LAYER_DRIFT`
- `BROWSER_VERSION_DRIFT`
- `PROFILE_SESSION_DRIFT`
- `COOKIE_STATE_DRIFT`
- `NETWORK_REPUTATION_OR_ROUTE_DRIFT`
- `TIMING_OR_RESOURCE_FAILURE`
- `UNKNOWN_PROTECTED_SITE_POLICY_CHANGE`

A generic `CHALLENGE_TIMEOUT` is only the symptom envelope.

## 8. Metrics worth absorbing

- last-known-good timestamp/version tuple;
- first-known-bad timestamp/version tuple;
- reproduction rate on fresh vs retained session;
- reproduction rate on native-browser negative control;
- detector-state mismatch rate;
- time-to-detect;
- time-to-attribute;
- time-to-safe-route.

## 9. What not to copy

- Site-specific challenge interaction routines are not a durable Ordivon architecture.
- Hard-coded selectors/titles must not become domain truth.
- A returned cookie is evidence of one browser/session observation, not proof of general admissibility.
- The vendored driver fork should be treated as an external experimental provider, not absorbed into Ordivon core.

## Sources

- Local clone of `https://github.com/FlareSolverr/FlareSolverr`, HEAD `fe5e1e8cea10a68952e2eadd40401e973aa3b44f`
- `src/flaresolverr_service.py`
- `src/sessions.py`
- `src/utils.py`
- `src/undetected_chromedriver/*`
- `requirements.txt`
