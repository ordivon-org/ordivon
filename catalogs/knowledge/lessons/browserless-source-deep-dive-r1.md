# Browserless Source Deep Dive R1

Date: 2026-09-17
Upstream: `browserless/browserless`
Observed upstream HEAD: `016ffa7a72d6249b947a378b152cb437fc330bda`
Local production Browserless: 2.56.7 / Chromium 153.0.8010.12
Scope: source-level architecture analysis for Ordivon Agent Birth and Browser Automation Dynamic Defense. This records control surfaces and attribution hypotheses; it is not a runbook for bypassing third-party production security controls.

## 1. Browserless is not one browser path

The upstream repository contains at least two materially different Chromium control paths:

### CDP route

Relevant source:

- `src/browsers/browsers.cdp.ts`
- `src/shared/chromium.ws.ts`

Behavior:

- Browserless launches Chromium through `puppeteer.launch()` by default.
- If `stealth=true` is supplied, it switches to `@zorilla/puppeteer-extra` + `@zorilla/puppeteer-extra-plugin-stealth`.
- Browserless allocates a concrete remote-debugging port and appends it to launch args.
- It appends Browserless-owned launch flags such as `--no-sandbox`, `--no-first-run`, `--disable-features=LocalNetworkAccessChecks`, and `--disable-component-update`.
- User launch options are merged/passed through to Puppeteer.
- Browserless then proxies the raw Chrome DevTools Protocol websocket to the client.

### Playwright route

Relevant source:

- `src/browsers/browsers.playwright.ts`
- `src/shared/chromium.playwright.ws.ts`

Behavior:

- Browserless starts the browser with version-matched `playwright.launchServer()`.
- If the request does not explicitly choose a headless state, Browserless adds `--headless=new`.
- Browserless merges version-specific Playwright `--disable-features` state with Browserless additions to avoid command-line drift between supported Playwright versions.
- The external websocket is a Browserless proxy for the Playwright server JSON-RPC stream rather than a raw CDP endpoint.

### Ordivon consequence

`Browserless` is too coarse a provider identity. At minimum the witness must carry:

`browserless_route_family = CDP_PUPPETEER | PLAYWRIGHT_SERVER | BQL/OTHER`

because these routes have different launchers, default arguments, protocol surfaces, and page-observable side effects.

## 2. Current Agent Birth uses the CDP/Puppeteer Browserless route

Current `/etc/ordivon/agent-automation-browserless.json` configures:

- `ws://127.0.0.1:3011/chromium`
- `ws://127.0.0.1:3012/chromium`
- `ws://127.0.0.1:3013/chromium`

with `headless=false`, persistent `/data`, and Network-v2 namespace `nv2-browserless-prod`.

Therefore the production carrier is:

`Ordivon Playwright client -> connect_over_cdp -> Browserless /chromium -> browser launched by Puppeteer -> Chromium`

It is **not** Browserless's Playwright-server route.

This matters for attribution. Current `navigator.webdriver=true` and public BotD automation classification occur on a browser that was launched under Puppeteer's launch semantics, then controlled by Playwright over CDP.

## 3. Browserless actively shapes the control plane

The CDP wrapper is not a transparent process supervisor. `ChromiumCDP` installs page listeners and Browserless-owned security machinery. Examples in current upstream source:

- target/page lifecycle listeners;
- request/response/navigation observation;
- console and page-error listeners;
- `Network.enable` on the page's active Puppeteer CDP session;
- `Network.setBlockedURLs` for the navigation/security guard;
- fallback creation of a fresh CDP session when Puppeteer's page session cannot be reused.

This does not prove any one of these signals is responsible for Cloudflare classification. It does establish a stronger architecture fact: Browserless CDP mode changes the browser's protocol/control state before Ordivon's Playwright client performs application work.

## 4. Browserless open-source `stealth` is launcher-level Puppeteer-extra stealth

The open-source CDP path imports:

- `@zorilla/puppeteer-extra`
- `@zorilla/puppeteer-extra-plugin-stealth`

and selects that launcher only when the Browserless `stealth` option is true.

This should not be conflated with BrowserQL `/stealth/bql`. Browserless's current documentation describes BrowserQL stealth as a separate managed/hardened browser path with fingerprint mitigations and entropy injection. Therefore there are at least three distinct concepts:

1. ordinary `/chromium` CDP route;
2. open-source `stealth=true` Puppeteer-extra launch path;
3. BrowserQL `/stealth/bql` managed stealth path.

Ordivon must name these distinctly in experiments.

## 5. Why the old Ordivon carrier could differ materially

Pre-Browserless Ordivon launched Chromium directly with a concrete non-zero debug port and opened ChatGPT in the browser launch command, then attached Playwright later with `connect_over_cdp`.

Current Browserless production path instead has Browserless/Puppeteer own browser creation before the site is controlled by Ordivon's Playwright client.

The differential hypothesis is therefore not merely `Browserless vs not Browserless`. It decomposes into:

- launcher owner: direct Chromium vs Puppeteer;
- initial launch flags/default args;
- whether an automation library owns the browser before first navigation;
- Browserless-owned CDP domain activation/listeners;
- Ordivon Playwright attachment timing;
- profile and network differences.

This decomposition should become the experiment matrix.

## 6. Version drift is first-class in Browserless itself

Browserless 2.56.7 (2026-09-10) pins/supports:

- Puppeteer core 25.10.0;
- Playwright core 1.59.1 through 1.63.0;
- Chromium 153.0.8010.12;
- Chrome 153.0.8010.36.

Its source carries explicit version-specific Playwright disabled-feature lists and a drift test because launch behavior changes across Playwright versions. This is direct upstream evidence for Ordivon's `CONTROL_LAYER_DIGEST` requirement.

## 7. What to absorb vs what not to duplicate

### Absorb / retain

- Browserless browser lifecycle, queueing, health, session accounting, persistence and reconnect infrastructure.
- Exact route-family identity.
- Version-pinned browser/framework compatibility evidence.
- Session metadata and replay/reconnect concepts.
- Clear separation of CDP and Playwright-server paths.

### Do not infer

- Browserless health does not imply security-boundary admissibility.
- `headless=false` does not imply native-browser equivalence.
- open-source `stealth=true` does not imply BrowserQL stealth or universal anti-bot compatibility.
- a Puppeteer-launched browser later controlled by Playwright is not equivalent to the old direct-Chromium/late-attach architecture.

## 8. Required Ordivon witness additions

Add or derive these fields for future browser-security experiments:

- `browserSubstrate`
- `browserlessVersion`
- `browserlessRouteFamily`
- `browserBinary/version/digest`
- `launchOwner` (`DIRECT`, `PUPPETEER`, `PLAYWRIGHT_SERVER`, `BQL`, ...)
- `controlClient` and version
- `controlProtocol`
- `firstNavigationControlState`
- `effectControlState`
- `launchOptionsDigest`
- `profileIdentity`
- `networkAuthorityDigest`

These are provenance, not a stealth score.

## Sources

- Local clone of `https://github.com/browserless/browserless`, upstream HEAD `016ffa7a72d6249b947a378b152cb437fc330bda`
- `src/browsers/browsers.cdp.ts`
- `src/browsers/browsers.playwright.ts`
- `src/shared/chromium.ws.ts`
- `src/shared/chromium.playwright.ws.ts`
- `src/types.ts`
- Browserless changelog 2.56.7
- Browserless BrowserQL and stealth-route documentation
