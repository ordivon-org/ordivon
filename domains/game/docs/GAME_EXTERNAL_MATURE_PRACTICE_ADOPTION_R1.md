---
schema_version: 1
id: game.external-mature-practice-adoption-r1
title: Ordivon Game — External Mature Practice Adoption R1
profile: research-engineering
lifecycle: active
source_role: canonical-adoption-policy
visibility: public
owners:
  - ordivon-game
updated: 2026-09-10
summary: Research E2E evidence map and Engineering E2E composition policy for adopting mature external design, human-research, quality, lifecycle, accessibility, experimentation, provenance, rights and release mechanisms directly instead of rebuilding them inside Game.
evidence_status: externally-grounded
readiness: CURRENT
applies_to:
  - ordivon-game
related:
  - game.development-core
  - game.development-paradigm-research
  - game.player-evidence-programme
  - game.e2e.r5.m7.graduation-protocol
---
# External Mature Practice Adoption R1

## 0. Frozen question

> For the remaining Game problems above the graduated Game E2E infrastructure layer, which mature external standards, practices and platform-native mechanisms should Ordivon adopt directly, and what is the smallest Game-owned semantic/profile layer needed to compose them without duplicating their authority?

This R1 intentionally reverses the earlier default of deriving a local Game methodology first.

```text
Default = DIRECTLY ADOPT mature external mechanism inside its native scope.
Local Game addition = admitted only for Game-specific semantics or an observed external gap.
```

A single external framework is **not** promoted into universal Game product authority. Direct adoption is per problem/owner boundary.

## 1. Adoption vocabulary

```text
DIRECT_ADOPT
    Use the external standard/process/mechanism as the default authority for its scope.
    Do not recreate a competing Game-local process.

PROFILE
    Keep the external mechanism unchanged and add only Game-specific questions,
    fields, mappings, thresholds, content semantics or claim boundaries.

PLATFORM_NATIVE
    Consume the actual platform workflow/service rather than emulating it locally.

REFERENCE_ONLY
    Use a mature conceptual lens or method source; do not claim compliance
    and do not let it mint product/release authority.

ADAPT_ONLY_IF_FALSIFIED
    Do not extend first. Add a local mechanism only after a concrete external
    mismatch/failure witness demonstrates that direct adoption is insufficient.

DO_NOT_OWN
    Game must not become the owner of this generic infrastructure/process.
```

## 2. Research E2E evidence map

### 2.1 Product discovery: external reference before internal direction search

**Canonical Game profile:** [`GAME_FRONT_HALF_EXTERNAL_REFERENCE_PROFILE.md`](GAME_FRONT_HALF_EXTERNAL_REFERENCE_PROFILE.md).

The default first move for a new Game product is to learn from **successful, mature, comparable existing games**, not to generate an Ordivon-internal GameForm portfolio and treat that portfolio as product authority. Steamworks' Tag Wizard explicitly uses detailed genre/subgenre, player activities, mechanics, visuals, themes and similar titles as a similarity surface; use platform/current-market evidence to construct bounded reference classes. Popularity alone is not a design or feasibility score.

```text
External comparable references
→ direct play / teardown
→ bounded baseline reproduction
→ Human baseline validation
→ controlled subtraction / variation / recombination
→ G0 Game Definition
```

**Divergent/convergent process skeleton:** Design Council Double Diamond remains `DIRECT_ADOPT` for generic search discipline, but Discover is seeded by external reference evidence and unresolved player/product opportunity rather than internal novelty generation alone.

**Game-design lenses:** MDA and other mature methods remain `REFERENCE_ONLY`; they can structure teardown and causal hypotheses without becoming universal Game authority.

**Industry precedent:** Nintendo's published *Echoes of Wisdom* developer interview documents parallel gameplay prototyping and a major direction change after features/feel could be tested. It is evidence for prototype-led learning, not a normative standard.

Disposition:

```text
Steam/platform similarity + current catalogue evidence  DIRECT_ADOPT as reference-class input
External successful mature games                         PRIMARY BASELINE MATERIAL
Double Diamond                                           DIRECT_ADOPT process skeleton
MDA / mature game-design lenses                          REFERENCE_ONLY teardown aids
GAME_FRONT_HALF_EXTERNAL_REFERENCE_PROFILE               PROFILE Game-specific composition only
Game Foundations / old Pre-G0 search                     SUPPORT: coverage/falsifiers/apparatus only
G0–G8                                                    PROFILE project commitment projection only
```

Sources:
- Steamworks Tags / similar titles: https://partner.steamgames.com/doc/store/tags
- Design Council, Double Diamond: https://www.designcouncil.org.uk/our-resources/the-double-diamond/
- AAAI MDA paper: https://aaai.org/papers/ws04-04-001-mda-a-formal-approach-to-game-design-and-game-research/
- Nintendo, *Ask the Developer: The Legend of Zelda: Echoes of Wisdom*: https://www.nintendo.com/sg/interview/bdge/index.html

### 2.2 Requirements and acceptance definition

**Direct standard:** ISO/IEC/IEEE 29148:2018 Requirements engineering.

Use it for requirements processes and information-item discipline. Game does not need a parallel generic requirements-engineering standard.

Disposition:

```text
requirements lifecycle / information items     DIRECT_ADOPT ISO/IEC/IEEE 29148
Experience Intent / Playable Semantics          PROFILE Game-specific requirement content
Game-specific falsifiers / acceptance oracles   PROFILE
```

Source:
- https://www.iso.org/standard/72089.html

### 2.3 Product quality and quality in use

**Direct standards:**

- ISO/IEC 25010:2023 product quality model.
- ISO/IEC 25019:2023 quality-in-use model.

Use 25010 characteristics to structure technical/product quality requirements and acceptance criteria. Use 25019 when the claim is about stakeholders using the product in a specified context of use.

Do not collapse the two:

```text
ProductQuality != QualityInUse
```

Game-specific playability, rules, fairness, legibility and experience hypotheses are profiles/requirements mapped onto the external models, not a replacement quality standard.

Sources:
- https://www.iso.org/standard/78176.html
- https://www.iso.org/standard/78177.html

### 2.4 Human-centred design, usability and player research

**Direct standards:**

- ISO 9241-210:2019 human-centred design activities across the interactive-system lifecycle.
- ISO 9241-11:2018 usability concepts; usability is an outcome of use.
- ISO 20252:2026 market, opinion and social research / insights / data analytics service requirements.

**Ethics/professional practice:** ICC/ESOMAR International Code 2025 where its research/data-analytics scope applies.

**Game-specialist method guidance:** Games User Research practice for choosing playtest methods from the research objective, separating measurement/understanding and behaviour/opinion, and using playtests to inform decisions rather than as milestones.

Disposition:

```text
HCD lifecycle                         DIRECT_ADOPT ISO 9241-210
usability meaning/context             DIRECT_ADOPT ISO 9241-11
research-service quality              DIRECT_ADOPT ISO 20252:2026 when applicable
research ethics / participant duty    DIRECT_ADOPT applicable ICC/ESOMAR principles
playtest method selection             DIRECT_ADOPT mature GUR practice
Game claim families                   PROFILE only
PlayerEvidenceContract                LEGACY NAME; treat as GamePlayerEvidenceProfile,
                                      not a standalone research standard
```

Sources:
- https://www.iso.org/standard/77520.html
- https://www.iso.org/standard/63500.html
- https://www.iso.org/standard/88881.html
- https://standards.esomar.org/assets/documents/icc-esomar-code-2025.pdf
- https://gamesuserresearch.com/choose-the-right-playtest-method/
- https://gamesuserresearch.com/five-essential-playtests-throughout-development/

### 2.5 Playtest execution

When a public/closed external-player mechanism is needed, use a platform-native service instead of building a Game-local recruitment/access/release surrogate.

Steam Playtest is a mature example: a separate child appID can gate playtest access while remaining separated from the main app's reviews/wishlists.

Disposition:

```text
playtest objective / claim / population       Game + Research E2E PROFILE
participant research method                   ISO/GUR external practice
access / build delivery / enrollment          PLATFORM_NATIVE (e.g. Steam Playtest)
raw evidence provenance                       Research/Artifact boundary
```

Source:
- https://partner.steamgames.com/doc/features/playtest

### 2.6 Accessibility

**Game-specific mature guidance:** Xbox Accessibility Guidelines (XAG) v3.2.

**Web/UI normative target where applicable:** WCAG 2.2 W3C Recommendation.

XAG explicitly positions itself as game-development best practice/guardrails and test guidance rather than a legal-compliance certificate. Game should adopt the criteria and scoping structure directly rather than inventing an Ordivon accessibility checklist.

Disposition:

```text
gameplay accessibility                DIRECT_ADOPT XAG as design/test baseline
web/browser surfaces                  DIRECT_ADOPT applicable WCAG 2.2 criteria
Game-specific access condition        PROFILE
Human accessibility-fit claim         requires relevant Human/context evidence
```

Sources:
- https://learn.microsoft.com/en-us/xbox/accessibility/guidelines
- https://www.w3.org/TR/WCAG22/

### 2.7 Population telemetry and controlled experiments

Do not build a generic Game A/B experimentation platform merely because D8 needs causal population evidence.

**Mature mechanism:** PlayFab Experiments provides managed randomized variants, target audiences, experiment state, statistical scorecards and sample-ratio-mismatch checks; Microsoft experimentation literature documents the same core separation of randomization, treatment assignment, logging and analysis at scale.

**Metric framing:** HEART goal→signals→metrics is a useful mature UX measurement pattern, but remains `REFERENCE_ONLY` rather than a Game standard.

Disposition:

```text
experiment hypothesis / Game value interpretation     Game + Research PROFILE
random assignment / variant delivery / scorecard      PLATFORM_NATIVE (e.g. PlayFab)
telemetry storage/query                                PLATFORM_NATIVE / Operations owner
statistical experiment mechanics                      DIRECT_ADOPT mature controlled-experiment practice
metric goal→signal→metric mapping                      PROFILE/REFERENCE_ONLY HEART
ProductValue                                           never inherited from metric uplift by identity
```

Sources:
- https://learn.microsoft.com/en-us/xbox/playfab/live-service-management/game-configuration/experiments/
- https://www.microsoft.com/en-us/research/publication/online-experimentation-at-microsoft/
- https://research.google/pubs/measuring-the-user-experience-on-a-large-scale-user-centered-metrics-for-web-applications/

### 2.8 Software/product lifecycle

**Direct current standard:** ISO/IEC/IEEE 12207:2026.

It provides the common framework for software lifecycle processes across supply, development, operation, maintenance and disposal. Game G0–G8 remains a project-specific commitment view; it must not present itself as an alternative generic software lifecycle standard.

Disposition:

```text
generic software lifecycle               DIRECT_ADOPT ISO/IEC/IEEE 12207:2026
Game G0–G8                                PROFILE / coordination projection
Game Development Core D1–D8              ROUTING VIEW only
Engineering E2E                           execution/falsification implementation
```

Source:
- https://www.iso.org/standard/90219.html

### 2.9 Build provenance, SBOM and open-source license compliance

**Direct mechanisms/standards:**

- SLSA v1.2 for build/source provenance and supply-chain assurance.
- SPDX 3.0 as the current SPDX information model/specification; do not misstate it as already-final ISO/IEC 5962 edition 2 while that ISO revision remains in progress.
- ISO/IEC 5230:2020 OpenChain for a quality open-source license compliance programme; confirmed current in 2026.

Disposition:

```text
build/source provenance              DIRECT_ADOPT SLSA
SBOM/license/component exchange      DIRECT_ADOPT SPDX
open-source license compliance       DIRECT_ADOPT ISO/IEC 5230 where applicable
Game asset/product rights semantics  PROFILE + actual legal/source evidence
Artifact generation/storage          Artifact E2E owner
```

Do not infer:

```text
SLSA PASS  => rights cleared
SPDX exists => every creative asset is legally distributable
OpenChain conformance => all non-open-source media rights are cleared
```

Sources:
- https://slsa.dev/spec/v1.2/
- https://spdx.dev/use/specifications/
- https://www.iso.org/standard/81039.html

### 2.10 Distribution and release

There is no benefit in inventing a universal Game-local release workflow that pretends all platforms have the same gate.

For Steam, directly consume Steamworks' native release model: separate Store Presence and Game Build checklists, Valve review, explicit permissions, and explicit release action. Future Xbox/PlayStation/Nintendo/mobile/web surfaces should likewise consume their own current platform gates through Distribution E2E profiles.

Disposition:

```text
platform review/checklists/permissions/release   PLATFORM_NATIVE
Artifact identity                                Artifact E2E
rights standing                                 Rights/owner evidence
Game release semantics                          PROFILE: which product/candidate is intended
cross-platform orchestration                    Distribution E2E
```

Sources:
- https://partner.steamgames.com/doc/store/releasing
- https://partner.steamgames.com/doc/store/review_process

## 3. What external practice does NOT eliminate

Direct adoption leaves a small irreducible Game layer.

```text
Game owns:
  Experience Intent
  Playable Semantics
  Mechanics / Dynamics / player-relevant causal hypotheses
  game rules, content and scenario meaning
  content/progression grammar
  game-specific claim questions and falsifiers
  interpretation of whether an observed effect matters for this game
  product-direction decisions

Game does NOT own:
  generic HCD methodology
  generic usability definition
  generic market-research service process
  generic requirements engineering
  generic software lifecycle process
  generic experimentation platform
  generic telemetry warehouse
  generic SBOM/provenance standard
  open-source compliance programme
  platform release workflow
  universal accessibility checklist
```

MDA remains a useful `REFERENCE_ONLY` causal vocabulary for Mechanics→Dynamics→Aesthetics and bidirectional design reasoning, but it is not a normative standard and is not sufficient to replace Game's richer semantic kernel.

Source:
- AAAI MDA paper: https://aaai.org/papers/ws04-04-001-mda-a-formal-approach-to-game-design-and-game-research/

## 4. D1–D8 becomes a routing profile, not a methodology

```text
D1 Intent / Audience
  → Double Diamond Discover/Define
  → ISO 9241-210 context of use
  → ISO 56002 innovation guidance

D2 Play Causality
  → Game Domain Kernel (irreducible Game semantics)
  → MDA/FADT as reference lenses

D3 Player Learning / Legibility
  → ISO 9241-210 / 9241-11
  → XAG / WCAG where scoped
  → Games User Research

D4 Evidence / Prototyping
  → Research E2E for question/estimand/protocol
  → ISO 20252 / ISO 9241 for Human studies
  → GUR for method choice
  → Steam Playtest or equivalent for external playtest delivery

D5 Content / Progression
  → Game-owned content/progression semantics
  → mature game-design references, not a new generic external service

D6 Expression / Feel
  → Game meaning + Studio production
  → XAG/WCAG accessibility criteria where applicable
  → Human study through ISO/GUR mechanisms

D7 Production Realization
  → ISO/IEC/IEEE 12207 lifecycle vocabulary
  → ISO/IEC/IEEE 29148 requirements
  → ISO/IEC 25010 product quality
  → Workstation/Engineering/Artifact E2E
  → SLSA/SPDX/OpenChain

D8 Product Ecology / Evolution
  → Distribution E2E + platform-native release
  → Operations E2E + platform-native analytics
  → PlayFab/other mature experimentation service
  → ISO/IEC 25019 quality-in-use
  → ISO 20252/Research E2E for population/Human interpretation
```

The routing view is useful because Game problems span multiple disciplines. It has no authority to redefine those disciplines.

## 5. Engineering E2E composition architecture

```text
                 External mature practices
                         │
     ┌───────────────────┼────────────────────┐
     │                   │                    │
Design/Research       Engineering         Real-world platforms
Double Diamond       29148 / 12207        Steam Playtest/Release
9241 / 20252          25010                PlayFab Experiments
GUR / XAG             SLSA/SPDX/OpenChain platform analytics
     │                   │                    │
     └─────────────── explicit profiles/adapters ───────────────┐
                                                                │
                    Ordivon horizontal E2Es                     │
Research ─ Engineering ─ Workstation ─ Artifact ─ Distribution ─ Operations
                                │                               │
                                └──────── GameEvidence edges ───┘
                                                │
                                      Game Domain Kernel
                                                │
                                      actual Game product
```

### Composition rules

1. **Reference, do not clone.** Store standard/profile identity and local mapping; do not copy a standard into a Game-owned schema unless machine interoperability forces an adapter.
2. **Profiles add; they do not redefine.** A Game profile can add `GameVersion`, `Scenario`, `ClaimFamily`, or `ExperienceIntent`; it cannot redefine what ISO usability or SLSA provenance means.
3. **Platform IDs stay platform-native.** Steam appID/build/depot/review state and PlayFab experiment/variant IDs remain external identities referenced by Distribution/Operations evidence.
4. **No synthetic compliance.** Repository tests may prove `ALIGNED_TO_PROFILE`; only actual required assessment/certification can justify a formal compliance/conformance claim.
5. **Currentness is explicit.** Every consumed standard/platform profile records edition/version and revalidation condition.
6. **Unknown stays unknown.** A missing Human study, rights review, platform review or population experiment is not replaced by local simulation.
7. **No generic local replacement by convenience.** If an external mechanism is temporarily unavailable, standing is `NOT_CONFIGURED/UNAVAILABLE/UNKNOWN`; absence does not authorize Game to build a permanent clone.
8. **Local extension requires falsifier.** New generic-seeming Game infrastructure must name the exact external mechanism tested, failure condition, lost Game-specific invariant and why a profile/adapter cannot solve it.

## 6. Reclassification of existing Ordivon Game mechanisms

```text
GAME_DEVELOPMENT_CORE D1–D8
  before: derived development responsibility/evidence model
  now:    routing/profile view over external mature mechanisms + irreducible Game semantics

GAME_PLAYER_EVIDENCE_PROGRAMME
  before: derived player-evidence ecology with PlayerEvidenceContract
  now:    Game claim/transport profile over ISO 9241, ISO 20252, GUR,
          controlled-experiment and platform execution mechanisms

G0–G8
  remains: Game project commitment/stage projection
  not:     replacement for ISO/IEC/IEEE 12207

Product Value evaluators
  remain:  Game-specific hypotheses/falsifiers
  not:     generic Human research, telemetry or experimentation infrastructure

Game E2E
  remains: graduated Game-specific evaluator/composition boundary
  not:     a replacement for the external owner mechanisms above
```

## 7. External validity / second-game generalization

No single mature external standard proves that one Game architecture generalizes to every game form.

Use existing external concepts rather than inventing a universal `GeneralityScore`:

```text
ISO/IEC 25019 context-of-use specificity
+ Research E2E explicit target population/context/claim boundary
+ independent replication on materially different GameForms
+ exact record of what changed and what was transported
```

Game E2E reopens only if a new real consumer falsifies the composition/kernel boundary.

## 8. Strategic-advantage evaluation

External frameworks can measure quality, usability, behavior and causal effects, but they do not decide Ordivon's strategic product thesis.

Use a comparative estimand instead of a bespoke maturity score:

```text
For a matched product/design task:
  external-baseline process
  versus
  external-baseline process + Ordivon leverage

Measure separately:
  search breadth
  time/cost to reject bad directions
  realization/iteration latency
  defect/failure discovery
  Human outcome
  population effect when available
  production throughput
```

Only differences supported by appropriate evidence may become an Ordivon advantage claim.

## 9. Reopen rule

Reopen this adoption policy only when one of the following is observed:

- an adopted external standard/mechanism changes materially;
- a real Game consumer cannot express a necessary Game-specific invariant through a profile/adapter;
- an external platform mechanism is demonstrated to be unsuitable for the required claim or execution condition;
- a local mechanism is shown to duplicate an external mature mechanism and can be removed;
- a formal compliance/conformance target becomes necessary.

Do not reopen merely because another framework exists.
