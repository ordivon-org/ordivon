---
schema_version: 1
id: game.front-half.external-reference-profile
title: Ordivon Game — External-Reference Front-Half Profile
type: development-profile
profile: product-discovery
lifecycle: active
source_role: canonical-front-half-profile
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - researcher
  - builder
  - producer
  - agent
updated: 2026-09-14
summary: External-first but non-waterfall product-discovery profile before canonical G0: use bounded external orientation to prevent local capability bias, then iterate reference learning, competing product theses, throwaway prototypes, claim-specific evidence and structured decision analysis until a specific game earns commitment.
evidence_status: externally-grounded
readiness: CURRENT
applies_to:
  - ordivon-game
related:
  - game.external-mature-practice-adoption-r1
  - game.development-model
  - game.development-core
  - game.player-evidence-programme
---
# External-Reference Front-Half Profile

## 0. Authority and purpose

This document owns the **Game-specific product-discovery profile before canonical G0**. It does not create a second software lifecycle, a universal game-design theory, a market-success formula, or a replacement for mature external practice.

```text
BOUNDED EXTERNAL ORIENTATION
  success surfaces / player practice / audience / opportunity
  -> success-universe census without feasibility filtering
  -> archetype/reference coverage sufficient for the current decision
  -> STOP broad expansion when marginal decision value is low

                 ↓

ITERATIVE EXPLORATION

  Reference learning  <->  Product theses  <->  Throwaway prototypes
          ^                    |                      |
          +------- claim-specific evidence -----------+
                    |
                    v
        scoped findings + uncertainty
                    |
                    v
  Structured Decision Making / Value of Information
                    |
          kill / revise / continue / learn more

PRODUCT COMMITMENT
  -> canonical G0 Game Definition only when a specific game is justified
```

Strong rules:

```text
Innovation is not the required input.
A justified differentiation is an output of learning from mature patterns and evidence.

External orientation prevents blindness; it is not permission for endless research.
Prototype early when a playable artifact is the cheapest way to answer a real question.
```

The previous broad Pre-G0 GameForm search, D-series hypotheses, A/D/I playables and C0/C1/C2 packets remain useful **coverage, apparatus and falsifier assets only**. They do not select a product, rank genres, or create momentum merely because they already exist.

## 1. External authorities and reference practice

This profile composes mature external practice rather than renaming it.

### 1.1 Success-universe census before comparable-game discovery

Steamworks' current Tag Wizard explicitly uses genre/subgenre, player activities, mechanics, visuals, themes and other descriptors to identify similar titles and advises developers to inspect similar games. Platform-native taxonomy is useful **after** the success universe has been observed; it must not become an early feasibility filter.

R0 therefore keeps three questions separate:

```text
Universe membership:
  what games are empirically successful on each bounded external surface?

Representative reference:
  what mature archetype / interaction grammar does each successful game help us understand?

Cheap causal baseline:
  what is the smallest lawful reproduction that can test one transfer claim?
```

Success-universe membership should preserve source-native evidence such as platform, region, time window, revenue/download/player/lifetime-sales metric and observed rank or unit count. It is **not filtered** by our team size, engine, art capacity, networking capacity, Runtime Agent affinity or expected reproduction cost.

Only after archetype coverage is established should a representative reference stack preserve additional dimensions such as:

```text
GameForm / player activity
Target platform + input
Session / progression shape
Solo / social / online burden
Commercial or audience success evidence
Longevity / design maturity
Evidence availability for teardown
Expression/content dependencies
Production / LiveOps burden
Smallest causal baseline cost
```

A globally successful game may be an essential flagship/canonical design reference while being an invalid full-product production baseline for a tiny team. Do not delete it from the research universe for that reason; instead shrink only the **causal reproduction**, not the reference set.

Source: https://partner.steamgames.com/doc/store/tags

### 1.2 Divergence and convergence

The Design Council Double Diamond remains a useful external process skeleton for divergent/convergent work. In Game's front half it is **subordinate to external reference, claim-specific evidence and the decision actually being informed**, and it must not be misread as a waterfall. Discover may include early making/testing; evidence may send work backward, sideways, or terminate it.

```text
Discover: external reference classes + audience/context + unresolved opportunity + early probes
Define: current thesis / learning question / decision to inform
Develop: competing prototypes / reference reproduction / variation
Deliver: enough evidence for the current decision, not necessarily a shipped product

Any step may reopen another when evidence changes the problem.
```

Source: https://www.designcouncil.org.uk/our-resources/the-double-diamond/

### 1.3 Game-design analysis

MDA and other mature game-design lenses may be used as `REFERENCE_ONLY` teardown vocabulary. They help connect mechanics, resulting dynamics and player-facing aesthetics/experience, but no one lens becomes Game's product authority.

Source: https://aaai.org/papers/ws04-04-001-mda-a-formal-approach-to-game-design-and-game-research/

### 1.4 Prototype-led learning

Nintendo's published Echoes of Wisdom development interview is retained as a concrete industry precedent, not a universal standard: multiple gameplay directions were prototyped, played, and materially redirected after the team could verify features and feel. This supports the rule that gameplay evidence may overturn an apparently mature internal concept.

Source: https://www.nintendo.com/sg/interview/bdge/index.html

### 1.5 Human participant evidence when the claim requires it

Human evaluation is one evidence family inside the external-first Player Evidence routing, not the default approval path. Use it when the target variable is actual Human behaviour, interpretation, preference, comprehension, meaning or experience. ISO 9241-210/9241-11 apply where HCD/usability applies; Games User Research practice supplies question-method fit; platform-native playtest delivery may be useful. Structural, reachability, causal-control, robustness or strategy claims should use formal, synthetic, telemetry or experimental carriers when those identify the claim better. A 2026 GDC small-team session also documents a lightweight repeatable 1-on-1 playtest practice centered on focused sessions, interviewing, actionable feedback and continuous iteration.

Sources:
- https://www.iso.org/standard/77520.html
- https://www.iso.org/standard/63500.html
- https://gamesuserresearch.com/choose-the-right-playtest-method/
- https://schedule.gdconf.com/session/playtesting-process-for-ultra-small-teams/913818

### 1.6 Mature studio operating precedents — precedent, not authority

Public studio practice supports the same empirical loop without becoming a universal standard:

- Riot R&D separates opportunity/thesis/audience work from prototype and later pre-production; prototype engineering emphasizes iteration and disposable code, while playtests can materially redirect or kill a direction.
- Nintendo's published Echoes of Wisdom development history shows multiple prototypes, direct play, and major redirection after the team discovered what was actually fun in the implemented interaction.
- Supercell publicly documents a culture of killing playable projects rather than allowing sunk effort to force production.

These are **operating precedents**, not compliance authorities. They support the process law that pre-commitment code exists to learn, and that evidence may kill or pivot a direction.

Sources:
- https://www.riotgames.com/en/news/r-d-foundations-opportunity-thesis-and-audience
- https://www.riotgames.com/en/r-and-d-office/engineering-in-riot-r-d
- https://www.riotgames.com/en/r-and-d-office/prototype-building-a-games-substance
- https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-13-the-legend-of-zelda-echoes-of-wisdom-part-1/
- https://supercell.com/en/new-games/

## 2. Front-half operating profile — not a waterfall

R0-R4 are **profile activities/lenses**, not mandatory sequential gates and not additional G-stages. Canonical product-stage semantics still begin at G0.

The default operating model is:

```text
R0 bounded external orientation
        ↓
R1 reference learning ───────────────┐
R2 reference causal reproduction ───┤
Product-thesis formation ────────────┼─> claim-specific evidence
Throwaway product prototypes ────────┤        ↓
R4 controlled comparison/variation ─┘   scoped findings + uncertainty
                                             ↓
                               SDM / Value of Information
                                             ↓
                              kill / revise / continue / learn more
```

A product-thesis throwaway prototype is **not** R2 merely because it contains code. R2 specifically means reproducing a bounded mature reference mechanism as an experimental control. Product-thesis prototypes may begin earlier when they are the cheapest way to falsify an independent product claim.

### R0 — Success universe → archetype map → reference stacks

Question: **What successful game space exists before we ask what is cheap for us to reproduce?**

R0 contains three ordered views, not three new stages:

```text
R0-A Success Universe
  observe complete or explicitly bounded platform/market success surfaces
  preserve each source's metric, region and time window

R0-B Archetype Map
  derive coverage of materially different successful game forms / interaction grammars
  without treating the map as a universal ontology or scalar ranking

R0-C Representative Reference Stacks
  for each important archetype, distinguish:
    Flagship reference     — high-expression / high-scale ceiling
    Canonical reference    — mature repeatedly validated grammar
    Cheap causal baseline  — smallest lawful reproduction for one claim
```

Do:
- include successful games regardless of whether the whole product is feasible for us to build;
- use more than one external success surface so PC current-concurrency does not define the whole market;
- preserve current/breakout evidence separately from mature/lifetime evidence;
- use implementation cost only when choosing a cheap causal baseline or learning order;
- record why each reference is relevant and which product burdens must not be inherited;
- include negative/nearby references when they distinguish the target mechanism.

Exit / saturation condition:
- the current bounded success universe and source limitations are explicit;
- materially different archetypes are represented rather than prefiltered by Ordivon capability;
- representative stacks distinguish flagship/canonical references from cheap baselines;
- the next decision can be informed without material blind spots from broad reference classes;
- additional broad census work has low expected decision value.

After saturation, **stop expanding R0**. Reopen only a bounded reference question when a live thesis exposes a missing class, contradiction or transfer risk.

### R1 — Teardown

Question: **What repeatedly happens when a player actually plays the reference, and what appears to make it work?**

Prefer direct play and observable product behavior. Deconstruct only what the current decision needs:

```text
player fantasy / promise
core verbs + control feel
cadence / timing
micro / session / meta loop
information and decision structure
failure / retry / recovery
progression and content grammar
feedback / camera / audio / animation dependencies
social or online dependencies
production burden and operational burden
```

Separate:

```text
ObservedReferenceFact
!= InferredDesignCause
!= TransferableDesignLaw
```

Exit:
- the baseline mechanism can be stated without copying protected expression;
- causal hypotheses and uncertainty are explicit;
- the smallest valid reproduction is known.

### R2 — Reference causal baseline reproduction / clone-to-learn

Question: **Can we reproduce one relevant mature reference interaction well enough to test a transfer claim?**

R2 is reference-learning infrastructure, not a global permission gate for all playable experimentation. A separate throwaway product prototype may run before R2 if it tests a different thesis and does not claim that a mature reference effect was reproduced.

Reproduce only the bounded mechanism needed for comparison. Use original placeholder assets, names, narrative, audio and expression unless licensed material is intentionally consumed.

The purpose is not a commercial clone. It is an experimental control.

```text
Reference product
  -> mechanism hypothesis
  -> lawful original-expression reproduction
  -> mechanical verification
  -> human comparison where the claim is experiential
```

Do not assume a failed reproduction falsifies the reference. First distinguish implementation error, invalid carrier, missing expression dependency and wrong causal hypothesis.

Exit:
- the reproduction is mechanically stable enough that design observations dominate engineering noise;
- represented and omitted dimensions are explicit;
- rights/provenance boundaries are clean;
- no product momentum is inherited merely because code exists.

### R3 — Claim-specific evidence / baseline validation

Question: **Did the effect we claim actually occur under the tested condition, and what evidence carrier can identify that claim?**

Evidence may evaluate a reference, a reproduced causal baseline, a product-thesis prototype or a controlled variation. The method follows the claim; R3 is not postponed until all R2 work is complete and is not synonymous with Human playtesting.

Use mature methods selected from the claim. For felt experience, comprehension, meaning, preference or other Human-state claims, relevant Human participant evidence is required and synthetic Agents/browser completion are controls only. For structural, reachability, robustness, causal-control or strategy claims, use the strongest applicable formal, synthetic, telemetry or controlled-experiment carrier instead of recruiting Humans by default.

Record:
- decision to inform;
- reference claim;
- target player/context;
- method;
- observed behavior and interview evidence;
- implementation confounds;
- result scope and limitation.

Exit:
- either the baseline claim survives at the observed scope, or the reproduction/causal hypothesis is revised;
- no differentiation claim is admitted against an unverified baseline.

### R4 — Controlled differentiation / comparative learning

Question: **What should we retain or change, and does that change create a better or meaningfully different game for the intended player?**

A product thesis may be stated before a perfect reference baseline exists. However, any *comparative causal claim* against a mature pattern must wait until the compared baseline is sufficiently verified to make the comparison interpretable.

Prefer the smallest informative intervention:

```text
baseline
  vs subtraction
  vs one-variable variation
  vs bounded recombination with another proven pattern
```

Measure unlike outcomes separately. Do not collapse feel, comprehension, replay desire, production cost and market demand into one scalar score.

Candidate differentiation survives only when:
- the baseline is still recognizable enough for the comparison to be interpretable;
- the changed variable is explicit;
- observed player effect is attributable at the claimed scope;
- added production/operational burden is visible;
- the difference is not merely AI novelty or presentation volume.

Exit toward G0:
- a concrete product thesis is more valuable than continued broad reference search;
- the candidate can state what mature pattern it retains, what it changes, and why;
- major unknowns are explicit rather than hidden by prototype polish.

## 3. G0 product-commitment boundary

G0 does not ask whether Ordivon has invented something unprecedented. It asks whether the accumulated opportunity, reference, prototype and claim-specific evidence, interpreted through explicit objectives, alternatives, consequences, uncertainty and remaining information value, justify intentionally committing to a specific game.

Before G0 the controlling question is **Should we build this game?** After G0/pre-production the question becomes **How should we build this game well?** Durable architecture, production pipelines and content scale should follow that commitment rather than manufacture it.

The G0 packet should therefore add to the existing Game Definition:

```text
Audience / Context
PlayerPromise / ProductThesis
CoreInteraction / Loop
ReferenceClass
RetainedMaturePatterns
DeliberateDifferences
ClaimSet + scoped findings
EvidenceByClaim, including Human participant evidence only where required
BaselineEvidence where comparative claims rely on it
DecisionObjectives / Alternatives / Consequences
KeyUncertainty + remaining ValueOfInformation / reopen conditions
KnownRisks / KnownTransferLimits
```

Then the existing `DEVELOPMENT_MODEL.md` G0-G8 projection takes over.

## 4. Role of old Pre-G0 assets

Existing Pre-G0 material remains valuable, but its authority narrows:

```text
GAME_PRE_G0_DIRECTION_SEARCH              historical exploratory research
GAME_PRE_G0_DS1_CHEAP_FALSIFIERS         falsifier library
GAME_PRE_G0_FORM_AGENT_ROLE_DECOUPLING    anti-Agent-bias guard + coverage vocabulary
GAME_PRE_G0_PLAYABLE_PROOF_PORTFOLIO      reusable prototype/evidence apparatus
GAME_PRE_G0_PLAYABLE_WAVE1_APPARATUS      regression/mechanical proof
```

They may answer:
- which dimensions a reference teardown omitted;
- how to build a cheap control;
- whether an Agent role is actually necessary;
- which counterexample should attack a proposed transfer.

They may not answer:
- what product to make;
- what genre is strategically best;
- whether an internally generated direction deserves investment;
- whether a successful mechanical test implies Player Value.

## 5. Agent boundary

Production Agents are strongly admitted in R0-R4 for research, teardown, implementation, content drafts, experiment construction, QA and analysis.

Runtime Agents remain `none` by default. They are admitted only after a retained mature baseline plus a concrete differentiation hypothesis shows that a cheaper script/policy/human baseline loses a central player-relevant distinction.

```text
Agent production leverage != reason to choose an Agent-visible game
```

## 6. Rights / imitation boundary

This profile requires learning from mature products, not copying their protected expression. Preserve the distinction between mechanics/methods of play and protected game text, art, music, audiovisual expression, trademarks and other rights. Product-specific legal review still governs any commercial release.

For bounded clone-to-learn work:
- use original placeholder expression by default;
- retain exact source/provenance for any third-party material intentionally consumed;
- do not publish a learning reproduction as if it were an original commercial product;
- escalate patents, trademarks, trade dress or uncertain jurisdiction-specific rights rather than inferring clearance from this profile.

US Copyright Office background on games and copyright: https://www.copyright.gov/register/tx-games.html

## 7. Stop and reopen rules

Stop broad external orientation when it is sufficient for the current decision; stop front-half **method expansion** when the existing loop can route real evidence toward kill/revise/continue/G0. Do not add another local discovery framework merely because one exists externally.

Current standing on 2026-09-14:

```text
Broad R0 expansion               SATURATED_FOR_CURRENT_DECISION
Reference learning               ACTIVE
Competing product theses         ADMITTED_IN_PARALLEL
Throwaway product prototypes     ADMITTED_IN_PARALLEL
Claim-specific evidence routing  ACTIVE
Human participant evidence       PENDING_WHERE_LIVE_CLAIM_REQUIRES_IT
Reference R2 baseline            CLAIM_SPECIFIC / NOT_GLOBAL_GATE
Product selected                 false
G0 entered                       false
```

Reopen this profile when:
- a real product cannot be learned from or compared through reference/reproduction/playtest/variation;
- a mature external method materially changes;
- rights constraints make the assumed reproduction method invalid;
- a materially different game form demonstrates that the reference-first sequence introduces a systematic false negative;
- repeated products show a smaller profile can replace part of R0-R4 without losing decision quality.
