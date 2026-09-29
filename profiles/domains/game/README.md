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
                    decompose unresolved claims
                               ↓
              select the best evidence carrier per claim
       formal / simulation / synthetic / telemetry / experiment / Human
                               ↓
                    scoped findings + uncertainty
                               ↓
       Structured Decision Making / Value-of-Information judgement
                               ↓
             kill / revise / continue / learn more
                               ↺

          ↓ sufficient decision basis

PRODUCT COMMITMENT
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

Evidence is selected by claim and decision value. Human play/evaluation supplies evidence when the target variable is Human behaviour, interpretation, preference or experience; structural, causal, reachability, robustness and other claims should use the strongest applicable formal, synthetic, telemetry or experimental carrier. A reference session is not a prerequisite for every prototype, and historical prototypes may be reused only for the mechanism/coupling claims they actually evidence.

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

## Current composition standing

The broad external success/reference census is saturated for the current decision. Product Thesis Sprint artifacts are retained as sample composition evidence, not as product destinies. Mechanism-space expansion is not the next task. The current forward workload is **whole-product composition from the registered mechanism graph**, with experiment search serving only to falsify uncertain couplings inside those products.

```text
Category/genre crosswalk        READY_R1
Mechanism catalog               READY_R1_WORKING_EXTENSIBLE
Structural design axes          READY_R1
Composition graph vocabulary    READY_R1
Historical mechanism evidence   R2_CURRENT_50_SPECIMENS
Pair/set compatibility evidence R2_CURRENT_60_CONTEXT_BOUND_CLAIMS
Experiment composition search   R2_READY_10_BRIDGE_DRIVEN_GRAPHS
Physical realization ledger     R1_ACTIVE
Whole-product compositions      R1_ACTIVE_3
PC01 evidence                   F0_SURVIVES + F1_MECHANICAL_INTERACTIVE_PASS
PC02 evidence                   F0_DURABLE_STRUCTURAL_SURVIVES
PC03 evidence                   F0_MECHANICAL_STRUCTURAL_SURVIVES
Autonomous-interest experiment  R1_PROTOCOL_FROZEN
Candidate generation            NOT_STARTED
Live Human judgment             FORBIDDEN_UNTIL_BUILD_FREEZE
Product selected                false
G0 entered                      false
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
- [`GAME_PRODUCT_COMPOSITION_R1.md`](GAME_PRODUCT_COMPOSITION_R1.md) — whole-product composition definitions: PC01 Causal Works, PC02 Persistent Workshop, PC03 Loop Cartographer;
- [`game-product-composition-r1.json`](game-product-composition-r1.json) — machine-readable original product-composition slate and execution order;
- [`GAME_PRODUCT_COMPOSITION_VOI_R1.md`](GAME_PRODUCT_COMPOSITION_VOI_R1.md) — post-F0 Value-of-Information comparison that supersedes only the next experiment-allocation decision;
- [`game-product-composition-voi-r1.json`](game-product-composition-voi-r1.json) — machine-readable post-F0 allocation decision and PC03-F0 minimum carrier contract;
- [`GAME_AUTONOMOUS_INTEREST_PROTOCOL_R1.md`](../../../studies/game/autonomous-interest/domains/game/GAME_AUTONOMOUS_INTEREST_PROTOCOL_R1.md) — frozen no-live-Human-judgment autonomous whole-product synthesis and sealed-holdout protocol;
- [`game-autonomous-interest-protocol-r1.json`](../../../studies/game/autonomous-interest/domains/game/game-autonomous-interest-protocol-r1.json) — machine-readable R1 search budget, surrogate/anti-Goodhart contract, freeze rules and Human endpoint;
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

PC01 and PC02 now have whole-composition survival evidence at different depths, and the post-F0 VoI decision allocates the next bounded experiment to **PC03 Loop Cartographer** as the orthogonal anti-system-bias control. PC03 must reuse PGP-A rather than reopen infrastructure: build one interactive whole-composition falsifier that couples stable movement, reusable rule knowledge, route choice, fast retry and retained execution demand. Apparatus-valid evidence upgrades only the claim it actually identifies: Human felt/experienced Player Value requires relevant Human participant evidence, while structural, behavioural, causal and population claims use their own admissible evidence carriers. Product commitment remains a domain decision over scoped findings, objectives, consequences, uncertainty and remaining information value; it is not a generic Human approval gate.

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
