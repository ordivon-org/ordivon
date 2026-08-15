---
schema_version: 1
id: game.product.station-zero-v3.domain-value-gv
title: Station Zero v3 — Domain Value / GV Evidence
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-15
summary: Failure-driven consumer validation for Station Zero v3. External failures create transfer hypotheses; only reproduced Game failures may pressure product changes, and pressure stops at the highest layer that resolves the failure.
evidence_status: mixed
readiness: ACTIVE
---
# Station Zero v3 — Domain Value / GV Evidence

## Purpose

This lane asks a narrower question than the v3 authority, planning, Vertical Slice, or G4 Product Value work:

> **Does the delegated-WEGO thesis create repeatable player value, and what must actually change when consumption fails?**

The rule is deliberately asymmetric. External products, research, postmortems, and standards may reveal failure classes we have not sampled ourselves, but they do not authorize Ordivon changes. They create transfer hypotheses. A Game change is admitted only after the failure is reproduced against current Station Zero or a current product boundary makes the failure directly observable.

This is not a new Game framework, KPI service, Scenario factory, or universal evaluator.

---

# Modification-pressure law

```text
L0  evidence / research only
 ↓ only if failure is reproduced
L1  authored content / Scenario data
 ↓ only if L1 cannot resolve it without semantic distortion
L2  expression / UI / audio / feedback
 ↓ only if L2 cannot resolve it
L3  player-facing semantic projection / Agent Context / planning
 ↓ only if L3 cannot resolve it
L4  World rules / model / reducer / persistence
 ↓ only after repeated owner-level proof
L5  cross-Game / Ordivon abstraction
```

After every smallest treatment, rerun the exact failing consumer probe. If it passes, **stop downward propagation**.

A large behavioral difference is not automatically valuable. A technically correct mechanic is not automatically legible, fair, tense, memorable, or replayable.

---

# GV0 — Current truth freeze

Baseline owner revision at the start of this lane:

```text
850625c1c87ee2f70a36ae64f95db7d385580508
```

Current v3 truth at that revision:

- player loop: `OBSERVE → COMMAND → REVIEW → COMMIT → RESOLVE → OBSERVE`, terminal `DEBRIEF`;
- browser exposes real Commander Order, bounded Deliberation, Plan Preview, sealed enemy commitments, explicit Commit, Aftermath, plan review, and terminal debrief;
- one bounded 20-Turn encounter form;
- exactly two production Scenario Cases: `fixed-genesis` / **Contested Signal** and `junction-bottleneck` / **Junction Bottleneck**;
- `junction-bottleneck` changes exactly one retained content fact: `junction-cover.capacity: 2 → 1`;
- five high-fidelity Agent actors coexist with cheaper deterministic policy actors;
- human delight, attachment, replay desire, market appeal, target-player comprehension, perceived suspense, and preference remain unproven.

A fresh Runtime Workspace initially failed `pnpm check` because `node_modules` was absent and `tsc` could not be found. After `pnpm install --frozen-lockfile`, the current source passed **304/304 tests**. The first failure was therefore classified as bootstrap/environment friction, not Game failure.

## GV0 consumer failure A — implicit favicon request

Real Chromium `e2e:v3` then failed because the browser emitted two 404 console errors. Exact tracing showed both requests were implicit `/favicon.ico` requests, not Game API, media, World, or Agent failures.

Pressure classification:

```text
consumer failure: browser shell emits 404 noise
required layer:   L2 expression / document shell
forbidden descent: server routing / API / World / Agent core
```

Smallest treatment: `web-v3/index.html` explicitly declares an empty data favicon.

Exact re-probe: complete 20-Turn `pnpm e2e:v3` passed with `browserErrors: []`.

Pressure stopped at L2.

---

# GV1 — External failure-transfer matrix

External evidence is used as a **falsifier generator**, not as imported requirements.

| External failure / evidence | Observed failure class | Transfer precondition to Station Zero | Non-transfer reason | Station Zero probe | Pressure only if reproduced |
| --- | --- | --- | --- | --- | --- |
| *Invisible, Inc.* alarm-system postmortem | structurally meaningful pressure can still feel unclear/unpredictable | Heat/Oxygen/Alert/Turn pressure changes choices but upcoming consequence is not legible | Station Zero has different information rules and deterministic consequence | compare planning thresholds, visible warnings, damage onset, and player prediction | L2 first; L4 only if the mechanic itself lacks useful decision space |
| *Never Alone* postmortem | repeated internal play can miss companion-AI failures visible to fresh players | internal/Agent evaluation is positive while fresh players lose trust/control | Station Zero uses delegated command rather than platforming companion traversal | fresh-player prediction, trust, and causal reconstruction | L2/L3 depending reproduced cause |
| MKULTRA / AI-heavy game legibility pattern | players need implementation knowledge to understand an AI system | Mission Control surfaces provider/internal tokens or explanations require architecture knowledge | Station Zero already has a bounded player projection | inspect real browser copy; fresh players receive no architecture briefing | L2 first |
| *Phantom Brigade* repetition criticism and later content expansion | signature simultaneous mechanic can outlive shallow mission/content variety | different Station Zero runs ask the same question despite parameter variation | Station Zero is a different scale/form and does not imply campaign/meta systems | research-only content archetypes plus replay behavior | L1 only; no mission factory by default |
| Game Feel survey | correct mechanics can lack moment-to-moment predictability, amplification, or support | Commit/consequence is understandable but weak, delayed, or low-salience | tactical command has different feel needs than action controls | command/Deliberation/Preview/Commit/Aftermath visual + timing audit | L2 first |
| AI-Native Games survey | generative AI may be substitutable rather than constitutive | fixture/policy produces materially equivalent play to live cognition | local behavior variation alone may still matter if players value it | matched seed/order fixture ↔ live-Agent ablation | L3/provider usage only after value proof |
| GUESS / GUESS-18 | player satisfaction is multidimensional | a later product decision needs scoped human satisfaction evidence | no single score establishes product truth | selected applicable dimensions plus behavior and qualitative explanation | evidence only; never a universal KPI |
| Player–AI interaction research | learning AI behavior may require observation, prediction, and consequence | players cannot form a usable model of specialist autonomy | Station Zero already exposes Preview/Aftermath, which may be sufficient | predict specialist tendency → observe → explain → adapt | L2/L3 only if fresh-player failure repeats |

External evidence therefore expands coverage without deciding the implementation.

---

# GV2 — Current product baseline consumption

## Browser baseline

After the favicon treatment:

```text
pnpm e2e:v3       PASS
pnpm e2e:v3:g5    PASS
```

Canonical v3 Chromium journey:

- 20 committed Turns;
- World revision 20;
- media assets return 200;
- delayed Preview path works;
- mobile command surface remains ahead of the tactical map;
- browser errors are empty.

Junction Bottleneck also completes 20 Turns with retained `junction-cover.capacity = 1` and no browser errors.

This proves the two current products are executable. It does **not** prove they provide two materially distinct human experiences.

## Fixture strategy baseline

A heavyweight all-profile evaluator exceeded a 240-second experiment budget before its full matrix completed. That is an experiment-cost fact, not a semantic failure. The observed profiles already establish non-trivial strategy separation:

- `rescue-two-civilians + cautious/cohesive` → `2/2`, required `2/2`, **victory**;
- the same objective with `cautious/split` → `1/2`, required `1/2`, **partial**;
- balanced/aggressive preserve the same cohesive-vs-split distinction in the observed rows;
- `recover-research-core + cautious/split` can recover the Core and reach partial, while several adjacent posture/formation combinations fail.

The current strategy surface therefore is not one dominant cosmetic choice.

---

# GV3 — Delegated agency

Current machine-level evidence supports **causal command bandwidth**, not yet human agency.

Same-world Preview perturbations from the current Product Value evaluator:

| Commander control | Current machine result |
| --- | --- |
| Primary objective | 39 / 40 probes changed selected action — strong leverage |
| Posture | 3 / 40 — narrow leverage |
| Formation | 2 / 20 — narrow leverage |
| Lethal force | 4 / 40 — narrow leverage |
| Commander directive | 19 / 20 changed direct Commander action |
| Retreat threshold | generic probes miss it; relevant-state audit changes 7 / 8 opportunities |
| Priority target | generic probes miss it; relevant-state audit changes 22 / 63 opportunities |
| Loot policy | 46 relevant pickup contexts, 0 decision changes — correctly absent from current player UI |

This is an important distinction:

```text
Commander choices have causal leverage      PROVEN at machine level
player feels strategic ownership             UNPROVEN
player can predict specialist tendencies     UNPROVEN
player accepts autonomous disagreement       UNPROVEN
```

Plan Preview and Aftermath already retain the machine-readable causal bridge: planned action → authoritative status/reason → next-turn feedback. GV7 must determine whether fresh players can actually reconstruct that bridge.

---

# GV4 — Pressure and moment-to-moment command feel

## Mechanical pressure

Three representative full deterministic runs produced:

```text
classification: PRESSURE_REACHES_PLANNING_AND_DAMAGE_THRESHOLDS
heat planning-pressure Turns:    18 / 20 in all three runs
oxygen planning-pressure Turns:   7 / 20 in all three runs
pressure-damage Turns:           15–18 / 20
```

Observed ranges include Oxygen down to 20 in the Core profile, Reactor Heat up to 100, Alert up to 5, and Biomass up to 36 in the Hive profile.

Therefore the open question is **not** whether meters move or pressure has consequence. It is whether players can anticipate, interpret, and act on that pressure before punishment.

## Real mobile visual audit

A real 390×844 Chromium journey was captured at Command, Deliberation, Preview, and Aftermath.

Machine/Agent-observable positives:

- Commander Order is visually dominant and grouped into Mission intent / This Turn / contingencies;
- Deliberation keeps the command context visible, explicitly states `World paused`, `Enemy plans sealed`, elapsed client time, and `no fake progress`;
- Aftermath gives each specialist `Planned → status → reason` and retains mission-front reconciliation;
- the product does not need a loading-screen replacement or new game engine to express these states.

## GV4 consumer failure B — implementation identity leaked into player Preview

The real Preview visibly displayed:

```text
fixture-station-zero-v3-agent-v1
```

and rendered the internal provider-generated summary containing the raw objective token:

```text
rescue-two-civilians
```

This directly reproduced the GV1 AI-internals-legibility risk. A normal player should not need provider identity or internal object tokens to understand a team plan.

Pressure classification:

```text
consumer failure: implementation/debug identity visible in normal player flow
required layer:   L2 expression
retained evidence: providerId + internal summary remain in Game data/evidence
forbidden descent: Agent Context / Preview schema / planning / World
```

Smallest treatment:

- stop rendering `preview.providerId` in normal Mission Control;
- build the visible one-line summary from already projected player semantics (`view.experience.order` + objective display name + intent count);
- retain provider identity and internal summary below the presentation boundary.

An initial treatment incorrectly assumed browser Preview retained internal `playerOrder`; targeted tests failed immediately. The final treatment consumed the existing public `view.experience.order` instead. This is positive boundary evidence: the browser projection did not need to widen.

Re-probe after the final treatment:

```text
station-zero-v3-web targeted tests  5 / 5 PASS
web syntax gate                     PASS
full 20-Turn Chromium e2e:v3        PASS
browserErrors                        []
```

Pressure again stopped at L2.

Human-only remainder:

- whether ~1.5–2s live Deliberation feels suspenseful or slow;
- whether Commit has enough weight;
- whether Aftermath salience is sufficient without overexplaining;
- whether pressure feels fair rather than merely deterministic.

---

# GV5 — Replay / content breadth without a mission factory

The current production catalog still contains only two Cases, and the second is one exact topology delta. GV5 therefore used **research-only compositions of already admitted axes**. Nothing below was registered as a Scenario Case.

Three temporary archetypes were tested across the three representative Rescue strategy profiles:

1. `triage-collapse` — existing environmental pressure raised at Genesis;
2. `core-intercept` — Research Core moved beside the Pirate route + one-body Junction choke;
3. `swarm-escalation` — Swarm starts near its existing Biomass threshold + one-body Maintenance choke.

All mutated Worlds passed the existing v3 World validator; no new rule, model, reducer, Scenario DSL, or mission factory was added.

| Research archetype | Aggregate selected-action divergence | Strategic consequence changed | Most relevant profile result |
| --- | ---: | ---: | --- |
| `triage-collapse` | 13.83% | 2 / 3 profiles | Rescue profile 32.79% selection divergence; `2/2 victory → 1/2 partial` |
| `core-intercept` | 49.81% | 3 / 3 profiles | Core profile `1/1 → 0/1`; broad cross-profile disturbance warns it may be too strong |
| `swarm-escalation` | 22.74% | 1 / 3 profiles | Core profile 0% selected-action change; Hive profile 46.15% and `1/1 → 0/1` |

The important result is not “all three should ship.” It is:

> **The existing v3 core can already support materially different problem surfaces through outer content composition. A mission factory or new core mechanic is not currently justified.**

`swarm-escalation` is especially useful evidence because its effect is directionally concentrated: it leaves the observed Core strategy nearly unchanged while materially changing the Hive-focused problem. `core-intercept` is the opposite warning: large difference can be too globally disruptive.

Human replay/value remains unproven until players experience these or production-quality descendants.

---

# GV6 — Agent indispensability ablation

## Current live-provider revalidation

The current default private authority exposed six usable DeepSeek credential files with owner-only file permissions. A bounded current live probe therefore revalidated the provider instead of relying on old evidence.

Two-Turn smoke:

- 10 / 10 provider calls succeeded;
- no retries;
- no hidden-reference detections;
- Preview latency ~1.36–1.54s.

Expanded matched run:

```text
3 strategic profiles
× 5 Turns
= 75 high-fidelity Agent decisions/calls
```

Provider result:

- 75 / 75 calls succeeded;
- zero retries;
- zero hidden references;
- call latency p50 ≈ 1.39s, p95 ≈ 2.03s;
- Preview latency p50 ≈ 1.57s, observed max ≈ 2.45s.

## Matched fixture ↔ live trajectories

Same seed, same Commander strategy, same 5-Turn horizon:

| Profile | Rescue decision exact-match | Live-only behavior examples |
| --- | ---: | --- |
| Core / cautious / split | 13.3% | repair Power Grid, direct attacks on Hacker/Raider, different Reactor routing |
| Hive / balanced / split | 20.0% | repair, different overwatch/attack choices |
| Rescue / cautious / cohesive | 46.7% | Medical routing, civilian custody, additional combat choices |

Live Agent cognition therefore produces materially different local trajectories from the cheaper fixture.

But after five Turns, none of the three primary objectives had completed in either treatment. Difference alone is not sufficient evidence of player value. Live runs also exposed six short movement-oscillation patterns, concentrated in Pirate Captain movement, which is a useful future quality probe rather than a reason to expand architecture.

Current GV6 judgment:

```text
live cognition is operational              PROVEN
live cognition changes local behavior      PROVEN
live cognition avoids hidden-reference leak in this sample  PROVEN
live cognition is cheaper/faster           FALSE
live cognition improves player value       UNPROVEN
live cognition is constitutive/indispensable UNPROVEN
```

Classification: **DIFFERENT_BUT_VALUE_UNPROVEN**.

Do not promote “more model autonomy” merely because exact-match is low. GV7 must ask whether players notice and value the difference; longer matched outcome experiments are justified only when they answer that product question.

---

# GV7 — Fresh-player validation protocol

Status: **WAITING_FOR_FRESH_HUMAN_EVIDENCE**.

Agent/model review may pre-falsify copy, hierarchy, hidden-information leaks, causal inconsistency, or obvious routing defects. It may not be relabeled as evidence of delight, preference, suspense, attachment, or replay desire.

A fresh-player round should therefore use the actual browser without architecture documentation and collect raw behavior before explanation.

## Minimum tasks

1. **First command** — identify role, success condition, and choose a meaningful first Order without reading implementation docs.
2. **Prediction** — before Commit, state what each specialist is likely trying to accomplish and one thing that could go wrong.
3. **Causal reconstruction** — after Aftermath, explain which result came from the Commander Order, specialist choice, enemy contest, or environmental pressure.
4. **Adaptation** — make the next Order and explain what changed because of the previous Turn.
5. **Deliberation experience** — classify live waiting as suspense/meaningful observation/neutral wait/friction and explain why.
6. **Replay choice** — after a bounded encounter, choose whether to replay the same Case, another Case/archetype, or stop, and state what new problem is expected from another run.

## Evidence to retain

- time and corrections before first meaningful Order;
- mistaken assumptions about direct control vs delegation;
- specialist-action prediction and surprise reasons;
- causal reconstruction errors after Aftermath;
- whether pressure thresholds were anticipated before damage;
- whether internal implementation terms are mentioned because the UI forced them, not because the tester already knows them;
- explicit replay choice and reason;
- selected applicable GUESS/GUESS-18 dimensions as supplementary diagnostics, never as one universal launch score;
- qualitative failure clusters, including minority but severe comprehension/control failures.

Do not require a large population before fixing a clear repeated usability defect. Do require appropriately scoped human evidence before claiming population preference, market appeal, or retention.

The current owner/developer is not a clean substitute for a fresh player because prior implementation knowledge changes the test.

---

# GV8 — Failure-driven treatments

Current admitted product changes from this lane:

| Failure | Layer reached | Treatment | Exact re-probe | Downward pressure |
| --- | --- | --- | --- | --- |
| implicit `/favicon.ico` 404s break real browser acceptance | L2 | explicit empty data favicon | full `e2e:v3` | **STOP** |
| provider ID + internal objective token visible in normal Preview | L2 | player-facing summary from existing projection; hide provider ID in normal render | targeted web + syntax + full `e2e:v3` | **STOP** |

Current count:

```text
L1 content treatments admitted to production: 0
L2 expression treatments:                    2
L3 semantic/planning changes:                 0
L4 World/core changes:                        0
L5 cross-project abstractions:                0
```

That distribution is itself evidence: the current hard core has not yet been shown to be the bottleneck.

---

# GV9 — Promotion boundary

Status: **NOT ELIGIBLE**.

Station Zero alone cannot justify a cross-project Domain Value service, KPI database, workflow engine, universal failure ontology, or generic consumer framework.

Before Computing promotes any stable cross-domain rule, require:

- independent real-consumption evidence from more than Game;
- repeated evidence that the same responsibility belongs above owner boundaries;
- failure to resolve the problem cleanly inside the consuming domain;
- a narrower abstraction than simply documenting the decision rule.

The current reusable knowledge is still primarily conceptual:

```text
external failure → transfer hypothesis
current consumption → reproduced failure or no-op
smallest owner-local treatment
exact re-probe
stop pressure when fixed
```

That is a decision discipline, not yet another service.

---

# Current judgment

Station Zero v3 has crossed an important boundary:

> We no longer need to ask primarily whether the Agent/World machinery can produce valid consequences. Current evidence says it can. We now need to ask whether players can understand, anticipate, care about, and want to revisit those consequences.

The strongest current findings are:

- the lower authority/planning substrate survived the first real consumer failures without modification;
- Commander intent has real causal bandwidth;
- environmental pressure is mechanically consequential;
- outer content composition can create materially different problem surfaces without a mission factory;
- live Agent cognition creates substantially different local trajectories, but its additional player value is not yet proven;
- two directly observable product-shell/legibility defects were resolved at L2 and stopped there;
- human delight, preference, replay desire, suspense, and market value remain explicitly open rather than inferred from machine evidence.

Next legitimate hinge: **fresh-player evidence**, followed by the smallest failure-driven treatment it actually demands.
