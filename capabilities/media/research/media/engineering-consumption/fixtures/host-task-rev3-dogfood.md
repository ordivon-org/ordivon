# OMPC-v0 Fixture A — Destructive dogfood contract

## Source

`task:ordivon-media-project-inception-m0-m1-20260818` at exact Host revision `3`, checkpoint digest `sha256:695cf6a3cba795a3a93c774c65517b6741f093fd953d6ca20978fcffff7988b0`.

## Projection pair

- `host-task-rev3-human.md` — Human/Web-oriented realization.
- `host-task-rev3-agent.json` — Agent/structured realization.

The two files are intentionally not byte/schema equivalent. They must preserve the same source fence, owner boundary, project identity and material uncertainty.

## Tests

### A1 — Source-authority conservation

Pass when neither projection claims to be Host authority or replaces the Host checkpoint.

### A2 — Observer relativity

Pass when Human and Agent representations differ materially in form/selection while retaining the same source-fenced claims.

### A3 — Omission disclosure

Pass when each compressed projection states that omitted Host information is projection-local rather than absent from Host.

### A4 — Currentness non-fabrication

Advance the Host task beyond revision 3. The revision-3 projections must then be classified as historical/source-fenced with respect to Host progression. They must not silently remain `current` merely because the fixture files remain available or recently rendered.

### A5 — Action non-execution

Expose a `continue` affordance. Pass only if the projection distinguishes affordance, authorization, Host admission, execution and external-domain completion.

### A6 — Cross-modality semantic equivalence

Pass if the Human/Web and Agent versions agree on:

- source owner and exact revision/digest;
- the READY continuity state being Host-only;
- Media/Studio/Web/Game owner boundaries;
- MF10 not admitted;
- no Media engine/SDK admitted;
- omitted Runtime/Git/domain validation.

## Failure routing

A failure may revise OMPC-v0 role wording or derived projection rules. It must not reopen MF0–MF9 or admit MF10 by convenience. A source-owner semantic problem routes to the source owner rather than being patched into Media authority.
