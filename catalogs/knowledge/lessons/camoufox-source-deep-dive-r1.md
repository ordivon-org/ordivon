# Camoufox Source Deep Dive R1

Date: 2026-09-17
Upstream: `daijro/camoufox`
Observed upstream HEAD: `52d6746a4a67830ec8a24e2196822204ba843134`
Scope: source-level study of engine-level automation isolation and cross-layer identity consistency. This is not a production anti-bot bypass runbook.

## 1. Camoufox is a custom browser distribution, not a Playwright plugin

The repository includes:

- Firefox source patch sets under `patches/`;
- patched Playwright Firefox/Juggler integration under `patches/playwright/` and `additions/juggler/`;
- Python launch/config generation under `pythonlib/camoufox/`;
- browser fingerprint datasets/configuration;
- native/build/service tests;
- platform build tooling.

The build-system diagram in the repository makes the ownership clear:

`Firefox source + fingerprint patches + system fonts + patched Juggler + addons/debloat -> custom Firefox build`

Therefore the correct Ordivon provider identity is a **browser distribution digest**, not merely `Playwright + wrapper`.

## 2. Automation isolation is implemented below ordinary page JavaScript

Camoufox patches Firefox/Juggler so Playwright's Page Agent operates in an isolated scope rather than exposing ordinary injected objects in the page world. The repository explicitly documents this as a defense against JavaScript inspection of Playwright bindings and page-agent behavior.

The transferable architectural idea is:

`page-visible execution world != automation-control execution world`

For Ordivon Security this should become a detector family: `CONTROL_WORLD_ISOLATION`.

It does **not** imply general invisibility. The project itself warns that browser identity can still be detected through inconsistent fingerprint combinations.

## 3. Fingerprint consistency is a graph problem in the actual source

The Python library does not just choose a UA. It generates/repairs related surfaces including:

- navigator/platform/oscpu;
- screen/window geometry;
- OS marker fonts;
- speech voices;
- WebGL vendor/renderer;
- locale/languages/Accept-Language;
- timezone/geolocation;
- media devices;
- WebRTC/network-related configuration.

Recent source tests explicitly encode relationships between fields, e.g. WebGL renderer ↔ screen plausibility, navigator architecture ↔ UA, screen ↔ window bounds, and locale ↔ default speech voice.

The project fixed issue #729 because synthetic BrowserForge fingerprints sampled WebGL independently from screen/platform, creating impossible combinations. This is direct evidence for Ordivon's `cross-layer consistency graph` model.

## 4. Camoufox contains explicit leak warnings

`pythonlib/camoufox/warnings.yml` and launch validation warn that manually overriding one domain can make the whole identity inconsistent, including examples around navigator, screen/window, WebGL, fonts, and touch capability.

This is an important inversion for Ordivon:

**more spoofing knobs can reduce trust quality** if they break correlations.

The experiment system should therefore score/record constraint violations, not count how many fields were changed.

## 5. Input behavior is a browser-engine subsystem

Camoufox centralizes synthesized mouse/wheel dispatch in Juggler (`MouseDispatch`) and has dedicated regression tests for whether events are acknowledged and observed by the content renderer. Its 2026 input-dispatch documentation records repeated deadlocks caused by geometry/rounding interactions across spoofed OS profiles.

Transferable lesson:

behavioral realism and automation correctness share one input pipeline. A humanization layer that is not mechanically correct can deadlock or create new observable anomalies.

Therefore Ordivon should treat `INPUT_DISPATCH_IMPLEMENTATION` as provenance and keep functionality/correctness tests beside any behavior-observability test.

## 6. Playwright compatibility is a maintained protocol fork

`docs/playwright-maintenance.md` shows Camoufox must continuously sync Playwright's Firefox patches and Juggler implementation while preserving Camoufox-specific changes and Firefox-version migrations.

Recent release notes show the cost concretely:

- Playwright-version keyed browser floors;
- Firefox/Juggler compatibility updates;
- headless/geometry tell fixes;
- speech-voice leak fixes;
- WebGL/screen coherence fixes;
- WebRTC/proxy fixes;
- input trajectory regressions.

This is not a small dependency. It is a high-maintenance browser+protocol fork.

## 7. Native controls remain mandatory

Camoufox issue history contains cases where stock Firefox under the same Playwright protocol behaved differently from Camoufox while TLS/HTTP2 fingerprints were identical. Other reports show proxy introduction changing outcomes while direct connectivity did not.

Therefore every Ordivon lab experiment involving a specialized browser should include:

- stock/native browser negative control;
- same automation protocol when possible;
- same network path;
- same browser major if possible;
- one-factor-at-a-time changes.

## 8. What to absorb

- Cross-layer consistency graph and invariant tests.
- Control-world isolation as its own detector family.
- Browser distribution + protocol fork as versioned provenance.
- Browser/runtime compatibility gates tied to control-client version.
- Native browser controls.
- Regression tests for geometry/input/identity contradictions.

## 9. What not to absorb into Ordivon core

- Firefox/C++ anti-detect patches themselves.
- Fingerprint-spoofing recipes.
- Site-specific WAF behavior assumptions.
- A private browser fork as a correctness dependency for Agent Birth.

If evaluated, Camoufox belongs behind a replaceable experimental provider boundary.

## 10. Required witness extensions

- `browserDistributionDigest`
- `browserEngineMajor`
- `automationProtocol` (`JUGGLER`, `CDP`, ...)
- `controlWorldIsolationMode`
- `fingerprintSource` (`NATIVE`, `SYNTHETIC`, `PRESET`)
- `identityConstraintSetDigest`
- `identityConstraintViolations[]`
- `inputDispatchImplementationDigest`
- `controlClientVersion`
- `browserControlCompatibilityFloor`

## Sources

- Local clone of `https://github.com/daijro/camoufox`, HEAD `52d6746a4a67830ec8a24e2196822204ba843134`
- `README.md`
- `docs/playwright-maintenance.md`
- `docs/input-dispatch.md`
- `pythonlib/camoufox/fingerprints.py`
- `pythonlib/camoufox/utils.py`
- `pythonlib/tests/test_webgl_screen_consistency.py`
- `pythonlib/tests/test_fingerprint_fixes.py`
- `patches/*`
