---
schema_version: 1
id: game.deep-foundations.gdf0-f
title: Ordivon Game Deep Foundations — GDF0-F Social, Cultural and Historical Constitution
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-17
summary: Social/cultural/historical pressure on PlayPractice, GameCategory, rule transmission and institutional authority. Cross-cultural game/play evidence rejects competition, central authorship, exact rules and social negotiation as universal requirements; longitudinal and historical evidence shows practices and rules are transmitted, negotiated and institutionalized; matched framing evidence shows category/frame cues can causally feed back into behavior without constituting GameStructure. Reconstructs GameCategory as historically transmitted social classification with causal framing effects rather than mechanical essence.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.deep-foundations.gdf0-a
  - game.deep-foundations.gdf0-b
  - game.deep-foundations.gdf0-c
  - game.deep-foundations.gdf0-d
  - game.deep-foundations.gdf0-e
  - game.foundations-research.r29
---
# Ordivon Game Deep Foundations — GDF0-F

## 0. Question

E separated three questions:

```text
A. causal participant relation
B. effective action structure
C. cultural category
```

A and B already have strong mechanistic/intervention handles.

F asks whether C can be reduced to them.

> Why does a community/history stabilize some practices as `game`, `sport`, `play`, `gambling`, `ritual`, `training` or `work`, how do rules persist without one designer/artifact, and do these categories feed back causally into what participants do?

F also tests a second unresolved problem:

> Does PlayFrame require social negotiation, or can one participant sustain a frame alone?

Canonical evidence ledger:

```text
evidence/gdf0-f/social-cultural-historical-evidence.json
scripts/gdf0-f/audit-social-cultural-evidence.mjs
```

---

# 1. F's first correction — cross-cultural variation is structured, not noise

The Austronesian Game Taxonomy contains 907 ethnographic/historical game descriptions and was explicitly built to expand research beyond older definitions that treated competition as part of the definition of games.

Its coding distinguishes multiple goal-interdependence structures, including:

```text
competitive
cooperative group vs cooperative group
fully cooperative group
solitary / non-interdependent structures
other mixed forms
```

The filtered subset reported by the authors contains substantial variation across cultural groups; competitive forms are common, but they are not the whole space.

Therefore:

```text
Competition != universal Game requirement
```

This is stronger than merely pointing to one modern cooperative game because it survives a broad historical/cross-cultural corpus.

At the same time, cross-cultural play research using the Six Cultures material and eHRAF shows that children's observed play forms, materials, spatial opportunities and relations to adult work differ with local social/ecological conditions.

Therefore:

```text
PlayBehavior / PlayPractice
is culturally patterned.
```

This does **not** imply unlimited relativism. It means the mechanism space must distinguish:

```text
species/developmental capacities
from
culturally available practices, materials, meanings and institutions.
```

---

# 2. F1 — Culture selects and shapes the reachable Play/Game repertoire

Cross-cultural evidence supports a simple but important causal architecture:

```text
Developmental / bodily / cognitive capacities
              ×
Available materials / spaces / peers / adult models
              ×
Cultural permission / obligation / work ecology / norms
              ↓
Reachable PlayPractice repertoire
```

This avoids two bad extremes:

```text
Universalism error:
all children everywhere naturally instantiate the same Play forms if left alone.

Relativism error:
there are no cross-context mechanisms because culture differs.
```

The stronger view is:

```text
shared capacities
× different environments/practices
→ structured cultural variation.
```

Status:

```text
F-A CulturalPatterning = N1 synthesis
```

---

# 3. F2 — Folk/playground games directly falsify CentralDesigner ontology

Buchholz's four-year longitudinal ethnography of a multi-age playground community is unusually important for Ordivon.

The local game had persisted for nearly a decade through embodied/oral transmission before an `official` rulebook was introduced.

The written rulebook did not simply become authority.

Instead it triggered disputes over:

```text
ownership
authorship
who may change the rules
whose memory counts
what tradition is
what text can legitimately fix
```

and written transmission coexisted with continued oral/embodied negotiation.

Therefore:

```text
CentralDesigner != necessary for stable GamePractice

WrittenRulebook != automatic final RuleAuthority

Codification != AuthorityCapture
```

This is a direct real-world counterpart to Ordivon's EffectiveRuleTopology.

---

# 4. F3 — Rule transmission is generative, not exact-copy persistence

Children's singing-game ethnography likewise documents variation, transmission and innovation across text, music and movement.

This suggests:

```text
Transmission != ExactReplication
```

A practice can remain historically continuous while individual realizations mutate.

The same general issue appears in traditional games, board-game diffusion and sport history.

Therefore exact rule equality is too strong for longitudinal Game identity.

Working law:

```text
GameIdentity_t→t+1
can survive bounded rule/content variation
when enough practice/lineage/authority continuity remains.
```

But this is not permission to call any descendant `the same game`.

The unresolved variable is **identity-relevant continuity**:

```text
which rules/roles/goals/practices/history are treated as constitutive
by the relevant community/institution?
```

Status:

```text
F-B ExactRulesetIdentity → REJECTED
Lineage/PracticeContinuity → RETAIN as N1 identity model
```

R24 already supplies identity/continuity coordinates; no new semantic primitive is required.

---

# 5. F4 — Formalization changes governance, not merely representation

The rulebook ethnography exposes a deeper mechanism.

Turning an oral/embodied convention into text changes more than storage format.

It can change:

```text
who can point to authority
who can contest interpretation
who appears to own the rule
how disagreements are resolved
how changes are proposed
what counts as evidence of precedent
```

So:

```text
RuleRepresentation
can causally modify
RuleGovernance.
```

This is an important cross-link to Media/World:

```text
Representation != Authority
```

but representation can alter authority relations when social actors treat it as evidence/precedent.

Strong law:

```text
Codification can be constitutive of governance without being constitutive of all gameplay mechanics.
```

Status:

```text
F-C CodificationGovernanceEffect = N1 synthesis
```

---

# 6. F5 — Sport institutionalization shows that GamePractice can become governed at a new scale

Historical sport research gives the long-timescale version of the playground case.

Vamplew's analysis distinguishes constitutive, auxiliary and regulatory rules and documents how gambling, fair-play ideology, economics, technology and law have shaped sports regulation.

Comparative work on traditional sports and esports likewise describes institutionalization through organizations, standardized competitions and governance/cultural output.

So institutionalization is not:

```text
GameMechanic + institution = same thing but official.
```

It can modify:

```text
RuleAuthority
Eligibility
Standardization
Evidence/record requirements
Sanctions
Competition topology
Economic coupling
Spectatorship
Professional roles
Category legitimacy
```

Therefore:

```text
Institutionalization
= governance / legitimacy / scale transformation
```

rather than a new Game essence.

Status:

```text
F-D InstitutionalizationTransformation = N1 synthesis
```

---

# 7. F6 — Game/Sport identity does not require immutable rules

Historical sport rule change pressures an earlier GDF0 result:

```text
StableRuleContent != required.
```

A sport can remain recognizable across substantial rule/equipment/eligibility/regulatory changes when institutions and participants treat the continuity as legitimate.

Conversely, a small rule overlay can produce a new recognized category/practice in speedrunning.

Therefore identity does not scale monotonically with rule-diff size.

```text
LargeRuleChange can preserve Identity.
SmallRuleChange can create distinct Practice/Category.
```

The deciding structure includes:

```text
lineage
recognized authority
participant/community practice
purpose/goal continuity
institutional legitimacy
historical narrative
```

This strongly warns against:

```text
GameIdentity = hash(ruleset)
```

for social/historical identity.

Executable implementation identity may still require exact hashes; cultural GameIdentity does not.

---

# 8. F7 — Social PlayFrame is negotiated through metacommunication and enactment

Social pretend-play studies separate:

```text
negotiation of roles / object properties / actions
from
actual enactment of pretend episodes.
```

Observed preschool social pretense contains both.

Animal social-play work from D similarly shows play solicitation/signalling, role-sensitive restraint and other interactional regulation.

The common abstraction is:

```text
SocialFrameMaintenance =
signals / proposals
+ mutual interpretation
+ enacted conformity / repair
+ continuation / termination
```

Importantly:

```text
FrameMaintenance != explicit verbal agreement.
```

A gesture, restraint pattern, repeated role enactment or correction can all participate.

This is a useful future Social Play foundation, but F refuses to generalize it to all Play.

---

# 9. F8 — Solitary pretense kills SocialNegotiation as a universal requirement

Naturalistic studies observe solitary pretend play in young children without an active co-player.

Therefore:

```text
ContemporaneousSocialNegotiation
!= necessary for PretendPlay / PlayFrame.
```

A participant can locally sustain:

```text
object substitution
imagined role
counterfactual state
self-generated constraint
sequence coherence
```

alone.

But a crucial correction remains:

```text
Solitary episode
!= socially uncaused semantics.
```

The child may have acquired language, roles, scripts and object meanings through prior culture/social learning.

Thus F distinguishes:

```text
FrameOrigin
from
FrameMaintenanceLocus.
```

A frame can have culturally learned origins and be maintained individually in the current episode.

Status:

```text
F-E FrameAuthorityLocus = N1 synthesis
```

with possible loci:

```text
self
dyad/group
community
institution
artifact/system
hybrid
```

This is a derived authority view over F6, not a new primitive.

---

# 10. F9 — GameCategory is not a passive label

E increasingly separated cultural category from mechanics.

F adds a crucial correction: `category` may still be causally active.

Lieberoth's framing experiment held a serious discussion activity substantially similar while changing game vernacular/artifacts/mechanics. A framing condition with game artifacts/vernacular but without the full competitive mechanics produced much of the psychological effect on interest/enjoyment seen in the fuller game condition.

Economic-game label experiments similarly show that calling the same payoff structure `The Teamwork Game` versus `The Paying Taxes Game`, or inducing comparable spontaneous frames, can alter contributions.

Therefore:

```text
Category / Frame cue
→ activates expectations / norms / interpretations
→ can alter participant policy or experience.
```

So reject the weak view:

```text
GameCategory = epiphenomenal post-hoc label only.
```

But also reject:

```text
GameCategory cue = GameStructure.
```

A label can change interpretation without changing the actual transition/constraint system.

---

# 11. F10 — Category is better modeled as a feedback loop

A stronger synthesis now becomes possible:

```text
Historical Practice
      ↓
Community / Institutional Recognition
      ↓
Category Labels / Expectations / Norms
      ↓
Participant Interpretation / Entry / Authority Expectations
      ↓
Enactment / Rule Negotiation / Experience
      ↓
New Practice / Records / Institutions
      └────────────→ feeds back
```

Call this only a law, not a new entity:

# F-F CategoryFeedback

```text
Social category can be both an outcome of historical practice
and a causal input into later enactment.
```

This resolves the false choice:

```text
Category is either real mechanism
OR
mere arbitrary label.
```

It can be historically constructed **and** causally efficacious through expectations/authority/norms.

Novelty status:

```text
N1 synthesis.
```

Adjacent framing, institutional and cultural-practice theories already contain these ingredients; no N2 claim.

---

# 12. F11 — Cross-cultural correlations imply coupling, not one-way reflection

Classic and replicated cross-cultural studies report associations between game-type repertoires and wider social organization, such as strategy games and social complexity.

These results are historically important but easy to overread.

They do **not** identify direction:

```text
Society → Games
Games → Socialization → Society
shared ecology → both
coevolution
sampling/coding artifact
```

are competing possibilities.

Therefore the correct GDF0 law is:

```text
GamePractice is culturally coupled,
not proven to be a one-way mirror of society.
```

Future causal/phylogenetic work would need to distinguish these models.

The Austronesian dataset is particularly useful because it exposes historical game descriptions and phylogenetic matching for precisely these future tests.

---

# 13. F12 — Competition is not the invariant; normatively differentiated participation is more robust

Older anthropological game definitions often required:

```text
organized play
competition
two or more sides
winner criterion
agreed rules
```

The Austronesian corpus directly demonstrates why this is too restrictive: cooperative and solitary rule-based games disappear under such a definition.

What survives more broadly is closer to:

```text
some participant-recognizable normative structure
that differentiates what actions/states/roles count within the practice.
```

But GDF0 already knows this is too broad for Game identity because ritual, law and workflow also satisfy it.

Thus F does **not** resurrect a structural essence.

It only records:

```text
Competition is cultural/form variation,
not foundational gameness.
```

---

# 14. Reconstructing GameCategory after F

F gives a much more defensible status to `GameCategory`.

It is neither:

```text
A. a primitive natural-kind essence recoverable from mechanics alone
```

nor:

```text
B. a causally inert word that science can ignore.
```

Working model:

```text
GameCategory =
a historically transmitted, socially recognized classification/practice identity
whose boundaries depend on lineage, institutions, language and community authority,
and whose recognition can feed back into participant expectations and enactment.
```

This explains why:

```text
same mechanics can be framed differently;
related practices can diverge into new categories;
changing institutions can standardize one variant;
labels can change behavior without changing mechanics;
exact rules can change while category identity persists.
```

Status:

```text
N1 reconstruction.
```

It is not claimed as a newly discovered academic theory.

---

# 15. Mechanistic Game Science vs Category/Practice Science

E suggested separating these programmes.

F confirms the split but also adds their coupling.

## Mechanistic Game Science

Studies:

```text
agency scaffolds
challenge / skill
information
feedback
rule/evaluation topology
control
consequence
learning
player-value coupling
```

## Social-Historical Game Practice / Category Science

Studies:

```text
rule transmission
practice lineage
community authority
institutionalization
legitimacy
category labels
cultural variation
ritual/sport/work/gambling boundaries
```

## Coupling layer

Studies:

```text
how category/frame expectations alter enactment;
how practices change effective rules;
how institutions change consequence coupling;
how mechanics feed back into community/history.
```

Therefore these are separate but not isolated owners.

---

# 16. What F rejects

```text
Competition is necessary for Game
→ REJECTED.

Social negotiation is necessary for PlayFrame
→ REJECTED.

Central designer is necessary for GameStructure
→ REJECTED.

Written rulebook is final rule authority
→ REJECTED.

GameIdentity = exact ruleset identity
→ REJECTED for social/historical identity.

GameCategory is mechanically deducible
→ NOT SUPPORTED.

GameCategory is causally inert
→ REJECTED as too weak.

Institutionalization creates Game essence
→ REJECTED.

Culture variation means anything counts
→ REJECTED.
```

---

# 17. New/strengthened GDF0-F laws

```text
F-A CulturalPatterning
Shared capacities × different cultural opportunity/practice structures
produce structured variation in PlayBehavior/Practice.

F-B Practice/Lineage Continuity
GameIdentity can persist across bounded rule/content variation;
exact ruleset equality is not cultural identity.

F-C Codification Governance Effect
Representing rules in a new authoritative medium can change governance,
authorship and dispute resolution without automatically replacing prior authority.

F-D Institutionalization Transformation
Institutionalization changes scale, legitimacy, standardization,
rule authority, eligibility and external coupling rather than adding a hidden Game essence.

F-E Frame Authority Locus
A PlayFrame can be maintained by self, group, community, institution,
artifact/system or hybrids; contemporaneous social negotiation is not universal.

F-F Category Feedback
Category recognition is historically produced but can feed back causally
through expectations, norms and authority into later enactment.

F-G Category/Mechanism Nonidentity
Mechanistic similarity != cultural category identity,
and cultural category identity != mechanical equivalence.
```

All are N1 syntheses/current research laws.

No N2 or N3 promotion occurs in F.

---

# 18. Agent-era implications

Agents can already participate in some structural/social loci without any phenomenology assumption.

Possible roles:

```text
rule proposer
rule interpreter
moderator
community participant
historical record analyst
opponent/co-player
production designer
category recommender
```

But Agent participation raises authority questions rather than automatically creating a new Game type:

```text
Who may amend a community rule?
Does an Agent-generated convention become legitimate if players adopt it?
Can an Agent moderator become authoritative without community delegation?
How is provenance of rule changes retained?
```

These are already expressible through:

```text
F3 relation
F5 time/history
F6 authority/provenance
F7 representation
F8 evaluation
F9 action/policy
```

No claim about Agent PlayExperience is required.

---

# 19. FoundationReopenCondition audit

F adds no missing semantic coordinate.

Social/cultural/history pressure is representable through existing foundations:

```text
practice lineage → F3/F5/F6
rule transmission → F4/F5/F6/F7
institution → derived entity/relation/authority view
category label → F1/F7 + social relation/history
frame effect → F7/F8/F9 coupling
solitary/social frame locus → F3/F6/F7/F8
```

Current result:

```text
FoundationReopenCondition = NOT TRIGGERED
```

This is increasingly strong evidence that R29 is a genuine semantic substrate rather than merely a product-biased schema.

---

# 20. Discovery ledger after F

## N0 — external evidence / rediscovery

```text
- competition is not the whole cross-cultural rule-game space;
- children's play forms vary with cultural/social opportunity structure;
- folk/playground games can be orally/embodiedly transmitted and changed by children;
- rule codification can generate authority/authorship disputes;
- sport rules/institutions change historically under social/economic/legal pressure;
- social pretend play uses negotiation and enactment;
- solitary pretend play exists without contemporaneous co-player negotiation;
- framing/category cues can alter interest/enjoyment or social decisions without deep rule changes.
```

## N1 — Ordivon synthesis

```text
F-A CulturalPatterning
F-B Practice/LineageContinuity
F-C CodificationGovernanceEffect
F-D InstitutionalizationTransformation
F-E FrameAuthorityLocus
F-F CategoryFeedback
F-G CategoryMechanismNonidentity
```

plus earlier:

```text
C0 CoupledLudicConfiguration
C3 ModelConflictProtocol
C4 EvaluationLayering
C7 MechanismFamilyView
C10 ProgressSeparation
C11 Structural/ExperientialDissociation
C12 downscoped configuration causal-factorization
E-A/B/C operational laws
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

# 21. Strongest GDF0-F laws

```text
1. Competition != universal Game requirement.
2. PlayPractice is culturally patterned without being culturally arbitrary.
3. CentralDesigner != necessary for stable GamePractice.
4. WrittenRulebook != automatic RuleAuthority.
5. Transmission != ExactReplication.
6. Social/historical GameIdentity != ExactRulesetIdentity.
7. Codification can change governance because representation can become authority evidence.
8. Institutionalization transforms governance, legitimacy, standardization and external coupling rather than supplying Game essence.
9. Contemporaneous SocialNegotiation != necessary for PlayFrame; solitary pretense exists.
10. Frame origin != current frame-maintenance locus.
11. GameCategory is neither mechanical essence nor causally inert label.
12. Category/frame recognition can alter participant interpretation and behavior.
13. Category can be historical outcome and later causal input: CategoryFeedback.
14. Mechanistic similarity != cultural category identity.
15. Game repertoires are culturally coupled to wider society, but correlation does not prove one-way reflection or function.
```

---

# 22. What remains unresolved after F

F narrows GDF0 substantially, but several hard problems remain:

```text
1. Is there any cross-cultural invariant of GameCategory beyond practice lineage + normative differentiation + recognition?
2. Which dimensions of a rule/practice may vary while community GameIdentity remains stable, and when does a variant become a new Game?
3. How do frame signals/repair work in adult social play, sport and online play beyond animal/child pretend evidence?
4. How does solitary PlayMode arise from prior culturally learned meanings without current social enforcement?
5. Can cultural phylogenetic methods distinguish society→game, game→socialization and coevolution models?
6. How do institutions acquire legitimate rule authority, and how is authority lost/contested?
7. How should cross-linguistic differences in play/game lexical categories map to Ordivon's non-lexical mechanism model?
8. What happens when Agent participants become persistent members of rule-making communities?
```

Some of these belong to later Social Play / Institution / Culture deep foundations rather than GDF0 itself.

---

# 23. GDF0-G exact frontier

A dedicated Agent-era round is now justified, but only because Agent systems create **new dissociations of locus, authority, identity and frame**, not because AI novelty deserves its own theory.

# GDF0-G — Agent-Era Boundary Falsification

G should attack the current reconstruction with:

```text
synthetic player with no phenomenology claim
AI co-player negotiating rules
AI moderator/adjudicator
AI-generated mutable rules
human-AI co-creation without GameStructure
Agent-created game adopted by community
persistent Agent entering a folk/community practice
LLM language-as-action / open-intent interaction
Agent with false belief about current rules
Agent rule proposal vs authoritative rule change
multiple Agents with conflicting rule memories/provenance
```

Questions:

```text
- Does GameExecution still separate cleanly from PlayExperience?
- Does EffectiveRuleTopology handle Agent proposals vs authoritative changes?
- Can category/practice legitimacy be represented without treating Agent output as authority?
- Does open natural language create a new Game primitive or only a wider Action/Representation surface?
- Can Agent identity/continuity matter to GamePractice without new semantic foundations?
- Does any Agent-era case finally trigger R29 FoundationReopenCondition?
```

If G does not break the substrate, GDF0-H should become final adversarial reconstruction/freeze rather than continuing alphabetically by habit.

---

# Evidence anchors used in F

- Leisterer-Peoples et al. (2021), *The Austronesian Game Taxonomy: A cross-cultural dataset of historical games*, Humanities and Social Sciences Communications, DOI 10.1057/s41599-021-00785-y.
- Edwards (2000), *Children's Play in Cross-Cultural Perspective: A New Look at the Six Cultures Study*, Cross-Cultural Research 34(4), DOI 10.1177/106939710003400402.
- Ember & Cunnar (2015), *Children's Play and Work: The Relevance of Cross-Cultural Ethnographic Research for Archaeologists*, Childhood in the Past 8(2), DOI 10.1179/1758571615Z.00000000031.
- Buchholz (2019), *Author(iz)ing a Playground Game: “The Arguing Started Once the Rules Were Written Down”*, Journal of Literacy Research 51(1), DOI 10.1177/1086296X18821144.
- Marsh (1995), *Children's Singing Games: Composition in the Playground?*, Research Studies in Music Education 4(1), DOI 10.1177/1321103X9500400102.
- Vamplew (2007), *Playing with the rules: Influences on the development of regulation in sport*, International Journal of the History of Sport 24(7), DOI 10.1080/09523360701311745.
- Summerley (2020), *The Development of Sports: A Comparative Analysis of the Early Institutionalization of Traditional Sports and E-Sports*, Games and Culture 15(1), DOI 10.1177/1555412019838094.
- Howes et al. (1989), *Negotiation and enactment in social pretend play*, Early Childhood Research Quarterly 4(3), DOI 10.1016/0885-2006(89)90015-X.
- Bornstein et al. (1996), *Solitary and collaborative pretense play in early childhood*, Child Development 67(6), DOI 10.1111/j.1467-8624.1996.tb01895.x.
- Smith-Nielsen et al. (2024), *The significance of parental mentalizing for four-year-old children's solitary pretend play*, PubMed PMID 38295066.
- Lieberoth (2015), *Shallow Gamification: Testing Psychological Effects of Framing an Activity as a Game*, Games and Culture 10(3), DOI 10.1177/1555412014559978.
- Eriksson et al. (2014), *Spontaneous associations and label framing have similar effects in the public goods game*, Judgment and Decision Making 9(5), DOI 10.1017/S1930297500006756.
- Chick (1998), *Games in Culture Revisited: A Replication and Extension of Roberts, Arth, and Bush (1959)*, Cross-Cultural Research 32, 185-206; HRAF coded summary.
