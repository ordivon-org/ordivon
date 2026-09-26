# Cloudflare / Provider Security Experiment R9

Date: 2026-09-18
Standing: **R9 WINDOW-PLACEMENT MECHANISM ATTRIBUTED / PROVIDER CAUSALITY OPEN**

Primary evidence:

- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r9-window-placement-run1-20260918.json`
- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r9-window-placement-run2-20260918.json`
- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r9-repeatability-20260918.json`

## One-sentence result

R9 closes the last unexplained page-visible geometry residual in the current neutral Browser Security detector set. The production carrier-11 Chromium profile stores `browser.window_placement` bounds of exactly 1288x851, matching the frozen production outer-window observation. A fresh canary-91 Browserless service given a synthetic profile containing only those allowlisted placement fields reproduced outer 1288x851 exactly in two byte-identical runs while preserving the Browserless 800x600 inner viewport and page=2 target topology. This attributes the measured outer-window geometry to Chromium profile-restored window state in this setup; it does not establish why that state was historically created or whether a protected provider uses it.

## Privacy and authority boundary

R9 does **not** copy the production profile.

It projects only:

```text
browser.window_placement.left
browser.window_placement.top
browser.window_placement.right
browser.window_placement.bottom
browser.window_placement.maximized
browser.window_placement.work_area_left
browser.window_placement.work_area_top
browser.window_placement.work_area_right
browser.window_placement.work_area_bottom
```

No cookie values, history contents, tokens, account data, prompt text, provider page content, or session material are projected.

The synthetic canary Preferences document contains only:

```json
{
  "browser": {
    "window_placement": {
      "...": "allowlisted geometry only"
    }
  }
}
```

R9 does not connect to the production browser and does not visit a protected provider.

## Production projection

The current production profile projects:

```text
left              0
top               0
right          1288
bottom          851
maximized      false

work area:
  left             0
  top              0
  right         1440
  bottom        1000
```

Therefore:

```text
projected outer = 1288x851
```

This is exactly the outer geometry frozen in the R8 production reference.

## Synthetic causal check

R8 fresh Browserless baseline:

```text
outer          1050x980
inner           800x600
targets         page=2
```

R9 synthetic-placement fresh Browserless:

```text
outer          1288x851
inner           800x600
targets         page=2
```

Frozen production reference:

```text
outer          1288x851
inner           800x600
targets         page=2
```

Thus:

```text
synthetic window placement
        |
        +--> outer window 1050x980 -> 1288x851
        |
        +--> inner viewport unchanged at 800x600
        |
        +--> target topology unchanged at page=2
```

The synthetic input is therefore sufficient to reproduce the exact measured production outer-window residual without production credentials/session state.

## Repeatability

Run1 and run2 are byte-identical.

```text
raw run SHA-256
sha256:1f4dc26e898b05fa432534d0d143b5dae1765e4b12604009189689b749e3f2b7

whole canonical JSON
sha256:7110ca4e4554bb43f7f2f60476e88b99bbb1f70690dacdf16bf3635bb8e7f3c4

mechanism canonical JSON
sha256:eddcafb45f16a6cccf3cc7d6d65eba377f9918091dc18766aa4e94d0717d2fba
```

Each run fully removed canary-91 container, profile, X socket, and Xauthority. Production topology remained carrier-11 active with carriers 12 and 13 sleeping.

## R1-R9 localization chain

The measured neutral Browserless differences now decompose as:

```text
CF02 transport
  current normalized detectors stable
  observer outages separated by Observation Validity

CF03 HTTP presentation
  measured main-document header order stable

CF04 browser presentation
  --enable-automation -> navigator.webdriver=true mechanism supported
  provider relevance unknown

CF05 browser/control
  browser_ui + service_worker target classes
      -> managed launcher defaults (R7)

  extra page target
      -> fresh Browserless service/control lifecycle (R8)

  page-visible consequence of target topology
      -> not established

CF06 cross-layer/runtime
  fonts + canvas metrics
      -> host/container runtime boundary (R5)

  browser-level GPU summary
      -> host/container runtime boundary (R5)
      -> page WebGL remained unavailable/non-discriminating

  part of geometry
      -> managed launcher defaults (R7)

  inner 800x600 viewport
      -> fresh Browserless service/control lifecycle (R8)

  production outer 1288x851
      -> profile-restored browser.window_placement (R9)

CF07 session/lifecycle
  metadata characterized (R4)
  prospective content-minimal telemetry active (R6)

CF08 provider outcome
  CHALLENGE_GATED
  cause UNKNOWN
```

For the current detector set, the previously unexplained neutral presentation differences are now mechanistically localized enough that further decomposition has low information value unless a new detector, new drift, or new independent causal design appears.

## What R9 does not establish

R9 does **not** establish that:

- `browser.window_placement` causes a Cloudflare or ChatGPT challenge;
- changing or deleting window placement would alter provider admission;
- the provider observes outer-window dimensions;
- the historical origin of the 1288x851 placement is known;
- `navigator.webdriver`, target topology, fonts, GPU, geometry, or any other neutral signal is provider-authoritative challenge evidence;
- a protected challenge can or should be bypassed.

The provider-authoritative root cause remains unknown.

## Current research decision

For the measured neutral detector set:

```text
mechanism localization  -> substantially closed
provider causality      -> open
protected-provider probing solely for experimentation -> not warranted
```

Future CF07 telemetry should accumulate only through operationally necessary preflights. The neutral attribution branch should reopen only when there is a new unexplained drift, a materially new detector, or an independent causal design that does not use a protected challenge as its detector oracle.
