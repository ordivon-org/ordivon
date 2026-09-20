# Ordivon Media Deep Foundations — Round B-F: Selection / Gatekeeping / Visibility Allocation Reducibility

**Date:** 2026-08-18  
**Continuity Task:** `task:media-foundations-mf2h-20260817`  
**Parent:** `media-whole-domain-round-b-e-artifact-work-edition-performance-generative-identity-reducibility-20260818.md`  
**Status:** **destructive reducibility / ownership audit only; no MF10 admitted**

---

# 0. Question

Round B-B reduced Encounter / Exposure but left an upstream residual:

```text
candidate set
+ selector / curator policy
+ ranking / allocation
+ presentation opportunity
```

Round B-D strengthened the same residual because:

```text
PublicAccess ≠ Discoverability ≠ Visibility
```

A fully public object can remain effectively invisible if no process surfaces it.

Round B-F asks:

> **Does Selection / Gatekeeping / Visibility Allocation contain a Media-specific irreducible standing absent from MF0–MF9 and adjacent owners?**

The cheapest falsifier is:

```text
same candidate objects
same object identity/content
same eligibility/access rules
same Network reachability
same consumer population
same presentation capacity
DIFFERENT selector/ranking/allocation policy
→ different visibility / exposure opportunity distribution
```

If that difference cannot be represented by MF4/MF7/MF8 plus B-B ExposureProfile and adjacent owners, a new primitive may exist.

---

# 1. Term separation

Ordinary recommender/gatekeeping language conflates many stages.

At minimum distinguish:

```text
Candidate Universe
Candidate Formation
Eligibility
Filtering
Retrieval / Recall
Scoring
Ranking
Reranking
Constraint Application
Selection
Allocation
Scheduling
Placement / Slot Assignment
Presentation
Visibility Opportunity
Exposure
Attention
Engagement
Outcome
Feedback
Learning / Policy Update
```

No pair is assumed identical.

Especially freeze:

```text
Eligibility ≠ Retrieval
Retrieval ≠ Selection
Score ≠ Rank
Rank ≠ Slot
Slot ≠ Presentation
Presentation ≠ Exposure
Exposure ≠ Attention
Attention ≠ Engagement
Engagement ≠ Value / Truth / Quality
```

---

# 2. Internal frozen substrate already covers most generic machinery

## MF2

MF2 already defines attention as selective allocation/biasing of finite perceptual/cognitive/acquisition resources.

But this is **consumer-internal selection**.

It must not be reused as the ontology of editorial/platform/media selection.

Thus:

```text
ConsumerAttentionAllocation
≠ PlatformVisibilityAllocation
```

although they can interact.

## MF4

MF4 supplies:

```text
candidate-set / collection organization
role/slot/order composition
many-to-many relational standing
```

## MF7

MF7 supplies:

```text
selector state
policy/configuration standing
ranking/ordering state
selection transition
feedback/update dynamics
resource/control constraints without requiring agency
```

## MF8

MF8 supplies genuine:

```text
editorial choice
autonomous agent curation
platform policy action
user choice
```

when bearer/evaluation/guidance/action standing is independently grounded.

Crucially, MF8 is not universally required because deterministic filters or random selectors can operate without rich AgencyStanding.

## B-B derived layer

B-B already reconstructs:

```text
Presentation / Coupling
→ ExposureOpportunity
→ Sampling / Sensing
→ Attention
→ Perception / Recruitment
```

Therefore Selection must prove something beyond merely causing a later ExposureOpportunity.

---

# 3. Classical newsroom gatekeeping — same incoming pool, different accepted set

David Manning White's 1950 `Gate Keeper` study is a canonical empirical hard case.

The setup explicitly compared:

```text
incoming wire stories
→ stories selected for publication
→ stories rejected
```

and analyzed the editor's stated reasons for those choices.

This matters ontologically because the incoming information pool can be held approximately fixed while the realized newspaper content depends on a gatekeeper's selection process.

Thus:

```text
AvailabilityToEditor
≠ SelectionForPublication
```

and:

```text
InputPool ≠ OutputMediaComposition
```

However the case decomposes cleanly:

```text
candidate stories                   → MF3/MF4 representations/collection
editor evaluation/criteria          → MF8 if genuine agency
selection state / accepted subset   → MF7 + MF4
publication status                  → B-D / Institution
final newspaper composition         → MF4
```

No new primitive is required merely because selection has causal consequences.

---

# 4. Selection does not require agency

Cheap falsifiers:

```text
chronological sort
round-robin scheduler
random sampler
fixed keyword filter
hard threshold
static whitelist
first-N truncation
reservoir sampling
```

These can determine which media objects receive presentation opportunity without a genuine agent bearer satisfying MF8.

Therefore:

```text
Selection ≠ Agency universally
Gatekeeping ≠ Intentional editorial choice universally
```

The generic core must fit non-agential selectors.

MF7 state/transition/rule structure is sufficient for those cases.

---

# 5. Agency is also insufficient for Media selection

An agent can choose among:

```text
routes
tools
food
financial assets
physical actions
jobs
hypotheses
```

without any MediaRole.

Thus:

```text
Choice / Policy / Allocation
```

is generic Agency/decision structure, not Media-owned by default.

Media specialization begins only when the selected alternatives are MediaRoles, representation objects, presentation opportunities, audience relations or circulation actions.

This is an ownership boundary.

---

# 6. Candidate formation ≠ ranking

Modern large-scale recommendation systems expose this separation operationally.

The YouTube recommender architecture described by Covington et al. explicitly uses:

```text
candidate generation
→ separate ranking model
```

Meta's Instagram and Feed engineering documentation likewise uses multi-stage funnels such as:

```text
retrieval / sourcing
→ early ranking
→ later ranking
→ final reranking / rules
```

Therefore:

```text
CandidateInclusion
≠ RankingScore
≠ FinalPresentation
```

An object excluded at retrieval can never win a later ranker regardless of its hypothetical score.

This makes the complete selector a composition of stages, not one ranking primitive.

---

# 7. Same candidate set / different ranking policy falsifier

Construct two worlds.

## Shared conditions

```text
candidate set C = {m1...mn}
same Media/Representation standing
same eligibility
same access rights
same Network routes
same consumer U
same presentation slots K
same current user history
```

## World A

```text
rank by recency
```

## World B

```text
rank by predicted engagement
```

The visible top-K may differ substantially.

This difference is real and causally important.

But it maps to:

```text
Policy/Scoring rule             → MF7 represented/operational dynamics; MF8 if agent-governed
Ordered candidate composition   → MF4
Selected/top-K state            → MF7
Presentation assignment         → MF4 + MF7
Exposure opportunity            → B-B derived profile
```

Thus the prescribed falsifier establishes **selector-relative visibility** but does not establish a new atom.

---

# 8. Ranking score ≠ rank

Two systems can produce the same score vector but different final ranks because of:

```text
tie-breaking
diversity rules
freshness constraints
integrity filters
business rules
quota constraints
randomization
multi-objective reranking
```

Meta's feed systems explicitly apply multiple passes and rules after prediction scores, including diversity/integrity logic.

Therefore:

```text
ScoreIdentity ≠ RankingIdentity
```

and:

```text
ModelPrediction ≠ FinalAllocation
```

This further supports a composite profile rather than one `RankingStanding` primitive.

---

# 9. Rank ≠ presentation

A ranked object can still fail to be shown because:

```text
viewport/session ends first
latency deadline expires
rendering fails
slot budget is exhausted
higher-priority interruption occurs
client-side filtering applies
the user closes the interface
```

Therefore:

```text
RankedHigh
↛ Presented
```

Actual presentation remains a downstream MF0/MF5/MF6 + Runtime/UI realization.

B-B already separates presentation from exposure.

---

# 10. Selection ≠ visibility without slot semantics

Suppose an object is selected into a 1000-item candidate output but the interface exposes only the first five items unless the consumer scrolls.

Selection alone does not determine actual observation opportunity.

Thus:

```text
SelectedSetMembership
≠ VisibilityOpportunity
```

Visibility requires placement/slot/order plus consumer route/session conditions.

This can be represented with MF4 positional/order role + MF5/MF6 + B-B ExposureProfile.

---

# 11. Visibility allocation is many-sided

Recommendation/fairness research usefully shows that allocation should be considered from both:

```text
consumer side: what information each consumer is exposed to
producer/item side: which producers/items receive exposure opportunity
```

Google research on joint multisided exposure fairness explicitly treats disparities in item/group exposure across user groups and optimizes stochastic ranking policies toward exposure goals.

This demonstrates that:

```text
VisibilityAllocation
```

is a real many-to-many distributional object.

But mathematically/ontologically it is still reconstructible as:

```text
CandidateItems × Consumers × Slots × Time
→ assignment / probability / opportunity relation
```

with:

```text
MF4 relation/composition
MF7 policy/state/dynamics
B-B exposure opportunity
Finance/Institution/Human fairness/value criteria where applicable
```

No new Media primitive is forced.

---

# 12. Deterministic ranking is not universal

Selection may be stochastic.

Examples:

```text
random exploration
A/B allocation
lottery
bandit exploration
stochastic ranking policy
```

Therefore:

```text
VisibilityAllocation ≠ one deterministic total ordering
```

A valid derived model must allow distributions over selections/slots.

MF7 already admits stochastic dynamics and uncertainty-bearing state profiles.

---

# 13. Total ordering is not necessary

Media selection can produce:

```text
unordered chosen subset
grid layout
multiple carousels
category buckets
simultaneous screens
parallel channels
spatial placements
notification schedule
```

Therefore:

```text
Selection ≠ Ranking universally
```

Ranking is one realization of allocation.

MF4 typed organization handles ordered and non-ordered arrangements.

---

# 14. Selection may be user-driven rather than platform-driven

Examples:

```text
search query
channel tuning
library browsing
menu navigation
manual playlist choice
user-curated subscription list
```

The user can partly construct their own candidate set and select presentation.

Thus:

```text
Gatekeeper = platform/editor
```

is not universal.

The relevant selector bearer may be:

```text
producer
editor
institution
platform
consumer
community
algorithm
agent
hybrid ensemble
```

Selector identity is a profile field, not a primitive owner.

---

# 15. Selection can be distributed

A newspaper story may survive several gates:

```text
reporter
wire service
editor
desk
layout
printing/distribution
consumer choice
```

A modern feed may use:

```text
source eligibility
retrieval model
first-stage ranker
second-stage ranker
integrity systems
reranker
client presentation
user scroll/attention
```

Therefore there need not be one central Gatekeeper.

This mirrors the broader Ordivon lesson that functional relations can be distributed across several owners/stages.

A centralized gatekeeping agent is not constitutive.

---

# 16. Selection can be rule-constrained without being value-neutral

A deterministic filter can encode:

```text
policy
law
moderation rule
commercial objective
safety restriction
capacity constraint
fairness constraint
```

The execution mechanism itself may be non-agential while the rule's origin/authority is agential or institutional.

Therefore distinguish:

```text
SelectorMechanism
PolicyContent
PolicyAuthority
ExecutionEpisode
```

This decomposes through MF3/MF7/MF8/Institution rather than requiring `Gatekeeping` as one substance.

---

# 17. Eligibility filtering ≠ recommendation

An object can be filtered out because it is:

```text
illegal
unsafe
private
blocked
incompatible
already seen
outside language/region
expired
```

without any positive judgment about which remaining item is most relevant.

TikTok's current official explanation explicitly separates recommendation/prediction from eligibility/safety filters and additional diversity/freshness considerations.

Thus:

```text
Filtering ≠ PositiveRanking
```

and:

```text
NotShown ≠ LowPredictedPreference
```

This matters for causal explanation and governance.

---

# 18. Freshness/diversity rules prove multi-objective allocation

Modern platforms commonly do not simply sort by one predicted utility.

TikTok's current official For You explanation includes considerations such as:

```text
avoid repetitive recommendations
promote freshness/locality
apply eligibility/safety rules
```

Meta systems likewise apply content-diversity and integrity logic around ranking.

Therefore:

```text
FinalVisibility
≠ argmax(single relevance score)
```

The final allocation is a constrained multi-objective composition.

This is naturally represented by MF7 policy/constraint structure and MF4 slot assignment.

---

# 19. Search ranking is a selection specialization, not a new primitive

Search introduces:

```text
query-conditioned candidate generation
matching
retrieval
ranking
snippet/presentation
```

The user provides an explicit constraint/query, but the ontology remains:

```text
candidate universe
→ filtered/retrieved set
→ ordered/selected subset
→ presentation
```

Search therefore falls under the same derived SelectionProfile.

No separate Media foundation is needed for search ranking.

---

# 20. Editorial curation and algorithmic recommendation share a structural core

Despite major differences in agency, scale and accountability, both can instantiate:

```text
CandidateSet
+ Criteria/Policy
+ SelectorMechanism/Bearer
+ AllocationConstraint
+ Selected/Ordered Result
+ Presentation Route
```

What differs is:

```text
standing route
policy provenance
agency status
model uncertainty
feedback speed
institutional authority
scale
personalization
```

Thus Agent-era ranking is a new realization regime, not proof of a new primitive.

---

# 21. Feedback creates endogenous selection data

A crucial modern hard case is feedback endogeneity.

YouTube production research on off-policy correction explicitly notes that implicit feedback is biased because the system only observes user reactions to recommendations selected by earlier behavior policies.

Therefore:

```text
Selection_t
→ Exposure_t
→ ObservedFeedback_t
→ TrainingData_t
→ Policy_{t+1}
→ Selection_{t+1}
```

This produces reflexive dynamics.

But each stage is already representable:

```text
selection/policy state     → MF7
exposure                   → B-B
user action                → MF8/Human
measurement                → MF1
learning/update            → Runtime/Harness + MF7
```

The feedback loop strengthens `Reflexive Mediation Ecology` as an operational reconstruction but does not rescue Selection as a primitive.

---

# 22. Exposure bias falsifies naive preference inference

Recommender research directly documents exposure/selection bias:

```text
more frequently rendered item
→ more opportunity for clicks/interactions
→ more observed positive data
```

Therefore:

```text
ObservedEngagement
≠ latent/pre-existing user preference
```

without accounting for selection/exposure process.

This is an important epistemic rule for Media consumers.

But the bias is caused by a causal chain among existing standings; it is not an ontological atom.

---

# 23. Selection can change the environment it later predicts

Creators may adapt to ranking systems:

```text
observe what receives visibility
→ modify titles/content/timing/style
→ candidate distribution changes
→ ranking model retrains
```

Consumers likewise adapt behavior.

This means the candidate universe is not exogenous.

Yet this maps to:

```text
MF7 feedback/dynamics
MF8 creator/platform/consumer agency
Finance incentives
Human learning/social response
Media representation/selection/exposure profiles
```

Again this is a reflexive ecology, not a new Selection substance.

---

# 24. Scarcity is common but not universally economic

Visibility allocation often arises because presentation resources are finite:

```text
screen slots
newspaper columns
broadcast time
notification budget
human attention horizon
context-window budget
```

But finite capacity does not imply market/economic allocation.

Selection can be chronological, random, institutional, algorithmic or physical.

Therefore:

```text
Selection ≠ MarketAllocation universally
```

Finance owns generic value/auction/market/resource-allocation structures where they genuinely appear; Media owns specialization to presentation opportunities.

---

# 25. Market allocation can alter Media visibility without defining it

Advertising auctions, sponsorship or paid placement can influence which content occupies scarce slots.

But:

```text
auction outcome
≠ exposure
≠ attention
≠ persuasion
```

Auction/value is Finance territory; slot assignment is Media/Composition specialization; exposure is B-B.

This preserves ownership boundaries.

---

# 26. Institutional censorship / moderation is not the universal core

Gatekeeping can involve power and authority, but not all selection is censorship or moderation.

Examples:

```text
chronological sort
random sampling
user playlist
technical capacity truncation
```

have no constitutive governance action.

Therefore:

```text
Selection ≠ Censorship
Selection ≠ Governance
Selection ≠ Moderation
```

Institution/Governance are optional typed causes/constraints.

---

# 27. Selection without content understanding

A selector can operate on:

```text
time
identifier hash
file size
random seed
network locality
quota
```

without interpreting semantic content.

Therefore:

```text
SemanticUnderstanding ≠ necessary for Selection
```

This blocks a hidden Meaning/Pragmatics requirement.

---

# 28. Semantic relevance is also insufficient

An item can be maximally relevant yet not be selected because of:

```text
policy exclusion
slot diversity
freshness requirement
quota
latency
creator cap
legal restriction
random exploration
```

Thus:

```text
Relevance ≠ Visibility
```

and:

```text
Truth ≠ Visibility
Quality ≠ Visibility
Popularity ≠ Visibility
```

unless the selector explicitly uses those criteria.

This is why SelectionProfile must preserve policy provenance.

---

# 29. Machine-only Agent selection

Agent-era media removes the human audience entirely.

Example:

```text
retriever has 100,000 candidate documents/tools/messages
context budget permits 20
selector chooses 20 for model context
```

Hold constant:

```text
stored objects
permissions
network
model
context size
```

Change only retrieval/ranking policy.

The model receives different information and may act differently.

This is a real visibility/allocation relation for a machine consumer.

But it maps to:

```text
candidate representations       → MF3/MF4
retrieval/ranking policy        → Runtime/Harness + MF7
selection action                → MF8 only if an agent bearer genuinely selects
context slot composition        → MF4
materialization/presentation    → Runtime/Harness
functional recruitment          → MF0
```

No human-centric Media primitive is necessary.

---

# 30. Agent can itself be both selector and consumer

An agent may:

```text
generate query
retrieve candidates
rerank
select context
consume selected context
change query
```

so selector and consumer roles can occupy the same broader bearer at different stages.

Therefore:

```text
Selector ≠ necessarily external platform
Selector ≠ necessarily distinct agent from Consumer
```

Role typing is required.

---

# 31. Selection can be delegated / layered

An agent may delegate retrieval to a search engine, ranking to a reranker, filtering to a safety layer and final choice to its own policy.

Thus:

```text
one SelectionEpisode
```

may be a composition of several selector roles with different authorities.

This is MF4 role composition + Runtime/Harness orchestration, not a new primitive.

---

# 32. Selection is not necessarily stable

The same candidate set/user can produce different outputs because of:

```text
randomization
changed time
updated model
exploration
load shedding
A/B treatment
context changes
```

Therefore:

```text
Selector(C,U) = fixed list
```

is not universal.

A full profile needs policy/version/time/uncertainty.

MF7 already supplies state/time-varying dynamics.

---

# 33. Visibility opportunity is not an intrinsic property of an item

An item can be:

```text
highly visible to U1
not surfaced to U2
visible at t1
buried at t2
prominent in surface S1
absent from surface S2
```

while its bytes/content stay unchanged.

Thus:

```text
Visibility ≠ intrinsic item property
```

It is relational:

```text
VisibilityOpportunity(M, Consumer, Surface, Slot, Time | Policy, Scope)
```

This follows directly from B-B's consumer-relative exposure model plus allocation context.

---

# 34. Proposed derived SelectionProfile

No new Foundation is introduced.

```text
SelectionProfile(C,U | Σ) = <
  CandidateUniverse,
  CandidateFormationRoute,
  EligibilityRules,
  SelectorBearer/Mechanism,
  SelectorAgencyStanding?,
  Policy/Criteria,
  PolicyAuthority/Provenance,
  ScoringModels?,
  RetrievalStage?,
  Ranking/Ordering?,
  Reranking/ConstraintStages?,
  Resource/Slot Budget,
  Allocation Rule,
  SelectedSubset,
  Placement/Schedule,
  Randomization/Exploration?,
  PresentationRoute,
  DownstreamExposureProfile?,
  Feedback/MeasurementRoute?,
  PolicyVersion,
  Time,
  Uncertainty,
  Scope
>
```

This profile applies to:

```text
news editing
search
recommendation
playlist curation
broadcast scheduling
museum/gallery curation
library display
notifications
advertising
agent context selection
```

without claiming they share one institutional purpose.

---

# 35. Proposed derived VisibilityAllocationProfile

For systems where opportunity distribution matters:

```text
VisibilityAllocationProfile = <
  Item/Producer Population,
  Consumer Population,
  Surfaces,
  Slots/Positions,
  Time Horizon,
  Eligibility Matrix,
  AllocationPolicy,
  Assignment/Probability Distribution,
  Expected Presentation Opportunity,
  Expected Exposure Opportunity,
  ConsumerUtilityCriteria?,
  ProducerOpportunityCriteria?,
  Diversity/FairnessConstraints?,
  Provenance,
  Uncertainty,
  Scope
>
```

This is highly useful operationally.

But it is a relation over existing entities/standings, not a new foundational entity class.

---

# 36. Strongest irreducibility test

Construct A and B identical in:

```text
candidate set
candidate representations
eligibility
consumer state
slot capacity
Network routes
presentation interface
selector policy/rule
selector state
random seed / stochastic realization where applicable
policy authority
```

and ask for different selection/visibility allocation.

If every relevant condition is truly identical, no grounded difference remains.

To force a difference we must alter at least one of:

```text
policy
state
randomness
candidate composition
constraint
authority
consumer relation
slot assignment
time
```

all of which are already representable by MF4/MF7/MF8/adjacent owners.

Therefore no independent `SelectionAtom` survives.

---

# 37. Cheapest falsifier matrix

| Proposed universal claim | Cheapest counterexample | Result |
| --- | --- | --- |
| Selection requires agency | chronological/random/fixed filter | falsified |
| Agency/choice is inherently Media selection | tool/route/action choice | falsified |
| Selection = ranking | unordered subset / schedule / grid | falsified |
| Candidate set = final ranking | retrieval vs ranking funnels | falsified |
| Score = rank | tie-break/rerank/diversity rules | falsified |
| Rank = presentation | session/latency/render failure | falsified |
| Selection = exposure | selected but offscreen/not rendered | falsified |
| Visibility is intrinsic item property | personalization/time/surface differences | falsified |
| One central gatekeeper is necessary | multi-stage newsroom/platform pipeline | falsified |
| Semantic understanding is necessary | random/time/hash selector | falsified |
| Relevance is sufficient for visibility | policy/diversity/quota exclusion | falsified |
| Ranking is deterministic | exploration/stochastic policies | falsified |
| One scalar utility defines final allocation | multi-objective/diversity/safety constraints | falsified |
| Platform must be selector | user search/tuning/manual curation | falsified |
| Human consumer required | agent context retrieval | falsified |
| Market allocation is universal | chronological/random/institutional selection | falsified |
| Governance/moderation is universal | neutral technical truncation | falsified |

The survivor is a typed policy/constraint/assignment relation over candidate MediaRoles and presentation opportunities.

---

# 38. Irreducibility test

Question:

> Does Selection / Gatekeeping / Visibility Allocation require a primitive absent from MF0–MF9 and adjacent owners?

Round B-F answer:

**No concrete irreducible survivor.**

Reduction:

```text
Candidate object standing         → MF3/MF4
Candidate-set composition         → MF4
Eligibility state/rules           → MF7 + Institution where normative
Retrieval/filter transformation   → MF7/Runtime/Harness
Scoring/ranking representation    → MF3 + MF7
Ordered/selected composition      → MF4
Selection policy                  → MF7; MF8 where genuinely agential
Resource/slot allocation          → MF4 + MF7; Finance where market/value allocation
Scheduling/placement              → MF4 + MF6/MF7
Presentation                      → MF0/MF5/MF6 + Runtime/UI
Exposure opportunity              → B-B derived profile
Consumer attention                → MF2
Institutional/editorial authority → Institution/Human + MF8
Feedback/learning                 → MF1 + MF7 + Runtime/Harness + Human
```

Therefore the candidate fails foundation-level irreducibility.

---

# 39. Ownership test

Media legitimately needs:

```text
SelectionProfile
CurationProfile
VisibilityAllocationProfile
RecommendationProfile
SearchPresentationProfile
```

because selection changes what MediaRoles become available for actual recruitment.

But generic ownership is distributed:

```text
MF4             set/order/slot/assignment composition
MF7             policy/state/constraint/update dynamics
MF8             genuine editorial/platform/user/agent choice
MF2             downstream consumer attention only
Network         delivery/reachability
Runtime/Harness computational retrieval/ranking/materialization
Human           preference/attention/social/editorial judgment
Institution     authority/moderation/policy/censorship/governance
Finance         markets/auctions/value/resource allocation
```

No independent universal Media Selector ontology survives.

---

# 40. Cross-regime test

Selection/gatekeeping appears across:

```text
oral storytellers choosing what to retell
scribal/manuscript copying choices
print editors
book/library curation
newsrooms
broadcast schedules
music programming
cinema distribution/exhibition
search engines
social feeds
recommendation systems
notification systems
immersive/spatial surfaces
agent retrieval/context selection
```

But the invariant is not one gatekeeper substance.

It is approximately:

> **a scope-relative mapping from eligible candidate media relations to a selected/ordered/scheduled presentation allocation under typed criteria, constraints and provenance.**

That is already expressible as MF4 organization + MF7 policy/state, with MF8 optional.

Cross-regime persistence supports a powerful operational abstraction, not a new foundation.

---

# 41. Agent-era perturbation

Agent era intensifies:

```text
autonomous retrieval
continuous reranking
context-window allocation
dynamic tool/result selection
multi-agent delegation
personalized generation + selection fusion
policy self-modification
closed-loop feedback at high frequency
```

Yet the same ontology holds:

```text
CandidateSpace
→ Eligibility
→ Retrieval
→ Selection/Allocation
→ Materialization
→ Recruitment
→ Feedback
```

Agent-era systems make exact selection provenance and policy version more important because two runs with the same source corpus can receive different world-model evidence solely from changed retrieval/ranking.

This is an engineering/evidence consequence, not a new foundation.

---

# 42. Important survivor — Reflexive Mediation Ecology

B-F does not close the broader ecology in which:

```text
selection affects exposure
exposure affects behavior
behavior affects training data
training affects selection
selection affects creator incentives
creators alter candidate distribution
```

The loop is likely reducible to MF1 measurement + MF7 dynamics + MF8 agency + Human/Finance/Institution + Selection/Exposure profiles.

But whole-loop emergent standing has not yet been destructively tested as a referent.

Keep:

```text
Reflexive Mediation Ecology
= CROSS-CUTTING / still unresolved
```

not a foundation claim.

---

# 43. Important survivor — Meaning / Pragmatics / Context Integrity

Selection can change the surrounding context of an otherwise unchanged representation:

```text
headline placement
neighboring stories
playlist order
search-result context
recommended-after relation
agent context-window neighbors
```

This may alter interpretation/pragmatic/evidential force without changing underlying bytes.

B-F explains **why an item was placed there**, but not whether contextual meaning changes are completely reducible.

So Context Integrity remains open.

---

# 44. Important survivor — Audience / Public Formation

Repeated selection can help constitute publics/audiences by repeatedly co-presenting issues, creators and participants.

But B-F does not prove that public formation reduces to selection.

Likely ownership remains Human/social/Institutional, with Media selection as one causal input.

---

# 45. Important survivor — Authorship / Creation / Attribution

Ranking/selection does not settle who created, authored, contributed or deserves attribution for selected media, especially in generative/agentic systems.

Remain open.

---

# 46. Foundation consequence test

Would a numbered Selection/Gatekeeping foundation allow classifications unavailable under the frozen substrate?

Current answer: **no**.

It would risk collapsing:

```text
eligibility
retrieval
ranking
policy
slot allocation
presentation
exposure
attention
institutional authority
market allocation
```

into one oversized term.

Typed profiles preserve causal and ownership boundaries more accurately.

---

# 47. Classification update

Canonical Round-B-F classification:

```text
Selection / Gatekeeping / Visibility Allocation
= REDUCIBLE / CROSS-CUTTING
= NOT genuinely-new-foundation at current frontier
```

More specifically:

```text
Candidate formation/retrieval     → Runtime/Harness + MF4/MF7
Eligibility/filtering             → MF7 + Institution
Scoring/ranking                   → derived representational/policy state
Selection                         → MF4/MF7; MF8 optional
Curation                          → cross-cutting Human/Institution/MF8 + selection profile
Visibility allocation             → derived many-sided assignment/opportunity profile
Recommendation                    → derived computational selection specialization
Search ranking                    → derived selection specialization
Editorial gatekeeping             → Human/Institution/MF8 + selection profile
Market/paid allocation            → Finance + Media slot specialization
Consumer attention                → already-covered / MF2, downstream not identical
```

No MF10 is admitted.

---

# 48. FoundationReopen audit

No MF0–MF9 FoundationReopenCondition is triggered.

B-F instead validates:

```text
MF2 attention is consumer resource allocation, not all selection
MF4 typed organization/order/assignment is needed
MF7 policy/state/dynamics works without agency
MF8 agency remains optional rather than silently attached to algorithms
B-B presentation/exposure distinction remains necessary
```

No frozen claim was falsified.

Thus:

```text
MF0–MF9 = FROZEN
```

---

# 49. Research anchors used

Representative primary/authoritative comparison anchors:

- David Manning White (1950), `The Gate Keeper: A Case Study in the Selection of News` — direct empirical case of incoming wire stories being accepted/rejected through an editor's selection process.
- Covington, Adams & Sargin (2016), `Deep Neural Networks for YouTube Recommendations` — production recommendation architecture explicitly separates candidate generation from ranking.
- Google Research production recommender work on top-K off-policy correction — logged feedback is selection-biased because reactions are observed only on recommendations chosen by previous behavior policies; exploration and off-policy correction are required.
- Google Research, `Joint Multisided Exposure Fairness for Recommendation` (SIGIR 2022) — exposure opportunity is a many-sided distribution across items/producers and consumers; stochastic ranking policies can optimize different exposure-fairness goals.
- Meta Engineering, `News Feed ranking, powered by machine learning` — inventory query, prediction scoring, multi-pass ranking and diversity/integrity rules are separate stages before final ranked stories are returned for rendering.
- Meta Engineering, Instagram recommendation-system architecture — retrieval/sourcing, early-stage ranking, late-stage ranking and reranking form a multi-stage funnel; current systems operate many different ranking surfaces and models.
- TikTok official `Making your feed For You` / recommendation documentation — current feed selection uses interaction/content/user signals while also applying eligibility, diversity, freshness/locality and safety considerations.
- MF2/MF4/MF7/MF8 frozen Ordivon foundations and Round B-B/B-D derived profiles.

These sources are falsification/comparison anchors rather than external authority over Ordivon's ontology.

---

# 50. Round B-F closeout

```text
Round B-F target       = Selection / Gatekeeping / Visibility Allocation
Result                 = REDUCIBLE / CROSS-CUTTING
New Media primitive    = NONE
MF10                    = UNKNOWN / NOT ADMITTED
FoundationReopen       = NONE
```

Deep result:

> **Selection is a real causal layer between candidate availability and presentation/exposure, but it is not a Media-specific primitive. The cross-regime core is a typed mapping from eligible candidate media relations to selected/ordered/scheduled presentation opportunities under policy, resource, state and provenance constraints. Candidate generation, filtering, ranking, reranking, slot assignment, presentation and exposure must remain separate. MF4 organization + MF7 policy/state/dynamics cover the generic core; MF8 enters only for genuine agents, while Institution, Finance, Runtime/Harness and Human own their respective specializations.**

The whole-domain search remains open. Surviving residual pressure now includes:

```text
Meaning / Pragmatics / Context Integrity
Inscription / Fixation / Materialization
Authorship / Creation / Attribution
Archive / Preservation Responsibility
Audience / Public Formation
Reflexive Mediation Ecology
Translation / Remediation
unknown continents
```

No ordering is canonical and none is admitted as MF10.
