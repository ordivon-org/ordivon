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
updated: 2026-09-11
summary: External-first product-discovery profile before canonical G0: select mature comparable reference games, deconstruct and reproduce bounded baselines, validate with human playtesting, then use controlled variation to earn differentiation and a Game Definition.
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
External successful games / platform evidence / player practice
    -> reference-class selection
    -> teardown / play / deconstruction
    -> bounded baseline reproduction
    -> human playtest against the reference claim
    -> controlled subtraction / variation / recombination
    -> differentiated product thesis
    -> canonical G0 Game Definition
```

Strong rule:

```text
Innovation is not the required input.
A justified differentiation is an output of learning from proven baselines.
```

The previous broad Pre-G0 GameForm search, D-series hypotheses, A/D/I playables and C0/C1/C2 packets remain useful **coverage, apparatus and falsifier assets only**. They do not select a product, rank genres, or create momentum merely because they already exist.

## 1. External authorities and reference practice

This profile composes mature external practice rather than renaming it.

### 1.1 Comparable-game discovery

Steamworks' current Tag Wizard explicitly uses genre/subgenre, player activities, mechanics, visuals, themes and other descriptors to identify similar titles and advises developers to inspect similar games. Use platform-native similarity/taxonomy and current market/catalog evidence as **reference-class inputs**, not as proof that a game will succeed.

Reference-class selection should preserve at least:

```text
GameForm / player activity
Target platform + input
Session / progression shape
Solo / social / online burden
Production-team / content-scale comparability
Commercial or audience success evidence
Longevity / design maturity where relevant
Evidence availability for teardown
```

A globally successful game can be a design reference while being an invalid production baseline for a tiny team. Do not inherit AAA/MMO/live-service burden by popularity alone.

Source: https://partner.steamgames.com/doc/store/tags

### 1.2 Divergence and convergence

The Design Council Double Diamond remains a useful external process skeleton for divergent/convergent work. In Game's front half it is **subordinate to external reference evidence**: Discover includes finding and playing mature comparable products, not only generating internal concepts.

```text
Discover: external reference classes + audience/context + unresolved opportunity
Define: bounded baseline and learning question
Develop: reproduce + vary competing treatments
Deliver: evidence sufficient to enter G0, not a shipped product
```

Source: https://www.designcouncil.org.uk/our-resources/the-double-diamond/

### 1.3 Game-design analysis

MDA and other mature game-design lenses may be used as `REFERENCE_ONLY` teardown vocabulary. They help connect mechanics, resulting dynamics and player-facing aesthetics/experience, but no one lens becomes Game's product authority.

Source: https://aaai.org/papers/ws04-04-001-mda-a-formal-approach-to-game-design-and-game-research/

### 1.4 Prototype-led learning

Nintendo's published Echoes of Wisdom development interview is retained as a concrete industry precedent, not a universal standard: multiple gameplay directions were prototyped, played, and materially redirected after the team could verify features and feel. This supports the rule that gameplay evidence may overturn an apparently mature internal concept.

Source: https://www.nintendo.com/sg/interview/bdge/index.html

### 1.5 Human playtesting

Human evaluation uses the existing external-first Player Evidence routing: ISO 9241-210/9241-11 where HCD/usability applies, Games User Research practice for question-method fit, and platform-native playtest delivery where useful. A 2026 GDC small-team session also documents a lightweight repeatable 1-on-1 playtest practice centered on focused sessions, interviewing, actionable feedback and continuous iteration.

Sources:
- https://www.iso.org/standard/77520.html
- https://www.iso.org/standard/63500.html
- https://gamesuserresearch.com/choose-the-right-playtest-method/
- https://schedule.gdconf.com/session/playtesting-process-for-ultra-small-teams/913818

## 2. Front-half sequence

These are **profile steps**, not additional G-stages. Canonical product-stage semantics still begin at G0.

### R0 — Reference class

Question: **Which successful mature games are valid things for us to learn from?**

Do:
- construct a small stratified reference set rather than one favorite title;
- separate design success from production-scale comparability;
- record why each reference is relevant and what must not be inherited;
- include negative/nearby references when they distinguish the target mechanism.

Exit:
- at least one bounded comparable reference class exists;
- the learning question is clearer than an internal genre brainstorm;
- evidence of popularity is not being used as design authority by itself.

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

### R2 — Baseline reproduction / clone-to-learn

Question: **Can we reproduce the relevant mature interaction well enough to learn from it?**

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

### R3 — Human baseline validation

Question: **Did we reproduce the player-relevant effect we claim to be studying?**

Use mature playtest practice selected from the claim. For a feel, comprehension or meaning claim, synthetic Agents and browser completion are controls only.

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

### R4 — Controlled differentiation

Question: **What should we change, and does that change create a better or meaningfully different game for the intended player?**

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

## 3. G0 admission boundary

G0 does not ask whether Ordivon has invented something unprecedented. It asks whether the accumulated external-reference and player evidence justifies defining a specific game.

The G0 packet should therefore add to the existing Game Definition:

```text
ReferenceClass
RetainedMaturePatterns
DeliberateDifferences
BaselineEvidence
DifferentiationEvidence
KnownTransferLimits
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

Stop front-half method expansion when R0-R4 can route a real product into G0. Do not add another local discovery framework merely because one exists externally.

Reopen this profile when:
- a real product cannot be learned from or compared through reference/reproduction/playtest/variation;
- a mature external method materially changes;
- rights constraints make the assumed reproduction method invalid;
- a materially different game form demonstrates that the reference-first sequence introduces a systematic false negative;
- repeated products show a smaller profile can replace part of R0-R4 without losing decision quality.
