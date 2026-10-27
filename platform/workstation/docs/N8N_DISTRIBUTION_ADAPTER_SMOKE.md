# n8n Distribution adapter acceptance

This slice verifies a synthetic decision event routed through a replaceable n8n provider adapter. It does not grant n8n domain authority and it does not perform publication writes.

```text
Caller-constructed synthetic CloudEvent
        -> n8n webhook
        -> validate envelope
        -> IF decision.action == preflight_ready
            false -> blocked result (no provider node)
            true  -> GitHub provider-native GET/readback
                  -> readback result
```

The workflow implementation ID is `ordivon-dist-adapter-smoke-v1`; domain contracts must not embed this ID.

## Safety property

A synthetic Artifact-backed decision with `artifact_release_not_ready` is routed to `Build Blocked Result`. The persisted n8n execution must not contain `GitHub Provider Readback`. The result reports `providerCalled=false` and `externalEffectPerformed=false`.

The positive branch is deliberately read-only. `preflight_ready` causes a GitHub public `GET` of the already-existing `ordivon-runtime` issue 72. The result reports `providerCalled=true`, `externalMethod=GET`, and still `externalEffectPerformed=false`.

This proves branching and provider reachability only. It does **not** implement or authorize GitHub release creation, issue creation, upload, mutation, or any other provider write.

## Sources

- workflow: `n8n/workflows/ordivon-distribution-adapter-smoke-v1.json`
- convergence: `scripts/converge-n8n-distribution-adapter-smoke.sh`
- invocation: `scripts/invoke-n8n-distribution-adapter-smoke.py`
- persisted-execution acceptance: `scripts/accept-n8n-distribution-adapter-smoke.sh`

The acceptance script uses the Distribution R7 development Artifact fixture only as a negative input. The invocation script constructs the decision directly; it does not call a Distribution approval, authority, admission or reconciliation engine. This fixture/event seam remains valid after those unused reference implementations retire.
