# A3-1 — Response loss / durable identity cross-medium trial

## Question

Can one evidence-bound Runtime fact retain its meaning and expressive force when translated into two different media without forcing both media into the same visual grammar?

## Frozen proposition

The experiment uses the existing `runtime-introduction` production evidence rather than current Runtime feature breadth:

> After delivery becomes uncertain, one admitted operation still has a stable request identity and recorded Job. A later client can recover that same Job instead of blindly creating new work.

Evidence anchor:

```text
productions/runtime-introduction/evidence/runtime-demo.receipt.json
sameJobAfterReplay = true
recoveredByTaskList = true
```

The production remains revision-bound historical evidence. This trial does not claim that the frozen production represents every capability in the current Runtime repository.

## Experiential intent

Primary outcomes:

- **clarity** — understand that response continuity and work continuity are different;
- **presence** — make the moment of uncertainty perceptually real rather than describing it as API trivia;
- **identity** — the durable Job should feel like the stable center of the scene;
- **memorability** — retain the idea “the response can disappear without erasing the work.”

Secondary outcomes: trust, interest.

## Tension profile

| Tension | Chosen region | Reason |
| --- | --- | --- |
| unity ↔ variety | strong unity, one meaningful break | a stable visual grammar makes the broken response legible |
| fluency ↔ challenge | fast model, one conceptual inversion | users know request/response; the surprise is that execution identity survives |
| familiarity ↔ novelty | familiar client/job language, novel spatial treatment | novelty should express the property rather than obscure it |
| predictability ↔ surprise | establish route → interrupt return → reconnect | the broken expected return creates the event |
| continuity ↔ discontinuity | execution continuity across communication discontinuity | this is the semantic core of the experiment |
| restraint ↔ expression | restrained evidence, expressive rupture/recovery | proof remains calm; uncertainty/recovery gets the expressive peak |
| explicitness ↔ ambiguity | explicit fact, minimal visual metaphor | no ambiguity about “same Job”; ambiguity is allowed only in the transient broken channel |
| density ↔ space | sparse central proof | the identity needs visual persistence across the sequence |

## Medium hypotheses

### Web

Web should show the whole causal relation at once:

```text
first request  ──╳── response lost
        \             
         \        durable Job
          └────────────●────────── reconnect
```

The visitor can scan non-linearly, so simultaneous spatial comparison is an advantage. The treatment should remain readable without animation and should not invent a new navigation behavior.

### Motion

Motion should exploit temporal expectation:

1. first client/request enters;
2. durable Job identity appears and persists;
3. the expected response path begins, then visibly fails;
4. the scene holds on the still-existing Job rather than cutting away;
5. a second client enters from another direction;
6. the same request identity reconnects to the same Job/Attempt;
7. proof resolves to `same Job · same Attempt`.

The temporal discontinuity is the communication channel. The event continuity is the Job.

## Shared invariants

Both media must preserve:

- same proposition;
- same proof identity source;
- explicit distinction between communication loss and work loss;
- no implication that every external effect is idempotent;
- no fabricated terminal interaction;
- no claim of semantic Task completion;
- stable Job/Attempt identity as the focal object.

## Deliberately medium-specific choices

Web may use static spatial simultaneity, selectable text, progressive page reading, and responsive reflow.

Motion may use timing, anticipation, interruption, hold, directional movement, and a final resolution beat.

A successful cross-medium transfer therefore **must not** produce pixel similarity.

## Evaluation before promotion

Evaluate against the nine aesthetic dimensions in `../aesthetic-model.md` and record concrete failures. In particular:

- can the causal model be recovered quickly?
- is the “break” semantically attached to response delivery rather than execution?
- does the stable identity remain perceptually dominant?
- does expression add meaning rather than decorate evidence?
- does each medium use a capability the other medium does not have?

No human preference ballot is required for this first trial. The experiment is testing whether the laboratory's concepts change and constrain real composition decisions.


## First rendered result

The first implementation produced both medium-specific candidates and real renderer/browser outputs rather than stopping at rationale.

### Motion render evidence

Three 1920×1080 frames from `a31-runtime-response-loss` were rendered from the Receipt-driven composition:

```text
frame 30   sha256:8844681e9dbab9b3718e5f8900fb5345162ddb208682925ca6d45da1b5c7f310
frame 98   sha256:cef0cfe591abc293fc64a4dbe72e5e6c283074d1e754f17fbf25ec6e9458f75e
frame 198  sha256:383d3b11b8e0807a93f3172d0466bbf64c642c2b51b6bd1f87b2ed845a7512bf
```

The existing pre-laboratory `runtime-request-replay` composition was also rendered at frame 145 as a craft baseline:

```text
sha256:9a2aa406f65a2b8901bffa8cf05ee99d842a706688d5d0e71017549c5e58a2c9
```

The baseline is good at explicit proof-card comparison. The A3-1 candidate changes the organizing event: the Job/Attempt identity becomes the persistent focal object, while the response channel visibly ruptures and a later client reconnects around that still-present center.

### Web render evidence

The Web consumer produced real element captures at desktop and mobile widths. The first desktop pass exposed a semantic composition defect even though build/type/lint were correct: the `same recorded Job` resolution sat on the opposite side from Client B without a complete spatial path, so recovery was textually true but visually under-specified.

That layout was revised to two parallel causal rows:

```text
Client A  →  durable Job  →  response lost
Client B  →  durable Job  →  same recorded Job
```

The corrected desktop geometry gives the durable Job approximately 492 px width versus approximately 265 px for either client/loss/resolution endpoint. The focal hierarchy is therefore implemented rather than merely stated. Mobile reflow contains no horizontal overflow and preserves the semantic sequence as a single column.

Corrected Web capture:

```text
desktop  sha256:36c96dbb3abcccc32a4c2192c0a8ef4edd4319eac0fae5fbb926c9b13bc7041b
mobile   sha256:538832a6c7e85fa75c78246c3baa05dfa88fbeba38f9ca54fed9c5ec4e2fb7f0
```

The existing Web Runtime four-step mechanism was also captured as the pre-laboratory baseline:

```text
sha256:5c54e61650ec9b29660dbdda898fba651c8034c15bb86931fe0c3d99ddbc5d2b
```

## What transferred across media

The strongest transfer was **not geometry**. It was the event model:

```text
transient communication can fail
while
durable execution identity remains continuous
```

Four things transferred cleanly:

1. **focal identity** — Job/Attempt is the stable center rather than one equally weighted step;
2. **continuity/discontinuity** — communication breaks while work identity remains continuous;
3. **semantic contrast** — accent marks durable identity, signal marks loss/uncertainty, success marks recovered continuity;
4. **expressive peak placement** — evidence stays restrained while rupture/recovery receives the strongest perceptual event.

These are higher-level expression relations. Neither medium needed the other's component arrangement.

## What remained medium-specific

### Web: topology and simultaneous comparison

Web benefits from showing the whole causal model at once. The reader can move backward and forward, compare both rows, select text, and continue into exact project evidence. Spatial hierarchy therefore carries more of the explanation than temporal anticipation.

### Motion: expectation, rupture, hold, resolution

Motion can make the expected return path appear before breaking it. Holding on the Job after the response disappears creates a perceptual proof that persistence survived the communication event. A later Client B can then enter as a new event rather than another static node.

The same proposition therefore becomes:

```text
Web     → relation topology
Motion  → event trajectory
```

## First falsification

The initial Web candidate proves why the laboratory cannot stop at naming tensions. `continuity ↔ discontinuity` was conceptually correct, yet the first spatial implementation left one recovery relation visually disconnected. Rendering exposed the mismatch and forced a concrete compositional correction.

Therefore:

> an expression rationale is not evidence that the rendered artifact implements the rationale.

This is the artistic analogue of the existing Ordivon rule that a plausible Agent claim does not replace world evidence.

## Provisional conclusion

A3-1 supports a useful first cross-medium claim:

> **event model, focal authority, and expressive tension transfer across media more reliably than component geometry.**

This is still a local experiment. It does not establish that the new candidates are more beautiful or preferred by a population. It does establish that the Art & Expression Laboratory changed real composition decisions, exposed one concrete visual-semantics bug, and produced different but semantically homologous Web and Motion expressions from one evidence-bound proposition.

The next pressure should therefore not be another generic aesthetics survey. It should test a different expressive problem where the target is not recovery/clarity — for example emotion, suspense, awe, intimacy, or deliberate ambiguity — and see whether the same tension/context model remains useful.
