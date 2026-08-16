---
schema_version: 1
id: game.g-series.product-search
title: Ordivon Game G-Series Product Search
type: research
profile: product
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - builder
  - agent
  - producer
updated: 2026-08-16
summary: G1-G3 product-space search and candidate set for the first player-value-first Ordivon Game after Station Zero is reclassified as a reference experiment.
evidence_status: derived
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.g-series.reset
  - game.development-model
---
# Ordivon Game G-Series Product Search

## Search question

What game form makes Ordivon's strongest durable capability — authoritative worlds containing consequential autonomous actors — valuable to a player rather than merely impressive to an engineer?

The search does not ask which existing Game code is easiest to extend.

## External structural lessons

The benchmark set is used for design pressure, not feature copying.

### Duskers — uncertainty can be the interface

Remote sensors and unreliable equipment turn incomplete information into the player's actual job. The transferable law is that missing information is valuable only when the player can reason from evidence and act on that uncertainty.

### RimWorld — autonomous actors create stories when state persists

Psychology, relationships, injuries, work and world events matter because colonists persist and their history changes later possibilities. The transferable law is that autonomy becomes memorable when the player can recognize consequences in particular characters over time.

### Wildermyth — character history converts mechanics into attachment

Characters age, form relationships and receive permanent transformations. The transferable law is that persistence is not a database feature; it is valuable when the past becomes identity.

### The Alters — competence plus conflict creates dependency

The crew is operationally necessary, but individual members also carry incompatible histories and needs. The transferable law is that a subordinate becomes a character when the player needs their capability but cannot reduce them to a tool.

### Shadows of Doubt — autonomous inhabitants can make the world itself a puzzle

Citizens have independent routines and the player's job is to infer hidden truth from traces. The transferable law is especially compatible with Ordivon: authoritative World truth can remain separate from what each inhabitant knows, says and believes.

### Return of the Obra Dinn / Pentiment — deduction needs commitment and consequence

Investigation is valuable when the player must form and commit a model of events or people rather than merely reveal a canonical exposition path.

### Rain World / Alien: Isolation — an autonomous opponent can create fear without dialogue

The strongest lesson is negative for LLM-first design: adaptive or individualistic behavior can be valuable even when language and model calls are absent. If a deterministic/policy adversary creates the same experience, expensive cognition should be deleted.

## Candidate space

The first pass keeps six materially different forms.

| Candidate | Fantasy | Core value | Agent role | Main risk | Prototype burden |
| --- | --- | --- | --- | --- | --- |
| A — Delegated Crisis Command | command a capable team through a hostile crisis | responsibility under uncertainty | autonomous subordinates + adversaries | administrative UI overwhelms play | low; Station Zero exists |
| B — Social Detective | enter a living incident and infer who did what | curiosity, suspicion, deduction | witnesses/suspects with bounded knowledge, motives and memory | dialogue becomes exposition or random noise | low-medium |
| C — Last Companion | survive a journey with one person you need but do not control | trust, dependency, attachment, loss | persistent autonomous companion | attachment requires writing/expression quality | medium |
| D — Adaptive Predator | survive/explore while learning an intelligent threat | fear, pattern learning, mastery | adversary | cheaper policy may fully replace Agent cognition | low |
| E — Living Outpost | shape a small society without puppeteering each resident | stewardship, emergent story | autonomous inhabitants | scale/content/economy explodes before fun is proven | high |
| F — Creative Social World | build/perform with autonomous inhabitants and co-creators | expression, surprise, shared history | co-creators/inhabitants | product promise and moderation/content scope are too open | very high |

## G2 experience foundation

### A — Delegated Crisis Command / Station Zero baseline

**Fantasy:** I am responsible for a team I cannot and should not micromanage.

**Emotional core:** tension from commitment, incomplete information and accepting another actor's imperfect execution.

**Moment loop:** observe → set intent → inspect delegated plan → commit → interpret consequence.

**Return motivation:** master doctrine and encounter variation.

**Agent-value claim:** local autonomy changes execution enough to make delegation itself meaningful.

**Cheapest replacement:** deterministic tactical policy.

**Current concern:** the prototype already demonstrates that technically rich delegation can feel like configuration/review work. It stays as a baseline, not a presumed winner.

### B — Social Detective / working codename `Casefile`

**Fantasy:** I enter a small living social system after something has gone wrong and reconstruct truth from people who know different things and want different outcomes.

**Emotional core:** curiosity → suspicion → confidence → doubt → commitment.

**Moment loop:** inspect trace / question person → receive bounded testimony → connect or contradict evidence → spend limited attention → accuse or defer.

**Session arc:** one 10–20 minute incident with 4–8 persistent people and one authoritative hidden history.

**Return motivation:** different incidents, motives, relationships and evidence topologies produce different reasoning problems rather than shuffled answer keys.

**Agent-value claim:** inhabitants need independent bounded beliefs, memory, motive-sensitive disclosure and adaptation to prior questioning. If fixed dialogue trees produce equivalent deduction, Agent cognition should shrink.

**Strong Ordivon fit:** `World truth ≠ observation ≠ belief ≠ statement ≠ accusation` maps directly onto existing authority discipline without exposing engineering concepts to the player.

### C — Last Companion / working codename `Last Light`

**Fantasy:** cross a dangerous place with one companion whose competence I need and whose trust I can lose.

**Emotional core:** dependency, care, frustration, sacrifice.

**Moment loop:** read situation → choose plan/request → companion accepts, modifies or refuses → shared consequence → relationship/memory updates.

**Session arc:** short journey with irreversible resource and relationship consequences.

**Return motivation:** different companion dispositions, route pressures and remembered choices create distinct relationships.

**Agent-value claim:** autonomous judgment and memory must produce meaningful negotiation/trust that direct player control cannot.

**Main falsifier:** if players prefer the puppet baseline or interpret refusals as arbitrary friction, reject or radically redesign.

### D — Adaptive Predator / working codename `Echo Hunt`

**Fantasy:** enter a hostile structure with a threat that is also learning me.

**Emotional core:** dread, inference, cleverness, relief.

**Moment loop:** move/listen/bait/hide → receive partial sensory evidence → infer threat pattern → take risk → survive consequence.

**Session arc:** 5–10 minute extraction run.

**Return motivation:** procedural layout plus adversary doctrine creates new inference problems.

**Agent-value claim:** adaptation to the player's behavior materially changes suspense and strategy.

**Main falsifier:** a small deterministic adaptive policy is likely sufficient. This candidate is deliberately retained as a control against the assumption that model cognition is required.

### E — Living Outpost

High long-term fit with the Ordivon vision, but rejected from the first cheap prototype wave. Its value depends on many interacting systems, persistent content and long observation windows; a poor prototype can fail because of missing scale rather than because the concept is bad.

**Status:** defer, do not delete.

### F — Creative Social World

Potentially high long-range fit but the product promise is too unconstrained for the first true product. It risks requiring content generation, moderation, multiplayer/social policy and creative tooling before one repeated core desire is proven.

**Status:** defer, do not delete.

## G3 survivors

The first prototype wave contains three new concepts plus Station Zero as an existing baseline:

```text
A  Station Zero / Delegated Crisis Command      baseline
B  Casefile / Social Detective                 build cheap falsifier
C  Last Light / Persistent Companion           build cheap falsifier
D  Echo Hunt / Adaptive Predator               build cheap falsifier + cognition control
```

E/F remain opportunity-space records only.

## G4 falsifier contract

All three new treatments must be playable from one browser Concept Lab and deliberately share only presentation scaffolding. Their game state and rules remain concept-local.

Each treatment must establish at minimum:

1. the player can understand the immediate goal without architecture documentation;
2. at least three decisions have visibly different consequences;
3. hidden/autonomous state affects play but is not shown as debug truth;
4. the session can end in at least two materially different outcomes;
5. resetting creates a meaningfully different reasoning problem or trajectory;
6. the Agent/autonomy mechanism has an explicit cheaper baseline mode;
7. the prototype can be deleted without touching Station Zero or a shared Game platform.

## G5 selection rubric

A prototype may advance only if evidence is promising across all four groups:

### Immediate play

- player can identify what to do next;
- choices are not mostly configuration;
- consequence arrives soon enough to teach;
- uncertainty creates inference rather than confusion.

### Desire

- the session creates anticipation before commitment;
- outcomes create relief, regret, surprise, attachment or mastery;
- another run has an understandable reason to exist.

### Agent value

- autonomous behavior is legible enough to learn;
- autonomy creates a value unavailable in the cheapest baseline;
- model cognition is not assumed when policy cognition suffices.

### Production viability

- one satisfying content unit is cheap enough to author/test;
- expression requirements are identifiable;
- scaling does not require a universal platform before the first product exists.

Machine/Agent evaluation can eliminate structurally weak candidates. Human/fresh-player delight and replay claims remain unproven until actual player evidence exists.
