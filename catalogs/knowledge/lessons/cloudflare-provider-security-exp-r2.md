# Cloudflare / Provider Security Experiment R2

Date: 2026-09-18
Standing: **R2 COMPLETE / ROOT CAUSE OPEN**
Evidence: `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r2-20260918.json`

## One-sentence result

R2 eliminated several attractive but unsupported explanations: current Browserless and direct controls have the same observed request-header order and the same execution-context shape, while the real remaining presentation differences are primarily launch presentation from R1 plus R2's **container-specific font/window environment** and a **shared KR-network vs Asia/Shanghai-timezone mismatch**; all three persistent carriers are independently `CHALLENGE_GATED`.

## CF03 — request presentation

A local neutral HTTP server recorded the complete main-document header sequence from three arms:

- direct Chromium, page loaded before Playwright attach;
- direct Chromium, Playwright attached before page load;
- current Browserless/Puppeteer + Playwright path.

All three produced the same header set and order. Combined with R1's identical JA4, HTTP/2 fingerprint and PeetPrint, there is currently no stable evidence that the Browserless route changes the measured HTTP/TLS presentation families.

This does **not** prove that every network observable is identical. It closes only the detector families actually measured.

## CF05 — control-layer observability

### Console / Error side-effect probe

A neutral page instrumented `Error.stack` getter reads around `console.log`, `console.dir`, and `console.debug`.

All three arms produced zero reads. No obvious Playwright/Puppeteer-named page globals were found.

Therefore this detector is classified:

```text
NON_DISCRIMINATING_CURRENT_BUILD
```

It must not be used as evidence merely because older/public discussions associate it with CDP observability.

### Execution-context/world probe

For a page with one child iframe, a fresh observer session enabled Runtime and enumerated existing execution contexts.

Both direct Playwright and Browserless + Playwright produced exactly four contexts:

```text
main default
main Playwright utility world
iframe default
iframe Playwright utility world
```

The utility-world suffix changed between runs, as expected for invocation identity. No additional Puppeteer/Browserless isolated world remained visible in this measurement.

Current standing:

```text
Browserless extra execution world: NOT OBSERVED
broader CDP domain-state difference: OPEN
```

The Browserless source-level fact that it enables/observes CDP domains remains useful provenance, but source provenance is not equivalent to page-visible detection evidence.

## CF06 — cross-layer consistency

### Shared presentation

With the same Chromium build and Network-v2 namespace, direct and Browserless arms agreed on:

```text
Chrome 153.0.8010.12
Linux x86_64
en-US / [en-US]
Asia/Shanghai (-480)
16 hardware threads
8 GiB deviceMemory
0 touch points
1440x1000 screen
DPR 1
webdriver=true  [both arms intentionally matched for this experiment]
```

### Shared network/timezone mismatch

Cloudflare trace for the current Network-v2 namespace reported:

```text
country = KR
colo    = ICN
HTTP    = h2
TLS     = TLS 1.3
```

while the browser reports:

```text
timezone = Asia/Shanghai
language = en-US
```

This is a concrete cross-layer mismatch. It belongs in CF06, but it is shared by direct and Browserless arms and therefore cannot explain the Browserless-vs-direct difference by itself.

No claim is made that this mismatch causes the protected provider challenge.

### Browserless-specific presentation differences

Two route-specific differences remained:

1. **Window geometry** differed despite the same Xvfb screen.
2. **Font presentation** differed materially because direct Chromium sees host/Windows-mounted fonts while the Browserless container sees its Linux image font set.

System `fc-match` verified examples:

```text
host DejaVu Sans -> Verdana (Windows font mount)
container DejaVu Sans -> DejaVu Sans

host Arial -> Arial
container Arial -> Liberation Sans

host Segoe UI -> Segoe UI
container Segoe UI -> Selawik

host Noto Sans -> Verdana fallback
container Noto Sans -> Ubuntu fallback
```

Canvas text metrics independently reflected this difference. Therefore the font difference is not merely a JavaScript measurement artifact.

This is a genuine consequence of changing from host-launched Chromium to a containerized Browserless browser even when the Chromium executable bytes are identical.

## CF07 — session/profile hypothesis

Read-only preflight was run independently on all three current persistent carriers:

```text
carrier-11: substrate healthy + CHALLENGE_GATED
carrier-12: substrate healthy + CHALLENGE_GATED
carrier-13: substrate healthy + CHALLENGE_GATED
```

The profiles are distinct and have different cookie metadata counts; no cookie values were read or recorded.

This weakens:

```text
"one corrupt/bad persistent profile explains the incident"
```

but does not distinguish among shared network, shared launch presentation, shared provider policy, or correlated session histories.

## Updated fault tree

```text
CHALLENGE_GATED on 11/12/13
│
├── CF02 transport
│   ├── JA4                same
│   ├── HTTP/2 fingerprint same
│   ├── PeetPrint          same
│   └── JA3                noisy / non-attributable one-shot
│
├── CF03 HTTP request presentation
│   └── measured header set/order same
│
├── CF04 browser presentation
│   └── --enable-automation -> webdriver=true   SUPPORTED in R1
│
├── CF05 control plane
│   ├── console/Error probe             no discrimination
│   ├── execution-context shape         same
│   └── other protocol-domain state     OPEN
│
├── CF06 cross-layer consistency
│   ├── KR egress vs Asia/Shanghai TZ   OBSERVED / shared
│   ├── font environment                DIFFERENT / Browserless-specific
│   └── window geometry                 DIFFERENT / Browserless-specific
│
├── CF07 session/profile
│   └── 3 independent profiles all gated
│
└── CF08 challenge cause
    └── UNKNOWN
```

## What should become permanent infrastructure

The useful artifact is no longer another one-off browser script. Security should own a repeatable witness suite that records:

- exact Chromium digest;
- effective launch-argument digest;
- network-authority digest and coarse egress geography;
- JA4 / HTTP2 / request-presentation witness;
- browser JS presentation witness;
- execution-context/world witness;
- cross-layer consistency witness;
- profile/session metadata without credential contents;
- detector coverage and detector-version identity;
- last-known-good / first-known-bad comparison.

This gives future repair work a regression surface independent of a protected provider challenge.
