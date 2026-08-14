---
schema_version: 1
id: game.product.station-zero-v3.product-value
title: Station Zero v3 — G4 Product Value Research
profile: product
lifecycle: accepted
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - builder
  - agent
  - producer
updated: 2026-08-15
summary: Comparative product-design research for Station Zero v3. Decomposes mature structural analogues, derives transferable laws and incompatible choices, maps Station Zero strengths/gaps, and defines falsifiable G4-V experiments before G5 Production.
evidence_status: verified
readiness: READY
applies_to:
  - station-zero-v3-unregistered
related:
  - game.product.station-zero-v3
  - game.product.station-zero-v3.vertical-slice
  - game.development-model
  - game.authority
---
# Station Zero v3 — G4 Product Value Research

## Status

This document owns the **comparative product-value lane** inside Station Zero v3 G4.

It does not replace:

- `STATION_ZERO_V3_PRODUCT.md` for stable product identity;
- `STATION_ZERO_V3_VERTICAL_SLICE.md` for the current production slice and machine UX/perception gate;
- P0–P3 for exact World, reducer, persistence, planning, and browser contracts.

The purpose of this lane is to answer a different question:

```text
Why should this particular command game be worth producing,
not merely why its current implementation is valid?
```

The primary evidence is not a tiny preference poll. Mature products have already explored many of the same structural pressures at real product scale. We first study those design spaces, derive bounded hypotheses, and then falsify the hypotheses on Station Zero itself.

Human play remains important later, but it tests the resulting Station Zero claims; it does not invent the product thesis for us.

---

# Evidence hierarchy

Use this order:

```text
L1  Comparable product structure
    What do mature products actually make the player do?

L2  Design pressure / tradeoff
    What problem is that structure solving, and what does it sacrifice?

L3  Station Zero transfer hypothesis
    Why should the pressure apply here?

L4  Controlled Station Zero experiment
    Does our current game actually exhibit the intended value?

L5  Human behavioral evidence
    Do target players understand/use the resulting structure as predicted?

L6  Market evidence
    Replay, retention, recommendation, purchase, and longer-term demand.
```

Do not jump from `L1` directly to feature copying, and do not treat `L5` preference votes as a substitute for `L1–L4` reasoning.

---

# Comparison axes

Products are compared by shared **design pressure**, not by genre label.

| Axis | Question |
| --- | --- |
| Player fantasy | Who is the player pretending to be, and what responsibility sells that fantasy? |
| Direct control | What can the player command exactly? |
| Autonomy boundary | What does a subordinate/system decide without player micromanagement? |
| Information topology | What is known, hidden, stale, inferred, or actively acquired? |
| Planning / commit timing | When can decisions be revised, and when do consequences become irreversible? |
| Consequence model | What can be lost: position, time, people, resources, information, campaign state? |
| Explanation / feedback | How does the player build a correct causal model after execution? |
| Pressure / pacing | What prevents infinite safe optimization and gives each decision context? |
| Waiting / execution | What happens between decision and consequence, and why is that time valuable? |
| Actor identity | Why does one subordinate feel mechanically/behaviorally different from another? |
| Content grammar | What dimensions create meaningfully different missions rather than cosmetic variation? |
| Replay loop | Why is another run strategically different? |
| Expression burden | Which UI/audio/animation choices actually carry game semantics? |
| Production burden | What content/system costs dominate at scale? |

---

# Primary benchmark set

## Frozen Synapse — precise WEGO commitment

**Structural role:** strongest analogue for `plan → test → commit → simultaneous execution`.

Its product surface gives detailed orders, lets the player test planned movement, then commits both sides to simultaneous execution. It combines a large authored campaign with skirmish generation and random + hand-authored map/content structure.

**Pressure-tested lesson:** remove uncertainty about the rules and your own intended plan, but preserve uncertainty about the opponent. Commit becomes tense because the player understands what *their* plan means without knowing exactly what the enemy chose.

**Do not copy:** detailed per-unit waypoint scripting. Station Zero intentionally delegates local execution.

**Question for Station Zero:** does Plan Preview make the consequences of *our delegated plan* legible enough that uncertainty comes from the hostile World/enemy commitment rather than from not understanding our own Agents?

Sources:
- https://store.steampowered.com/app/98200/Frozen_Synapse/

---

## Phantom Brigade — prediction is not enough

**Structural role:** strong analogue for prediction/timeline planning followed by cinematic simultaneous execution.

The product exposes future enemy movement on a timeline, lets the player compose timed counter-actions, then executes the result as real-time physics. Its later 2.0 work expanded mission generation, overworld variety, pilot identity, damage prediction, and campaign structure.

The important negative lesson is as valuable as the mechanic: the original release was praised for visual execution and the prediction system, yet reviews identified weak/repetitive opposition, repetitive missions, and shallow pilot/story identity as limits on long-term product value. A sophisticated signature mechanic did not substitute for opponent quality, actor attachment, or content grammar.

**Question for Station Zero:** are Agent cognition and deterministic consequence merely an impressive execution trick, or are enemy behavior, specialist identity, and encounter grammar strong enough to sustain repeated play?

Sources:
- https://store.steampowered.com/app/553540/Phantom_Brigade/
- https://www.pcgamer.com/phantom-brigade-review/
- https://www.pcgamer.com/games/strategy/this-mech-themed-xcom-like-just-got-a-gargantuan-update-that-overhauls-its-campaign-redesigns-its-overworld-and-adds-personalities-to-pilots-with-over-100-unique-traits/

---

## Radio Commander — information is a command responsibility

**Structural role:** strongest analogue for commander distance, incomplete battlefield knowledge, and reports-as-interface.

The commander does not receive an omniscient battlefield. Situation reports arrive through radio; the strategic map is an operational notebook. Units are differentiated by statistics, voices, personalities, morale, supplies, and stamina. The player can ask units for their location and must maintain a useful situation picture.

**Pressure-tested lesson:** partial information is valuable when the player has a *job* created by that information boundary. Uncertainty is not merely missing pixels; requesting, recording, trusting, and updating reports is part of being the commander.

**Do not copy:** manual coordinate bookkeeping for its own sake. Station Zero already has authoritative faction Knowledge and should not add clerical friction without product value.

**Question for Station Zero:** does bounded Knowledge change command inference and risk, or does the UI simply auto-project fewer facts while leaving the player intellectually passive?

Sources:
- https://store.steampowered.com/app/871530/Radio_Commander/
- https://www.pcgamer.com/ive-misplaced-all-my-soldiers-in-strategy-sim-radio-commander/

---

## Duskers — interface can embody uncertainty

**Structural role:** strongest analogue for remote command, unreliable sensing, and interface-as-fantasy.

Motion sensors may indicate that *something* exists without identifying it. Drone cameras degrade. Resources and tools fail. The command-line/wireframe presentation holds the player at a deliberate distance from the dangerous space.

**Pressure-tested lesson:** information deprivation can be product value when every sensory limitation is coherent with the role and teaches the player to interpret evidence. Better UX does not always mean revealing more.

**Do not copy:** a command line. The relevant mechanism is epistemic distance, not typing syntax.

**Question for Station Zero:** are `confirmed / estimated / stale`, last-known positions, scans, and sealed plans meaningful evidence the player reasons about, or merely technical metadata around a conventional tactical map?

Sources:
- https://store.steampowered.com/app/254320/Duskers/
- https://www.wired.com/2016/05/duskers-review/

---

## Door Kickers 2 — tactical depth needs expressive doctrine

**Structural role:** analogue for readable planning, pause/rethink/execute flow, non-linear mission space, and doctrine differentiation.

The player can pause at will, draw detailed plans, reconsider them during action, select genuinely different unit organizations, and attack non-linear/destructible levels. The product supports handcrafted missions plus generated campaigns, random mission generation, an editor, and Workshop content.

**Pressure-tested lesson:** tactical depth is not the number of buttons. It comes from an expressive action/doctrine language acting on spaces that admit meaningfully different plans. Unit organizations must produce different play, not cosmetic loadouts.

**Do not copy:** per-unit route scripting; it would collapse Station Zero's delegation thesis.

**Question for Station Zero:** does the Commander Order have enough *causal bandwidth* to express different doctrines while local Agents retain autonomy? Which current controls materially change behavior, and which are configuration noise?

Sources:
- https://store.steampowered.com/app/1239080/Door_Kickers_2_Task_Force_North/

---

## Aliens: Dark Descent — delegation through visible competence

**Structural role:** strongest analogue for squad-level command, automatic best-fit execution, specialist classes, and persistent consequence.

The player commands the squad as one unit. The Squad Behavior System automatically dispatches orders to appropriate Marines. Time can be slowed for tactical decisions. Health, stress, permanent death, classes, persistent levels, extraction, and between-mission recovery make squad competence and loss matter beyond one local action.

**Pressure-tested lesson:** delegation feels intentional when the player can predict *why this subordinate is the right one* without selecting every hand movement. Identity is reinforced by role competence plus persistent consequence.

**Question for Station Zero:** can the player predict Engineer/Medic/Security behavior from their roles and understand why an Agent chose an action, or are they visually distinct wrappers around nearly identical candidate selection?

Sources:
- https://www.focus-entmt.com/en/news/a-deep-look-into-aliens-dark-descent-with-its-gameplay-overview-trailer
- https://store.steampowered.com/app/1150440/Aliens_Dark_Descent/

---

## Invisible, Inc. — pressure needs predictable context

**Structural role:** strongest analogue for turn-by-turn pressure that gives every action a wider consequence.

The alarm/security system rises every turn and through player actions. Klei's design goal was a tight game about tough decisions. An earlier alarm implementation failed experientially because players could not tell when consequences would arrive and the consequences were too unpredictable; the eventual system used clearer discrete levels, visible thresholds, and contextualized consequences.

**Pressure-tested lesson:** a pressure meter is not valuable because it increases. It is valuable when it changes the context of every choice *and* communicates the next meaningful threshold clearly enough to support planning.

**Question for Station Zero:** do Turn budget, Oxygen, Reactor Heat, Alert, Biomass, and hazards produce readable strategic urgency before damage/terminal failure, or are they mostly numbers that matter only after crossing hidden thresholds?

Sources:
- https://store.steampowered.com/app/243970/Invisible_Inc/
- https://www.gamedeveloper.com/design/game-design-deep-dive-alarm-systems-in-klei-s-i-invisible-inc-i-

---

# Secondary benchmark

## RimWorld / colony-sim lineage — autonomy consumes attention

RimWorld is explicitly built as an AI-storyteller colony sim: colonists have moods, needs, wounds, relationships and other persistent internal state. It is not a close analogue for Station Zero's Turn loop, but it is useful for the indirect-control problem.

**Transferable lesson:** autonomous actors produce value only when their behavior is legible enough for the player to form expectations and stories. Simulation complexity that never changes player attention or interpretation is production cost without product value.

**Question for Station Zero:** does Agent autonomy create recognizable, persistent behavior and emergent responsibility, or does the player merely observe model-selected actions behind a formal authority system?

Source:
- https://store.steampowered.com/app/294100/RimWorld/

---

# Cross-product design map

Legend:

```text
HIGH       central product value
MEDIUM     important supporting structure
LOW        deliberately limited
N/A        not a meaningful product axis
```

| Product | Delegation | Partial info | Plan/commit | Own-plan preview | Opponent uncertainty | Per-turn pressure | Actor persistence | Content grammar | Interface-as-fantasy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Frozen Synapse | LOW | MEDIUM | HIGH | HIGH | HIGH | MEDIUM | LOW | HIGH | MEDIUM |
| Phantom Brigade | LOW | LOW | HIGH | HIGH | LOW | MEDIUM | MEDIUM | HIGH after 2.0 | MEDIUM |
| Radio Commander | HIGH | HIGH | LOW | LOW | HIGH | MEDIUM | HIGH | MEDIUM | HIGH |
| Duskers | MEDIUM | HIGH | MEDIUM | LOW | HIGH | HIGH | HIGH | HIGH | HIGH |
| Door Kickers 2 | LOW | MEDIUM | MEDIUM | HIGH | MEDIUM | MEDIUM | MEDIUM | HIGH | MEDIUM |
| Aliens: Dark Descent | HIGH | MEDIUM | LOW | LOW | MEDIUM | HIGH | HIGH | HIGH | HIGH |
| Invisible, Inc. | LOW | HIGH | LOW | HIGH | MEDIUM | HIGH | HIGH | HIGH | MEDIUM |
| RimWorld | HIGH | MEDIUM | LOW | LOW | HIGH systemic | MEDIUM | HIGH | HIGH | HIGH systemic |
| **Station Zero v3** | **HIGH** | **HIGH** | **HIGH** | **MEDIUM/HIGH** | **HIGH** | **UNPROVEN** | **MEDIUM within encounter** | **MISSING beyond one encounter** | **UNPROVEN** |

No benchmark above owns the exact Station Zero combination. That is promising, but novelty alone is not value.

---

# Convergent design laws

## Law 1 — Commit tension needs *selective* uncertainty

Across Frozen Synapse, Phantom Brigade, Radio Commander and Duskers, tension is produced by controlling which uncertainty is removed and which remains.

```text
Good:
understand your own intent / rules
+ cannot fully know hostile future
→ responsibility at Commit

Bad:
do not understand your own plan
+ do not understand consequences
→ confusion at Commit
```

**Station Zero hypothesis:** deterministic World authority and exact own-Plan Preview should remove self/rule ambiguity; sealed enemy plans and bounded Knowledge should preserve hostile uncertainty.

---

## Law 2 — Information asymmetry must create player work

Radio Commander makes the commander maintain a picture from reports. Duskers makes ambiguous sensors and degraded feeds into evidence the player interprets.

**Station Zero hypothesis:** faction Knowledge only has product value if scans, confidence, last-known contacts, stale evidence, and report provenance cause materially different Commander choices. Merely hiding current enemy coordinates is insufficient.

---

## Law 3 — Delegation needs visible competence

Aliens: Dark Descent automatically assigns suitable squad members to actions; colony sims rely on persistent actor characteristics; Radio Commander distinguishes subordinate units as people and capabilities.

**Station Zero hypothesis:** Engineer/Medic/Security must have predictably different *behavioral signatures*, not just different names/icons. A player should learn what each specialist is likely to contribute without issuing local actions directly.

---

## Law 4 — Pressure must transform decisions before failure

Invisible, Inc. deliberately ties alarm progression to every turn, but also found that unclear thresholds and unpredictable consequences made the system feel unfair rather than tense.

**Station Zero hypothesis:** Oxygen, Heat, Alert, Biomass and the 20-Turn budget must visibly change the value of actions *before* terminal damage. If the optimal Commander decision remains unchanged until a hidden threshold fires, the pressure layer is under-designed.

---

## Law 5 — Command depth is causal bandwidth, not control count

Door Kickers 2 gets depth from expressive plans and materially different doctrines. Station Zero cannot copy detailed path scripting without giving up delegation.

**Station Zero hypothesis:** each high-level control should change Agent choice or strategic outcome in relevant states. Controls with little marginal leverage are configuration noise; missing high-leverage doctrine dimensions are a product gap.

---

## Law 6 — A signature mechanic cannot carry weak content indefinitely

Frozen Synapse surrounds its simultaneous-turn mechanic with campaign/modes/generation. Door Kickers 2 combines authored missions with generators/editor/Workshop. Invisible, Inc. varies locations, threats, loot and builds. Phantom Brigade is the strongest cautionary example: its prediction/execution mechanic made a strong first impression, but repetitive missions, exploitable opposition and shallow identity materially limited the original product and motivated a broad 2.0 campaign/content overhaul.

**Station Zero hypothesis:** Agent cognition is not a content grammar. Before G5, we must identify which encounter variables generate distinct strategic problems and which merely reshuffle the same solution.

---

## Law 7 — Interface friction is justified only when it embodies the role

Radio Commander and Duskers deliberately withhold conventional omniscient control because the operational interface *is part of being that commander/operator*.

**Station Zero hypothesis:** Mission Control should feel like an operational command surface, but any friction must create command meaning. Generic web-form friction, manual bookkeeping without inference value, or model latency without dramatic/decision value should be removed rather than romanticized.

---

# Important incompatible choices

Convergence is not universal. Some benchmark choices are mutually exclusive.

## Full future prediction vs bounded enemy uncertainty

Phantom Brigade exposes enemy future actions; Frozen Synapse preserves opponent-plan uncertainty; Station Zero currently seals enemy Plans.

Station Zero deliberately chooses:

```text
predictable World rules
+ legible own delegated Plan
+ bounded current Knowledge
+ sealed hostile commitment
```

Do **not** add a Phantom-Brigade-style enemy future timeline unless evidence shows this uncertainty prevents meaningful planning. Doing so would erase part of the product thesis.

## Direct tactical scripting vs delegated local execution

Frozen Synapse and Door Kickers let players author local execution in detail. Aliens: Dark Descent and Station Zero deliberately compress local control.

Station Zero chooses delegation. Therefore improvement should target **doctrine bandwidth and Agent legibility**, not waypoint scripting.

## Manual information maintenance vs authoritative projection

Radio Commander turns manual map maintenance into commander responsibility. Station Zero currently auto-projects authoritative faction Knowledge.

Station Zero should not copy clerical map maintenance by default. A better transfer target is **evidence provenance and confidence-aware inference**: why is this contact believed to be here, how old is that evidence, and what command decision changes because of it?

---

# Station Zero value map

Status labels:

```text
STRONG                  already supported by direct game evidence
WEAKER THAN BENCHMARK   structural analogue exposes a current shortfall
DELIBERATELY DIFFERENT  different choice is part of product thesis
UNPROVEN DIFFERENTIATOR promising unique structure, value not yet established
MISSING                 required product layer absent at current G-stage
```

| Axis | Current status | Judgment |
| --- | --- | --- |
| Authoritative plan→commit→consequence | STRONG | G3/G4 proves exact Plan, Commit, deterministic resolution and Aftermath continuity. |
| Hostile uncertainty | STRONG | bounded Knowledge + sealed enemy Plans survive live Provider evaluation. |
| Delegated local execution | STRONG mechanically | Agent/fixture choice is real and bounded; G3 proves different strategy realization. |
| Commander doctrine bandwidth | UNPROVEN | objective/posture/formation matter, but the marginal value of the full control set is not yet measured. |
| Information as command responsibility | WEAKER THAN BENCHMARK | Knowledge is bounded but mostly auto-projected; player inference/provenance work is much weaker than Radio Commander/Duskers. |
| Pressure curve | UNPROVEN | many pressure resources exist, but product evidence has not shown they transform decisions before threshold effects. |
| Specialist behavioral identity | UNPROVEN | role equipment/abilities and visual identity exist; behavior-level recognizability is not yet measured. |
| Waiting/execution tension | UNPROVEN DIFFERENTIATOR | live deliberation is truthful and bounded, but whether latency becomes meaningful command suspense is unproven. |
| Opponent quality | UNPROVEN | Pirate/Swarm pressure is sufficient for current viability tests; long-run exploitability/behavioral variety is not established. |
| Content grammar | MISSING | one encounter proves the loop but does not define a repeatable mission grammar. |
| Cross-run actor persistence | DELIBERATELY DEFERRED | current product proves encounter-local identity; campaign attachment is a later choice, not a G4 prerequisite. |
| Interface-as-fantasy | WEAKER THAN BENCHMARK | current tactical instrument panel is structurally good but still resembles a web command form more than a role-defining Radio Commander/Duskers interface. |
| Replay value | MISSING beyond strategy matrix | three non-dominated strategy signatures exist inside one encounter; repeatable content variation is undefined. |

---

# G4-V2 experiment backlog

These are **research experiments**, not authorized features.

## V2-A — Commander Control Leverage Audit

**Benchmark pressure:** Door Kickers 2 doctrine expressiveness; Aliens: Dark Descent compressed squad command; colony-sim attention economy.

**Question:** does every player-facing Commander control have meaningful causal leverage?

Perturb independently where legal:

```text
primary objective
posture
formation
retreat threshold
lethal force
collateral policy
loot policy
protected Actor
priority target
Commander directive
```

Measure:

- selected Rescue Candidate changes;
- semantic action/tag changes;
- objective/front progress;
- casualties/extraction;
- pressure-state outcome;
- final faction result.

**Falsifier:** a control repeatedly changes neither local decisions nor relevant outcomes across states where its description says it should matter.

**Action if falsified:** prune, merge, contextualize, or redesign the control. Do not keep decorative configuration merely because the schema supports it.

---

## V2-B — Information-as-Command Audit

**Benchmark pressure:** Radio Commander + Duskers.

**Question:** does acquired/stale information materially alter feasible/reasonable command behavior?

Compare exact runs with and without objective-relevant scan information. Retain:

- discovered Zones;
- contact confidence and age;
- last-known position;
- Candidate-set changes;
- selected action changes;
- objective progress/time cost.

**Falsifier:** information state changes while Agent/Commander-relevant decisions remain effectively identical.

**Potential product response:** surface evidence provenance/age/uncertainty where it changes decisions. Do not add manual map bookkeeping unless inference value specifically requires it.

---

## V2-C — Pressure Curve Audit

**Benchmark pressure:** Invisible, Inc.

**Question:** do Turn, Oxygen, Reactor Heat, Alert and Biomass create escalating tradeoffs before terminal punishment?

For representative viable strategies record each Turn:

- pressure values and deltas;
- next visible threshold/consequence if known;
- damage/system/hazard effects;
- Candidate availability/selection;
- objective opportunity cost.

**Falsifier:** resources move numerically but do not change decision opportunity or consequence until an abrupt threshold/damage event.

**Potential product response:** improve pressure coupling or threshold forecastability; do not merely add more meters.

---

## V2-D — Specialist Behavioral Identity Audit

**Benchmark pressure:** Aliens: Dark Descent + autonomous-actor games.

**Question:** can Engineer, Medic and Security be recognized from what they are competent to do and what they choose in relevant contexts?

Measure across deterministic contexts:

- candidate tag distributions;
- role-unique abilities available/selected;
- responsibility ownership;
- selected action semantic distributions;
- action/outcome contribution to mission fronts.

**Falsifier:** specialists choose near-identical semantic action distributions even when role-specific opportunities are present, or the product gives no visible reason why one specialist handled an action.

---

## V2-E — Deliberation / Execution Value Audit

**Benchmark pressure:** Frozen Synapse commit suspense, Radio Commander order/report delay, Duskers uncertainty.

Machine evidence can require:

```text
World frozen
hostile plans sealed
relevant unresolved contacts/fronts remain visible
no fake percentage progress
Preview returns genuinely new actionable commitment information
```

Human evidence is still needed for the final claim:

```text
"the wait feels like my team is deliberating under uncertainty"
vs
"the model is loading"
```

Do not optimize latency presentation by exposing fake progress or hidden chain state.

---

## V2-F — Content Grammar Definition

**Benchmark pressure:** Frozen Synapse, Door Kickers 2, Invisible, Inc., Phantom Brigade 2.0.

Before authoring mission two, enumerate candidate variation dimensions:

```text
initial Knowledge
objective combination
Zone/passsage topology and choke structure
extraction geometry/capacity
civilian / objective-item placement
system / hazard coupling
enemy doctrine / faction pressure
Commander resources
specialist loadout
Turn budget
```

**Falsifier for a content dimension:** changing it produces the same dominant strategy, action semantics and outcome signature across the relevant matrix.

Only dimensions that create a different decision problem belong in the future production grammar.

---

# G4-V3 empirical audit results

The first canonical Product Value evaluator is:

```text
pnpm eval:v3:product-value
```

It combines same-World counterfactual Preview perturbation, same-seed information pairs, relevant-state contingency probes, representative 20-Turn pressure traces, and specialist semantic-distribution analysis.

## Commander control leverage

Across 20 exact baseline World states, one-control counterfactual Preview probes produced:

| Control | Relevant evidence | Product judgment |
| --- | ---: | --- |
| primary objective | 39 / 40 Agent selections changed | **high-leverage doctrine** |
| posture | 3 / 40 changed | **narrow doctrine modifier** |
| formation | 2 / 20 changed | **narrow locally, but G3 outcome matrix proves strategic consequence** |
| lethal force | 4 / 40 changed | **contextual contingency** |
| protected specialist | 1 / 13 natural probes changed | **contextual contingency** |
| Commander directive | 19 / 20 changed direct Commander action | **real direct command channel** |
| retreat threshold | 0 / 20 baseline probes | required relevant-state audit |
| priority target | 0 / 19 baseline probes | required relevant-state audit |
| loot policy | 0 / 40 baseline probes | required relevant-state audit |
| collateral policy | 0 / 20; no World/candidate collateral semantic exists | **not a current player control** |

The relevant-state audit then separated narrow controls from dead surface:

```text
retreat threshold
  relevant extraction/health states: 8
  changed decision:                  7
  → OBSERVED_CONTEXTUAL_LEVERAGE

priority target
  multi-target attack contexts:      63
  changed decision:                  22
  → OBSERVED_CONTEXTUAL_LEVERAGE

loot policy
  optional pickup contexts:          46
  ignore ↔ opportunistic changes:     0
  → RELEVANT_STATE_NO_LEVERAGE
```

**Product decision:** the browser no longer surfaces Loot policy. The exact Order field remains internal and is retained at `mission-only`; a future content grammar may re-admit it only after optional loot creates measured decisions. Collateral remains an internal exact field but is not a current player control because the World has no AoE/friendly-fire/collateral consequence to govern.

This is the intended attention hierarchy:

```text
Mission doctrine
  primary objective
  posture
  formation

This Turn
  remote capability

Standing contingencies
  lethal force
  retreat threshold
  protected specialist

Internal / not currently surfaced
  loot policy = mission-only
  collateral policy
  priority target (mechanically real, not yet exposed in current browser)
```

## Information-as-command evidence

Objective-relevant first-Turn scans produced different results because information value depends on what the delegated team would otherwise discover:

- `scan-life-support` changes immediate bounded Knowledge and the next Planning surface;
- `scan-maintenance` changes immediate bounded Knowledge and the next Planning surface;
- `scan-reactor` produces valid scan facts, but under the Core doctrine Engineer naturally enters Reactor during the same committed Turn and reveals the same sector. The scan therefore has **zero marginal information value in that specific doctrine/state**, not a broken implementation.

A deeper timing result matters more: Commander scans resolve during the committed Turn. They cannot retroactively alter the Preview that was already generated. Their information belongs to the **next Planning Head**. G4 copy now states this explicitly.

This is a deliberate current timing choice:

```text
Order + bounded Knowledge
→ Agent deliberation / Preview
→ Commit
→ scan + all-faction resolution
→ new Knowledge
→ next Planning Head
```

Do not describe scans as pre-Preview reconnaissance unless that lifecycle is intentionally redesigned later.

## Pressure and Cooling evidence

Three representative 20-Turn strategies all cross real planning and damage thresholds. Reactor Heat is particularly aggressive: baseline trajectories reach `100` by Turn 5 and remain in the red zone for most of the encounter.

The first intervention pair showed that `Power Cooling` alone did not help at Genesis because Cooling begins at `0.58` integrity while operational cooling requires `>= 0.60`. This initially looked like a false affordance. A canonical admitted-action causal probe then established the actual mechanism:

```text
Turn 3 start
  Heat                 78
  Cooling integrity    0.58
  Cooling powered      false

Commander
  Power Cooling

Engineer
  Field-repair Cooling

Same Turn resolution
  integrity            0.58 → 0.78
  powered              false → true
  Heat                 78 → 70

Next Turn
  Heat                 70 → 62
```

Therefore the World rule is **not** changed. The Product Value defect was information/coordination: Mission Control previously knew only the system ID and could not reason about the 60% operational prerequisite.

G4 now retains bounded known-system condition:

```text
systemId
observedIntegrity
observedPowered
observedAtTurn
```

The snapshot is established when a system is legitimately revealed. Existing known-system telemetry semantics also refresh it when a visible `system_changed` fact is received. Observation digests include this bounded condition. Mission Control shows last-confirmed condition and `Power Cooling` explains that power alone cannot cool below 60% integrity.

The pressure design remains intentionally hard. What is now proven is that the player has a coherent intervention chain rather than a silent no-effect button. Whether the Heat ramp is ultimately too dominant remains a later balance/value question, not a missing-causality defect.

## Specialist behavioral identity

A full deterministic Rescue run produced a maximum pairwise selected-tag Jaccard similarity of only:

```text
0.476190476
```

Security strongly concentrates on `combat` / `guard`; Engineer and Medic follow different responsibility and routing chains. Combined with the G4 silhouette/fallback work, specialist identity is therefore **behaviorally real at coarse semantic level**, not merely different names/icons.

No role-specific `use_ability` Candidate was selected in that representative run. Deeper ability-level identity is not yet claimed.

---

# G4-V4 product decisions

The comparative research has now caused concrete subtraction and clarification rather than feature accumulation:

1. **Remove player-facing Loot policy for the current slice.** Forty-six real optional-pickup contexts produced no changed Fixture decision. Keep `mission-only` internally until content proves a useful loot tradeoff.
2. **Do not claim collateral control.** No current collateral-damage semantic exists. Do not add friendly fire/AoE merely to justify an Order field.
3. **Keep retreat threshold and priority-target semantics.** Relevant-state probes prove both can materially change decisions; they are contextual rather than core doctrine.
4. **Keep current Cooling World numbers.** The exact `repair + power` chain works. Fix evidence/legibility, not the reducer just to make a button feel stronger.
5. **Expose bounded system condition, not omniscient telemetry.** Product value comes from usable evidence under authority boundaries.
6. **Describe scan timing truthfully.** Current scans inform the next Planning Head because they resolve after current Agent deliberation.

---

# Content Grammar v0

G5 must not interpret "content production" as cloning the same encounter with new names. A content dimension belongs in production only when it changes the decision problem.

Current evidence map:

| Variation dimension | Evidence | Current status |
| --- | --- | --- |
| primary objective package | 39/40 same-state selection leverage + distinct G3 outcome signatures | **PROVEN** |
| formation / deployment doctrine | narrow local leverage but Rescue-vs-Core viability basins differ sharply | **PROVEN** |
| initial / acquired Knowledge | Life Support and Maintenance scans alter next planning surface | **PROVEN** |
| encounter time budget | 14-Turn falsifier vs 20-Turn viable rescue basin | **PROVEN** |
| coupled system pressure | Heat/Oxygen thresholds alter scoring and cause authoritative damage | **PROVEN SYSTEMIC AXIS** |
| enemy faction objective package | Pirate/Swarm create current pressure, but alternate doctrine set not yet ablated | **UNPROVEN VARIATION AXIS** |
| topology / choke geometry | G5-P1 108-Run counterfactual: multiple bounded choke/capacity variants change Candidate surfaces, selected actions, and authoritative outcome vectors | **PROVEN OUTER CONTENT AXIS** |
| civilian / item placement | important in current solution paths, no controlled relocation study yet | **UNPROVEN VARIATION AXIS** |
| specialist loadout | mechanical content exists, but alternate loadout has not been isolated | **UNPROVEN VARIATION AXIS** |
| optional loot abundance | 46 opportunities with zero loot-policy leverage in current slice | **NOT YET A PRODUCT AXIS** |

The initial production grammar is therefore not a list of randomizers. It is a contract:

```text
A future encounter must deliberately vary at least:
  objective pressure
  information topology
  one systemic pressure profile
  one spatial or adversarial problem

and must produce a different strategy/action/outcome signature under evaluation.
```

Before scaling any unproven axis, use a research-only counterfactual or one bounded second-scenario slice to establish that it changes decisions.

## G5-P1 — topology/choke outer-axis admission

The first G5 production-grammar proof intentionally changed **no Game core contract**. `scripts/eval-station-zero-v3-topology-axis.ts` clones the canonical Genesis in memory, mutates only bounded Zone capacity, then reuses the existing Candidate, fixture-Provider, Plan, commitment, and deterministic reducer path. No Variant Engine, custom-Genesis Store API, or new World abstraction was introduced.

The evaluator runs the exact 18-profile strategy matrix across six conditions (`baseline` plus five bounded topology treatments), for 108 full deterministic Runs. Admission requires all three:

```text
Candidate-surface divergence >= 10%
selected-action divergence >= 10%
>= 1 profile with changed focus / raw outcome vector / faction outcome
```

Current results:

| Variant | Candidate divergence | Selected-action divergence | Strategic profiles changed | Focus completion | Judgment |
| --- | ---: | ---: | ---: | --- | --- |
| `central-choke` | 53.96% | 42.10% | 16 / 18 | Rescue 3/6→0/6; Core 1/6→3/6; Hive 6/6→2/6 | axis proof, **too destructive** as current production candidate |
| `console-choke` | 13.19% | 9.14% | 3 / 18 | Rescue 3/6→0/6; Core/Hive unchanged | **reject**; misses selected-action threshold |
| `cover-choke` | 51.09% | 39.96% | 15 / 18 | Rescue 3/6→3/6; Core 1/6→3/6; Hive 6/6→2/6 | **admit**; strongest bounded second-slice candidate |
| `wide-junction` | 52.67% | 41.02% | 11 / 18 | Rescue 3/6→3/6; Core 1/6→4/6; Hive 6/6→3/6 | **admit**; strong alternate production candidate |
| `reactor-choke` | 7.28% | 4.90% | 3 / 18 | all focus-completion basins unchanged | **reject**; too weak |

The result is deliberately narrower than “these exact capacities are good level design”:

```text
topology / choke geometry
= proven Content Grammar axis

cover-choke / wide-junction
= current outer production candidates

capacity=1 or capacity=4
!= Game core law
```

`cover-choke` is the current first candidate because it materially reshapes Candidate/action/outcome space while preserving the baseline Rescue viability basin. Human play and later production evidence may still reject the concrete treatment.

This evaluator is an **outer production instrument**, not a new permanent product authority. Retain it while G5 topology production remains decision-relevant; archive/localize it after the production grammar stabilizes.

G4 does not authorize a mission factory. With G4 exit accepted, G5 may now produce **one bounded second encounter/variant as a production-grammar proof** only if it deliberately varies the Content Grammar v0 axes above and is evaluated for a different strategy/action/outcome signature. Broad mission volume, campaign/meta progression, and random-content scaling remain unauthorized.

---

# G4-V execution order

```text
V1  comparative map                 DONE in this document
V2  design laws / incompatible choices  DONE in this document

V3-A Commander control leverage     DONE
V3-B Information-as-command         DONE
V3-C Pressure curve                 DONE
V3-D Specialist behavioral identity DONE

V4  synthesize proven defects       DONE
    → surfaced control subtraction + bounded system evidence

V5  content grammar definition      DONE (v0)
    → no second mission yet

Later product validation
    → human behavior / preference / replay evidence during G5/G6 as appropriate
```

This lane now produces a coherent product thesis and the current Vertical Slice supports it. **G4 Product Value is accepted and bounded G5 Production is admitted.** G5 is constrained to Content Grammar v0 and must continue to use falsification before scaling an unproven content axis.

---

# Current differentiation hypothesis

The current strongest candidate is:

> **Station Zero is a delegated WEGO command game where the player controls strategic intent rather than local movement, receives only faction-bounded evidence, reviews autonomous specialist commitments before an irreversible simultaneous Turn, and can reconcile each delegated plan with deterministic authoritative consequence afterward.**

Its components individually exist elsewhere. The possible value lies in the combination:

```text
delegation
+ bounded information
+ simultaneous commitment
+ deterministic consequence
+ explicit Agent accountability / aftermath reconciliation
```

G4-V now supports this combination as the production thesis: the components create measurable command leverage, information effects, pressure interventions, specialist differentiation, and strategy plurality rather than existing only as architecture. Long-term delight, retention, and market value remain later human/market claims.
