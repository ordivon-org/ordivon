# Expression knowledge model

## Why this exists

Art, design, rhetoric, narrative and communication contain both durable structure and substantial historical, cultural, medium-specific and situational variation. Ordivon should not treat that uncertainty as a defect to eliminate, nor treat every convention as equally unstable.

The system therefore keeps **evidence class** and **knowledge stability** separate:

```text
evidence class     → what kind of support do we have?
knowledge layer    → how broadly and durably should an Agent reuse it?
```

A peer-reviewed result can still be narrow. A centuries-old craft convention can still be medium-specific. A local experiment can expose a cross-medium candidate without immediately proving it.

## Five knowledge layers

### `hard_constraint`

Externally owned or mechanically testable facts whose violation is a defect rather than a creative disagreement.

Examples: source authority, provenance, exact time/frame identity, file integrity, color-space declarations, delivery format constraints, accessibility requirements, factual claim boundaries.

Default behavior: verify strongly; do not trade away for aesthetic effect.

### `durable_prior`

Cross-medium relationships that have survived substantial evidence, craft history, or repeated materially different production pressure.

Examples can include hierarchy, grouping, continuity, expectation, focalization, rhythm, figure/ground, unity/variety, and the principle that rendered semantics can imply more than literal text.

Default behavior: use as a scoped prior, not a law. Record conditions and counter-pressure.

### `medium_prior`

Knowledge that is useful because of a medium's affordances, production grammar, or established professional practice.

Examples: edit continuity, shot scale, responsive hierarchy, paragraph cadence, loudness practice, caption timing, crop behavior.

Default behavior: owned by the relevant medium profile; update faster than the core.

### `context_signal`

Time-, culture-, audience-, platform-, genre-, or distribution-sensitive information.

Examples: current feed conventions, fashionable visual language, platform attention patterns, present genre expectations, current audience vocabulary.

Default behavior: retrieve near the work; give it an expiry or volatility assumption; never silently promote it into durable core knowledge.

### `local_observation`

Evidence from one Ordivon artifact, experiment, audience encounter, production failure, or bounded comparison.

Default behavior: retain with exact provenance and scope. Promote only after repetition earns a broader claim.

## Minimum metadata for reusable priors

A reusable prior should be recoverable through qualitative fields rather than pseudo-precise taste scores:

```text
layer
statement
scope
support / evidence class
volatility
known counterexamples or counter-pressure
falsifier / update trigger
provenance
consuming profiles
```

`volatility` is descriptive (`low`, `medium`, `high`, or a domain-specific statement), not a numeric probability of artistic truth.

## Promotion and demotion

Knowledge can move in both directions.

```text
local observation
→ repeated medium evidence
→ medium prior candidate
→ cross-medium pressure
→ durable prior candidate
```

The reverse is equally valid:

```text
new counterevidence / new medium / cultural drift
→ narrow scope
→ demote to medium or context layer
→ retire if no longer useful
```

The goal is not an ever-growing canon. It is a compact set of useful, revisable priors whose authority matches their evidence.

## Fast and slow evidence

Agent generation, rendering, ablation and semantic audit can produce evidence quickly. Human response, culture, distribution and long-term consequence move more slowly.

Fast evidence can rapidly falsify implementation and local expressive hypotheses. It cannot accelerate the underlying human or cultural phenomenon merely by sampling itself more often.
