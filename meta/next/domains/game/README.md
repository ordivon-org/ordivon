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
  market categories + reference specimens + mature pattern/mechanism sources
  stop broad census when additional search has low decision value

          ↓

MECHANISM-COMPOSITION LOOP

  Reference decomposition → mechanism/rule/goal nodes + coupling evidence
                               ↓
                       candidate mechanism graph
                               ↓
                   predicted dynamics / player value
                               ↓
                       cheapest playable falsifier
                               ↓
                          Human evidence
                               ↓
               update node / edge / composition standing
                               ↺

          ↓ sufficient surviving composition

PRODUCT COMMITMENT GATE
  "Should we build this game?"

          ↓ yes

PRE-PRODUCTION → PRODUCTION → QA / PLAYER TEST → RELEASE → LEARN
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

### Mechanism-composition exploration

Three activities may run in parallel:

1. **Reference decomposition** — direct play/teardown extracts mechanics, rules, goals, coupling relations and observed dynamics from mature specimens.
2. **Composition search** — combine externally grounded design elements into explicit mechanism graphs under player/context constraints; genre is not selected first.
3. **Throwaway falsifiers** — build the cheapest playable implementation that can test one uncertain node, edge or composition-level dynamic.

Human play/evaluation feeds the graph evidence. A reference session is not a prerequisite for every prototype, and historical prototypes may be reused only for the mechanism/coupling claims they actually evidence.

## Commitment boundary

Before product commitment, the controlling question is:

> **Should we build this game?**

Commit only when the evidence is sufficient to state, at minimum:

- intended player/context;
- player promise / target experience;
- anchor mechanics and coupling graph;
- resulting core loop/dynamics;
- mature patterns intentionally retained;
- deliberate coupling differences worth testing/keeping;
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
- choose a genre first and then retrofit mechanics merely to match the label;
- treat a feature list as a mechanism graph without causal coupling edges;
- confuse automated mechanical PASS with player value.

## Current design-search standing

The broad external success/reference census is saturated for the current decision. Product Thesis Sprint artifacts are retained as sample compositions, not as five competing product destinies. Forward exploration is now **mechanism-composition search**.

```text
Category/genre crosswalk        READY_R1
Mechanism catalog               READY_R1_WORKING_EXTENSIBLE
Structural design axes          READY_R1
Composition graph vocabulary    READY_R1
Historical mechanism evidence   R2_CURRENT_50_SPECIMENS
Pair/set compatibility evidence R2_CURRENT_60_CONTEXT_BOUND_CLAIMS
Composition search             R2_READY_10_BRIDGE_DRIVEN_GRAPHS
First bridge-driven wave       CS2-03 / CS2-04 / CS2-01 / CS2-05
Product selected                false
```

Canonical local crosswalks:

- [`GAME_CATEGORY_CROSSWALK_R1.md`](GAME_CATEGORY_CROSSWALK_R1.md) — external market/category vocabulary;
- [`GAME_MECHANISM_CATALOG_R1.md`](GAME_MECHANISM_CATALOG_R1.md) — normalized mechanism/pattern families;
- [`GAME_MECHANISM_COMPOSITION_PROFILE_R1.md`](GAME_MECHANISM_COMPOSITION_PROFILE_R1.md) — graph-based design-search method;
- [`GAME_MECHANISM_EVIDENCE_R1.md`](GAME_MECHANISM_EVIDENCE_R1.md) — frozen first migration snapshot;
- [`GAME_MECHANISM_EVIDENCE_R2.md`](GAME_MECHANISM_EVIDENCE_R2.md) — current cumulative evidence and stronger composition gates;
- [`GAME_COMPOSITION_SEARCH_R1.md`](GAME_COMPOSITION_SEARCH_R1.md) — first evidence-guided mechanism-graph search and reuse-first experiment wave;
- [`GAME_COMPOSITION_SEARCH_R2.md`](GAME_COMPOSITION_SEARCH_R2.md) — current bridge-driven 10-graph experiment search with bounded unknowns and falsifier economics;
- [`GAME_COMPOSITION_REALIZATIONS_R1.md`](GAME_COMPOSITION_REALIZATIONS_R1.md) — execution ledger separating search snapshots from physically realized falsifier apparatus;
- [`GAME_TOP_MECHANISM_SPECIMENS_R1.md`](GAME_TOP_MECHANISM_SPECIMENS_R1.md) — 16 elite/canonical game decompositions and 12 recurring structural motifs;
- [`GAME_TOP_MECHANISM_SPECIMENS_R2.md`](GAME_TOP_MECHANISM_SPECIMENS_R2.md) — current cumulative 27-specimen / 23-motif mechanism map, with R2 gap-filling coverage;
- [`GAME_TOP_MECHANISM_SPECIMENS_R3.md`](GAME_TOP_MECHANISM_SPECIMENS_R3.md) — current cumulative 37-specimen / 33-motif map, coverage-guided but not coverage-optimized;
- [`GAME_MECHANISM_SPACE_COVERAGE_R1.md`](GAME_MECHANISM_SPACE_COVERAGE_R1.md) — diagnostic family/element coverage map and admission law;
- [`GAME_TOP_MOTIF_BRIDGE_R1.md`](GAME_TOP_MOTIF_BRIDGE_R1.md) — crosswalk from 33 top-game motifs to strong local evidence without causal upgrading;
- [`game-design-space-r1.json`](game-design-space-r1.json) — machine-readable category/mechanism crosswalk;
- [`game-mechanism-evidence-r1.json`](game-mechanism-evidence-r1.json) — frozen R1 machine ledger;
- [`game-mechanism-evidence-r2.json`](game-mechanism-evidence-r2.json) — current cumulative 50-specimen / 60-claim machine ledger;
- [`game-composition-search-r1.json`](game-composition-search-r1.json) — machine-readable 8-candidate composition search;
- [`game-composition-search-r2.json`](game-composition-search-r2.json) — current machine-readable 10-candidate bridge-driven composition search;
- [`game-composition-realizations-r1.json`](game-composition-realizations-r1.json) — machine-readable realization status and exact external apparatus anchors;
- [`game-top-mechanism-specimens-r1.json`](game-top-mechanism-specimens-r1.json) — machine-readable top-game mechanism specimen map.
- [`game-top-mechanism-specimens-r2.json`](game-top-mechanism-specimens-r2.json) — current cumulative top-game mechanism specimen/motif map.
- [`game-top-mechanism-specimens-r3.json`](game-top-mechanism-specimens-r3.json) — current cumulative top-game mechanism specimen/motif ledger;
- [`game-mechanism-space-coverage-r1.json`](game-mechanism-space-coverage-r1.json) — machine-readable coverage diagnostic.
- [`game-top-motif-bridge-r1.json`](game-top-motif-bridge-r1.json) — machine-readable external↔local motif evidence bridge.

Two evidence waves are materialized and Composition Search R1 has produced eight candidate graphs. The next high-value work is the **reuse-first falsifier wave MC01 / MC07 / MC03**, while Human C0/C1 remains the only route for upgrading apparatus-valid claims into Player Value evidence.

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
- Game Ontology Project: https://gameontology.com/
- Sicart, Defining Game Mechanics: https://gamestudies.org/0802/articles/sicart
- Björk/Lundgren/Holopainen, Game Design Patterns: https://dl.digra.org/index.php/dl/article/view/60
- Machinations framework: https://machinations.io/docs/framework-basics
- Valve Steam Tags / Tag Wizard: https://partner.steamgames.com/doc/store/tags
