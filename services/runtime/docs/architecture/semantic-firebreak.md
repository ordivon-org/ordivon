# Semantic Firebreak

Status: `current`
Authority: `source_of_truth`
Purpose: Define how Ordivon maps unstable language or latent meaning into stable governance objects.
Supersedes: historical claim-vocabulary, overclaim, AI-output, and semantic-governance notes.
Verification: document registry semantic checks, constructor validation tests, comparator verdict tests, red-team semantic bypass scenarios.

## Core Rule

```text
Meaning != Governed Commitment
Text must not directly move state.
```

Natural language, AI output, summaries, latent payloads, and human shorthand
can imply many things. Only evidence-bound, authority-scoped, receiptable
claims can enter Ordivon governance state.

## Why The Firebreak Exists

Semantic space is unstable. Small wording changes can create large governance
differences:

```text
"mostly resolved"        -> degraded readiness claim
"resolved"               -> closure claim requiring evidence and authority
"AI recommends closure"  -> proposal
"AI closed the debt"     -> unauthorized closure risk
```

Many different phrases also collapse to the same governance class:

```text
"looks fine"
"risk is controlled"
"we can move on"
"basically done"
```

All of these are unverified readiness or closure-adjacent claims until bound
to evidence and authority.

## Projection Model

Ordivon projects only the governance-relevant part of meaning:

```text
raw semantic input
-> candidate governance objects
-> evidence binding
-> authority binding
-> state classification
-> gate
```

The projection result is a candidate set, not immediate truth:

```json
{
  "input": "This phase is basically done.",
  "candidates": [
    {"type": "completion_claim", "risk": "closure_overclaim"},
    {"type": "readiness_claim", "risk": "missing_authority"},
    {"type": "debt_suppression_claim", "risk": "implicit_waiver"}
  ]
}
```

Ambiguity goes to `DEGRADED`, not `READY`.

## Controlled Vocabulary

High-risk claims must collapse into controlled types:

- `readiness_claim`
- `completion_claim`
- `closure_claim`
- `evidence_claim`
- `authority_claim`
- `risk_acceptance_claim`
- `policy_promotion_claim`
- `suppression_claim`
- `source_of_truth_claim`
- `execution_claim`

Free text may explain these objects. Free text may not replace them.

## Latent Payload Boundary

The same rule applies to model-to-model latent or semantic-state transfer:

- latent payload is not evidence;
- model-readable state is not human approval;
- human projection is not full latent meaning;
- protocol compatibility is not semantic alignment;
- semantic transfer is not execution permission.

Latent payloads require envelope metadata, source identity, codec version,
scope, checksum, expiry, human projection, and receipt before they can
influence governed execution.

## Failure Modes

- Keyword-only checker misses paraphrased closure claims.
- Human-readable summary is treated as the full source.
- AI generates a receipt-looking object and bypasses comparator emission.
- Latent payload carries unsafe intent while visible text looks safe.
- Suppression language hides an unresolved debt.
- A generated view is treated as registry truth.

## What This Changes In Implementation

- External inputs use draft or wire types with validation.
- `ObservedEvent`, `AuthorityToken`, `Receipt`, `Policy`, `Closure`, and
  `Suppression` cannot be made valid by ordinary struct literals.
- Comparator findings use stable root-cause codes, not free-text messages.
- Semantic red-team cases must include paraphrase, implication, and
  euphemistic completion or authorization claims.
- Documentation must label generated projections as projections, not sources
  of truth.
