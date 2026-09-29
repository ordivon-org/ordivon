# Evidence contract

Every material review claim must name the strongest evidence class that actually supports it. Evidence classes are not prestige scores; they describe what kind of truth can legitimately be inferred.

| Evidence type | Supports | Must not be used alone to prove |
| --- | --- | --- |
| `LIVE_OWNER_RECEIPT` | current owner state, committed receipt, current availability or domain read-back inside that owner's boundary | unrelated owner state; semantic meaning outside the receipt contract |
| `EXECUTED_VERIFICATION` | behavior/test/result bound to an exact source/config/input boundary | current production state after the evidence becomes stale; intended-use validation unless the test actually exercises it |
| `CURRENT_CODE_CONTRACT` | current implementation/contract structure at an exact revision | deployed/live behavior; external effect; domain completion |
| `INTENT_DOC` | intended architecture, plan, requirement, rationale | current implementation or deployment truth |
| `HISTORICAL_CONTEXT` | provenance and why a prior decision was made | present-tense truth |
| `EXTERNAL_PRIMARY` | current external standard/provider/product contract or first-party fact | local Ordivon adoption or realization |
| `EXTERNAL_SECONDARY` | independent interpretation/comparison/context | authoritative provider contract or local realization |

## Evidence precedence

For current local claims, prefer:

`LIVE_OWNER_RECEIPT > EXECUTED_VERIFICATION > CURRENT_CODE_CONTRACT > INTENT_DOC > HISTORICAL_CONTEXT`

This is not a universal truth ranking. A source is only strong inside the scope it can prove.

## Realized-capability law

A capability may be `REALIZED` only when at least one supporting evidence item is `LIVE_OWNER_RECEIPT` or `EXECUTED_VERIFICATION`, and that evidence exercises the claimed capability boundary rather than a nearby implementation detail.

Code presence, tests of a helper, or a planning document can establish `LATENT`, not `REALIZED`, unless the claimed capability is itself purely a code/contract property.

## Freshness

Each evidence item should record an observation time or exact source revision when applicable. Mark evidence `STALE` when a later change touched the owner/contract/configuration relevant to the claim and no re-verification exists. Mark `UNKNOWN` when freshness cannot be established.

## Contradiction handling

When sources disagree:

1. check whether they refer to different owners or layers;
2. compare timestamps/revisions;
3. distinguish intended vs deployed vs observed behavior;
4. prefer the natural owner's current authoritative evidence for that layer;
5. retain the contradiction as an intent-vs-reality or census-confidence finding if it remains unresolved.

Do not silently select the source that supports the preferred narrative.

## Claim ladder

For important conclusions preserve this ladder when useful:

`Observation -> Evidence interpretation -> Inference -> Diagnosis -> Decision implication`

Example:

- Observation: a read-only execution submission returned `reconciliation_required`.
- Evidence: Runtime's durable Job projection reports an orphaned attempt bound to exact request identity.
- Inference: this execution path did not establish ordinary delivery certainty.
- Diagnosis: UNKNOWN until competing causes are tested; do not label Runtime globally broken.
- Decision implication: lower census confidence for claims requiring that execution path and investigate/reconcile before relying on it.
