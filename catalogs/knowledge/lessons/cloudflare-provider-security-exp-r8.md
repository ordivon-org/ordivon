# Cloudflare / Provider Security Experiment R8

Date: 2026-09-18
Standing: **R8 FRESH SERVICE ATTRIBUTION COMPLETE / ROOT CAUSE OPEN**

Primary evidence:

- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r8-fresh-service-run1-20260918.json`
- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r8-fresh-service-run2-20260918.json`
- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r8-repeatability-20260918.json`

## One-sentence result

R8 replaces the production Browserless arm with an isolated fresh Browserless service using the current immutable image, an empty canary-91 profile, the same Network-v2 namespace, and the same production presentation environment. Across two byte-identical runs, a fresh Browserless service already contains one page before measurement, exposes two page targets while the neutral observation page is open, and uses an 800x600 inner viewport. Those features therefore do not require the production persistent profile. Fresh and frozen production Browserless are otherwise identical at the measured browser level; their only page-visible residual is outer-window geometry.

## Design

R8 does not connect to the production Browserless browser. It uses the repeatability-qualified R7 production observation as a frozen reference.

```text
R7 launcher-matched container-direct
        |
        | same image / Chromium / Network-v2
        v
fresh Browserless canary-91
        |
        | empty profile
        | fresh service lifecycle
        | neutral page only
        v
R7 frozen production Browserless reference
```

The fresh service reuses the production canary-91 lifecycle authority for image, Network-v2, display authentication, profile isolation, health checks, and cleanup. The R8 process must execute inside `/run/netns/nv2-browserless-prod`; a fail-fast namespace identity check prevents accidental connection to the wrong loopback namespace.

R8 never visits ChatGPT or another protected provider, never interacts with a challenge, never reads cookie values, never connects to the production browser, and never crosses SEND.

## Repeatability

Authoritative run1 and run2 are byte-identical.

```text
raw run SHA-256
sha256:d6c59d1efb230c445caea36ac4501ee3a579a0e05f670523714181c650198b9b

whole canonical JSON
sha256:e990fa78d9456552b7aa892f0fcbc02c665f43208d58a99a069e5248b22c5b33

comparisons canonical JSON
sha256:702573c9ee9839074efbfcd93ed8898421aee92afc3a05eef40721e044083ed9
```

Each run ended with:

```text
canary-91 container  absent
canary-91 profile    absent
X191 socket          absent
Xauthority           absent

production:
  carrier-11 active
  carrier-12 sleeping
  carrier-13 sleeping
```

## Launcher-matched direct -> fresh Browserless

R7 launcher-matched direct:

```text
target topology:
  page = 1

geometry:
  outer = 1050x980
  inner = 1050x893
```

Fresh Browserless:

```text
pre-existing pages before neutral collection = 1

target topology while neutral observation page is open:
  page = 2

geometry:
  outer = 1050x980
  inner = 800x600
```

Managed launcher flags are equal.

Therefore, in this measured setup:

- the extra page target is present in a fresh Browserless service and does not require the production persistent profile;
- the 800x600 inner viewport appears at the Browserless service/control boundary;
- the outer 1050x980 window remains the same as launcher-matched direct Chromium.

This is neutral local attribution, not evidence of provider relevance.

## Fresh Browserless -> frozen production Browserless

Fresh Browserless and the repeatability-qualified R7 production reference have:

```text
normalized browser-level observation  SAME
managed launcher flags                SAME
target topology                       page=2 / page=2
inner viewport                        800x600 / 800x600
```

The only measured page-visible residual is:

```text
fresh outer window       1050x980
production outer window  1288x851
```

Thus the remaining production-specific residual is outer-window geometry. R8 does not determine whether that comes from display lifecycle, window-manager behavior, persistent window state, or another production-only control.

## Updated localization

```text
R3 broad Browserless residual
        |
        +-- fonts / canvas / browser GPU
        |      -> host-to-container boundary (R5)
        |
        +-- browser_ui / service_worker target classes
        |      -> Browserless managed launcher defaults (R7)
        |
        +-- extra page target
        |      -> fresh Browserless service/control lifecycle (R8)
        |
        +-- inner viewport 800x600
        |      -> fresh Browserless service/control lifecycle (R8)
        |
        +-- production outer window 1288x851
               -> still open
```

## Evidence boundary

The extra page target is a browser-level CDP observation. R8 does not promote it into a page-visible provider-detection claim.

The page-visible residual after R8 is only the outer-window dimensions. Even that is not evidence that a protected provider observes or uses the value.

## What R8 does not establish

R8 does **not** establish that:

- any measured difference causes a Cloudflare or ChatGPT challenge;
- the extra page target is visible to page JavaScript;
- an 800x600 inner viewport is used by a provider;
- changing window geometry would alter provider admission;
- production outer-window geometry is caused by the persistent profile;
- a protected challenge can or should be bypassed.

The provider-authoritative cause remains unknown.

## Next smallest neutral experiment

The remaining measurable production-specific branch is narrow:

```text
outer window:
  fresh service = 1050x980
  production    = 1288x851
```

The next neutral experiment should isolate display/window-management lifecycle variables around the fresh canary without protected-provider access. It should stop if the outer-window residual is explained; browser-level target topology should remain outside provider-detection claims unless an independent page-visible mechanism is demonstrated.
