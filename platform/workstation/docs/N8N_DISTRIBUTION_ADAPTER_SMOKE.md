# n8n Distribution adapter acceptance

This slice verifies the Integration boundary between Distribution v2 admission and a replaceable n8n provider adapter. It does not grant n8n domain authority and it does not perform publication writes.

```text
Distribution admission CloudEvent
        -> n8n webhook
        -> validate envelope
        -> IF decision.action == preflight_ready
            false -> blocked result (no provider node)
            true  -> GitHub provider-native GET/readback
                  -> readback result
```

The workflow implementation ID is `ordivon-dist-adapter-smoke-v1`; domain contracts must not embed this ID.

## Safety property

An Artifact-backed Distribution decision with `artifact_release_not_ready` is routed to `Build Blocked Result`. The persisted n8n execution must not contain `GitHub Provider Readback`. The result reports `providerCalled=false` and `externalEffectPerformed=false`.

The positive branch is deliberately read-only. `preflight_ready` causes a GitHub public `GET` of the already-existing `ordivon-runtime` issue 72. The result reports `providerCalled=true`, `externalMethod=GET`, and still `externalEffectPerformed=false`.

This proves branching and provider reachability only. It does **not** implement or authorize GitHub release creation, issue creation, upload, mutation, or any other provider write.

## Sources

- workflow: `n8n/workflows/ordivon-distribution-adapter-smoke-v1.json`
- convergence: `scripts/converge-n8n-distribution-adapter-smoke.sh`
- invocation: `scripts/invoke-n8n-distribution-adapter-smoke.py`
- persisted-execution acceptance: `scripts/accept-n8n-distribution-adapter-smoke.sh`

The acceptance script uses the real Distribution R7 development Artifact intent by default only as a negative input. Distribution remains the owner of admission semantics; Operations/n8n only consumes its result.
