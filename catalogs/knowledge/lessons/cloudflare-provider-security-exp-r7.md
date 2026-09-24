# Cloudflare / Provider Security Experiment R7

Date: 2026-09-18
Standing: **R7 LAUNCHER DEFAULT ATTRIBUTION COMPLETE / ROOT CAUSE OPEN**

Primary evidence:

- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r7-controlled-run1-20260918.json`
- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r7-controlled-run2-20260918.json`
- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r7-repeatability-20260918.json`

## One-sentence result

R7 reproduces the Browserless/Puppeteer managed launch-default surface inside an otherwise direct Chromium container. Those launcher defaults explain the disappearance of the `browser_ui` and `service_worker` target classes and move window geometry substantially, but they do **not** reproduce production Browserless completely: with the managed launch flags matched, Browserless still has one additional page target and different inner/outer geometry. The neutral page-visible residual is geometry only. No protected provider was visited, so provider causality remains open.

## Three-arm neutral ablation

```text
container-direct baseline
        |
        | same image / Chromium / Network-v2 / TZ / LANG
        | replace direct flags with frozen Browserless-managed flags
        v
container-direct launcher-matched
        |
        | managed launcher flags equal to production
        v
production Browserless
```

The frozen launcher surface was derived from R5's authoritative `Browser.getBrowserCommandLine` observation after removing executable identity, dynamic profile/debug-port values, Chrome auto-added X11 flag-switch markers, and `about:blank`.

The experiment uses only a neutral `data:text/html` page. It does not visit ChatGPT or another protected provider, interact with a challenge, read cookie values, or cross SEND.

## Repeatability

Controlled run1 and run2 are byte-identical.

```text
raw run SHA-256
sha256:5b4dc770db2bc7c714619889d4d7af72ecb12bb415e3214b582c77086a5b0bd4

whole canonical JSON
sha256:b89bc18af1ea3faffea7588f8adeabad09211fe0d9bed4990bd3d6b8cc1d72b5

pairwise canonical JSON
sha256:6636efce540db243eb02703d06ef894d025d5e83efaaa5fd2e518360260a240c
```

Production topology after validation remained:

```text
carrier-11 active
carrier-12 sleeping
carrier-13 sleeping
```

No R7 temporary container or reserved listener remained.

## Baseline -> launcher-matched

Baseline container-direct:

```text
targets:
  browser_ui      2
  page            1
  service_worker  2

geometry:
  outer 1439x999
  inner 1439x856
```

Launcher-matched container-direct:

```text
targets:
  page            1

geometry:
  outer 1050x980
  inner 1050x893
```

Therefore, in this neutral environment, the managed launch-default bundle is sufficient to explain the disappearance of the measured `browser_ui` and `service_worker` target classes. It also has a substantial effect on window geometry.

This is local attribution only; it is not evidence that any provider observes or uses these browser-level signals.

## Launcher-matched -> production Browserless

The managed launcher flag set is equal by construction and verified from the live Browserless command line.

Residual:

```text
target topology:
  launcher-matched direct  page=1
  production Browserless   page=2

geometry:
  launcher-matched direct  outer 1050x980 / inner 1050x893
  production Browserless   outer 1288x851 / inner 800x600
```

The neutral page observation reports no residual JS/presentation change except the inner/outer geometry paths.

This splits the former R5 residual into:

```text
launcher-default-associated
  - browser_ui target disappearance
  - service_worker target disappearance
  - part of window geometry

service/control/profile-state residual
  - additional page target
  - remaining window geometry
```

The second label is intentionally broad. R7 does not yet distinguish Browserless service lifecycle from persistent-profile/open-page state or window/viewport management.

## Page-visible boundary

Browser-level observations:

```text
command line
target topology
```

are not promoted into page-visible claims merely because CDP can inspect them.

The neutral page-visible R7 residual is:

```text
window.innerWidth / innerHeight
window.outerWidth / outerHeight
```

No claim is made that a protected provider uses those values.

## What R7 does not establish

R7 does **not** establish that:

- any measured signal causes a Cloudflare or ChatGPT challenge;
- target topology is page-visible;
- the extra Browserless page target is created by Browserless service code rather than persistent state;
- matching geometry would alter provider admission;
- changing launcher flags should be used to evade anti-automation controls;
- a protected challenge can or should be bypassed.

The provider-authoritative cause remains unknown.

## Next smallest neutral experiment

Use an **isolated fresh Browserless service** with the current immutable image, fresh empty profile, same Network-v2/TZ/LANG, and only a neutral page. Compare it against launcher-matched container-direct and production Browserless.

That next experiment can separate:

```text
Browserless service/control lifecycle
vs
production persistent-profile/open-page state
```

for the remaining page-target and geometry residual without increasing protected-provider access.
