---
schema_version: 1
id: game.design-counterexample-memory.r1
title: Ordivon Game Design Counterexample Memory R1
profile: research
lifecycle: active
source_role: derived-evidence-navigation
visibility: public
owners:
  - ordivon-game
updated: 2026-09-18
summary: Source-grounded memory of rejected, removed, failed, cancelled, redesigned and conditionally successful game-development choices, retained as contextual counterexamples rather than anti-pattern law.
evidence_status: source-grounded-counterexample-hypotheses
readiness: ACTIVE_EXPANDING
---
# Ordivon Game Design Counterexample Memory R1

## Why this exists

A library built mostly from successful shipped forms has a structural bias: it can make historical survival look like design law.

Counterexample Memory asks the inverse questions:

```text
What looked reasonable but failed in context?
What succeeded on one local metric but damaged the larger product?
What was removed rather than polished?
What was cancelled after becoming playable?
What solution became too complex to enforce?
What old rejection became valid only after its premises changed?
What apparent constraint unexpectedly expanded the search space?
```

This is not an anti-pattern catalog and not a ranking of bad decisions. Failure is contextual evidence.

## Record shape

Each counterexample carries:

```text
assumption
  -> failure signal
  -> context
  -> revision / salvage
  -> transfer boundary
  -> false universalizations
  -> cheap discriminator
```

The two `falseUniversalizations` fields are mandatory because a failed approach can be abused just as easily as a successful one:

```text
"strict prevention became too complex here"
!=
"prevention is bad"

"a tutorial succeeded locally but misrepresented this product"
!=
"new-player feedback is misleading"

"an opaque interface contributed to one game's identity"
!=
"usability is unnecessary"
```

## Current high-value counterexamples

### Local success can still be global failure

Factorio's removed NPE/tutorial is useful because the developer account says it achieved many intended onboarding goals and received strong newcomer feedback, yet was still removed for product/demo-fit reasons. The lesson is not to ignore player evidence. It is to stop one proxy target from silently becoming the whole product target.

### Perfect prevention can lose to bounded prevention + recovery

Factorio's fluid-mixing history is a direct complexity counterexample. Making an almost-always-undesired state globally impossible accumulated edge cases across a legacy system. The eventual response targeted common accidental cases and added cheap recovery for the remainder.

### A useful secondary system can displace a core loop

Diablo III's Auction House provided real trade convenience, yet Blizzard later diagnosed it as undermining the kill-monsters-for-loot core and removed it while reworking itemization/rewards. This is an incentive-topology counterexample, not a universal argument against trading.

### Preproduction can create deletion debt

Deus Ex's large early character inventory had option value, but the postmortem also records characters becoming filler that designers were reluctant to cut after their purposes changed. Broad search is still useful; survival rights for search artifacts are the problem.

### Constraints do not only subtract

Psychonauts 2 provides a direct counterexample to the claim that constraints necessarily reduce creativity: its developer postmortem frames an empathy focus as expanding the design possibility space. The transferable question becomes whether a constraint creates new relationships/questions or only removes candidates.

## Relationship to Experience and Relationship Memory

```text
External Source
      ↓
Mechanism Experience
      ↓
Counterexample Memory
      ↓
cheap discriminator
```

Counterexamples do not replace the Mechanism Experience Library. They are a retrieval surface for experiences that attack over-broad assumptions.

Likewise, they do not create a closed mechanic ontology, recommendation engine, compatibility verdict, or creative gate. A completely novel mechanism remains open even when it has no historical counterexample match.

## Anti-capture rule

The desired learning loop is:

```text
historical failure
    -> weaken universal assumption
    -> name context
    -> design discriminator
    -> run new cheap probe

not

historical failure
    -> blacklist mechanism forever
```

The memory becomes more valuable as it accumulates contradictions, removals, reversals and failed prototypes—not because it can tell an Agent what game to make, but because it makes premature certainty harder.
