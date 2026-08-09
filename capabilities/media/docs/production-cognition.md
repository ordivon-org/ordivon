# Production cognition

## Purpose

A Production already owns source bindings, Claims, Assets, editorial sources, technical working profiles and Outputs. The Art & Expression protocol adds another need: an Agent continuing a real production must recover the **current creative judgment** without reconstructing it from every historical note.

C3 deliberately does not solve this with a workflow database or a large cognition schema.

## Minimal contract

`production.json` may declare one optional `sources.cognition` Markdown file. The record uses the shared six protocol sections in order, followed by one scoped learning section:

```text
FRAME
BIND
EXPRESS
RENDER
AUDIT
DECIDE

post-decision:
LEARNING
```

Only the presence and order of those sections are machine-validated. Their contents remain natural-language production judgment until repeated unrelated productions prove that a specific field deserves stronger structure.

## Authority

The cognition record is an **index of current judgment**, not physical or domain truth.

```text
Production manifest → identity, source binding, working profile, selected sources, outputs
Claims             → what may be asserted / must not be implied
Assets             → selected media identity and provenance
TimedText          → timed language source
OTIO / Resolve     → editorial structure / proprietary edit state
Receipts           → executable evidence
Cognition          → why the Agent is currently making the next production decision
```

If cognition repeats a fact differently from its owner, the owner wins and cognition must be corrected.

## Why Markdown first

Creative work contains real uncertainty and medium-dependent reasoning. Prematurely turning every target, strategy, audit observation, or learning into enums would freeze the first production's vocabulary into the system.

Markdown keeps the record:

- inspectable by people and Agents;
- easy to revise;
- source-controlled and recoverable;
- capable of linking exact authorities;
- structured enough to resume the six-stage protocol;
- weakly typed enough to let later productions falsify the first shape.

## Promotion rule

A cognition detail earns schema only when unrelated real productions repeatedly need the same machine operation over it. Examples could eventually include exact profile composition, promotion decision state, or render-evidence references. C3 does not assume those promotions in advance.

## First acceptance case

[`../productions/runtime-introduction/cognition.md`](../productions/runtime-introduction/cognition.md) is the first record. It demonstrates that the existing production substrate already contains most necessary facts; the missing layer is a thin current-decision index connecting those facts to `FRAME → BIND → EXPRESS → RENDER → AUDIT → DECIDE` and retaining only scoped learning.
