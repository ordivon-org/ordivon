# AI Red-Team Foundry R2 — Evaluation Target Binding

Status: EXPERIMENTAL SECURITY STUDY / SUCCESSOR TO R1 / NOT PRODUCTION SECURITY AUTHORITY
Date: 2026-09-26

## Narrow objective

R2 closes one gap only:

> Bind exactly what red-team subject/configuration was requested and what provider/runtime subject was
> actually observed, without pretending that opaque model providers expose byte-exact model identity.

R2 does **not** add attack payloads, new attack algorithms, a model registry, a policy engine, or a second
Security subject-identity owner.

## Owner boundary

`platform/security` already owns exact Security `SubjectIdentity` semantics through `subjectRef` and
`subjectRevision`, plus digest-bound `EvidenceRef` records. R2 consumes those values as explicit upstream
references. It does not infer subject identity from a process, session, container, provider connection, or
friendly display name.

The R2 object is therefore named `EvaluationTargetBinding`, not `TargetIdentity`.

## Why requested and realized targets are separate

For open-weight/local targets, the caller may be able to bind the exact model artifact digest before a run.
For closed providers, the caller often knows only a requested model id before dispatch; the provider may
later expose an effective model id, provider revision, system fingerprint, or other response metadata.
Those observations are useful evidence but are not silently promoted into byte-exact identity.

```text
RequestedEvaluationTarget
        |
        | provider dispatch
        v
RealizedEvaluationTarget
```

A finding must bind the realized receipt when live execution is used.

Before any live finding is admitted, `reconcile_realization` fails closed if an exact pre-run model artifact
or provider revision drifted. A `TargetBoundObservation` then binds the realized target digest, attack-spec
digest, provider-artifact digest, judge-spec digest, and observation digest. This relation is study-local;
it does not replace Security v2 `EvidenceRef` or production standing.

## Security-relevant evaluation surface

R2 binds the following independently because changing any one of them may invalidate a robustness comparison:

- Security subject reference and revision;
- target kind (`model`, `agent`, `monitor`, or `system`);
- model provider and requested model id;
- optional exact model artifact digest or provider model revision;
- Harness source revision and Harness configuration digest;
- instruction bundle digest;
- tool-catalog digest;
- authority/capability-surface digest;
- monitor-bundle digest;
- environment/world digest;
- adapter id/revision;
- generation parameters.

Generation parameters are canonicalized as JSON and are part of target-binding identity. A test with a new
sampling temperature, reasoning mode, or token limit is not silently treated as the same evaluation target.

## Identity strength

Realized model identity is classified conservatively:

1. `content_digest` — exact model artifact bytes are digest-bound;
2. `provider_revision` — provider exposes a concrete revision/version but not model bytes;
3. `provider_observation` — only response-time provider observation such as a system fingerprint is exposed;
4. `request_only` — only the requested model id is known.

The classification is epistemic standing, not a ranking of model quality. Claims must not exceed the
strongest identity evidence actually available.

## Non-collapse laws

- Security SubjectIdentity != EvaluationTargetBinding.
- Requested target != realized target.
- Provider/model display id != byte-exact model identity.
- Process/session/container identity != evaluation subject identity.
- Harness revision != model revision.
- Tool availability != effect authority; both are bound separately.
- Monitor identity is part of the evaluated system, not an external oracle.
- Same attack result under a changed binding is a new experiment, not an exact replay.

## Verification

```bash
python3 -m unittest discover -s studies/security/ai-redteam-foundry-r2/tests -p 'test_*.py' -v
python3 studies/security/ai-redteam-foundry-r2/scripts/run_target_binding_fixture.py
```

The fixture is synthetic and performs no external model calls.
