# Ordivon Studio Expression Card — production cognition

Status: active production decision record

## FRAME

This is the first ordinary Studio-consumption artifact in the dedicated Studio consumer thread. A viewer should understand the responsibility boundary in one glance: Studio does not seize truth; it transforms a bounded source claim into editable expression.

The artifact must work at 1200×630 and survive reduction to common social-preview sizes. It is not an architecture diagram and should not read like documentation.

## BIND

Owner authority is Ordivon Studio revision `90e2b5d46b0f16171d242633454714017a14f2f2`. `claims.json` binds the core responsibility, the ordinary expression journey, and the current cross-medium visual baseline.

## EXPRESS

Use a strong two-part hierarchy:

1. `SOURCE-BOUND REALITY` as the factual anchor;
2. `EDITABLE EXPRESSION` as the creative destination.

A compact right-side rail may expose `BIND / EDIT / RENDER / REVIEW / OUTPUT`, but it must remain subordinate to the headline. Purple marks transformation; green marks selected output. The visual language should feel editorial and compositional rather than like a dashboard.

## RENDER

Editable source: `source/card.svg`.
Selected candidate: `output/card.png`.
Canvas: 1200×630.
Renderer: `rsvg-convert --width 1200 --height 630`.

Git-tracked SVG/PNG bytes are sufficient for this bounded still-image Production.

## AUDIT

Before approval:

- PNG must decode as exactly 1200×630;
- source and output digests must match `assets.json` and `production.json`;
- all Claim source paths must exist at the bound Studio revision;
- `SOURCE-BOUND REALITY` and `EDITABLE EXPRESSION` must remain legible at reduced preview scale;
- no text may clip the safe outer frame;
- the right-side process rail must remain secondary;
- the visual must not imply that Studio owns the underlying truth.

## DECIDE

**V1 Output approved; Production remains review.** `rsvg-convert` rendered the exact editable SVG to PNG `sha256:fc19d4cf27982fd177c9411245fb994a970551e105866348ee03e9deed6bcce4` (115,196 bytes). Native Runtime image transport then exposed those exact bytes for direct visual inspection. The PNG probes as 1200×630 RGB.

The first render earns a bounded no-op: `FACTS STAY WITH THEIR OWNER.` dominates immediately; `Expression stays editable.` remains the second semantic layer; the right-side BIND→OUTPUT rail is legible but clearly subordinate; no text clips the safe frame; and the composition does not imply that Studio owns source truth. No visual revision is justified by the observed artifact.

The Production stays `review` because no external/public destination has deliberately consumed this exact Output yet. That is a publication boundary, not a visual defect.

## LEARNING

The first ordinary-consumption pass exposed one useful production-local constraint: a valid cognition record requires an explicit `LEARNING` section even when the first visual candidate is accepted without revision. That requirement is cheap and useful here because it separates the observed reusable lesson from the transient critique that led to the no-op.

No broader Studio mechanism was needed. The existing Claim → editable SVG → deterministic render → native pixel observation → decision path was sufficient for this still-image task.
