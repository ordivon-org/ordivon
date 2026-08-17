---
schema_version: 1
id: game.deep-foundations.gdf0-g
title: Ordivon Game Deep Foundations — GDF0-G Agent-Era Boundary Falsification
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-17
summary: Agent-era falsification round that uses synthetic players, dynamic rules, emergent conventions, open language action, rule-search Agents and persistent identity to attack GDF0's current Play/Game reconstruction. Finds no missing semantic primitive; instead Agent systems sharpen separations among competence/experience, proposal/authority, belief/current truth, language intent/effect, provider/Agent identity, generation/authorship and convention/legitimacy.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.deep-foundations.gdf0-f
  - game.foundations-research.r29
---
# Ordivon Game Deep Foundations — GDF0-G

## 0. Why Agent-era pressure matters

G is not an `AI games` survey.

It asks whether pre-Agent Play/Game theory accidentally fused variables that human participation usually kept correlated:

```text
competent player ↔ experiencing human
speaker ↔ social member
rule proposer ↔ possible authority holder
stable person ↔ stable biological body
natural-language intent ↔ interpretable action
creator ↔ author ↔ community-recognized origin
```

Agent systems can break these correlations.

That makes them unusually good falsifiers.

Canonical research inputs:

```text
evidence/gdf0-g/agent-era-evidence.json
scripts/gdf0-g/agent-boundary-probes.mjs
scripts/gdf0-g/audit-agent-boundaries.mjs
```

---

# 1. G1 — Synthetic competence does not collapse the experience boundary

Orak evaluates LLM agents across 12 real video games and explicitly measures game scores, strategies, visual-state handling and fine-tuning effects.

This makes a broad structural fact increasingly hard to ignore:

```text
GameExecution / competence
is measurable for synthetic systems
across materially different GameForms.
```

But none of those metrics establishes:

```text
PlayMode
felt enjoyment
attachment
subjective mastery
phenomenology
```

Therefore C11 survives its strongest Agent-era pressure:

```text
GameExecution != PlayExperience
```

This is not a claim that synthetic experience is impossible.

It is an evidence law:

```text
structural competence evidence
cannot be promoted into phenomenology evidence.
```

No new Game primitive is needed.

---

# 2. G2 — Dynamic rules force use/mention/currentness separation

Baba Is You is unusually valuable because rule statements are themselves manipulable world objects.

`Baba is LLM` reports that evaluated models struggle with dynamic rule changes and especially the use/mention distinction.

GDF0 interpretation:

```text
RuleText
!= RuleContent-as-current
!= Statement-about-a-rule
!= Action-that-changes-a-rule
```

The Game can contain all of these simultaneously.

So the effective state must distinguish:

```text
RuleRepresentation
RuleBelief
CurrentRuleTruth
RuleChangeAction
RuleAuthority
RuleHistory
```

This is exactly the pressure F6/F7/F9 already anticipated.

Agent-era dynamic rules do not reveal a new primitive.

They reveal why `rule` was too compressed.

---

# 3. G3 — RuleProposal != RuleAuthority

Agent systems make one old ambiguity especially dangerous:

```text
model can generate a plausible rule
```

can be mistaken for:

```text
rule has changed.
```

G rejects that collapse.

Canonical executable probe creates three cases over the same current rule head.

```text
fluent unauthorized proposal
→ NO_RULE_AUTHORITY
→ current rule truth unchanged

authorized current proposal
→ admitted
→ new exact rule head

authorized but stale proposal
→ STALE_RULE_HEAD
→ current rule truth unchanged
```

Therefore:

```text
RuleProposal != RuleAuthority
RuleBelief != CurrentRuleTruth
Fluency != Admission
Authority != CorrectBelief
```

A human referee can also be stale.

An Agent can also be authorized.

The important variable is the authority/currentness relation, not biological substrate.

---

# 4. G4 — Production Agent and Runtime Agent remain orthogonal

RuleSmith couples multi-Agent LLM self-play with Bayesian optimization over game-rule parameters.

Agents therefore occupy a design/search/evaluation loop over possible rule configurations.

That supplies strong real pressure for:

```text
ProductionAgentNeed != RuntimeAgentNeed
```

and also:

```text
CandidateRule
!= DeployedRule
```

The Agent can search, recommend and evaluate a rule without owning deployment authority or appearing in shipped gameplay.

This directly protects Ordivon Game from a recurring historical error:

```text
Agent useful for making Game
→ therefore Game should contain Agent subjects.
```

No.

---

# 5. G5 — Convention emergence != one-message authority

Population experiments with communicating LLM agents show that shared conventions can emerge from repeated local interactions and can shift when committed minorities cross relevant tipping conditions.

This is important because F established that human GamePractice can also persist through distributed transmission and negotiation.

Agent populations therefore show a structural analogue:

```text
local interactions
→ repeated coordination
→ population-level convention
```

But the result strengthens rather than weakens the distinction:

```text
OneProposal
!= Convention
```

and:

```text
ConventionEmergence
!= InstitutionalLegitimacy
```

A convention can become descriptively current because participants converge on it.

Whether it is **authorized**, **legitimate**, **official** or **morally acceptable** is a separate relation.

F6 authority/provenance and F8 evaluation remain necessary.

---

# 6. G6 — Natural language can carry norms without becoming authority

Natural-language norm-evolution experiments show LLM agents generating and following normative strategies through dialogue in multi-Agent games.

This establishes that:

```text
NaturalLanguage
can encode/propose/negotiate normative policy.
```

It does not establish:

```text
NaturalLanguageUtterance
= authoritative rule mutation.
```

The same distinction applies to human language.

Speech can be:

```text
proposal
promise
claim
threat
instruction
vote
rule citation
rule change
```

only when the relevant institutional/game semantics make it count as such.

Thus Agent language adds scale and ambiguity, not a new F1-F9 coordinate.

---

# 7. G7 — Open language action does not abolish structured action

Werewolf language-agent research is useful because action is not limited to a tiny enumerated command list.

The LSPO approach explicitly maps free-form language into a latent strategic space for policy learning and maps strategy back into dialogue.

GDF0 does **not** infer that every language game has a hidden discrete action ontology.

The stronger conclusion is narrower:

```text
Open linguistic realization
can coexist with structured strategic distinctions.
```

Canonical probe makes this boundary explicit:

```text
utterance
→ interpreted/proposed intent
→ admission against current legal/effect surface
→ effect or rejection
```

Examples:

```text
"open the door"
→ structured intent OPEN_DOOR
→ admitted when legal
→ effect

"move north"
→ structured intent MOVE_NORTH
→ rejected when illegal
→ no effect

unresolved poetic/open request
→ no structured intent
→ no authoritative effect
```

Therefore:

```text
NaturalLanguageIntent != AuthoritativeEffect
LanguageBreadth != EffectAuthority
```

This preserves the older Ordivon law:

```text
Open intent + structured consequence
```

---

# 8. G8 — Open-ended goal vocabulary also does not require a new Goal primitive

Open-Universe Assistance Games explicitly model an unbounded/evolving space of possible goals represented in natural language.

This is important pressure against finite enum thinking.

But:

```text
OpenGoalVocabulary
!= NewGoalOntologyPrimitive
```

The system still requires:

```text
goal representation
uncertainty over interpretation
current evidence
policy/action
consequence
update
```

The thing that becomes open is the **representation/search space**, not the semantic need for goal/evaluation/state/action relations.

Thus Agent-era open intent mainly expands F7/F8/F9 surfaces.

---

# 9. G9 — Agent identity is not provider-model identity

Human participants historically encouraged an implicit shortcut:

```text
same body/person
≈ same player identity
```

Agents break it.

Canonical probe distinguishes:

```text
PrincipalIdentity
ProviderModel
Memory/History Head
Recognition
Authority
```

and demonstrates the intended semantics:

```text
same principal
+ provider model A → model B
can remain same Agent identity

same provider model A
+ principal 17 vs principal 18
are different Agent identities
```

Therefore:

```text
ProviderModelIdentity != AgentIdentity
```

This is already compatible with R24 identity/continuity.

The Game may care about the persistent social subject while infrastructure swaps models underneath it.

No new primitive appears.

---

# 10. G10 — Generated content/rules do not settle authorship or legitimacy

Agent-era creation creates another forced separation:

```text
Generation
Authorship
RuleAdmission
PracticeAdoption
CategoryRecognition
```

are different events.

An Agent may generate a complete rule set.

That does not imply:

```text
players adopted it
community recognizes it
institution authorizes it
Agent is sole author in the relevant social/legal sense
```

Likewise a human may author a proposed variant that no one plays.

Therefore:

```text
Generation != Authorship
Authorship != Authority
Authority != Adoption
Adoption != CategoryLegitimacy
```

This is strongly continuous with R20 Creation/Authorship and F's social-history results.

A clean empirical Agent-created-game-adoption study is not yet admitted in G, so this remains a protocol-level boundary rather than an observed community law.

---

# 11. G11 — AI co-creation can be rich without being Game

A highly responsive language/image/music/code co-creator can provide:

```text
adaptation
surprise
negotiation
memory
style
critique
```

without necessarily creating:

```text
GameStructure
```

So Agent responsiveness is not sufficient for gameness.

The correct variables remain:

```text
Creation / expression
Participant authorship
Responsive other
Rule/evaluation topology
Action/consequence structure
Practice/category
```

This preserves the earlier D14 lesson:

```text
responsive-other hypothesis
!= Agent-necessary Game
```

and R20:

```text
Generation != Creativity / Authorship
```

---

# 12. G12 — Moderator/adjudicator authority must be delegated, not inferred from intelligence

G retains a protocol-level test for AI moderator/referee roles.

A moderator may be:

```text
highly competent
neutral-seeming
fluent
consistent
```

and still lack authority if the relevant GamePractice/institution has not delegated it.

Conversely, a bounded automated referee can have legitimate technical authority if the participants/institution explicitly grant it.

Thus:

```text
Competence != Authority
Intelligence != Legitimacy
Automation != Illegitimacy
```

What matters is:

```text
grant
scope
currentness
appeal/override
provenance
community/institution recognition
```

This is a direct Game consumption of Ordivon's broader evidence/authority discipline.

---

# 13. Agent-era dissociation map

G can now state the main result compactly:

```text
Synthetic competence
        != PlayExperience

Language representation
        != effect authority

Rule proposal
        != rule authority

Rule belief
        != current rule truth

Convention convergence
        != institutional legitimacy

Provider/model identity
        != persistent Agent identity

Generation
        != authorship
        != adoption
        != category legitimacy

Production-Agent utility
        != Runtime-Agent necessity
```

These are not new primitives.

They are **anti-collapse laws** over existing coordinates.

---

# 14. What Agent-era research actually adds to Game Foundations

The strongest result is methodological:

> Agent systems are useful because they create counterexamples to human-era hidden correlations.

Humans made several relations look naturally bundled:

```text
speaker + subject + experiencer + authority-candidate + persistent identity
```

Agents make each dimension independently variable.

Therefore Agent-era Game research should ask:

```text
Which locus?
Which authority?
Which identity?
Which evidence?
Which effect surface?
Which representation?
Which phenomenology claim?
```

before asking whether something is `an Agent game`.

Call this:

# G-A DissociationPressure

```text
Agent-era novelty is often epistemically valuable
because it breaks historical correlations among roles,
not because it supplies a new universal Game component.
```

Status:

```text
N1 synthesis.
```

---

# 15. Strong Agent-era falsifiers of bad theories

## Bad theory: intelligent synthetic player implies Play

Falsified by evidence boundary:

```text
competence measurements do not establish experience.
```

## Bad theory: a generated rule becomes the game rule

Falsified by proposal/admission/currentness separation.

## Bad theory: natural language means unbounded effect authority

Falsified by language-intent/admission/effect separation.

## Bad theory: emergent convention is official rule

Falsified by descriptive convention vs authority/legitimacy distinction.

## Bad theory: model replacement means new Agent

Falsified by persistent principal/history identity model.

## Bad theory: same model means same Agent

Falsified by multiple principal identities over one provider model.

## Bad theory: Agent can help make a Game, therefore runtime Agent is constitutive

Falsified by RuleSmith/production-locus separation.

---

# 16. Machine probe results

Running:

```text
node scripts/gdf0-g/agent-boundary-probes.mjs
node scripts/gdf0-g/audit-agent-boundaries.mjs
```

checks the declared structural model.

Required results:

```text
fluent unauthorized rule proposal
→ rejected NO_RULE_AUTHORITY

authorized current proposal
→ admitted

authorized stale proposal
→ rejected STALE_RULE_HEAD

natural-language intent
→ may resolve to structured action
→ still requires admission before effect

same principal across provider replacement
→ identity can persist

same provider model across different principals
→ identity differs
```

These are Ordivon structural falsifiers, not empirical human/Agent psychology.

---

# 17. FoundationReopenCondition audit

This was the central G question.

Every Agent-era pressure remains expressible through current R29 coordinates:

```text
synthetic subject/player
→ F1/F2/F3/F9

persistent Agent identity/history
→ F1/F3/F5/F6

rule proposal/belief/currentness
→ F2/F4/F5/F6/F7

natural-language intent
→ F7/F8/F9

authoritative effect
→ F4/F6/F9

convention/practice legitimacy
→ F3/F5/F6/F8

generation/authorship/adoption
→ F3/F5/F6/F7/F9
```

No missing coordinate appears.

Current result:

```text
FoundationReopenCondition = NOT TRIGGERED
```

This is a strong result because Agent-era cases were selected specifically to stress authority, representation, identity and action boundaries.

---

# 18. Discovery ledger after G

## N0 — external evidence / rediscovery

```text
- LLMs can execute and be benchmarked across diverse video games.
- LLMs struggle with some dynamic-rule/use-mention reasoning.
- multi-Agent LLM populations can form conventions through local interaction.
- natural-language norms can emerge in simulated Agent populations.
- free-form language can carry strategic action in social-deduction games.
- open language goal spaces can be represented/inferred without finite goal enums.
- Agents can participate in production-time game balancing/rule search.
```

## N1 — Ordivon synthesis / strengthened laws

```text
G-A DissociationPressure
RuleProposal != RuleAuthority
RuleBelief != CurrentRuleTruth
NaturalLanguageIntent != AuthoritativeEffect
ModelFluency != Legitimacy
ProviderModelIdentity != AgentIdentity
Generation != Authorship != Adoption != CategoryLegitimacy
ConventionEmergence != InstitutionalLegitimacy
ProductionAgentNeed != RuntimeAgentNeed
```

plus strengthened:

```text
C11 Structural/Experiential Dissociation
F-E FrameAuthorityLocus
F-F CategoryFeedback
EffectiveRuleTopology
```

## N2

```text
NONE newly earned.
```

## N3

```text
NONE.
```

---

# 19. Strongest GDF0-G laws

```text
1. Synthetic competence != PlayExperience evidence.
2. RuleText != RuleBelief != CurrentRuleTruth != RuleAuthority.
3. RuleProposal != RuleAdmission.
4. Fluency/intelligence != authority/legitimacy.
5. NaturalLanguageIntent != authoritative effect.
6. Open action/goal vocabulary expands representation/search space, not semantic primitives.
7. Convention emergence != institutional legitimacy.
8. Provider/model identity != persistent Agent identity.
9. Generation != authorship != adoption != category recognition.
10. Production Agent usefulness != Runtime Agent necessity.
11. Agent-era systems mainly expose hidden human-era correlations rather than a new Game atom.
12. Current F1-F9 substrate survives deliberately adversarial Agent-era pressure.
```

---

# 20. GDF0-H exact frontier

G was the final planned boundary round.

It did not produce a FoundationReopenCondition.

Therefore GDF0 should **not** continue with more alphabetic rounds by habit.

The exact next round is:

# GDF0-H — Final Falsification, Reconstruction & Freeze

H must:

```text
1. attack A-G as one combined model, not preserve every intermediate candidate;
2. retire obsolete terms and duplicate N1 syntheses;
3. decide whether Play and Game require separate foundations documents/models;
4. produce final target map: Structure / Enactment / Experience / Practice / Category / External Coupling;
5. state what Game owns versus Human / Media / World;
6. freeze only mechanisms that survived cross-context + matched + social-cultural + Agent-era pressure;
7. write explicit FoundationReopenConditions;
8. derive the dependency graph for later Game Deep Foundations;
9. decide first next deep branch based on dependency/weakness rather than product need.
```

Likely first downstream branch remains:

```text
Action / Control / Skill / Embodiment
```

but H must earn that dependency rather than inherit it from the original plan.

---

# Primary external pressure anchors used in G

- van Wetten, Plaat & van Duijn (2025), *Baba is LLM: Reasoning in a Game with Dynamic Rules*, arXiv:2506.19095.
- Zeng et al. (2026), *RuleSmith: Multi-Agent LLMs for Automated Game Balancing*, arXiv:2602.06232.
- Park et al. (2025), *Orak: A Foundational Benchmark for Training and Evaluating LLM Agents on Diverse Video Games*, arXiv:2506.03610.
- Ashery, Aiello & Baronchelli (2024), *The Dynamics of Social Conventions in LLM populations*, arXiv:2410.08948.
- Horiguchi, Yoshida & Ikegami (2024), *Evolution of Social Norms in LLM Agents using Natural Language*, arXiv:2409.00993.
- Xu et al. (2025), *Learning Strategic Language Agents in the Werewolf Game with Iterative Latent Space Policy Optimization*, arXiv:2502.04686.
- Li et al. (2025), *Optimus-2: Multimodal Minecraft Agent with Goal-Observation-Action Conditioned Policy*, arXiv:2502.19902.
- Ma et al. (2025), *Open-Universe Assistance Games*, arXiv:2508.15119.
