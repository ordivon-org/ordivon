# Browser Security Witness R1

Status: experimental Security-v2 evidence waist.

## Purpose

Browser/provider incidents must be diagnosed from versioned detector witnesses rather than a protected provider challenge alone. The witness model separates subject drift from detector drift and routes changed observable families to the owning repair surface.

Supported families:

- `CF02` network / TLS / transport;
- `CF03` HTTP request presentation;
- `CF04` browser launch / page-visible presentation;
- `CF05` automation-control / execution-context observability;
- `CF06` cross-layer consistency;
- `CF07` profile / session lifecycle;
- `CF08` challenge standing as an outcome observation only.

A witness deliberately contains detector observation digests rather than raw credentials, cookies, session tokens, provider secrets, or unrestricted browser dumps.

## Invariant

```text
protected challenge outcome != detector oracle
```

`protectedChallengeUsedAsDetectorOracle` must be exactly `false`. A challenge standing may be recorded as an outcome, but `compare_browser_security_witnesses()` never reports that a changed challenge standing establishes root cause.

## Detector drift

A detector version change is classified as `DETECTOR_DRIFT`, not as a changed browser-security family. This prevents a detector implementation update from being mistaken for provider/browser drift.

## Repair routing

Observed family drift maps to bounded repair ownership:

```text
CF02 -> network/provider-path
CF03 -> http-request-presentation
CF04 -> browser-launch-js-presentation
CF05 -> automation-control-layer
CF06 -> cross-layer-consistency
CF07 -> profile-session-lifecycle
CF08 -> provider-policy-drift-attribution-only
```

The router identifies where to investigate; it does not claim causality.

## CLI

```text
PYTHONPATH=src python scripts/compare_browser_security_witnesses.py baseline.json candidate.json
```

The output contains infrastructure changes, per-detector status, changed families, detector-version drift, repair routes, challenge-standing change, and `rootCauseEstablished=false`.
