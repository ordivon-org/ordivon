# Cloudflare / Provider Security Experiment R3

Date: 2026-09-18
Standing: **R3 NEUTRAL DIFFERENTIAL COMPLETE / ROOT CAUSE OPEN**

Primary evidence:

- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r3-20260918.json`
- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r3-run2-20260918.json`
- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r3-repeatability-20260918.json`
- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r3-geometry-ablation-20260918.json`

## One-sentence result

With the same Chromium 153.0.8010.12 bytes, the same Network-v2 namespace, and `navigator.webdriver=true` intentionally matched, the remaining repeatable direct-vs-Browserless differences are concentrated in **launch/control metadata, browser-level GPU/target topology, font/canvas presentation, and window geometry**; WebGL was unavailable in both arms, and no protected provider was visited, so provider causality remains open.

## Controls

Both arms used:

```text
Chromium digest:
sha256:8c599d43aec53f2460a31ae2f4af6bd863f8258b34ff519564bc5d4726bfaa1e

Network namespace:
nv2-browserless-prod

browser version:
153.0.8010.12

navigator.webdriver:
true in both arms by design
```

The direct arm deliberately included `--enable-automation` so R3 would not simply rediscover the R1 webdriver differential.

The neutral page was a `data:text/html` document. R3 did not visit ChatGPT or another protected provider, did not interact with a challenge, did not read cookie values, and did not cross SEND.

## Repeatability

Two independent R3 runs produced byte-identical selected evidence:

```text
run1 sha256 = 82995409641d45efe53a2014425bd1df398db69d1310c1104bee0985d86bd007
run2 sha256 = 82995409641d45efe53a2014425bd1df398db69d1310c1104bee0985d86bd007
```

Therefore the observed differential is not a one-shot artifact in this two-run sample.

## CF05 — control-layer findings

Page-visible R2 probes remain non-discriminating:

- console/Error stack side effect: not observed;
- execution-context shape: same.

R3 added browser-level CDP observations. The following differences were stable:

```text
Browser.getBrowserCommandLine
SystemInfo.getInfo.gpuDevices
Target.getTargets type counts
```

The direct arm exposed `browser_ui`, `page`, and `service_worker` target types, while the Browserless arm exposed only page targets in this measurement. Browserless also carries a much larger Puppeteer/Browserless launch-default surface.

These are **control/browser-level differences**, not proof of a page-visible detector. CDP domain enablement in another session is not directly queryable through the observer session, so the broader CF05 hypothesis remains only partially covered.

## CF06 — font and canvas presentation

System font resolution differs materially between host and Browserless container for every probed family. Examples:

```text
Arial:
  host       -> Arial
  Browserless-> Liberation Sans

Segoe UI:
  host       -> Segoe UI
  Browserless-> Selawik

Noto Sans:
  host       -> Verdana
  Browserless-> Ubuntu
```

Canvas text metrics independently differed for:

```text
DejaVu Sans
Ubuntu
Selawik
Verdana
```

This makes the font differential repeatable at both system-resolution and page-rendering layers.

`document.fonts.check()` returned true for all probed names in both arms and is therefore not discriminating in this environment.

## CF06 — GPU / WebGL

Browser-level `SystemInfo.getInfo` reported a stable GPU-summary differential:

- direct host Chromium: vendor/device numeric identities with empty vendor/device strings;
- Browserless container: Mesa llvmpipe / Google Inc. (Mesa) strings.

However page WebGL context creation returned unavailable in **both** arms, so R3 does not establish a page-visible GPU differential. Browser-level GPU metadata must not be promoted into a page-visible claim.

## CF06 — geometry correction

R3 confirms a stable window geometry difference, but also corrects R2's attribution.

Measured geometry:

```text
direct + --window-size=1440,1000:
  outer = 1439x999
  inner = 1439x856

direct without --window-size:
  outer = 1050x980
  inner = 1050x837

Browserless current:
  outer = 1288x851
  inner = 800x600
```

Removing `--window-size` materially changes direct Chromium geometry but still does not reproduce Browserless. Therefore:

```text
"geometry is purely a container effect"       -> unsupported
"geometry is solely --window-size"             -> falsified
"geometry is mixed launch/window-management"   -> supported by current neutral evidence
```

## Updated fault tree

```text
CHALLENGE_GATED
│
├── CF02 transport
│   └── measured stable / observer outages now separated by validity gate
│
├── CF03 request presentation
│   └── measured header order stable
│
├── CF04 launch/browser presentation
│   └── --enable-automation -> webdriver=true mechanism supported
│
├── CF05 control plane
│   ├── page console/Error probe       non-discriminating
│   ├── execution-context shape        same
│   ├── command-line topology          different / repeatable
│   ├── browser-level target topology  different / repeatable
│   └── provider relevance             unknown
│
├── CF06 consistency/runtime
│   ├── font resolution + canvas       different / repeatable
│   ├── geometry                       different / mixed attribution
│   ├── browser-level GPU summary      different / repeatable
│   ├── page WebGL                     unavailable both / non-discriminating
│   └── KR egress vs Shanghai TZ       shared across routes
│
├── CF07 session/profile
│   └── three persistent profiles all gated
│
└── CF08 challenge cause
    └── UNKNOWN
```

## What R3 does not establish

R3 does **not** show that changing fonts, geometry, GPU presentation, target topology, or launch flags would make a protected provider admit the browser. It does not use challenge outcome as an oracle and makes no bypass claim.

The next useful work is to improve neutral attribution: distinguish launcher defaults from container runtime effects and add non-secret CF07 session-age/cadence observability.
