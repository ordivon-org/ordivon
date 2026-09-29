# Cloudflare / Provider Security Experiment R4

Date: 2026-09-18
Standing: **CF07 METADATA CHARACTERIZED / PROVIDER CAUSALITY OPEN**

Primary evidence:

- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r4-cf07-metadata-20260918.json`
- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r4-cf07-analysis-20260918.json`
- `studies/security/browser-security/evidence/browser-security/cloudflare-provider-security-exp-r4-cf07-outcome-anchor-20260918.json`

## One-sentence result

R4 adds a privacy-preserving CF07 lifecycle/cadence witness: historical Agent Automation bindings are relatively balanced across all three persistent carriers, there were no new birth-ledger requests in the prior 24 hours, and a separate current read-only carrier-11 provider preflight still returned `CHALLENGE_GATED`; this weakens a single-overused-profile or current-Birth-burst explanation but does not resolve provider reputation, historical behavior, semantic provider-session age, or policy causality.

## Privacy boundary

The metadata snapshot did **not** read or retain:

- cookie values;
- browser history contents;
- saved credentials or tokens;
- prompt or turn text;
- handoff URLs;
- attempt receipt bodies;
- SQLite `request_json`, `detail`, or `provider_coordinate`;
- provider page content.

The metadata snapshot itself did not visit a provider, wake a sleeping carrier, attempt a provider effect, or cross SEND.

The separate outcome anchor retained only:

```text
endpointId
standing
providerEffectAttempted=false
clicked=false
composerFilled=false
sendAttempted=false
assistantOutputRead=false
```

It deliberately retained no page/challenge details and was not used as a detector oracle.

## Carrier usage distribution

Historical carrier bindings:

```text
carrier-11  114   36.42%
carrier-12   98   31.31%
carrier-13  101   32.27%

max - min = 16
coefficient of variation = 0.0666
```

Therefore the local evidence does not support a story in which one carrier accumulated nearly all Agent Automation use while the other two remained largely unused.

This does not prove equal provider-side reputation: the witness counts Ordivon bindings, not every network request or provider-side event.

## Receipt metadata distribution

Without reading receipt bodies:

```text
                    11    12    13
attempt receipts    113    98   101
pre-effect receipts  60    49    55
turn receipts         25    14    37
human handoff           0     0     1
```

All three profiles have substantial histories. The one historical human-handoff receipt was associated with carrier-13, but one event is not evidence that carrier-13 has a distinct provider reputation state.

## Birth-ledger cadence

The read-only SQLite query selected only:

```text
standing
effect_generation
created_at_ms
updated_at_ms
```

Snapshot:

```text
total requests                         313
new requests in prior 1h                0
new requests in prior 6h                0
new requests in prior 24h               0
new requests in prior 72h             165

newest request age                137082 s
newest update age                 134113 s

historical created interarrival:
  median                            12.453 s
  p90                              779.011 s
  max                            50174.969 s
```

The historical workload therefore contains bursty periods, but there was no current Birth-request burst at snapshot time.

## Current lifecycle snapshot

At metadata collection:

```text
carrier-11  active   sessionCount=0
carrier-12  sleeping
carrier-13  sleeping

human transport active: false on all three
carrier leases: available on all three
```

The last-use stamps were roughly 14 minutes old, but those stamps represent **Ordivon carrier lifecycle use**, not provider-session creation age. They can also be refreshed by neutral diagnostics.

Profile-root filesystem mtime/ctime is likewise not interpreted as profile creation age.

## Current provider outcome anchor

After the metadata snapshot, one official read-only preflight was performed on the already warm carrier-11.

Result:

```text
standing = CHALLENGE_GATED
providerEffectAttempted = false
clicked = false
composerFilled = false
sendAttempted = false
assistantOutputRead = false
```

This anchors the current provider standing while the Birth ledger had zero new requests in the prior 24 hours.

It does **not** show that provider rate limiting is absent. The provider may use IP reputation, historical behavior, unrelated traffic, challenge/session history, or policy state not visible to Ordivon.

## Hypothesis update

### Single overused persistent profile explains the shared challenge

```text
WEAKENED
```

Reason: all three persistent carriers have substantial and relatively balanced binding histories, and R2 independently observed all three gated.

### Current Agent Birth request burst is sufficient to explain the current challenge

```text
WEAKENED
```

Reason: no new birth-ledger requests existed in the prior 24 hours, while a current read-only preflight remained gated.

This does not falsify provider-side rate/reputation mechanisms because their state and inputs are not observable here.

### Historical burst or provider reputation contributes

```text
OPEN
```

Historical interarrival statistics show bursty periods, while provider reputation is unavailable to the local witness.

### Profile-specific corruption

```text
WEAKENED_NOT_FALSIFIED
```

Three distinct profiles were independently gated and have balanced histories. Credential/session contents were intentionally not inspected.

### Semantic provider-session age

```text
UNMEASURED
```

Neither filesystem timestamps nor Ordivon last-use stamps establish when the provider session was semantically created.

## Updated CF07 boundary

What is now measured:

```text
carrier active/sleeping state
carrier lease availability
session count for an already-active carrier
carrier last-use age
profile-root filesystem stat age
aggregate carrier binding/receipt counts and ages
aggregate birth-ledger standing/timing/effect-generation
```

What remains intentionally unavailable:

```text
credential/session contents
provider reputation state
provider rate-policy state
semantic provider-session creation age
durable historical per-preflight cadence
provider-side challenge attribution
```

## Next useful work

The next CF07 improvement should be **prospective non-secret telemetry**, not inspection of credentials:

1. record a durable timestamped metadata event for each provider preflight;
2. retain endpoint id, standing, lifecycle-started flag, session-count class, and no-SEND booleans only;
3. record an Ordivon `profileFirstObservedAt` marker distinct from provider-session creation;
4. keep page/challenge content, URLs, cookie values, and tokens outside this telemetry.

That would make future cadence and profile-history attribution measurable without weakening the current credential/privacy boundary.
