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

## Observed result — 2026-08-18

Fixture A passed its first destructive round.

- **A1 PASS — Source-authority conservation.** Both realizations explicitly identify themselves as derived projection fixtures and preserve Host as source authority.
- **A2 PASS — Observer relativity.** Human/Web is explanatory Markdown while Agent is structured JSON; representation form and selection differ materially.
- **A3 PASS — Omission disclosure.** Both projections disclose compressed/omitted Host material and do not equate omission from the projection with absence from Host.
- **A4 PASS — Currentness non-fabrication.** The fixture is bound to Host revision 3. A subsequent Host checkpoint advanced the same Task to revision 4 with checkpoint digest `sha256:6bdffc1c95dd9534c077b6aea3fa64d56693934d07e5021e18e354fb854a83bc`. The stored revision-3 projections are therefore historical/source-fenced **with respect to Host source progression only**. No broader Media, Runtime, Git or domain staleness is inferred.
- **A5 PASS — Action non-execution.** The Human affordance text and Agent action disclosure both separate exposure from authorization, admission, execution and external-domain completion.
- **A6 PASS — Cross-modality semantic equivalence.** Mechanical assertions confirm both realizations share the exact Task/revision/checkpoint binding and preserve the same material boundary claims while using different forms.

Mechanical fixture assertions were executed in Runtime Workspace `media-m0-preflight-20260818`; A1/A2/A3/A5/A6 passed. A4 is grounded in a Host observation of the same Task at revision 4. Host explicitly states its truth boundary is semantic continuity only, so this test does not lift Host progression into Git/Runtime/domain currentness.

### Falsification outcome

No OMPC-v0 role or invariant failed in Fixture A. This is **not** enough evidence to admit shared Media implementation. The next fixture must be materially different from Host continuity projection before any code extraction decision.
