# Game Domain Profile — R1 External-First Iterative Profile

Status: **READY_FOR_REAL_WORK**. This profile governs how Game problems are approached in Ordivon Next; it does not create a new universal game-design ontology or re-own Engineering, Media, Artifact, Security, Network, Distribution or Operations.

## Entity of interest

A game product/service and the player experience it is intended to create across the relevant life cycle.

## External authority model

There is no single universal authority for game development. Use the mature source native to the question:

- **Design/process:** Design Council Double Diamond as a divergence/convergence skeleton; it is explicitly iterative rather than a mandatory waterfall.
- **Human/player evidence:** ISO 9241-210 / ISO 9241-11 where human-centred design and usability apply, plus Games User Research practice for question-method fit.
- **Software/product engineering after commitment:** ISO/IEC/IEEE 12207, ISO/IEC/IEEE 29148 and ISO/IEC 25010 family as applicable.
- **Engine/platform:** engine-native documentation, SDKs, certification requirements, store rules and platform-native test/release mechanisms.
- **Accessibility:** Xbox Accessibility Guidelines and mature game-accessibility guidance where applicable.
- **Studio practice as precedent, not standard:** Riot R&D, Nintendo developer interviews, Supercell and other mature studios may provide falsifiable operating examples, but no studio-specific process becomes universal Game authority.

Historical `ordivon-game` remains an evidence, migration and active-work source. Its internally named stages or systems do not become external standards merely because they exist.

## Forward operating profile

The profile is deliberately **non-linear before product commitment**.

```text
BOUNDED EXTERNAL ORIENTATION
  success surfaces / references / audience / opportunity
  stop when additional search has low decision value

          ↓

ITERATIVE EXPLORATION LOOP

  Reference learning  ↔  Product theses  ↔  Throwaway prototypes
          ↑                    ↓                    │
          └──────────── Human play / evidence ─────┘

          ↓ kill / revise / continue

PRODUCT COMMITMENT GATE
  "Should we build this game?"

          ↓ yes

PRE-PRODUCTION
  "How should we build it?"
  requirements / architecture / pipeline / representative proof

          ↓

PRODUCTION → QA / PLAYER TEST → PACKAGE / RELEASE → OPERATE / LEARN
```

### Bounded external orientation

External reference work exists to prevent capability bias, local-tool bias and sunk-system bias. It may include success-universe census, archetype coverage and representative references. It is **not** an obligation to create an exhaustive taxonomy.

Stop/reopen law:

```text
Reference search saturated for the current decision
→ stop expanding it.

A later thesis exposes an uncovered reference class or contradictory evidence
→ reopen only that bounded question.
```

### Iterative exploration

Three lanes may run in parallel:

1. **Reference learning** — direct play, teardown and bounded reproduction of mature patterns when they answer a real question.
2. **Product thesis formation** — state audience/context, player promise, retained mature patterns, deliberate differences and major unknowns.
3. **Throwaway micro-prototypes** — the cheapest playable implementation that can falsify one important claim. Prototype code is disposable unless later evidence earns promotion.

Human play/evaluation feeds all three lanes. A reference-learning session is not a prerequisite for every prototype, and a prototype is allowed during discovery when its purpose is explicit.

## Commitment boundary

Before product commitment, the controlling question is:

> **Should we build this game?**

Commit only when the evidence is sufficient to state, at minimum:

- intended player/context;
- player promise / core experience thesis;
- core interaction or loop;
- mature patterns intentionally retained;
- deliberate differences worth testing/keeping;
- strongest surviving evidence;
- major unresolved risks and transfer limits.

After commitment the controlling question changes to:

> **How should we build this game well?**

That is where durable requirements, architecture, build/test pipelines, representative slices, production planning and quality models become proportionally more important.

## Anti-patterns

Do not:

- require all research to finish before any playable experiment;
- treat a success chart as proof of design causality;
- filter the external reference universe only by what the current team can reproduce;
- polish prototype code/art before its claim survives;
- allow existing infrastructure or historical prototypes to create product momentum;
- continue taxonomy/reference expansion after it stops changing decisions;
- confuse automated mechanical PASS with player value.

## Current first-formal-product standing

The active Game work has already completed a bounded external success/reference census and desk teardown sufficient to stop broad R0 expansion. The next learning period should therefore use the **iterative exploration loop**, not another generic Game-framework build and not another broad census.

Current intended work:

```text
reference canary/direct-play evidence
+ 3–5 competing product theses
+ 1–3 cheap throwaway prototypes against the highest-risk claims
→ compare evidence
→ kill / revise / continue
→ earn product commitment only if justified
```

## External references

- Design Council, Double Diamond: https://www.designcouncil.org.uk/our-resources/the-double-diamond/
- ISO 9241-210: https://www.iso.org/standard/77520.html
- ISO 9241-11: https://www.iso.org/standard/63500.html
- Games User Research, choosing playtest methods: https://gamesuserresearch.com/choose-the-right-playtest-method/
- Riot R&D foundations: https://www.riotgames.com/en/news/r-d-foundations-opportunity-thesis-and-audience
- Riot R&D engineering/prototype practice: https://www.riotgames.com/en/r-and-d-office/engineering-in-riot-r-d
- Riot prototype/playtest practice: https://www.riotgames.com/en/r-and-d-office/prototype-building-a-games-substance
- Nintendo developer interview, Echoes of Wisdom: https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-13-the-legend-of-zelda-echoes-of-wisdom-part-1/
- Supercell new-game / killed-game practice: https://supercell.com/en/new-games/
