# Ordivon Distribution

Distribution retains optional external-effect safety guidance, historical provider
observations and a source fixture consumed by Workstation's n8n acceptance.
It does not run an admission service or a generic distribution control plane.

## Current consumer boundary

Workstation's `accept-n8n-distribution-adapter-smoke.sh` reads
`evidence/r7-artifact-development-publication-intent.json` as a negative Artifact
input. Its invocation code extracts intent/effect fields and constructs a
synthetic CloudEvents 1.0 decision. The n8n workflow checks the blocked branch and
a separate GitHub GET-only readback branch.

That consumer does not invoke Distribution approval, authority, admission or
reconciliation code. Its acceptance proves event branching and readback
reachability, not provider-write admission or publication.

## Direct provider composition

A real delivery task should use the destination's native API, CLI or connector,
its IAM/OAuth and exact provider readback. Runtime supplies local physical
execution truth only when required; workflow and integration providers are
selected for the task.

Retain these effect-safety rules at the actual consumer:
- bind an authorized effect to its exact provider, account, payload and occurrence;
- credentials alone do not establish permission for an intended write;
- local transport/workflow success does not establish provider acceptance;
- reconcile ambiguous outcomes before retry unless provider idempotency or
  authoritative absence makes retry safe.

Postiz, rclone and OpenAPI Generator remain optional external-tool observation
profiles. Their probes do not establish current production availability or
authorize provider writes.

## Retired implementations

The former approval/EffectAuthority producer, bound-input admission wrapper,
reconciliation policies, schemas and synthetic tests had no tracked downstream
consumer outside their own reference suite. They are retired from active source.
The R7 input remains because Workstation reads it; that fixture does not justify
retaining an unused policy stack.

The former R8 Temporal dispatch smoke and R10 Steam local preflight are also
retired. Use Temporal or provider-native release tools at a real consumer when
needed. The old composition declaration and local LEGO plan were removed because
they had no actual execution consumer; no replacement registry or plan is needed.

R1-R7/R9 migration notes were retired from the working tree; Git history
retains their dated text. The R8 note remains as a cross-reference named in
`evidence/r8-validation-20260912.json`, but that record's historical SHA-256
does not match the current note. Neither describes an active executable path.
Historical evidence JSON is source-cut evidence, not live deployment proof.

## Source verification

Run `mise run verify` in this owner. It validates retained JSON profiles and the
consumed R7 fixture, checks retired surfaces are not wired into forward scripts,
and runs native ShellCheck.

`bash scripts/test-external-carriers.sh` remains an optional observation of the
provider/tool interfaces. It is separate from deterministic source verification
and may require external binaries, credentials or network access.
