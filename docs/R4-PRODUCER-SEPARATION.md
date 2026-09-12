# Distribution v2 R4 — Producer Separation and Exact Payload Binding

R4 keeps Distribution v2 greenfield and external-first.

## Provider observation producer

No GitHub observer framework is added to this repository. The mature GitHub CLI/API is the provider-side producer. A Runtime Job executes `gh api repos/<owner>/<repo>`, records the exact command and provider response in Runtime artifacts, derives only the narrow capability facts required by Distribution, and materializes the resulting provider observation into the existing consume-only `distribution-r3-evidence` InputAuthority. A later `workspace.execBound` call re-verifies the exact expected digest before admission.

For the current bounded `create_issue` candidate on `ordivon-org/ordivon-runtime`, the provider observation established `has_issues=true`, `archived=false`, and authenticated `push/admin=true`. Admission nevertheless remained `user_action_required` because provider/credential capability is not exact effect authority.

## Exact payload binding

R4 changes the occurrence projection so `effect.payload` is canonicalized with RFC 8785 and hashed into `effectPayloadRef`. Therefore any payload mutation changes `occurrenceRef`; previously bound provider observations, approval requests, and effect-authority objects cannot be replayed onto a different title/body/parameters.

## Approval request, not authority

`EffectApprovalRequest` is a non-authoritative object. It binds the exact occurrence, provider, account, effect name, and payload digest while explicitly carrying standing `approval_required_no_effect_authority`. Tests require that it does not validate as an `effect-authority` object.

Distribution does not mint a grant from this request.

## Reused Runtime ingress boundary

Production Runtime already implements mature external-file ingress through `input.ingest`, but ingress is independently operator-configured per named InputAuthority. At the R4 observation cut, `ORDIVON_INPUT_INGRESS_JSON` enables only `artifact-golden-r1`; `distribution-r3-evidence` is consume-only.

The correct authority path is therefore a separate operator-owned authority such as `distribution-effect-approvals`, explicitly added to both `ORDIVON_INPUT_AUTHORITIES_JSON` and the Runtime ingress configuration under an Operations-controlled rollout. User/operator approval bytes can then enter through `input.ingest`; `workspace.execBound` can independently freeze/reverify them; only then may a narrow authority translator produce an `effect-authority` bound to the same occurrence.

R4 deliberately does not reuse `artifact-golden-r1`, does not turn provider evidence into approval authority, and does not mutate production Runtime configuration just to bypass this boundary.

## Standing

Provider producer: proven.
Payload binding: proven.
Approval request: proven non-authoritative.
Exact effect grant producer: blocked pending a dedicated operator-configured approval ingress authority.
Real external write: not admitted.
