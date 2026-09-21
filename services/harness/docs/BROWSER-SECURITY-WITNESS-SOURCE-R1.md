# Browser Security Witness Source R1

Status: **neutral/read-only Harness observation adapter**

## Purpose

Harness owns browser/provider observation. Security-v2 owns canonicalization, sensitive-field rejection, observation digests, bundle validation, and drift comparison.

This adapter emits the source-manifest shape accepted by Security-v2; it does not import Security-v2 and does not make Security an execution authority.

```text
Harness / Network observation authority
        -> Browser Security source manifest
Security-v2 canonicalization authority
        -> canonical witness bundle
Security-v2 comparison
        -> infrastructure / detector / subject drift
```

## Non-provider experiment boundary

The default collector does **not** visit ChatGPT or another protected provider, does not interact with a challenge, and does not cross SEND. Its `challengeStanding` is always `null`.

Targets used by the current collector are:

- an ephemeral loopback HTTP server for request-header order;
- `tls.peet.ws` for normalized browser TLS/HTTP2 presentation;
- Cloudflare's public trace endpoint for coarse network geography;
- the current Browserless browser itself for page-visible presentation and execution-context shape.

A provider preflight can be recorded separately as an outcome observation, but it is not an input detector oracle.

## Authority split

One Browserless carrier lease spans the whole collection.

Host-side facts are collected before the browser-network child starts:

- Browserless container image identity;
- exact Chromium executable SHA-256;
- container font resolution;
- non-secret persistent-profile cookie row and distinct-host counts.

The Playwright/network child is then executed inside the endpoint's configured Network-v2 namespace and observes:

- browser TLS/HTTP2 fields;
- neutral main-document request-header order;
- browser JS presentation;
- CDP Runtime execution-context shape;
- coarse network trace.

`podman` remains on the host side. The Network-v2 namespace is not treated as a Podman/cgroup control-plane authority.

While the child Browserless session is live, the host parent observes the actual Browserless Chromium process command line. The collector records `effectiveLaunchArgvNormalized` in `controlLayer`; only transient `--remote-debugging-port=<number>` is normalized to `--remote-debugging-port=<ephemeral>`. This makes Browserless/Puppeteer default launch-argument drift part of `controlLayerDigest` without binding a random port into every witness.

## Detector coverage

Current detector version: `harness-browser-security-r2`.

```text
CF02  normalized browser JA4 / PeetPrint / HTTP2 / TLS version
      JA3 deliberately excluded because R1 measured within-arm variability

CF03  neutral main-document request header order

CF04  webdriver / UA / platform / locale / hardware / geometry / timezone

CF05  Runtime execution-context count and normalized context shape
      broader protocol-domain subscription state remains uncovered

CF06  network geography + explicit network observer identity
      browser timezone/locale/geometry + container font resolution

CF07  cookie row count and distinct host count only
      no cookie value is read into the witness
```

Cloudflare trace's `observer` is explicitly recorded as `python-urllib`. Its `http`/`tls` values describe that coarse trace observer, not Chromium's browser transport; browser transport belongs to CF02.

## Invocation

```text
PYTHONPATH=. python scripts/browser_security_witness_source.py \
  --endpoint-id chatgpt-carrier-11 \
  --witness-id <stable-observation-id> \
  --output source-manifest.json
```

Feed the resulting manifest to Security-v2:

```text
PYTHONPATH=src python scripts/build_browser_security_witness.py \
  source-manifest.json --output witness-bundle.json
```

Then compare only like-for-like detector versions for subject-drift claims. A detector-version or coverage change is `DETECTOR_DRIFT`.

## R2 acceptance evidence

Two consecutive live observations of `chatgpt-carrier-11` were recorded as:

```text
evidence/browser-security-witness-source-r2-run1-20260918.json
evidence/browser-security-witness-source-r2-run2-20260918.json
```

Both used the same current Chromium binary, Network-v2 authority, Browserless image, and normalized effective launch surface. Security-v2 comparison of the two canonical bundles reported:

```text
browserBinary change   false
controlLayer change    false
networkAuthority change false
changedFamilies        []
detectorDrift          []
publicObservationChanges []
rootCauseEstablished   false
```

That establishes repeatability of this detector version under the measured two-run sample; it does not establish a Cloudflare or provider challenge cause.

## Pool runner

`browser_security_pool_runner.py` turns the per-carrier collector into one neutral/read-only pool operation while preserving the Harness/Security authority split and the on-demand Browserless lifecycle. A managed carrier that was already active remains active. A managed carrier that was sleeping may be temporarily started through `BrowserlessAutomationService.ensure_endpoint_active()` for the observation, then is restored to sleeping only after the same carrier lease is reacquired and `/sessions` is still empty. If a new session appears, the runner fails closed and leaves the carrier active rather than stopping another consumer's work. The receipt records this per-carrier lifecycle evidence.

```text
Harness pool runner
  -> verify Security-v2 pool-index + each baseline bundle SHA-256
  -> collect carrier-11 current source manifest
  -> Security-v2 canonicalize carrier-11
  -> collect carrier-12 current source manifest
  -> Security-v2 canonicalize carrier-12
  -> collect carrier-13 current source manifest
  -> Security-v2 canonicalize carrier-13
  -> Security-v2 pool classification
```

Harness does not reimplement drift semantics. The Security-v2 result is embedded unchanged in the run receipt.

Example:

```text
python scripts/browser_security_pool_runner.py \
  --run-id pool-check-20260918 \
  --security-root /root/projects/ordivon/platform/security
```

Use `--artifact-dir` when the candidate manifests, canonical bundles, comparison manifest, and final receipt should be retained. The runner verifies the digest-fenced LKG bundles before collection and refuses pool-index paths that escape the configured Security-v2 root.

The R1 live dogfood receipt is sealed at:

```text
evidence/browser-security/pool-runner-r1-acceptance-20260918.json
```

That run used all three production Browserless carriers and returned `NO_OBSERVED_DRIFT` with CF02-CF07 unchanged, no detector drift, no browser/control/network authority drift, `providerChallengeVisited=false`, and `providerSendAttempted=false`.

## Browserless paired canary qualification

`browser_security_browserless_canary.py` is a qualification-only transaction for an immutable, locally available Browserless image. It does not mutate the production Quadlet and does not restart carriers 11/12/13.

The runner derives its control arm from the **installed rendered production Quadlet**, not from a repository template and not from a requirement that all carriers be resident. The Quadlet owns immutable image, Network-v2 namespace, and Ordivon environment. Any currently active 11/12/13 carrier is cross-checked against that contract; a sleeping on-demand carrier is a legitimate lifecycle state rather than a qualification failure. The canary then uses reserved qualification instance `91` with an empty temporary profile, ephemeral headful Xvfb `:191`, the same Network-v2 namespace, and the same launch environment for two sequential arms:

```text
production image control -> neutral witness -> Security-v2 bundle
candidate image          -> neutral witness -> Security-v2 bundle
                                      \-> bundle differential -> canary standing
```

The candidate image must already exist locally and must be supplied by exact `ghcr.io/browserless/chromium@sha256:<digest>` identity. The canary never pulls an image, never visits ChatGPT, never uses a protected challenge as an oracle, never crosses SEND, and never promotes the candidate. Temporary container/profile/X11 authority/socket state is removed after each run.

Qualification distinguishes expected infrastructure identity change from unexpected observable presentation drift. A different image may change browser binary and control-layer digests, but detector drift, Network-v2 authority drift, challenge metadata drift, or any changed CF02-CF07 public observation holds the candidate. A same-image control must reproduce with no infrastructure or subject drift.

Live acceptance on 2026-09-18 produced both controls needed to validate the instrument:

- `evidence/browser-security/browserless-canary-control-r1-20260918.json`: current production image `b1ba7b...` versus itself -> `PASS_CONTROL_REPRODUCIBLE`; CF02-CF07 and all infrastructure digests unchanged.
- `evidence/browser-security/browserless-canary-known-different-r1-20260918.json`: older local image `5e3f3e...` versus current production -> `HOLD_PRESENTATION_DRIFT`; CF02 `peetprintHash` and CF04 `userAgent` changed while Network-v2 authority remained unchanged.

Neither receipt establishes a Cloudflare/provider root cause. The second image is a known-different positive control, not a downgrade recommendation.

During this work the repository template was found stale relative to the already-running production substrate. Production and historical Git commit `4896113` both bind Browserless image `b1ba7b...` with `TZ=Asia/Shanghai`, while current main still carried the older `5e3f3e...` pin. This slice forward-ports only that already-realized production truth and its exact test assertions; it does not replay the historical branch or its older challenge narrative.


## Browserless image promotion transaction

`browserless_image_promotion.py` separates candidate qualification from production mutation. A promotion request binds the exact candidate OCI digest, canary receipt digest, source-template digest, installed rendered-Quadlet digest, Network-v2 generation, and Harness commit. The read-only default action returns only `NOOP_ALREADY_CURRENT` or `READY_TO_APPLY`; it never changes a service.

The source Quadlet is a Network-v2 template, so promotion never compares or installs the raw repository bytes directly. It resolves the current Network-v2 authority through `browserless_podman_deploy.py`, renders the template, and requires the rendered candidate to differ from the installed Quadlet only at `Image=`. Active carriers must agree with the installed control image; sleeping on-demand carriers are recorded as inactive rather than treated as missing evidence.

The explicit `--apply` path reuses the existing Agent Automation admission fence. It stops MCP admission, waits for Temporal and the **currently active** Browserless carriers to become quiescent, records the exact pre-promotion active/inactive topology, snapshots the installed Quadlet, then starts/restarts carriers in order 11 -> 12 -> 13 with exact candidate-image and health checks for the qualification window. A post-change Browser Security pool observation is retained durably under the candidate transaction directory. Only shared `browserBinary` and/or `controlLayer` infrastructure changes are allowed at this stage; any CF02-CF07 family change, detector drift, challenge-standing change, Network-v2 drift, or carrier-local drift rolls the Quadlet back and restores the pre-promotion carrier topology.

A successful image mutation deliberately stops at `APPLIED_LKG_RESEAL_REQUIRED`: MCP remains stopped and CLI admission remains closed. Security-v2 then owns LKG reseal with `promote_browser_security_pool_lkg.py`. Harness `--finalize` temporarily retains all three candidate carriers active for a fresh live pool against the resealed LKG and requires exactly `NO_OBSERVED_DRIFT`. It then restores the exact pre-promotion active/inactive topology before starting MCP and removing the admission gate.

```text
paired canary PASS
  -> promotion plan
  -> apply / staged 11-12-13 restart
  -> durable post-change evidence
  -> Security-v2 LKG reseal + commit
  -> Harness finalize / fresh NO_OBSERVED_DRIFT
  -> reopen admission
```

Promotion artifacts live under `state/browserless-image-promotions/<candidate-digest>/` and include the durable promotion receipt, rollback Quadlet, post-change pool evidence, and finalize pool evidence. The transaction never pulls an image, treats a protected challenge as a detector oracle, or crosses provider SEND.


## Prospective CF07 provider-preflight telemetry

`BrowserlessAutomationService.provider_preflight()` now records content-minimal prospective CF07 metadata without making telemetry an admission authority.

Each successful telemetry write creates a new private JSON event under:

```text
<stateRoot>/cf07-provider-preflight-events/
```

The event allowlist is limited to:

```text
observedAtMs
endpointId
standing
lifecycleStarted
sessionCountClass
providerEffectAttempted=false
clicked=false
composerFilled=false
sendAttempted=false
assistantOutputRead=false
profileFirstObservedAtMs
semanticProviderSessionCreationKnown=false
```

The session-count class distinguishes `ZERO`, `NONZERO`, `NOT_OBSERVED`, and `LEASE_BUSY`. The event does not copy `pageRef`, detail text, substrate-health payloads, URLs, cookie values, tokens, prompts, turns, or provider page content.

The first observation of each endpoint also creates one private create-once marker under:

```text
<stateRoot>/cf07-profile-first-observed/
```

`profileFirstObservedAtMs` means only “first observed by Ordivon CF07 telemetry.” It is explicitly not interpreted as provider-session creation time.

Telemetry is non-authoritative. A write failure leaves the provider-preflight `standing` unchanged and adds `cf07Telemetry.standing=WRITE_FAILED` with only the local error class. A successful write reports `RECORDED`. This preserves provider admission behavior while making future cadence/history claims prospectively auditable.
