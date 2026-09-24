# ClaimPermission Context24 Pressure R1

Status: **PASS_STUDY_OWNED_CLAIM_PERMISSION_PRESSURE_R1**

This is a **Study-owned pressure prototype**, not a shared executable ClaimPermission policy and not scientific-truth authority.

## Empirical pressure surface

Context24 public Task1 train contains **474 claim instances** and **679 gold evidence links**. Exact upstream evidence content is bound for **256 links**; **423** remain identity-only.

At claim level the split is unusually sharp: **171 claims** have all annotated gold links content-bound, **303 claims** have no locally materialized gold content, and **0 claims** are partial. This makes representation availability a strong pressure case: `CONTENT_INSPECTABLE` must not silently become `SCIENTIFICALLY_SUPPORTED`.

Evidence multiplicity also cannot be promoted into support strength. **125 claims** have multiple annotated gold links (maximum **9**), while **28 evidence-content objects** are reused across more than one link (maximum **6 links per content object**). Link count is therefore neither an independence count nor a support-strength score.

Full-text carriers cover **229/229 train papers** and **46/46 test papers**, but content availability does not grant method adequacy, truth, causality, generalization, or hidden challenge-test gold.

## Candidate ceiling

For this pressure test, representation may grant only an inspection ceiling:

- evidence identity only -> `EVIDENCE_IDENTITY_TRACEABLE`;
- exact figure/table bytes -> `CONTENT_INSPECTABLE`;
- scientific claim strength -> always `OWNER_INFERENCE_REQUIRED` until the Study binds its own estimand/design/unit/dependence/uncertainty/sensitivity/scope authorities.

The prototype explicitly returns `NOT_GRANTED` for truth, causality, generalization, method adequacy, and automatic claim-strength promotion.

## Architecture consequence

The reusable rule is narrower than ClaimPermission itself: **representation state and scientific-inference authority are independent axes**. The full scientific permission object remains Study-owned. Cross-Study promotion is intentionally ineligible after this single Context24 pressure family.
