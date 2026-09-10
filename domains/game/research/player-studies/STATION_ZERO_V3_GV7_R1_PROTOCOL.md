# Station Zero v3 GV7 — Fresh-Player Study R1

Status: **PREPARED / NOT RUN / HUMAN EVIDENCE UNKNOWN**

Machine-readable packet: `research/player-studies/station-zero-v3-gv7-fresh-player-r1.json`

## Research vNext binding

This is one concrete Game research workload projected through the four current Research vNext universal roles. It is not a new Game research service, player database, method registry, or Human standing authority.

```text
researchIntent
  decide whether the current Command → Preview → Commit → Aftermath expression
  is understandable enough to exercise the intended delegation/causal loop,
  or whether a smallest L2 expression/usability repair is required.

targetOfInquiry
  Station Zero v3
  exact Game source fc74ad32a7c03f7c745c1e5ce27985f983ccb6b2
  /v3
  scenario fixed-genesis
  deterministic fixture cognition
  first two committed Turns
  fresh adult player without implementation knowledge

claimBoundary
  primary: C1 usability/actionability + C2 understanding/mental model
  excluded: fun, appeal, market, retention, population prevalence,
            unrelated accessibility populations, Veilwild Human standing,
            Game E2E default-ready standing

evaluationLogic
  observed moderated play + pre-Commit prediction + post-Aftermath causal
  reconstruction + neutral contextual probing, with predeclared falsifiers and
  a bounded repair/retest decision rule.
```

Research vNext source bound for this packet:

```text
bab965e19dd5ad06bb2427c3b599d775af4b6f6f
```

## Why this study exists

Station Zero GV7 already identifies fresh-player evidence as the next legitimate product hinge. Automated runs prove that the World/Agent machinery can generate bounded consequences; they do not prove that a new player understands indirect control or the causal structure shown after a Turn.

The canary therefore asks one decision-relevant question:

> Can a fresh player form and use a minimally correct delegation/causal model by the second Turn without being taught the implementation model?

This is deliberately narrower than “is Station Zero fun?”

## Participant boundary

For R1 use adults who:

- can comfortably read the current English UI;
- have not seen Station Zero or Ordivon implementation/design documentation;
- can use the current desktop/laptop browser surface;
- are willing to participate in a short internal product-research session.

Do not collect sensitive demographics. A coarse note such as `strategy-game experience: none / some / frequent` may be retained only when it helps interpret the session; it is not an eligibility score.

No audio/video recording is required. If recording becomes necessary, freeze explicit consent, access and retention rules before collecting it.

## Moderator script boundary

Before play:

1. State that this is an unfinished game/interface and the product is being tested, not the participant.
2. Ask the participant to act naturally and say what they expect when useful.
3. Do **not** explain the delegation model, internal Agent/provider architecture, intended correct strategy, or hidden causal answer.
4. Tell the participant they may stop at any time.

Allowed neutral probes include:

- “What do you expect will happen if you Commit this?”
- “What do you think each specialist is trying to do?”
- “What do you think caused that result?”
- “What changed your next Order?”

Avoid probes that supply the answer, such as “Did you notice the enemy blocked the Engineer?”

## Session sequence

### T0 — First command

Open the exact `/v3` surface at `fixed-genesis`. Do not provide architecture documentation.

Observe whether the participant can identify their role and make one meaningful Commander Order. Retain corrections, hesitation and any direct-control misconception.

### T1 — Pre-Commit prediction

Before the first Commit, ask the participant to predict what the three specialists are trying to accomplish and one thing that could go wrong.

The purpose is to observe the participant's current model before consequences reveal the answer.

### T2 — Post-Aftermath causal reconstruction

After the first Aftermath, ask the participant what caused the important outcomes. Do not require internal vocabulary. Classify whether their explanation distinguishes, where relevant:

- Commander intent;
- specialist action/choice;
- enemy contest;
- environmental pressure.

Record the participant's own explanation before interpretation.

### T3 — Adaptation

Ask for a second Commander Order and what changed because of the previous Turn. This is the first test that the mental model is actionable rather than merely repeatable as words.

### T4 — Optional exploratory experience note

After the bounded two-Turn canary, a participant may describe waiting, tension, friction or interest. These notes are **exploratory only** in R1 and may generate a later C3 study; they cannot close a C3 experience/appeal claim here.

## Raw evidence worksheet

Create one copy per participant/session. Do not overwrite a previous session when reality changes.

```text
studyId: station-zero-v3-gv7-fresh-player-r1
participantLabel: ____________________
sessionLabel: ____________________
exactGameSource: fc74ad32a7c03f7c745c1e5ce27985f983ccb6b2
surface: /v3
scenarioCaseId: fixed-genesis
providerCondition: fixture/deterministic cognition
freshToImplementation: yes / no / unclear
strategyGameExperience: none / some / frequent / not-recorded

T0 first meaningful Order:
- observed action/order: ____________________
- hesitation/corrections: ____________________
- direct-control misconception: yes / no / unclear
- apparatus defect: ____________________

T1 pre-Commit prediction, verbatim/near-verbatim notes:
____________________________________________________________

T2 post-Aftermath causal reconstruction, verbatim/near-verbatim notes:
____________________________________________________________
- Commander intent distinguished: yes / no / unclear / not-applicable
- specialist action distinguished: yes / no / unclear / not-applicable
- enemy contest distinguished: yes / no / unclear / not-applicable
- environmental pressure distinguished: yes / no / unclear / not-applicable
- moderator correction required: yes / no

T3 second Order/adaptation:
- second Order: ____________________
- participant explanation of change: ____________________
- acts on previous consequence: yes / no / unclear

Implementation/internal terms forced by UI:
____________________________________________________________

Clear severe mechanism-blocking defect observed: yes / no / unclear
If yes, exact observation only (do not diagnose yet):
____________________________________________________________

Optional exploratory experience note (not C3 evidence in this study):
____________________________________________________________
```

## Analysis separation

Preserve the following layers separately:

```text
Raw observation / participant report
!= coded finding
!= interpretation
!= Game repair/product decision
```

For each session, first retain raw notes. Then code only the C1/C2 distinctions named in the frozen packet. Do not add a new success criterion after seeing the data.

## Canary decision rule

This is a small formative canary, not a prevalence study.

- Start with three independent fresh participants on the exact same condition.
- A clear severe apparatus or expression defect may justify the smallest owner-local repair immediately; do not spend more participants proving a known broken reality.
- If reality changes, start a new evidence cut. Pre-repair sessions remain historical evidence and are not pooled into the new condition.
- Bounded C1/C2 support requires at least three completed independent sessions on the same exact condition, no unresolved mechanism-blocking defect, and evidence that participants can use an adequately correct delegation/causal model by the second Turn without moderator instruction.
- Repeated material failure to form or use that model supports `CONTRADICTED_WITHIN_SCOPE` for the affected C1/C2 claim.
- Apparatus failure, leading intervention, incomplete sessions, condition drift or unresolved heterogeneous evidence yields `INCONCLUSIVE`.

No result from this canary establishes population prevalence, enjoyment, market appeal, retention, accessibility fit outside the tested context, or general Game E2E maturity.

## Current standing

```text
Human sessions observed = 0
Human evidence standing = UNKNOWN
Product decision         = HOLD_FOR_HUMAN_EVIDENCE
```

This remains true until actual participant evidence is collected and bound to the exact packet.
