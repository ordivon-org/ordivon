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

Current R1 contains **44 counterexamples across 28 reference projects**, including AI architecture failures, cancelled projects, multiplayer/social-system boundaries, economy and currency rollbacks, procedural-generation rewrites, shipped-product relaunches, live-service rollbacks, foundation reversals, late rewrites, planning-process failures, product-viability mismatches and cases where useful work was salvaged after cancellation.

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

### A good local game can still have the wrong operating model

The Last of Us Online is retained because Naughty Dog reported a concept whose gameplay was becoming more refined and satisfying, yet whose multi-year live-service support burden would have redirected the whole studio. The counterexample separates local gameplay progress from sustainable studio/product topology.

### Old visions can outlive the premises that created them

Overwatch's Hero Missions history is retained as a legacy-vision counterexample: the team connected years of PvE/MMO ambition back to Project Titan, later judged that scope and resource diversion were no longer working, and cut Hero Missions rather than continue treating the old crawl-walk-run plan as destiny.

### Fixing the game side does not prove product viability

Artifact Foundry is retained because Valve reported achieving most game-side reboot goals while still lacking enough active players to justify further development. Gameplay, acquisition, activation, retention and sustainable concurrency remain separate evidence lanes.

### Shipped foundations are not automatically permanent

Final Fantasy XIV's relaunch and Destiny 2: Forsaken's weapon/ammo foundation rewrite are retained as different-scale counterexamples to shipped-state permanence. One replaced a failed product-level foundation; the other migrated a live combat taxonomy. Neither implies that rewriting foundations is generally preferable to local repair.

### Content cadence can yield to substrate health

Rainbow Six Siege's Operation Health is retained because Ubisoft explicitly delayed content, reduced map output and added staged deployment/rollback capacity. This conditions the assumption that a live service must preserve content cadence even while release/substrate failure accumulates.

### Social freedom can externalize coordination cost

Overwatch's Role Queue history is retained as a paired counterexample. Open role selection maximized local flexibility but pushed composition bargaining into a short social window; fixed role ratios reduced that burden but then exposed queue throughput to unequal role populations. The useful unit is not “free versus fixed roles” but where coordination cost is paid.

### Multiplayer can be architectural rather than additive

Subnautica is retained because co-op was considered early, deferred for schedule reasons, and later judged expensive enough to affect nearly everything. This does not make multiplayer a mandatory day-one commitment; it makes late multiplayer a hypothesis that should be tested against state authority, persistence, interaction conflict and reconnect costs.

### Currency friction must earn a decision role

Destiny 2's Unstable Cores are retained because Bungie explicitly judged them restrictive without producing interesting buildcraft decisions. Legendary Shard deprecation supplies a different economy boundary: a mature universal currency can become compatibility/balance baggage when newer systems no longer need the same abstraction.

### Procedural abstraction can fail in both directions

Factorio supplies both sides. Its noise compiler removed an over-clever procedure/deduplication abstraction when dependency machinery outweighed the reuse; elsewhere its fragmented terrain/resource placement representations were unified because cross-cutting generation constraints were hard to express. “Simpler” and “more unified” are therefore context-dependent responses, not opposing laws.

### AI capability can arrive before its requirement

Deus Ex and Thief are retained as requirement-timing counterexamples. Both projects began important AI work before the eventual interaction requirements were sufficiently stable. Deus Ex accumulated unnecessary features and adaptation around a shooter-oriented foundation; Thief later concluded that its early decision architecture did not fit the stealth game it had become. The transferable question is not whether AI should start early, but whether early work is bound to a stable observation/action/consequence contract.

### Rewrite aversion can become its own failure mode

Thief is also retained because the team initially interpreted repeated AI problems as bugs in an otherwise sound architecture and only later replaced most of it. This does not make rewrites preferable. It makes repair-versus-replacement a dependency-closure question rather than a standing cultural rule.

### Multiple AI systems need an explicit consequence-authority boundary

Assassin's Creed Odyssey is retained because Meta AI and the high-LOD GOAP planner could both try to drive the same NPC near subsystem boundaries. The counterexample does not require one global AI system; it asks whether more than one system can commit overlapping behavior without an explicit handoff.

### Migration can preserve the coupling it was meant to remove

Odyssey's GOAP migration is retained because wrapping complex legacy behaviors as planner Actions preserved production continuity but violated the new system's intended modularity and leaked game-specific concepts into blackboards/core code. Interface conformity is therefore not sufficient evidence of decoupling.

### Planner optimizations must preserve planner invariants

Immortals Fenyx Rising supplies two different counterexamples. Dynamic re-evaluation turned random action-cost noise into an inconsistent scoring mechanism, while aggressive nearest-object pre-pruning could discard candidates whose value only became clear in later plan steps. These records condition random variety and local pruning; they do not blacklist either technique.

### Architectural convergence has a timing problem

Odyssey's attempt to put multiple AI pillars under one planner is retained as a premature-convergence case: naval AI and the shared planner evolved in parallel, so the common capabilities were not ready when consumers needed them. The counterexample favors proving a shared contract before mandating a single pipeline, not permanent specialization.

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
