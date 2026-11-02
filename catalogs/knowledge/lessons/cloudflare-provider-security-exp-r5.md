# Cloudflare / Provider Security Experiment R5

Date: 2026-09-18
Standing: **R5 THREE-ARM NEUTRAL ATTRIBUTION COMPLETE / ROOT CAUSE OPEN**

Primary evidence:

- evidence/browser-security/cloudflare-provider-security-exp-r5-controlled-run1-20260918.json
- evidence/browser-security/cloudflare-provider-security-exp-r5-controlled-run2-20260918.json
- evidence/browser-security/cloudflare-provider-security-exp-r5-repeatability-20260918.json

## One-sentence result

R5 inserted a **container-direct Chromium** control between host-direct Chromium and production Browserless while holding Chromium bytes, Network-v2, webdriver intent, direct launch flags, TZ/LANG, and the neutral page constant. The resulting attribution is repeatable: **font/canvas and browser-level GPU differences arise on the host-to-container boundary**, while the residual container-direct-to-Browserless differences are **Browserless launch command-line, browser target topology, and window geometry**. No protected provider was visited, so provider causality remains open.

## Three-arm design

    host-direct Chromium
            |
            | same Chromium bytes
            | same Network-v2
            | matched direct launch args
            v
    container-direct Chromium
            |
            | same Browserless image/runtime
            | same container fonts/GPU stack
            | matched TZ/LANG
            v
    production Browserless

All three arms used Chromium:

    sha256:8c599d43aec53f2460a31ae2f4af6bd863f8258b34ff519564bc5d4726bfaa1e

Container-direct and Browserless used the current immutable Browserless image:

    ghcr.io/browserless/chromium@sha256:b1ba7b054af2891a8199f884d4bd249cf8c3bd2fa8a97b339077e40f92803ba8

The two direct arms used identical direct launch arguments apart from normalized debug-port/profile identity. Both intentionally used --enable-automation so R5 did not simply rediscover the R1 webdriver differential. Container-direct inherited only the non-secret production presentation variables TZ=Asia/Shanghai and LANG=C.UTF-8; it did not inherit TOKEN or other credentials.

The experiment visited only data:text/html, did not visit ChatGPT or another protected provider, did not interact with a challenge, did not read cookie values, and did not cross SEND.

## Repeatability

Controlled run1 and controlled run2 are byte-identical.

    raw evidence file bytes (each run):
    sha256:664034c1c524154e9e877d767932e5b00e34722cd4678c0b949ae0d28924af60

    canonical whole-evidence JSON:
    sha256:5ee012acbab0aea05a66d3d2a3601785038dbdd0a3920146c993a0a8ab1f9f5f

    selected evidence:
    sha256:ef01a38f692a8649fc085932a084df26d19f27e1b5119fe1731cbbaa915a2601

    pairwise differential:
    sha256:40fccba3dd7411f01fc59ba2de15a4fc5cb1b1b099a26081edbfea13fdc84d8f

The production topology after the repeatability check remained:

    carrier-11 active
    carrier-12 sleeping
    carrier-13 sleeping

The R5 temporary container and X11 resources were absent after the runs.

## Host-direct -> container-direct

Stable differences:

    browser:
      SystemInfo GPU devices

    page:
      canvas text widths:
        DejaVu Sans
        Ubuntu
        Selawik
        Verdana

    system font resolution:
      Arial
      Segoe UI
      Noto Sans
      DejaVu Sans
      Liberation Sans
      Ubuntu
      Selawik
      Verdana

No Browserless control layer is present in either arm. Therefore the R3 font/canvas differential and browser-level GPU differential are now localized to the **container/runtime boundary** in this environment, rather than to Browserless control itself.

This is neutral attribution, not provider relevance.

## Container-direct -> Browserless

Stable differences:

    browser:
      Browser.getBrowserCommandLine / SystemInfo command line
      Target.getTargets:
        browser_ui
        page
        service_worker

    page:
      window inner geometry
      window outer geometry

Stable non-differences:

    browser-level GPU summary   SAME
    font resolution             SAME
    canvas text metrics         SAME
    timezone / offset           SAME

This removes the largest R3 confounder. With the same container image/runtime, the residual Browserless-path differential is concentrated in **launch/control topology and window management**.

It still does not establish that any of these signals are visible to, or used by, the protected provider.

## Control corrections discovered during R5

The pilot R5 run exposed two experiment-control mistakes and was intentionally not retained as authoritative evidence:

1. the image default timezone was America/Los_Angeles, while production Browserless uses Asia/Shanghai;
2. raw Chromium executable paths differed even though the exact executable bytes were identical.

R5 therefore:

- explicitly matches production TZ and LANG for container-direct;
- does not copy credential-bearing environment variables;
- canonicalizes the executable path to <chromium-executable>;
- treats TCP TIME_WAIT as non-listening state by using SO_REUSEADDR in the reserved-port probe.

The two controlled runs after these corrections are the authoritative R5 evidence.

## Updated fault localization

    CHALLENGE_GATED
    |
    +-- CF02 transport
    |   measured stable for current detectors
    |
    +-- CF03 request presentation
    |   measured header order stable
    |
    +-- CF04 browser presentation
    |   --enable-automation -> webdriver=true mechanism supported
    |
    +-- CF05 control path
    |   page console/Error probe                 non-discriminating
    |   execution-context shape                  same
    |   container-direct -> Browserless command  different / repeatable
    |   container-direct -> Browserless targets  different / repeatable
    |   provider relevance                       unknown
    |
    +-- CF06 runtime consistency
    |   fonts/canvas          host -> container effect / repeatable
    |   browser GPU summary   host -> container effect / repeatable
    |   timezone              matched after control correction
    |   geometry              container-direct -> Browserless / repeatable
    |   page WebGL            unavailable both / non-discriminating
    |   provider relevance    unknown
    |
    +-- CF07 lifecycle/session metadata
    |   characterized in R4; causality open
    |
    +-- CF08 challenge cause
        UNKNOWN

## What R5 changes

R5 narrows future work. It is no longer useful to treat all of the R3 font/GPU/geometry/control differences as one Browserless bundle.

The neutral residual worth further attribution is now:

    Browserless launch command-line surface
    Browserless target topology
    Browserless window-management geometry

Fonts/canvas and browser-level GPU should be treated as container/runtime-associated in the current environment unless new evidence contradicts this result.

## What R5 does not establish

R5 does **not** establish that:

- Cloudflare or ChatGPT uses any measured signal;
- Browserless launch flags cause the provider challenge;
- target topology is page-visible to the provider;
- changing window geometry would change provider admission;
- container fonts/GPU are irrelevant to provider policy in general;
- the challenge can or should be bypassed.

The provider-authoritative cause remains unknown.

## Next smallest neutral experiments

1. Separate **Browserless launcher defaults** from **Browserless service/control lifecycle** using matched container-direct launch ablations, without visiting the protected provider.
2. Determine which residual command-line/target/geometry differences have a page-visible consequence; browser-level-only differences should not be promoted into provider-detection claims.
3. Continue R4's prospective non-secret CF07 telemetry so future cadence/history claims rely on durable evidence rather than retrospective file ages.
4. Use provider preflight only as a read-only outcome anchor after neutral attribution changes; never use the protected challenge as the detector oracle.
