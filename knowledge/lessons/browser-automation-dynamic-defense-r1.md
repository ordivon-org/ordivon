# Browser Automation Dynamic Defense R1

Date: 2026-09-17
Status: ACTIVE STUDY
Scope: external-first study of browser-automation detection, drift measurement, adaptive provider routing, and trust-boundary design for Ordivon Security and Agent Birth.

## Safety / architecture boundary

This corpus records externally documented detection surfaces, architecture patterns, maintenance/drift lessons, and authorized-lab experiments. It is not a runbook for defeating third-party production security controls. Production challenge boundaries remain separately governed; the transferable asset is faster measurement, attribution, regression, and provider switching.

## Research question

What observable properties distinguish an automated browser carrier from an ordinary supported client, how do those properties drift across browser/framework/security-provider releases, and how should Ordivon detect, attribute, and adapt to that drift without coupling correctness to one fragile carrier?

## 1. Browserless / BrowserQL

### Verified external facts

- Browserless' ordinary service exposes remote browsers to standard, unforked Puppeteer and Playwright clients. Browserless explicitly recommends BrowserQL when bot detectors or CAPTCHAs are the workload.
- Browserless separates ordinary browser infrastructure from premium BrowserQL / advanced stealth routes. Its documented premium capabilities include persistent sessions, session replay, fingerprint-randomization-oriented stealth routes, and proxy routing.
- Therefore ordinary Browserless health is not evidence that the carrier presents as an ordinary human-controlled browser. Browser infrastructure correctness and anti-automation observability are separate properties.

### Transferable kernel for Ordivon

1. Separate **browser substrate** from **trust presentation**. Browser process lifecycle, pooling, health, queueing, persistent sessions, replay, and resource isolation are mature substrate concerns worth retaining.
2. Treat anti-automation observability as an independent measurement plane, not as an implicit property of a healthy Browserless endpoint.
3. Preserve session replay and persistent-state concepts as diagnostic evidence: when a security boundary drifts, Ordivon should be able to compare the exact browser/runtime/profile/network witness before and after the change.
4. Route by workload: ordinary deterministic browser work can use normal Browserless/Playwright; challenge-sensitive/auth-sensitive work needs a distinct supported trust lane or authorized lab lane rather than assuming ordinary CDP is sufficient.
5. Do not reimplement Browserless queueing/session/resource machinery locally merely to regain browser-first semantics; preserve the mature substrate and isolate the trust-boundary decision above it.

### Agent Birth implication

Current `chatgpt-carrier-*` Browserless success should mean only `browser substrate available`. It must not mean `provider security boundary admissible`. Keep those states orthogonal in diagnostics and policy.

### Sources

- https://github.com/browserless/browserless
- https://github.com/browserless
- https://docs.browserless.io/

## 2. FlareSolverr

### Verified external facts

- FlareSolverr is a long-running Cloudflare-focused browser proxy built around Chrome/Selenium-family automation. Its GitHub history is especially valuable as a public drift ledger rather than as a production dependency recommendation.
- The project repeatedly records abrupt breakage after Cloudflare-side changes: e.g. a July 2026 issue reported that the same versions had worked roughly 12 hours earlier and then entered repeated managed-challenge loops/timeouts; June 2026 reports also show challenge-detection logic becoming stale.
- Its 2026 releases continue to chase moving boundaries: v3.5.0 included a Turnstile-related repair; v3.5.2 bumped Chromium and made challenge wait timing configurable while fixing multi-button and cookie timing defects.
- Operational failures are not only anti-bot failures. Current issues also expose concurrency, orphan-browser, secret/logging, cookie-validity and timing problems. This is useful evidence that a challenge adapter must be evaluated as a distributed system, not merely by pass/fail on a page.

### Transferable kernel for Ordivon

1. Use FlareSolverr's public issue/release stream as an **external change sensor**. A burst of challenge-loop, selector, timing, or browser-version regressions is evidence of possible ecosystem drift worth reproducing in our authorized lab.
2. Maintain a versioned **drift ledger** with `last-known-good`, `first-known-bad`, browser/framework/security-provider observations, environment and exact witness. Avoid narratives such as "Cloudflare broke it" without a bounded change window.
3. Separate failure classes: `DETECTION_POLICY_DRIFT`, `CHALLENGE_UI_DRIFT`, `BROWSER_VERSION_DRIFT`, `TIMING/PERFORMANCE`, `SESSION/COOKIE`, `CONCURRENCY/RESOURCE`, and `SECURITY_OF_THE_ADAPTER`.
4. Do not define adaptation as blind retry. A repeated challenge loop is a distinct state requiring attribution or provider switch; repeated clicking is not progress evidence.
5. Track release cadence and issue latency as measurable external signals. The useful competitive property is **time-to-detect / time-to-attribute / time-to-safe-route**, not a claim of permanent bypass.

### Agent Birth implication

When a provider boundary changes, Agent Birth should emit a structured drift event and preserve the pre-effect fence. The controller should be able to compare the failure against external ecosystem signals and route to a different admitted carrier without converting retries into duplicated effects.

### Sources

- https://github.com/FlareSolverr/FlareSolverr
- https://github.com/FlareSolverr/FlareSolverr/releases
- https://github.com/FlareSolverr/FlareSolverr/issues

## 3. Camoufox

### Verified external facts

- Camoufox is a Firefox fork that pushes fingerprint and automation-isolation work into the browser/Juggler layer rather than relying mainly on JavaScript monkey-patching. Its public design isolates Playwright page-agent behavior from the page-visible world and attempts cross-surface consistency across navigator, screen/window geometry, WebGL, fonts, locale/timezone, WebRTC and network headers.
- The maintainers explicitly warn that hiding the automation library is not sufficient: fingerprint rotation can still become internally inconsistent, and anti-bot providers can search for a single impossible combination.
- The repository itself is a live demonstration of drift pressure. In 2026 the project acknowledged a maintenance gap and degraded performance from an old Firefox base plus newly discovered inconsistencies. Recent releases repaired concrete coherence leaks such as WebGL↔screen, host speech voices, screen/window geometry and WebRTC/proxy behavior while updating the Firefox/Playwright baseline.
- The maintainers' 2026 long-term-plan discussion also states that being an openly branded anti-detect browser put the project on major anti-bot vendors' radar and made that positioning hard to sustain.

### Transferable kernel for Ordivon

1. Model browser identity as a **cross-layer consistency graph**, not a list of spoofable fields. A witness should relate browser version, engine, OS/arch, UA/UA-CH, navigator, screen/window, WebGL/GPU, fonts, locale, timezone, voices, WebRTC/network and transport observations.
2. Prefer measurements of **invariants and contradictions** over a single bot score. Example class: claimed platform and renderer impossible together; viewport and CSS screen disagree; locale/timezone/network geography disagree; host-only voices leak through a claimed foreign device profile.
3. Separate the page-visible world from the automation-control world conceptually. For authorized lab evaluation, record whether control-plane actions cause page-observable side effects or execution-context changes.
4. Treat browser-engine-level approaches as high-maintenance dependencies, not magic. They carry base-browser churn, build complexity, protocol compatibility and rapid anti-bot counter-research.
5. Add a `PATCH/PROFILE LEAK DETECTOR` concept to Ordivon Security: after any browser/runtime upgrade, automatically compare a clean baseline with the candidate and localize which observable family changed.
6. Maintain a plain/native browser negative control in every experiment. Camoufox's own issue stream shows that proxy/network changes can interact with browser identity, so attribution must vary one factor at a time.

### Agent Birth implication

Agent Birth should not try to synthesize a large fake identity surface itself. The useful lesson is to measure consistency and preserve native-browser controls. If a specialized browser is evaluated, it belongs behind a provider boundary with version-pinned evidence and regression gates, not embedded into Birth correctness semantics.

### Sources

- https://github.com/daijro/camoufox
- https://github.com/daijro/camoufox/releases
- https://github.com/daijro/camoufox/discussions/571
- https://github.com/daijro/camoufox/issues

## 4. SeleniumBase (UC Mode / CDP Mode)

### Verified external facts

- SeleniumBase UC Mode is explicitly designed around a modified ChromeDriver that disconnects and reconnects WebDriver at strategic times. Its documentation says the disconnect period exists to reduce detectability during sensitive page transitions.
- SeleniumBase later introduced CDP Mode as a successor/extension because anti-bot systems advanced beyond what UC Mode alone handled. In CDP Mode, WebDriver can remain disconnected while direct CDP control continues; reconnecting WebDriver is documented as potentially restoring a detectable state.
- The project has very high release velocity: its GitHub release history contains over a thousand releases, and 2026 releases repeatedly carry `CDP Mode: Patch N` increments. This is a concrete example of dynamic maintenance rather than a fixed stealth recipe.
- Public issue history shows abrupt external drift: examples document Cloudflare checks that worked continuously and then stopped within hours, plus later updates that forced test/example changes.

### Transferable kernel for Ordivon

1. Preserve **browser-control decoupling** as a first-class architecture pattern. Browser lifetime and browser-control lifetime do not have to be identical.
2. Model control attachment as state: `NATIVE/UNATTACHED`, `CDP_ATTACHED`, `WEBDRIVER_ATTACHED`, `GUI/HUMAN`, rather than treating "browser running" as one state. Record transitions in the witness.
3. Add an `ATTACHMENT_WINDOW` experiment dimension: compare what the site can observe before control attachment, while attached, after detachment, and after reattachment. This directly tests the hypothesis raised by old Ordivon Agent Birth.
4. High-frequency patch releases are evidence that stealth/detection compatibility is a living dependency. Provider admission should therefore be version-fenced and continuously requalified.
5. Do not copy SeleniumBase's anti-bot interaction routines into Ordivon. The transferable asset is the **dynamic connection-state model** and regression cadence, not its site-specific bypass behavior.
6. Keep an ordinary/native browser negative control and a standard unmodified automation positive control in every lab batch so a change in the detector can be separated from a change in the candidate carrier.

### Agent Birth implication

Old Ordivon's `launch Chromium first -> navigate -> later connect_over_cdp` deserves preservation as an explicit experimental/control architecture. Agent Birth should be able to express `browser alive` independently of `automation attached`, and should capture the exact attachment state at first navigation and at provider effect time.

### Sources

- https://github.com/seleniumbase/SeleniumBase
- https://github.com/seleniumbase/SeleniumBase/blob/master/help_docs/uc_mode.md
- https://github.com/seleniumbase/SeleniumBase/blob/master/examples/cdp_mode/ReadMe.md
- https://github.com/seleniumbase/SeleniumBase/releases

## 5. Patchright

### Verified external facts

- Patchright is a Chromium-only Playwright fork/driver patch set. Its documented focus is not browser lifecycle infrastructure but automation-library observability: `Runtime.enable`, `Console.enable`, default Playwright launch flags, init-script behavior and other driver-level leaks.
- It explicitly treats `Runtime.enable` as a major detection surface and changes execution-context handling to avoid the standard Playwright behavior. It also changes several default Chromium flags associated with automation presentation.
- Patchright runs upstream Playwright tests after releases and automatically tracks new Playwright versions, but its maintainers warn that upstream code changes can cause breakage and repairs can take days.
- Its 2026 issue stream provides a concrete regression witness: a user reported a Turnstile-related interaction that worked on Playwright/Patchright 1.59.4 and regressed on 1.60.0. Regardless of the site's private decision logic, this is exactly the kind of version-local behavioral change Ordivon should detect before promotion.

### Transferable kernel for Ordivon

1. Maintain an explicit **automation-leak taxonomy** independent of browser fingerprints. Initial families: protocol-domain activation, console/debugger side effects, execution-context lifecycle, injected/init-script observability, launch-flag presentation, page-agent globals, and timing side effects.
2. Treat upstream automation-framework upgrades as security-observability changes, not merely dependency upgrades. A version bump must re-run the browser-security matrix before production promotion.
3. Preserve a `STANDARD_PLAYWRIGHT` arm and a `CANDIDATE_CONTROL_LAYER` arm in lab tests. Differential observation is more informative than accepting a project's own "passes X" claim.
4. Record **functionality trade-offs introduced by stealth modifications**. A change that removes a leak can disable console/debug tooling, alter init-script semantics, or create race conditions; stealth quality and automation correctness must be tested together.
5. Introduce an Ordivon concept of `CONTROL_LAYER_DIGEST`: exact framework/driver version + patch set + browser build. Browser identity alone is insufficient provenance.
6. Never assume a patched framework is permanently clean. Patchright's continuous release/test model is itself evidence that this boundary must be requalified continuously.

### Agent Birth implication

For Agent Birth, compare the current Browserless + stock Playwright control layer against old raw-Chromium/late-attach and other candidate control layers in an authorized neutral lab. Promotion should require both ordinary workflow correctness and no regression in the agreed observability witness; neither bot-score success nor framework unit tests alone is sufficient.

### Sources

- https://github.com/Kaliiiiiiiiii-Vinyzu/patchright
- https://github.com/Kaliiiiiiiiii-Vinyzu/patchright/releases
- https://github.com/Kaliiiiiiiiii-Vinyzu/patchright/issues

## 6. Rebrowser Patches

### Verified external facts

- Rebrowser Patches is deliberately narrow: it patches Puppeteer/Playwright source-level behavior that cannot be removed by normal launch settings, with `Runtime.enable` execution-context observability as the flagship mechanism and `sourceURL`/utility-world behavior as additional leak classes.
- The project itself warns that source patches are fragile across upstream library changes. Its latest published package line remains much smaller and less release-dense than SeleniumBase/Patchright, making it more useful as a mechanism study than as a default production substrate.
- A July 2026 issue provides an unusually useful negative result: on the same Chrome build, stock Playwright and Rebrowser scored identically on a JS↔network consistency checker because that checker measured `navigator.webdriver`, headless UA and cross-layer consistency while Rebrowser intentionally targets a different layer (`Runtime.enable`). This demonstrates that "automation detection" is not one scalar phenomenon.
- Current issues also contain reports of residual detection and compatibility regressions, reinforcing the project's own warning that one patched side channel does not make a browser generally indistinguishable.

### Transferable kernel for Ordivon

1. Split the Security witness into **orthogonal detector families**. Minimum initial families:
   - control-protocol / execution-context side channels;
   - browser launch and webdriver presentation;
   - page-world injected artifacts;
   - JS/browser fingerprint consistency;
   - network/transport consistency;
   - behavioral/session observations.
   A candidate can improve one family while leaving all others unchanged.
2. Prefer **mechanism-level A/B experiments**: same browser build, same network, same page, same profile class, one control-layer change. Rebrowser's 2026 issue is an excellent template for avoiding false attribution.
3. Do not collapse external test scores into a universal `bot_score`. Store per-detector observations plus detector version/digest so changes in the detector itself remain visible.
4. Use narrow patch projects as hypothesis generators and laboratory controls, not as proof that the whole client is trustworthy or production-admissible.
5. Add a `DETECTOR_COVERAGE_MATRIX` to Ordivon Security. Every experiment should say which observable families each detector actually covers and which it cannot see.

### Agent Birth implication

The current Browserless/Playwright failure must be decomposed rather than labelled simply `automation detected`. The next neutral experiment should hold Chrome/network/profile constant and vary attachment/control-layer state while collecting multiple detector families. This can distinguish `webdriver/launch`, `CDP Runtime`, fingerprint-consistency, transport, and session effects instead of guessing from a single challenge result.

### Sources

- https://github.com/rebrowser/rebrowser-patches
- https://github.com/rebrowser/rebrowser-patches/issues/127
- https://github.com/rebrowser/rebrowser-patches/issues

## Cross-project synthesis

The six projects converge on one architecture lesson: **browser automation observability is a moving, multi-layer state space, not a one-time stealth setting.** Browserless supplies mature browser infrastructure; FlareSolverr exposes ecosystem drift; Camoufox demonstrates engine-level consistency work; SeleniumBase demonstrates dynamic attachment state; Patchright catalogs driver-level leaks; Rebrowser shows why detector families must remain orthogonal.

For Ordivon Security, the durable asset should therefore be a `Browser Automation Dynamic Defense Lab` with:

- version-fenced carrier matrix;
- native-browser negative controls;
- standard-automation positive controls;
- attachment-state witnesses;
- cross-layer consistency graph;
- automation-leak taxonomy;
- detector coverage matrix;
- last-known-good / first-known-bad drift ledger;
- time-to-detect, time-to-attribute, and time-to-safe-route metrics;
- provider routing that keeps browser substrate health separate from security-boundary admissibility.

This lab belongs to authorized measurement and red-team environments. Production correctness must not depend on continuously defeating a third-party security challenge; the adaptive capability is measurement, attribution, regression, and safe routing.
