# Browser AX Generalization R1

## Standing

Research gate: PASS.
Production migration: NOT AUTHORIZED.

The experiment now supports an evidence-backed split:

- Chromium/browser accessibility owns role, accessible name, description, state and AX structure.
- Browser DOM metadata owns HTML effect-safety facts that AX alone cannot distinguish.
- Ordivon owns only executor-specific effect binding, ephemeral decision context, semantic freshness
  witnessing, admission and evidence.

## Why pure AX was rejected

The first generalization fixture exposed a safety regression in the AX-only prototype. Chromium's
AX tree represented a password input as an editable textbox and a file input as a button. A
decision projector using AX alone would therefore have granted effects that the legacy Jev
snapshot deliberately excluded.

The same run also showed three non-safety gaps: native summary was omitted, contenteditable was
omitted, and a gridcell containing a button was duplicated.

These failures were not fixed by recomputing accessibility semantics. The projector now consumes
minimal browser-owned DOM descriptors keyed by backendDOMNodeId.

## Hardened effect gate

The hardened projector:

- fails closed in strict mode when DOM metadata is missing;
- excludes password, file and hidden input types;
- recognizes contenteditable without changing the browser-owned accessible name;
- recognizes native summary as a clickable HTML affordance;
- suppresses a gridcell when an actionable AX descendant already owns the effect;
- binds frameId into candidate/witness identity;
- keeps SELECT optionName structural instead of flattening control and option into one label.

## Final fixture equivalence

After hardening, the expanded light-DOM fixture produced:

- Jev: 27 effects;
- AX projection: 27 effects;
- normalized intersection: 27;
- only-Jev: 0;
- only-AX: 0.

The same AX observation additionally exposed three Shadow DOM effects that the Jev light-DOM
querySelector traversal did not observe.

A same-process iframe produced 3 Jev effects and 3 AX effects with exact normalized equivalence.

Dialog context was preserved; inert, disabled, hidden, aria-disabled, password and file controls
were excluded as intended.

## Semantic freshness

A decision witness over the fellowship action was checked after two mutations:

- surrounding decision context changed while the node survived: SEMANTIC_CHANGED;
- the target node was replaced by a same-looking clone: MISSING.

This retains the earlier distinction between node-reference freshness and decision-semantic
freshness.

## DOM metadata owner

Per-candidate DOM.describeNode is rejected as the default composition.

On the final fixture:

- 114 sequential describeNode calls: median about 108.27 ms;
- one DOM.getDocument(depth=-1, pierce=true): median about 3.27 ms;
- DOMSnapshot.captureSnapshot: median about 3.17 ms.

R1 therefore uses one DOM.getDocument acquisition per CDP target and flattens browser-owned
metadata locally. DOMSnapshot remains a future alternative if its additional snapshot semantics
become useful.

## Frame / target topology

The observation unit is not merely a Page.

For same-process child frames, the parent CDP session can request the child's full AX tree by
frameId.

With Chromium forced into site-per-process mode, a cross-site iframe became a separate iframe
target. The parent AX tree no longer contained the child semantics. Playwright was able to create a
CDP session directly for that child Frame, and the normal AX+DOM projection produced:

- CLICK Apply cross origin;
- FILL Cross query;
- CLICK Cross query.

Therefore no custom cross-process browser protocol is required. The composition rule is:

1. one observation session per CDP target;
2. within a target, one AX tree per relevant browsing context;
3. one pierced DOM metadata acquisition per target;
4. every candidate is bound to its frame identity before decision and witness generation.

## Latency

On the final two-frame local fixture:

- legacy Jev snapshot median: about 6.43 ms;
- strict AX+DOM all-frame observation median: about 15.26 ms.

The approximately 9 ms local overhead is currently acceptable as research evidence because the
decision architecture is dominated by a separate reranker budget and the migration removes
hand-written accessibility-name semantics while adding Shadow/frame coverage. This is not yet a
production latency SLA.

## Frozen R1 observation architecture

Browser target
  -> DOM.getDocument(depth=-1, pierce=true)
  -> browser-owned DOM metadata map
  -> frame / target topology
  -> Accessibility.getFullAXTree per browsing context
  -> strict AX + DOM effect gate
  -> ephemeral evidence-rich candidate projection
  -> decision provider
  -> decision-bound semantic witness
  -> freshness-bound executor

OOPIF target
  -> frame-specific Playwright CDP session
  -> the same AX + DOM pipeline

## Remaining gates before production

1. Target-domain reranker duel: Jev vs browser-domain CrossEncoder vs specialized Laya.
2. Larger real-page census beyond controlled fixtures.
3. Production executor binding for frame-aware backend node identity.
4. Latency/error-budget gate on the actual Windows Chrome carrier.
5. Only after those gates may provider-internal-decision be removed from the production Jev route.
