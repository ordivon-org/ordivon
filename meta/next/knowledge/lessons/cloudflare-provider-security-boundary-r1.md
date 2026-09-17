# Cloudflare / Provider Security Boundary R1

Date: 2026-09-17  
Status: **REGISTERED DIAGNOSTIC MODEL**  
Graph: `knowledge/graphs/cloudflare-provider-security-boundary-r1.json`

## Kernel

A provider challenge is an observed state, not a root-cause diagnosis. Ordivon therefore models challenge attribution as eight orthogonal detection/decision surfaces:

```text
CF01 Edge / Policy Decision
CF02 TLS / Transport Fingerprint
CF03 HTTP Presentation
CF04 Browser JS Presentation
CF05 Automation Control Observability
CF06 Cross-layer Consistency
CF07 Session / Behavior
CF08 Challenge State
```

The repair objective is not "make Browserless pass Cloudflare". It is:

```text
observe -> localize changed surface -> falsify alternatives -> repair/replace only that node -> requalify
```

## Current evidence summary

Already falsified locally:

- broken localhost HTTP/CDP bridge as the current explanation;
- missing persistent Browserless profile as the current explanation.

Observed but not causally attributed:

- ChatGPT provider preflight can return `CHALLENGE_GATED` before composer fill/SEND;
- current production Browserless route is `/chromium`, Puppeteer-launched Chromium, then Ordivon Playwright `connect_over_cdp`;
- `headless=false` is configured;
- persistent `/data` profile is present;
- current local study observed `navigator.webdriver=true` and public automation classification;
- Browserless CDP mode installs its own protocol/listener machinery before Ordivon performs application work.

Still unknown:

- exact provider-authoritative reason for a challenge;
- browser-carrier TLS/JA4 differential;
- exact HTTP presentation differential;
- cross-layer identity consistency of the production carrier;
- whether control attachment timing materially changes the challenge outcome;
- whether session behavior/profile history materially changes the challenge outcome.

## Why this changes repair work

Old repair pattern:

```text
Challenge
  -> assume Browserless detected
  -> change many browser/network knobs
  -> retry
  -> attribution lost
```

New repair pattern:

```text
Challenge
  -> CF01..CF08 witness
  -> identify changed/unknown layer
  -> one-variable differential
  -> classify SUPPORTED/FALSIFIED/UNCHANGED/UNRESOLVED
  -> repair only the responsible component
  -> rerun the same witness
```

This makes the browser-provider boundary compatible with the same LEGO discipline already used for Agent Birth.

## Agent Birth coupling

```text
AB15 CarrierCandidateRouter
   -> CF02 Transport / CF07 Session

AB16 CarrierLease
   -> CF07 Session continuity

AB17 ProviderPreflightObserver
   -> CF01 decision + CF08 challenge observation

AB18 CarrierBindingStore
   -> exact CF02/CF07 provenance

AB22 BrowserlessMaterializationAdapter
   -> CF04/CF05/CF06/CF07 presentation provenance

AB23 ChatGPTSubmitExecutor
   -> blocked by CF08 challenge state before SEND

AB24 SubmitEvidenceInterpreter
   -> CF08 observed evidence -> Birth standing

AB26 BirthReconciler
   -> same-effect observation; never blind resend

AB28/AB29 Human handoff
   -> CF08 challenge + CF07 session liveness
```

The key boundary remains:

```text
Browser substrate healthy
!=
Provider security boundary admissible
```

and:

```text
CHALLENGE_GATED
!=
AUTOMATION_ROOT_CAUSE_CONFIRMED
```

## Standard incident witness

Every future provider-challenge incident should carry at least:

```text
providerChallengeStanding

CF01 policy/decision observation
CF02 network authority + egress + transport fingerprint witness
CF03 HTTP presentation witness
CF04 browser JS/presentation witness
CF05 launchOwner + attachment state + controlLayerDigest
CF06 cross-layer consistency witness
CF07 profile/session identity + session age/history metadata
CF08 challenge metadata and pre/post-SEND boundary

browser build/version/digest
browserless route family/version
control client/version
launch options digest
profile identity
network authority digest
last-known-good
first-known-bad
```

Secrets/cookies themselves are not diagnostic payloads; store only the minimum non-secret metadata/digests needed for attribution.

## Experiment discipline

For mechanism attribution, hold as much as possible constant and vary one architectural node at a time:

```text
same target
same browser build
same network authority
same profile class

vary:
  launchOwner
  controlAttachmentState
  Browserless route family
  controlLayerDigest
  network authority
  profile identity
  session age
```

A clean example is the current old-vs-new control-path hypothesis:

```text
DIRECT Chromium
  first navigation
  late CDP attachment

vs

Browserless /chromium
  Puppeteer owns launch
  Browserless CDP machinery active
  Playwright connect_over_cdp
```

The output is not a universal bot score. The output is a per-node evidence vector plus challenge standing.

## Repair router

```text
CF02 changed -> Network/provider path
CF03 changed -> HTTP presentation
CF04 changed -> Browser runtime/presentation
CF05 changed -> Control layer/attachment
CF06 changed -> Identity consistency
CF07 changed -> Profile/session lifecycle
CF08 changed alone -> Provider policy/drift attribution; preserve pre-effect fence
```

This is what makes future repair cheap: the challenge becomes a bounded diagnostic graph instead of a monolithic browser failure.

## Safety / trust boundary

This model supports authorized measurement, attribution, regression testing, provider routing, and robust human-handoff behavior. It does not make production correctness depend on defeating or bypassing a third-party security challenge. Agent Birth continues to fail closed at challenge boundaries and preserves exactly-once-ish provider-effect semantics.
