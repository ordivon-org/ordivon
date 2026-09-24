# Cloudflare / Provider Security Experiment R6

Date: 2026-09-18
Standing: **CF07 PROSPECTIVE TELEMETRY ACTIVE / PROVIDER CAUSALITY OPEN**

Primary evidence:

- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r6-cf07-prospective-telemetry-20260918.json`
- `catalogs/knowledge/graphs/browser-security-detector-coverage-r6.json`

## One-sentence result

R6 closes R4/R5's instrumentation gap by putting content-minimal, prospective provider-preflight metadata into the production Agent Automation release: two live read-only acceptance events were durably recorded for carriers 11 and 12, including the on-demand wake/reap path, while URLs, page/challenge content, cookie/token material, prompts, and SEND remained outside the telemetry. This creates a future cadence/history evidence stream; it does **not** establish any provider-challenge cause.

## Production activation

The telemetry implementation is live in Agent Automation release:

```text
dc23c0c6894f415cc6eca624a8740c856ab9009b
```

The release transaction itself passed the Browser Security pre-switch gate:

```text
classification = NO_OBSERVED_DRIFT
providerChallengeVisited = false
providerSendAttempted = false
runningWorkflowCount = 0
release standing = ACTIVE
```

Telemetry is not an admission authority. The provider-preflight standing remains the provider observation. Telemetry adds a separate `RECORDED` or `WRITE_FAILED` metadata standing.

## Event model

Each preflight creates a private, create-new event containing only:

```text
schemaVersion
kind
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

A separate private create-once marker records the first time **Ordivon telemetry** observed each endpoint. This timestamp is not provider-session creation time.

The live acceptance explicitly rejected persistence of:

```text
pageRef
detail text
substrateHealth payload
URLs
cookie values
tokens
prompt or turn text
provider page content
```

Event and profile-marker files were mode `0600`.

## Live acceptance

The first two prospective production events were:

```text
carrier-11
  standing          CHALLENGE_GATED
  lifecycleStarted  false
  sessionCountClass ZERO
  provider effect   false
  SEND              false

carrier-12
  standing          CHALLENGE_GATED
  lifecycleStarted  true
  sessionCountClass ZERO
  provider effect   false
  SEND              false
```

Carrier-12 began sleeping, was started through the normal on-demand lifecycle for the read-only preflight, and was then reclaimed through the normal idle-reaper decision path:

```text
carrier-11  SKIP_WARM_FLOOR
carrier-12  REAPED
carrier-13  ALREADY_COLD
```

The post-reap doctor remained healthy and final topology returned to 11 warm / 12-13 sleeping.

## What R6 changes

The R5 CF07 gap:

```text
durable per-preflight cadence telemetry is not yet available
```

is now replaced by:

```text
prospective telemetry ACTIVE
longitudinal evidence INSUFFICIENT_YET
causality OPEN
```

This matters because future cadence/history analyses no longer need to reconstruct provider-preflight timing indirectly from unrelated receipt mtimes.

## What R6 does not establish

Two accepted events are instrument acceptance, not a behavioral dataset. R6 does not establish that:

- preflight cadence causes `CHALLENGE_GATED`;
- historical burstiness caused the current provider state;
- `profileFirstObservedAtMs` is provider-session age;
- provider reputation or rate-policy state is locally observable;
- a different cadence would change admission;
- any challenge should be bypassed.

The provider-authoritative cause remains unknown.

## Next work

The telemetry should now accumulate **only as ordinary operational preflights occur**. Ordivon should not generate extra protected-provider requests merely to fill a dataset.

The next active neutral-attribution branch therefore remains R5's CF05/CF06 residual:

```text
Browserless launch command-line
Browser target topology
window-management geometry
```

Those should be decomposed with neutral container-direct ablations and page-visible consequence tests before using another provider outcome anchor.
