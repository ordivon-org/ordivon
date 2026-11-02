# Cloudflare / Provider Security Experiment R1

Date: 2026-09-17
Standing: **BASELINE COMPLETE / ABLATIONS COMPLETE / ROOT CAUSE OPEN**
Evidence: `evidence/browser-security/cloudflare-provider-security-exp-r1-20260917.json`

## Result in one sentence

With the **same Chromium 153.0.8010.12 binary and the same Network v2 namespace**, the current Browserless/Puppeteer route exposed `navigator.webdriver=true` while direct Chromium exposed `false`; the difference was reproduced by adding `--enable-automation`, whereas changing early-vs-late CDP attachment alone did not change `navigator.webdriver`. Stable transport fingerprints (JA4, PeetPrint, HTTP/2) were identical across Browserless and direct arms.

## 1. Production baseline

A read-only production provider preflight on `chatgpt-carrier-11` returned:

```text
Browserless substrate: HEALTHY
ChatGPT provider standing: CHALLENGE_GATED
providerEffectAttempted: false
clicked: false
composerFilled: false
sendAttempted: false
```

This is direct evidence for the model law:

```text
browser substrate healthy
!=
provider security-boundary admissible
```

No challenge was clicked or solved and no SEND boundary was crossed.

## 2. Exact browser identity control

The host Playwright cache and Browserless container both contain Chromium 1243 / Chrome for Testing `153.0.8010.12`.

Both browser executables have the exact same SHA-256:

```text
8c599d43aec53f2460a31ae2f4af6bd863f8258b34ff519564bc5d4726bfaa1e
```

This allowed the first meaningful same-browser-build A/B.

## 3. CF04 / CF05 ablation

All arms used the same Network v2 namespace and neutral target `https://example.com/`.

| Arm | Launch / control topology | `navigator.webdriver` |
|---|---|---:|
| Browserless current | Browserless `/chromium` -> Puppeteer launch -> Playwright CDP | `true` |
| Direct late attach | direct Chromium -> navigate -> Playwright CDP attach | `false` |
| Direct late attach + `--enable-automation` | direct Chromium + flag -> navigate -> late attach | `true` |
| Direct early attach, no flag | direct Chromium -> attach -> navigate | `false` |

The live Browserless process command line included `--enable-automation` plus the expected Puppeteer/Browserless launch surface.

### Interpretation

For the specific page-visible observable `navigator.webdriver`:

```text
--enable-automation contribution                 SUPPORTED
CDP attachment timing contribution               FALSIFIED_IN_THIS_MECHANISM
Browserless-specific broader control side effects UNRESOLVED
```

This is narrower and stronger than saying “Browserless is detected”. It identifies one concrete observable mechanism while preserving the open hypotheses around Runtime/Console domains, execution-context lifecycle, Browserless listeners and other control-layer effects.

## 4. CF02 transport A/B

The same Browserless and direct browser paths were measured against the neutral diagnostic endpoint `https://tls.peet.ws/api/all`.

Stable values were identical:

```text
JA4       t13d1518h2_8daaf6152771_4980c97edce0
PeetPrint 493a80d6a4267c7820685d29d92aa946
HTTP/2    52d84b11737d980aef856699f885ca86
HTTP      h2
UA        Chrome/153 on Linux x86_64
```

Three fresh connections per arm produced six different JA3 hashes. Therefore:

```text
one-shot JA3(Browserless) != JA3(direct)
```

is **not** evidence of a stable Browserless transport difference in this environment.

Current CF02 standing:

```text
JA4 difference        FALSIFIED_IN_THIS_SAMPLE
HTTP/2 difference     FALSIFIED_IN_THIS_SAMPLE
PeetPrint difference  FALSIFIED_IN_THIS_SAMPLE
JA3 difference        UNRESOLVED / within-arm variability
```

## 5. What this actually narrows

Before R1:

```text
Browserless -> Challenge
```

was one opaque observation.

After R1:

```text
CF02 transport
  stable normalized witnesses: SAME

CF04 browser JS
  navigator.webdriver: DIFFERENT
  sufficient mechanism: --enable-automation

CF05 control layer
  attachment timing -> webdriver: NOT CAUSAL IN THIS TEST
  other protocol/execution-context surfaces: OPEN

CF08 provider challenge
  PRESENT in production
  causal link to CF04/CF05: NOT ESTABLISHED
```

This is the intended repair workflow: eliminate entire branches instead of tweaking the whole browser stack.

## 6. Explicit non-claims

R1 does **not** establish that:

- Cloudflare challenged ChatGPT because of `navigator.webdriver`;
- removing `--enable-automation` would make ChatGPT admissible;
- Browserless-specific CDP listeners are irrelevant;
- JA3 is irrelevant generally;
- a challenge can or should be bypassed automatically.

The provider-authoritative challenge cause remains unknown.

## 7. Next smallest experiments

The next useful experiments are now much smaller:

1. **CF05 protocol/execution-context witness** — same Chromium/network/page; Browserless control layer vs direct CDP, measuring only the side-channel families already identified by Patchright/Rebrowser research.
2. **CF03 request presentation** — exact browser-generated header set/order differential under the same Chromium/network.
3. **CF06 consistency graph** — geometry, locale/timezone, UA/UA-CH, GPU/WebGL and network coherence.
4. Only then repeat the existing read-only production preflight and treat the challenge as an outcome variable, not as a detector oracle.
