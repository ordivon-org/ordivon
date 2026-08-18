# Ordivon Media Deep Foundations — Round B-I: Authorship / Creation / Attribution Reducibility

**Date:** 2026-08-18  
**Continuity Task:** `task:media-foundations-mf2h-20260817`  
**Parent:** `media-whole-domain-round-b-h-inscription-fixation-materialization-reducibility-20260818.md`  
**Status:** **destructive reducibility / ownership audit only; no MF10 admitted**

---

# 0. Question

Round A classified:

```text
Creation / Authorship
= cross-cutting / reducible-candidate
```

B-E showed that Work identity does not solve Authorship.
B-G showed that source attribution/provenance does not solve Authorship.
B-H showed that inscription/capture can occur without Authorship.

Round B-I therefore asks:

> **Does Authorship / Creation / Attribution contain a Media-specific irreducible standing beyond MF3 provenance/representation, MF4 composition, MF7 history/lineage, MF8 Agency/Action, Human creative/social practices and Institution/Law status?**

Strongest destructive test:

```text
hold fixed:
  contribution history
  action/source history
  work/token/content
  provenance
  intentions
  institutional/legal regime
  attribution record
  ownership/right status
  responsibility regime

then ask whether AuthorshipStanding can still differ.
```

If no grounded difference survives, there is no new primitive.

---

# 1. Mandatory term separation

At minimum distinguish:

```text
Producer
Generator
Recorder
Performer
Contributor
Creator
Author
Co-author / Joint Author
Collective-Work Author
Editor
Compiler / Curator
Director
Publisher
Commissioner
Employer
Principal
Tool / Instrument
Model / Agent
Source
Attributed Source
Credited Person/Entity
Rights Holder
Owner
Responsible Party
Accountable Party
Authenticating Authority
```

The word `author` cannot safely substitute for all of them.

Especially:

```text
Contribution ≠ Authorship
Authorship ≠ Attribution
Attribution ≠ Provenance
Authorship ≠ Ownership
Ownership ≠ Material Possession
Authorship ≠ Responsibility
Authorship ≠ Agency universally
Producer ≠ Author universally
Tool ≠ Author universally
```

---

# 2. Frozen substrate already covers most generic machinery

MF3 provides:

```text
producer/design history
provenance/source grounding
authorship as one provenance dimension
content identity ≠ provenance/authenticity identity
authority standing distinct from content
```

MF4 provides:

```text
multi-contributor composition
role structure
collective/part-whole organization
```

MF7 provides:

```text
production history
lineage
successor/derivative relations
state/version history
```

MF8 provides:

```text
attributable source of activity
action attribution
collective agency
delegated agency
authority provenance
```

Human owns generic:

```text
creative intention
social recognition
contribution norms
tradition
individual/collective practices
```

Institution/Law owns:

```text
legal authorship
rights ownership
work-made-for-hire status
joint-work status
moral rights / official attribution regimes
```

Therefore B-I must find a remainder beyond these.

---

# 3. Contribution ≠ Authorship

NISO CRediT is an unusually clean operational hard case.

It models multiple contribution roles such as:

```text
Conceptualization
Data curation
Formal analysis
Investigation
Methodology
Project administration
Resources
Software
Supervision
Validation
Visualization
Writing — original draft
Writing — review & editing
```

but explicitly states that these contributor roles are **not intended to define what constitutes authorship**.

Therefore:

```text
ContributionRoleStanding
≠ AuthorshipStanding
```

A contributor can be important without being formally an author; an author can hold several contribution roles.

This immediately defeats one universal `Creator/Author` role.

---

# 4. Authorship ≠ one physical production act

A person can physically type, draw, record or render a token while acting as:

```text
scribe
technician
camera operator
printer
transcriber
assistant
executor
```

without necessarily being treated as the author of the resulting work under the relevant practice.

Conversely an author may establish relevant expressive/organizational standing while others perform much of the physical realization.

Thus:

```text
PhysicalProduction ≠ Authorship
```

MF8 action attribution and MF3 provenance can represent physical source activity without forcing author status.

---

# 5. Recorder ≠ Author

B-H already showed automatic or human recording can create a source-linked token.

A camera operator or logging system may record an event without being the author of the underlying event/performance/work.

Thus:

```text
RecorderOf(E)
≠ AuthorOf(E)
```

The recording itself may have separate creative/authorship standing under some regimes, but that is a new relation to the recording work/token, not proof that recorder=source-work author.

---

# 6. Performer ≠ underlying Work author

A performer can realize a musical/dramatic/choreographic work created by another author.

A performance may itself generate neighboring performance/recording rights or new creative standing depending regime, but:

```text
PerformerOf(W)
≠ AuthorOfUnderlyingWork(W)
```

B-E already separated Work, score, performance and recording.

Authorship must inherit that separation.

---

# 7. Editor ≠ underlying author universally

An editor may:

```text
correct spelling
restructure content
select contributions
write new text
transform an edition
```

The exact role can range from non-authorial technical intervention to independently creative authorship.

Thus:

```text
EditorRole
↛ Authorship universally
```

and:

```text
Authorship contribution cannot be inferred from the title `editor` alone.
```

A typed contribution/action profile is required.

---

# 8. Compilation authorship gives layered authorship

U.S. Copyright Office collective-work practice treats creative selection, coordination and arrangement as authorship of the collective whole while component works may have their own separate authors.

Therefore one media object can support:

```text
AuthorOfComponent(Alice, Article1)
AuthorOfComponent(Bob, Photo2)
AuthorOfCompilation(Editor, Issue)
```

simultaneously.

Thus:

```text
OneArtifact → one Author
```

is false.

MF4 layered composition + MF3/MF7 provenance handles the structure.

---

# 9. Joint work ≠ collective work

U.S. copyright law distinguishes:

```text
JointWork
```

where two or more authors intend contributions to merge into inseparable/interdependent parts of a unitary whole,

from:

```text
CollectiveWork
```

where separate and independent works are assembled into a collective whole.

Therefore:

```text
MultipleContributors
```

does not decide the authorship structure.

Intent, contribution relation and composition organization matter.

This maps to MF4 + MF8/Human intention + Institution/Law.

---

# 10. Joint authorship does not require equal contribution

A jointly authored work can contain contributions of very different form, size or function.

The ontology therefore cannot use:

```text
ContributionMagnitude
```

as a universal authorship threshold.

Authorship standing is rule/practice-relative.

---

# 11. Contribution magnitude is neither necessary nor sufficient

Large technical contribution may not satisfy a practice's authorship rule.

A small but decisive expressive contribution may qualify under another rule.

Therefore:

```text
AmountOfLabor
≠ Authorship
```

and:

```text
PercentageContribution
≠ universal authorship criterion
```

---

# 12. Work-made-for-hire decisively separates actual creator from legal author

Under U.S. copyright law, a qualifying work made for hire can treat the employer or commissioning party as the author rather than the individual who physically prepared the work.

This is a decisive institutional hard case:

```text
PhysicalCreator = Person P
LegalAuthor = Organization O
```

Therefore:

```text
AuthorshipStanding
```

cannot be one natural causal relation between a token and whoever moved the pen/keyboard/camera.

Legal authorship is an institutionally constituted standing.

---

# 13. Authorship ≠ copyright ownership

Normally authorship may ground initial copyright ownership, but ownership can later be transferred.

U.S. copyright law also explicitly separates ownership of copyright from ownership of the material object embodying the work.

Therefore distinguish:

```text
Author
InitialRightsHolder
CurrentRightsHolder
MaterialObjectOwner
```

These may all be different entities.

Thus:

```text
Author = Owner
```

is not foundation-safe.

---

# 14. Moral attribution rights further separate authorship from economic ownership

For certain U.S. visual-art works, statutory attribution/integrity rights are attached to the author even independently of copyright ownership.

This provides another regime-specific hard case:

```text
AuthorStanding persists
while
CopyrightOwner may differ
```

Again Authorship and Ownership are separate dimensions.

---

# 15. Attribution ≠ Authorship

A work/token may display a name/credit that is:

```text
correct
incorrect
pseudonymous
fraudulent
outdated
incomplete
honorary
ghost-written
machine-generated metadata
```

Therefore:

```text
AttributedAuthor(X,W)
≠ GroundedAuthorship(X,W)
```

Attribution is itself a representation/claim about authorship.

MF3 can represent that claim and separately evaluate its provenance/accuracy.

---

# 16. Anonymous authorship proves identifiable attribution is not necessary

U.S. law explicitly recognizes `anonymous work` where no natural person is identified as author on copies/phonorecords.

Therefore:

```text
AuthorshipStanding
↛ PubliclyKnownAuthorIdentity
```

A work may have an author even where public attribution is absent.

Thus:

```text
Attribution ≠ Authorship
```

in the strongest possible sense.

---

# 17. Pseudonymity further separates name from bearer

A pseudonymous/public credit can stabilize a creator identity role without revealing the underlying natural/legal bearer.

Therefore:

```text
DisplayedName
≠ BearerIdentity
```

Attribution systems must preserve the distinction between:

```text
credited identifier
claimed bearer
verified bearer
legal bearer
```

---

# 18. False attribution does not rewrite production history

If a third party falsely claims authorship of an existing work, the public attribution standing may change while the historical production relation does not.

Therefore:

```text
AttributionChange
↛ CreationHistoryChange
```

MF3 standing/provenance and MF7 history naturally distinguish these.

---

# 19. Creation event ≠ authorship status

A system/person can causally produce novel material without receiving author status in a given legal/social regime.

Therefore:

```text
CausalGeneration
≠ Authorship universally
```

This is central to machine/AI cases.

---

# 20. U.S. AI copyrightability gives a clean Agent-era legal boundary

The U.S. Copyright Office's 2025 Part 2 AI report concludes that generative-AI outputs are copyrightable only where a human author determines sufficient expressive elements.

It distinguishes cases where:

```text
human-authored material remains perceptible
human creatively selects/arranges/modifies output
```

from mere prompting that does not by itself provide sufficient human authorship.

At the same time, using AI as an assistive tool does not bar copyright protection for the human-authored portions/work.

Therefore:

```text
AI causal contribution
≠ legal human Authorship
```

and:

```text
AI use
≠ absence of human Authorship
```

The relation is contribution/profile dependent.

---

# 21. Legal AI authorship policy is not universal ontology

The U.S. human-authorship rule is a legal standing in one jurisdiction/regime.

Ordivon must not infer:

```text
NonhumanAuthorship is metaphysically impossible
```

from that legal rule.

The correct ontology separates:

```text
CausalGenerationStanding
AgencyStanding
CreativeContributionStanding
SocialAuthorshipStanding
LegalAuthorshipStanding
AttributionStanding
```

Different regimes can populate these differently.

---

# 22. AI as tool ≠ AI as autonomous contributor

At minimum distinguish:

```text
spellchecker
noise reduction
camera autofocus
style transfer
suggestion/completion tool
prompted generative model
iterative co-creative model
agent autonomously planning/generating/revising
multi-agent production system
```

No single `AI-assisted=true` field determines authorship.

The relevant question is which bearer contributed what under which source/agency/practice criteria.

---

# 23. Prompt author ≠ output author automatically

A prompt may causally influence an output but causal influence alone does not fix the output's authorship standing.

The U.S. Copyright Office expressly rejects mere prompts as automatically sufficient authorship of AI-generated expressive elements.

Thus:

```text
InstructionProvider
≠ OutputAuthor automatically
```

This generalizes beyond AI to directors, commissioners and tool operators.

---

# 24. Director / commissioner / principal roles are not universally authorship

A principal can establish goals, constraints or selection criteria while other agents produce concrete expressive material.

Depending on the regime, the principal may be:

```text
commissioner
legal author
producer
director
rights holder
non-author client
```

Therefore:

```text
GoalSetter ≠ Author universally
```

MF8 delegation/authority handles the action structure; Institution decides status consequences where relevant.

---

# 25. Delegated agency does not collapse responsibility

An agent may act under delegated goals/authority.

MF8 explicitly allows delegated operational agency.

But:

```text
Agent performs action
Principal delegates action
Institution assigns responsibility
```

are distinct relations.

Therefore:

```text
ActionSource
≠ ResponsiblePrincipal
≠ Author universally
```

---

# 26. Tool causation does not imply authorship

A camera, compiler, brush, generative function or editing tool may causally shape the output.

But causal necessity is insufficient for authorship.

Otherwise every indispensable tool would become a co-author.

Thus:

```text
CausalContributor
≠ Author
```

unless the governing authorship practice explicitly grounds such standing.

---

# 27. Human creator may not be legally Author — work-made-for-hire

This deserves repetition because it is the strongest anti-natural-kind case.

The same physical creative actions can occur in:

```text
Case A: independent creator
Case B: qualifying employee work-made-for-hire
```

while legal author status differs because employment/commissioning conditions differ.

So legal Authorship cannot be read directly from physical/psychological creation acts.

---

# 28. Same contribution history can yield different formal attribution

Two journals/institutions may apply different authorship/credit conventions to the same contribution graph.

CRediT intentionally avoids deciding authorship precisely because contribution description and authorship criteria are distinct layers.

Therefore:

```text
ContributionGraph
+ Practice/Policy
→ Authorship/Attribution standing
```

rather than:

```text
ContributionGraph alone
→ universal author set
```

---

# 29. Authorship practices can be discipline-relative

Scientific, literary, film, software, journalism, visual art and traditional-cultural practices distribute credit/author labels differently.

This does not imply arbitrariness: each regime can have grounded criteria.

But it falsifies one universal operational threshold such as:

```text
wrote text
made majority contribution
had original idea
owned project
pressed generate
```

as sufficient across all Media.

---

# 30. Traditional cultural expressions pressure individual-author ontology

WIPO describes Traditional Cultural Expressions as forms of traditional culture passed from generation to generation and integral to community identity/heritage.

Such expressions may involve:

```text
music
dance
art/design
performance
ceremony
narrative
symbols
```

without one identifiable originating individual author or fixed creation event.

Therefore:

```text
IndividualOriginatingAuthor
```

is not a universal requirement for culturally grounded creative standing.

Ownership here is strongly Human/Community/Institutional rather than generic Media.

---

# 31. Traditional continuation ≠ anonymous modern authorship

Do not collapse:

```text
anonymous authored work
```

with:

```text
intergenerational traditional expression
```

The former may have an unknown individual author; the latter can be constituted by distributed/community practice across generations.

Different provenance/identity structures apply.

---

# 32. Collective agency is not necessary for every collective work

A collective work can consist of contributions by several independent authors coordinated by an editor/assembler without there being one strongly unified collective agent satisfying MF8.

Therefore:

```text
MultipleAuthors
≠ CollectiveAgency necessarily
```

MF4 composition + individual MF8 agents + institutional rules can suffice.

---

# 33. Collective agency does not imply co-authorship of every output

A corporation, newsroom, lab or agent collective may satisfy some collective-agency criteria while particular works are attributed to subsets, employees, a legal entity or none of the group as author depending regime.

Therefore:

```text
CollectiveAgencyStanding
↛ AuthorshipOfEveryCollectiveOutput
```

---

# 34. Creation can be emergent/distributed

Complex works can emerge through:

```text
writer + editor
composer + performers
open-source contributors
film crew
scientific collaboration
model + human revisions
multi-agent generation
community tradition
```

No one source necessarily explains every expressive distinction.

A provenance graph is more appropriate than one `createdBy` edge.

---

# 35. Provenance graph ≠ Authorship graph

A provenance graph may record every causal/process contributor:

```text
person
model
tool
dataset
editor
runtime
camera
compiler
```

but authorship typically selects/constitutes some subset or higher-order standing under a practice.

Thus:

```text
ProvenanceContributor
≠ Author
```

while provenance remains evidence for authorship judgments.

---

# 36. Attribution graph ≠ Provenance graph

A credits list can omit causal contributors or include honorary/organizational credits.

Thus three graphs are needed:

```text
Production/Provenance Graph
Contribution Graph
Attribution/Credit Graph
```

with additional:

```text
Authorship Standing
Rights/Ownership Graph
Responsibility Graph
```

No single edge covers all five.

---

# 37. Rights holder ≠ Author

Copyright rights can be transferred, licensed or initially vested under legal rules different from natural-person production.

Therefore:

```text
CurrentRightsHolder
≠ HistoricalAuthor
```

B-E work identity and B-D publication also require this distinction.

---

# 38. Material-object owner ≠ rights holder ≠ author

17 U.S.C. §202 explicitly separates copyright ownership from ownership of the material object embodying the work.

Thus a collector owning a painting/object need not own copyright; neither ownership relation is identical to authorship.

This is a decisive three-way separation:

```text
MaterialOwner
CopyrightOwner
Author
```

---

# 39. Responsibility/accountability ≠ Authorship

A publisher, principal, institution or platform may be accountable for publication/use without being the author of all underlying content.

Conversely an author may lack operational control over later publication/distribution.

Therefore:

```text
Authorship
≠ OperationalControl
≠ LegalResponsibility
≠ PublicationAuthority
```

These belong to MF8/Institution/Host specializations.

---

# 40. Authorship ≠ truth/trustworthiness

An identified real author can be wrong or deceptive.

An anonymous work can be true/reliable.

Therefore:

```text
KnownAuthor
≠ TrustedContent
```

Authorship/provenance are evidence inputs, not truth predicates.

B-G already separated provenance from truth.

---

# 41. Authorship ≠ authenticity

A genuine authorized copy can correctly attribute an author; a forged signature can falsely attribute a genuine-looking token; a faithful unattributed reproduction can preserve work content while losing credit information.

Thus:

```text
WorkAuthenticity
AuthorAttributionAccuracy
TokenAuthenticity
```

are independent profiles.

---

# 42. Attribution can be partial

Complex outputs may need credits such as:

```text
written by
edited by
translated by
performed by
recorded by
visualization by
model-generated portions
human-selected/arranged by
```

A single `author` slot erases contribution structure.

CRediT exists for exactly this general family of problem in scholarly publishing.

---

# 43. Attribution can be hierarchical

One may attribute:

```text
work-level author
chapter author
image creator
data source
software contributor
editor
publisher
AI system/tool
```

at different composition levels.

MF4 layered composition naturally supports such scoped attribution.

---

# 44. Creation ≠ first fixation universally at ontology level

U.S. copyright law uses a legal definition under which a work is `created` when first fixed for statutory purposes.

But ontology cannot generalize this to all Media because B-H already established valid unfixed live/oral creation/organization.

Thus:

```text
LegalCreatedAtFixation
```

is a legal convention, not a universal metaphysical creation criterion.

---

# 45. Creative process can precede, overlap or follow token materialization

Examples:

```text
mental planning → writing
live improvisation captured concurrently
iterative editing of stored draft
generative system producing then human selecting/rearranging
```

Therefore there is no universal single `CreationMoment`.

Creation history can be extended and iterative.

MF7 history + MF8 actions handle this better than a primitive event.

---

# 46. New authorship can arise during transformation without erasing old authorship

Derivative/adaptive cases can preserve relation to pre-existing authors while introducing new creative contribution.

Therefore:

```text
NewAuthorStanding
```

can coexist with:

```text
PreexistingAuthorStanding
```

under different work/derivative scopes.

B-E lineage already supports this.

---

# 47. Translation is an authorship hard case

A translator may preserve source semantic content while making substantial creative choices in target-language expression.

Some legal/practice regimes treat translation as derivative authorship.

Thus:

```text
SourceAuthor
≠ Translator
```

while both can stand in different authorial relations to source/translated works.

This reinforces Translation/Remediation as a remaining typed-preservation problem rather than a new Authorship primitive.

---

# 48. Curation/selection may itself become authorship at a higher composition level

B-F reduced selection/gatekeeping as generic policy/allocation.

But creative selection/coordination/arrangement can ground compilation authorship under copyright practice.

Therefore:

```text
SelectionAction
```

is not universally authorship, but may support AuthorshipStanding when a practice/institution treats the resulting composition as sufficiently creative/original.

Again the missing ingredient is a standing rule, not a new primitive.

---

# 49. Mere selection does not imply authorship

A chronological sort, automatic playlist, random sampler or mechanical aggregation need not be authored as a creative compilation.

Thus:

```text
Selection ≠ Authorship universally
```

This preserves B-F.

---

# 50. Machine agent as attributable action source

MF8 can, in principle, recognize artificial/delegated agents as genuine action sources when bearer, goals/evaluative standing, regulation and action domain are grounded.

Therefore an Agent can have:

```text
ActionSourceStanding
```

without Ordivon automatically assigning:

```text
LegalAuthorStanding
HumanSocialAuthorStanding
```

Authorship is an additional practice/status relation.

---

# 51. Non-agent generator pressure case

A deterministic procedural generator can produce complex novel output without satisfying MF8 AgencyStanding.

Therefore:

```text
NovelOutputGeneration
≠ Agency
≠ Authorship
```

unless some external practice grounds authorship elsewhere.

This blocks novelty-based author attribution.

---

# 52. Agent agency is not sufficient for authorship

An autonomous agent can perform many actions unrelated to expressive creation.

Even when it generates media, a legal/social regime may decline to recognize it as author.

Therefore:

```text
AgencyStanding
≠ AuthorshipStanding
```

MF8 is necessary only for some authorial routes, not sufficient universally.

---

# 53. Authorship is not necessary for all meaningful Media

Examples:

```text
natural causal traces
anonymous records
machine logs
traditional expressions
unattributed signs
sensor measurements
```

can be meaningful/useful Media without a relevant author relation.

Thus:

```text
Authorship ≠ universal Media constituent
```

This alone prevents Authorship from being a universal Media Foundation.

---

# 54. Proposed `ContributionProfile`

```text
ContributionProfile(C, W | Σ) = <
  Contributor Bearer,
  Contribution Role(s),
  Target Work/Component/Process,
  Actions/Outputs,
  Temporal Scope,
  Dependency on Other Contributions,
  Degree/Weight?,
  AgencyStanding?,
  Delegation/Authority?,
  Provenance Evidence,
  Verification Status,
  Uncertainty,
  Scope
>
```

This answers `who did what?` without answering `who is author?` automatically.

---

# 55. Proposed `AuthorshipProfile`

```text
AuthorshipProfile(A, W | Regime, Σ) = <
  Claimed Author Bearer,
  Work/Component Scope,
  Authorship Route,
  Relevant Contributions,
  Creative/Expressive Standing Criteria,
  Intent/Integration Criteria?,
  Human/Collective/Artificial Bearer Type,
  Joint/Collective/Derivative Structure?,
  Institutional/Legal Regime?,
  Attribution/Credit Standing,
  Production Provenance,
  Rights Relationship?,
  Responsibility Relationship?,
  Evidence,
  Uncertainty,
  Scope
>
```

`AuthorshipRoute` may include:

```text
individual creative practice
joint creation
collective compilation
institutional/work-made-for-hire
traditional/community standing
human-AI assisted creation
delegated/agentic candidate route
```

without claiming all regimes recognize every route.

---

# 56. Proposed `AttributionCreditProfile`

```text
AttributionCreditProfile(X, W | Σ) = <
  Credited Identity/Identifier,
  Claimed Role,
  Target Scope,
  Credit Source,
  Attribution Authority,
  Verification Evidence,
  Public/Private Standing,
  Pseudonymous/Anonymous Status,
  Conflict/Dispute Status?,
  Provenance Link,
  Display/Presentation Form?,
  Uncertainty,
  Scope
>
```

Attribution is represented as a claim/status layer rather than presumed true authorship.

---

# 57. Proposed `ProductionProvenanceGraph`

For complex Media, prefer a graph:

```text
Bearers/Agents/Tools/Models
   -- performed-role -->
Actions/Transformations
   -- generated/modified/selected/recorded -->
Components/Tokens/Works
```

Then separately derive or record:

```text
AuthorshipStanding
AttributionStanding
RightsStanding
ResponsibilityStanding
```

This is more expressive than one `createdBy` edge.

---

# 58. Strongest irreducibility test

Construct cases A and B identical in:

```text
work/token/content identity
all production actions
all contributor roles
agency standing
intentions
provenance/history
joint/collective structure
institutional/legal regime
authorship criteria
public attribution
rights ownership
responsibility rules
scope
```

and assert:

```text
AuthorshipStanding(A) ≠ AuthorshipStanding(B)
```

At the current frontier no grounded difference survives.

Any proposed difference requires changing at least one of:

```text
contribution
intent/integration relation
agency/source relation
history/provenance
practice/social recognition
institutional/legal rule
attribution evidence
work/component scope
```

all already modelable by MF3/MF4/MF7/MF8 + Human/Institution.

No independent Authorship atom survives.

---

# 59. Cheapest falsifier matrix

| Proposed universal claim | Cheapest counterexample | Result |
| --- | --- | --- |
| Contributor = Author | CRediT non-author contributor | falsified |
| Physical producer = Author | scribe/technician/work-made-for-hire | falsified |
| Recorder = underlying-work Author | performance recording | falsified |
| Performer = underlying-work Author | performance of another's composition | falsified |
| Editor = Author universally | technical copy edit | falsified |
| One artifact = one author | collective work/component authors | falsified |
| Multiple contributors imply joint authorship | collective work vs joint work | falsified |
| Contribution size determines authorship | discipline/practice variation | falsified |
| Actual creator = legal author | work made for hire | falsified |
| Author = current copyright owner | transfer/work-for-hire cases | falsified |
| Author = material-object owner | 17 USC §202 separation | falsified |
| Attribution = Authorship | false credit / anonymous work | falsified |
| Publicly identified author necessary | anonymous work | falsified |
| Displayed name = bearer identity | pseudonym | falsified |
| Attribution change changes creation history | false later claim | falsified |
| Causal generation = Authorship | AI/tool/non-agent generator | falsified |
| Prompt provider = output Author automatically | U.S. AI report mere-prompt case | falsified |
| AI involvement destroys human authorship | assistive AI + human-authored elements | falsified |
| Goal setter/principal = Author universally | commissioned/delegated cases | falsified |
| Causal tool = co-author | camera/compiler/brush | falsified |
| Provenance graph = author graph | tools/data/editors not all authors | falsified |
| Authorship = responsibility | publisher/platform accountability | falsified |
| Authorship = truth/trust | identifiable deceptive author | falsified |
| Individual originating author required | traditional cultural expressions | falsified |
| Collective work implies collective agency | editor + independent contributions | falsified |
| Collective agency implies authorship of every output | corporate/lab subset attribution | falsified |
| Novel output implies agency/authorship | deterministic generator | falsified |
| Agency implies authorship | non-creative agent action / unrecognized AI agent | falsified |
| Authorship required for all Media | logs/natural traces/traditional/unattributed media | falsified |

The survivor is a family of typed contribution, authorship, attribution, rights and responsibility standings—not a new foundation.

---

# 60. Irreducibility test

Question:

> Does Authorship / Creation / Attribution require a primitive absent from MF0–MF9 and adjacent owners?

Round B-I answer:

**No concrete Media-specific irreducible survivor.**

Reduction:

```text
Production/source provenance      → MF3 + MF7
Work/component composition        → MF4
Creation actions                  → MF8 where agential
Contributor roles                 → derived MF8/MF4/Human profile
Joint/collective structure        → MF4 + Human/Institution
Creative intention/practice       → Human + MF8
Authorship standing               → derived practice/institution-grounded relation
Attribution/credit claim          → MF3 + Institution/Human
Rights ownership                  → Institution/Law/Finance-like ownership specialization
Material-object ownership         → World/Institution
Responsibility/accountability     → Institution/Host/MF8
Delegation/principal relation     → MF8 + Host/Institution
AI/tool contribution              → Runtime/Harness + MF8 where agent + provenance
Traditional/community creation    → Human/social/Institution + MF7 lineage
```

Therefore the candidate fails foundation-level irreducibility.

---

# 61. Ownership test

Media legitimately needs derived operational concepts for:

```text
ContributionProfile
AuthorshipProfile
AttributionCreditProfile
ProductionProvenanceGraph
CreativeProcessProfile
```

because media production pipelines repeatedly need to distinguish who/what produced, selected, edited, recorded, authored and was credited.

But generic ownership is distributed:

```text
MF3          provenance/source/attribution representations
MF4          component/work/contributor organization
MF7          creation history/lineage/version
MF8          source action, agency, delegation, collective agency
Human        creativity, intention, social recognition, tradition
Institution  legal/social authorship, rights, work-for-hire, official credit
Runtime      tool/model execution and production realization
Harness      agent workflow/tool contribution provenance
Host         delegated authority/responsibility where operational
World        physical causation / truth about production history
```

A separate universal Media Authorship Foundation would duplicate these owners.

---

# 62. Cross-regime test

Authorship/creation/attribution pressure appears across:

```text
oral tradition
manuscript scribal culture
print authorship
journalism
music composition/performance
film production
photography
scientific collaboration
software/open source
collective publications
social media
AI-assisted production
generative media
multi-agent creative pipelines
```

No one author criterion survives every regime.

The cross-regime invariant is approximately:

> **a grounded relation between a bearer/entity and some scoped creative/contributory production standing, interpreted under a practice/institution that may or may not classify that relation as Authorship and may independently assign credit, rights and responsibility.**

That is a derived standing over existing foundation relations.

---

# 63. Agent-era perturbation

Agent era intensifies:

```text
human + AI co-production
agent-generated drafts
agent editing/revision
multi-agent decomposition
model/tool provenance
principal-agent delegation
synthetic personas
machine attribution claims
automated publication
```

The key requirement is not a new Author primitive but **role transparency**.

For every output ask:

```text
who/what generated which distinctions?
who selected/arranged/revised?
which bearer had AgencyStanding?
who set constraints/goals?
what was delegated?
what practice assigns authorship?
what public attribution is made?
who owns rights?
who bears responsibility?
```

Conflating these into `author` becomes even less defensible in Agent-era systems.

---

# 64. Important survivor — Archive / Preservation Responsibility

Authorship/provenance can matter to archival authenticity and access, but B-I does not solve:

```text
who has preservation responsibility?
for whom?
which representation information must remain?
what access commitment exists?
```

Archive/Preservation Responsibility remains open.

---

# 65. Important survivor — Audience / Public Formation

Creator/author relations do not determine who constitutes an audience/public.

Audience/Public Formation remains a Human/Institution cross-cutting residual.

---

# 66. Important survivor — Reflexive Mediation Ecology

Creators respond to analytics, selection and audience behavior; systems adapt to creators; agents increasingly participate on both sides.

B-I supplies contributor/production roles but does not close the whole-loop ecology.

---

# 67. Important survivor — Translation / Remediation

Translation/remediation can introduce new creative/authorship standing while preserving aspects of a source work.

B-I clarifies role/credit structure but does not solve equivalence/preservation across language/modality/carrier.

---

# 68. Foundation consequence test

Would a numbered Authorship/Creation foundation make distinctions unavailable under the current substrate?

Current answer: **no**.

It would risk collapsing:

```text
causal production
creative contribution
agency
authorship
credit
provenance
ownership
responsibility
delegation
```

into one culturally overloaded term.

Typed profiles and graphs are strictly more explanatory.

---

# 69. Classification update

Canonical Round-B-I classification:

```text
Authorship / Creation / Attribution
= REDUCIBLE / CROSS-CUTTING
= NOT genuinely-new-foundation at current frontier
```

More specifically:

```text
Causal production          → MF3/MF7 + World
Creative action            → MF8 + Human
Contribution roles         → derived operational profile
Authorship                 → derived practice/institution-grounded standing
Joint authorship           → MF4 + MF8/Human + Institution
Collective-work authorship → MF4 selection/arrangement + Institution
Legal work-made-for-hire   → Institution/Law
Attribution/credit         → MF3 + Human/Institution
Rights ownership           → Institution/Law
Responsibility             → Institution/Host/MF8
AI-assisted creation       → Runtime/Harness + Human/MF8 + provenance
AI/nonhuman legal authorship → regime-specific Institution question, not Media primitive
Traditional/community creation → Human/social/Institution + MF7
```

No MF10 is admitted.

---

# 70. FoundationReopen audit

No MF0–MF9 FoundationReopenCondition is triggered.

B-I instead validates:

```text
MF3 provenance/source/content/authority distinctions
MF4 layered/multi-role composition
MF7 lineage/history standing
MF8 action attribution, delegation and collective agency separations
```

No tested individual/collective/legal/traditional/AI case falsifies the frozen substrate.

Thus:

```text
MF0–MF9 = FROZEN
```

---

# 71. Research anchors used

Representative authoritative/comparison anchors:

- U.S. Copyright Office, *Copyright and Artificial Intelligence, Part 2: Copyrightability* (January 29, 2025) — copyrightability of AI-assisted/generated outputs remains tied to sufficient human expressive authorship; mere prompting is not automatically sufficient, while human-authored selection/arrangement/modification and AI assistance can coexist with copyrightability.
- 17 U.S.C. §§101, 201, 202 and Copyright Office Circular/registration guidance — joint work, collective work, anonymous work, work-made-for-hire, initial ownership and material-object/copyright ownership separations.
- U.S. Copyright Office Collective Works guidance — authorship of the collective whole can lie in original selection/coordination/arrangement while component works have distinct authorship.
- ANSI/NISO Z39.104 CRediT — 14 contributor-role taxonomy; explicitly describes contribution roles rather than defining authorship.
- WIPO Traditional Cultural Expressions — community-linked, intergenerational cultural expression pressure against universal individual-originating-author assumptions.
- MF3/MF4/MF7/MF8 frozen Ordivon foundations plus Round B-E/B-G/B-H.

These are comparison/falsification anchors rather than external authority over Ordivon's ontology.

---

# 72. Round B-I closeout

```text
Round B-I target       = Authorship / Creation / Attribution
Result                 = REDUCIBLE / CROSS-CUTTING
New Media primitive    = NONE
MF10                    = UNKNOWN / NOT ADMITTED
FoundationReopen       = NONE
```

Deep result:

> **`Author` is not a universal causal role. Media production requires a graph of contribution, action, provenance, composition and delegation; social/legal practices then classify some scoped relations as Authorship, independently record public Attribution/Credit, assign Rights, and allocate Responsibility. A physical producer can fail to be the legal author; a collective work can have compilation authorship distinct from component authorship; an anonymous work can have authorship without public attribution; AI can causally contribute without receiving legal authorship, while human authorship can survive AI assistance; traditional expressions can lack a single identifiable originating author. The correct Media reconstruction is therefore ContributionProfile + AuthorshipProfile + AttributionCreditProfile + ProductionProvenanceGraph, not a new Foundation or one `createdBy` field.**

The whole-domain search remains open. Surviving residual pressure includes:

```text
Archive / Preservation Responsibility
Audience / Public Formation
Reflexive Mediation Ecology
Translation / Remediation
unknown continents
```

No ordering is canonical and none is admitted as MF10.
