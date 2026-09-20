# Provider Boundary Diagnosis R1

## Purpose

Agent Birth must distinguish three different facts that were previously too easy to collapse:

1. the Browserless carrier/substrate is unavailable;
2. the provider is currently not admissible or its UI is unresolved;
3. the provider is ready.

A provider challenge is not an instruction to restart Browserless, rotate profiles, clear profile state,
change launcher flags, or mutate Network-v2.

## Runtime state

The pure `provider_boundary_diagnosis.py` classifier consumes one read-only ProviderPreflight
observation and returns:

- substrate standing;
- provider admission standing;
- carrier routing;
- human-verification eligibility;
- explicit re-entry policy;
- allowed automatic actions;
- forbidden automatic infrastructure repairs.

For a healthy carrier with `CHALLENGE_GATED` the state is:

```text
SUBSTRATE_HEALTHY_PROVIDER_NOT_ADMISSIBLE
```

and the selected carrier is preserved. Existing human-verification handoff remains available.

## Browser Security R9 relationship

The runtime diagnosis reports `browser-security-r9` only as a **knowledge-policy reference**:

```text
REFERENCE_ONLY_NOT_LIVE_ASSERTION
```

This is intentional. ProviderPreflight does not re-run R1-R9 neutral experiments and must not claim
that current neutral presentation was freshly measured. R1-R9 constrain repair routing: current
neutral differences were mechanistically localized, so a provider-boundary observation by itself
does not authorize automatic Browserless/Network/Profile mutation.

## Automatic repair policy

Provider-boundary and unresolved-UI observations forbid automatic:

- carrier rotation;
- carrier restart;
- profile clearing;
- launcher-flag mutation;
- network-authority mutation.

Carrier failover remains allowed only for the narrow pre-SEND carrier/transport standings already
defined by the Birth contract.

## Human verification

`CHALLENGE_GATED` and `AUTH_REQUIRED` remain human-verification eligible. The diagnosis layer does
not remove or bypass the existing bounded handoff path. It only prevents that provider condition
from being misdiagnosed as substrate failure.
