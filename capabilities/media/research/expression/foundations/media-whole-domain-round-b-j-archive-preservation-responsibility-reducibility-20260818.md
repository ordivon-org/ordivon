# Ordivon Media Deep Foundations — Round B-J: Archive / Preservation Responsibility Reducibility

**Date:** 2026-08-18  
**Continuity Task:** `task:media-foundations-mf2h-20260817`  
**Parent:** `media-whole-domain-round-b-i-authorship-creation-attribution-reducibility-20260818.md`  
**Status:** **destructive reducibility / ownership audit only; no MF10 admitted**

---

# 0. Question

Round A explicitly warned:

```text
Archive is not merely persistence.
```

B-H then reduced:

```text
materialization
fixation
storage
persistence
fixity
```

without reducing archival responsibility.

B-G separated provenance/context preservation from truth.
B-I separated authorship/ownership/responsibility.

Round B-J therefore asks the strongest remaining archival question:

> **Does Archive / Preservation Responsibility contain a Media-specific irreducible standing beyond MF3 representation/provenance, MF4 composition/roles, MF6 time, MF7 persistence/state/policy, MF8 agency/delegation, and Institution/Host ownership of obligation/authority/organization?**

The decisive counterfactual is:

```text
World A and World B contain the same information objects,
identical bits, fixity, provenance, representation information,
storage topology and current accessibility.

In A, no bearer has accepted an ongoing preservation/access obligation.
In B, an organization has accepted responsibility to preserve the information
for a defined Designated Community under explicit objectives/policies.
```

There is a real standing difference.

The question is whether that difference is **Archive primitive** or a derived institutional responsibility relation.

---

# 1. Mandatory term separation

Do not collapse:

```text
Collection
Repository
Storage System
Backup
Record
Recordkeeping System
Archive Collection
Archive Institution
Preservation Service
Custodian
Steward
Owner
Rights Holder
Preservation Responsibility
Preservation Capability
Preservation Action
Preservation Outcome
Preservation Objective
Retention Obligation
Access Commitment
Designated Community
Current Consumer
Representation Information
Preservation Description Information
Fixity / Integrity Evidence
Authenticity Evidence
Appraisal / Selection
Succession / Transfer of Custody
Trustworthiness / Certification
```

Especially:

```text
Stored ≠ Archived
Persistent ≠ Preserved
PreservationOutcome ≠ PreservationResponsibility
Custody ≠ Ownership
Ownership ≠ PreservationAuthority
CurrentAccess ≠ AccessCommitment
PublicAccess ≠ OAIS access
DesignatedCommunity ≠ CurrentAudience
Fixity ≠ Authenticity ≠ Truth
Repository ≠ ArchiveInstitution universally
Certification ≠ underlying ArchiveStanding
```

---

# 2. Current OAIS v3 is unusually useful for this destructive test

The current OAIS reference model is:

```text
CCSDS 650.0-M-3
Issue 3
December 2024
```

It explicitly makes section 3.2 `Mandatory Responsibilities` normative.

An OAIS shall, among other responsibilities:

```text
negotiate for and accept appropriate information;
obtain sufficient control for Long Term Preservation;
determine the Designated Community and its Knowledge Base;
ensure the information is Independently Understandable to that community;
follow documented preservation policies/procedures against reasonable contingencies,
including demise of the Archive;
make preserved information available to the Designated Community
with traceability/authenticity evidence.
```

This is direct evidence that `Archive` in OAIS is not merely a storage topology.

---

# 3. Same bits / same storage / different responsibility — the core falsifier

## World A — accidental persistence

```text
Object X stored in replicated storage
checksums valid
metadata complete
format still readable
public access currently possible
no institution has accepted future preservation responsibility
```

## World B — archival stewardship

All physical/information conditions are identical, but organization O has:

```text
accepted preservation responsibility for X
specified target community C
specified preservation objectives
obtained authority/control needed for migration
committed to monitor risks and maintain interpretability
committed to access/dissemination under governing rights
committed to documented preservation policy
```

Then:

```text
ArchiveResponsibilityStanding(B) ≠ ArchiveResponsibilityStanding(A)
```

So B-H persistence mechanics are insufficient.

But the difference is already institutionally expressible as:

```text
Obligation(O, X, C, Objectives, Horizon | Authority, Policy)
```

plus operational capabilities.

This initially favors `cross-cutting / Institution-owned`, not a Media atom.

---

# 4. Responsibility ≠ preservation success

An institution can genuinely accept responsibility and still fail because of:

```text
catastrophic funding loss
unanticipated technical failure
corruption
war/disaster
policy error
lost key/dependency
organizational collapse
```

Therefore:

```text
PreservationResponsibility
↛ PreservationSuccess
```

Responsibility is normative/institutional standing; success is an outcome over time.

MF7 + Institution already require this distinction.

---

# 5. Preservation success ≠ accepted responsibility

The reverse is also possible.

A file/object may survive for centuries because:

```text
storage conditions happen to remain favorable
copies are independently maintained
someone casually keeps it
physical medium is unusually stable
```

without any bearer having undertaken archival stewardship.

Therefore:

```text
PreservationOutcome
↛ PreservationResponsibility
```

This strongly falsifies any naturalistic reduction:

```text
Archive = whatever successfully persisted.
```

---

# 6. Archive institution ≠ archive collection

`Archive` is overloaded.

It may denote:

```text
an organization/institution
a managed collection of records
a physical/digital repository location
a package/container of historical data
a colloquial old-data folder
```

OAIS deliberately uses the organizational sense.

Therefore:

```text
ArchiveCollectionStanding
≠ ArchiveInstitutionStanding
```

A collection can be transferred between institutions while the objects remain largely unchanged.

The institutional bearer/obligation changes independently of collection identity.

---

# 7. Repository ≠ archival responsibility

A repository can provide:

```text
storage
versioning
access
checksums
replication
```

without accepting active Long Term Preservation responsibility for a community.

CoreTrustSeal's current preservation-level position is explicit: to fall within certification scope, applicants must take responsibility for active long-term digital preservation for a defined/designated community.

Thus:

```text
RepositoryCapability
≠ PreservationResponsibility
```

and the repository word alone cannot establish ArchiveStanding.

---

# 8. Backup ≠ Archive

Backup primarily supports recovery of operational state after loss/corruption.

Archive preservation may instead require:

```text
long-term identity/provenance
representation information
authenticity evidence
rights management
community-relative intelligibility
migration/emulation
retention/appraisal policy
future discovery/access
```

Therefore:

```text
BackupCopy ≠ ArchivalInformationObject by role
```

The same bytes may participate in both roles, but role/standing differs.

---

# 9. Custody ≠ responsibility

A cloud/storage provider can physically hold bits while contractual/institutional preservation responsibility remains with another organization.

Thus:

```text
PhysicalCustodian
≠ PreservationResponsibleBearer
```

This matters strongly in outsourced and federated archives.

Physical custody is an operational relation; responsibility is institutional/authority standing.

---

# 10. Responsibility ≠ physical custody

The reverse also holds.

Organization O may remain preservation-responsible while:

```text
storage is outsourced
replicas are geographically distributed
representation information is maintained by a partner archive
access services are delegated
```

OAIS explicitly allows representation information to be referenced from another trusted/partner OAIS rather than all held locally.

Therefore:

```text
PreservationResponsibility
↛ LocalCustodyOfEveryDependency
```

A universal centralized Archive bearer is not required.

---

# 11. Ownership ≠ custody ≠ preservation authority

OAIS explicitly distinguishes ownership/custody/possession of Content Information from intellectual-property rights.

The Archive needs **sufficient control** to carry out long-term preservation, including where necessary authority to migrate representation forms.

Therefore:

```text
ObjectOwner
RightsHolder
Custodian
PreservationAuthority
PreservationResponsibleBearer
```

can be different roles.

This strongly validates B-I role separation.

---

# 12. Sufficient control ≠ total ownership

An Archive may preserve content under:

```text
license
statutory mandate
deposit agreement
contract
delegated authority
```

without owning the underlying copyright/IP.

Thus:

```text
PreservationAuthority
≠ FullOwnership
```

The relevant ontology is scoped authority over preservation actions.

MF8/Host/Institution already owns delegation/authority.

---

# 13. Designated Community ≠ actual current users

OAIS defines a Designated Community as the community that should be able to understand the information.

It may be:

```text
general public
specialist researchers
future operators
particular scientific discipline
restricted professional community
```

There may be zero current users.

Therefore:

```text
DesignatedCommunity
≠ CurrentAudience
≠ ObservedConsumers
```

B-D/B-B publicness/exposure cannot substitute for this role.

---

# 14. Designated Community is a beneficiary/competence scope

The important relation is approximately:

```text
PreservedInformation X
must remain independently understandable/useful
relative to KnowledgeBase(C)
of community C
```

This is not an intrinsic property of X.

The same package may be independently understandable to expert community C1 but opaque to C2.

Therefore:

```text
Understandability(X)
```

is underspecified.

Use:

```text
IndependentUnderstandability(X, C | KnowledgeBase, Objectives, Time)
```

---

# 15. Understandability ≠ current successful interpretation

A package can satisfy an archive's Representation Information requirements even when no current consumer is presently interpreting it.

Conversely one surviving expert can understand an under-documented object even if the archive has failed to make it independently understandable to the designated community.

Therefore:

```text
CurrentInterpretation
≠ IndependentUnderstandabilityStanding
```

This parallels MF3 standing vs current activation.

---

# 16. Named expert dependency is precisely an archival failure mode

OAIS v3 defines Long Term Preservation in terms of information being Independently Understandable by a Designated Community, without needing special resources such as named individuals.

This exposes a powerful hard case:

```text
File bits remain perfect
one retiring engineer still knows how to decode it
no adequate Representation Information exists
```

Then:

```text
BitPersistence = yes
PracticalInterpretationByExpert = yes
IndependentUnderstandabilityForCommunity = no / fragile
```

This is not a new representation primitive.

It is a future-oriented preservation obligation over MF3 Representation Information relative to a Human/community knowledge profile.

---

# 17. Representation Information is itself information/representation

OAIS requires data objects to be associated with enough Representation Information to make them understandable to the Designated Community.

But Representation Information may itself require further Representation Information.

Therefore preservation can create a network:

```text
Data Object
→ Representation Information
→ Representation Information for that information
→ ...
```

The termination condition depends on the community Knowledge Base.

This is already MF3 recursive representation + community-relative grounding.

No archival semantic atom is needed.

---

# 18. Representation Information need not be co-located

OAIS explicitly permits an archive to reference Representation Information held in another trusted/partner Archive.

Therefore:

```text
PreservationPackageCompleteness
≠ PhysicalCoLocation
```

and:

```text
ArchiveBoundary
```

can depend on trusted external relations.

MF4 composition + Network/Institution trust/dependency relations suffice.

---

# 19. Designated Community can change over time

OAIS v3 explicitly notes that a Designated Community definition or Knowledge Base may evolve.

Information understandable today may become opaque tomorrow because terminology/software/domain knowledge disappears.

Therefore:

```text
IndependentUnderstandability_t1
↛ IndependentUnderstandability_t2
```

without changes to the preserved bytes.

This is a dynamic relation among:

```text
MF3 representation information
MF6 time
MF7 community/knowledge/preservation state
Human knowledge
Institutional preservation actions
```

---

# 20. Preservation Objectives make preservation profile-relative

OAIS v3 newly emphasizes Preservation Objectives to make independent-understandability claims more testable.

A preservation objective is expected to be specific, actionable and measurable.

Thus:

```text
Preserved = true
```

is too coarse.

A valid claim must state:

```text
what properties/information/functions are to remain available
for which community
under which horizon/conditions
with which authenticity evidence
```

This strongly aligns with MF3/MF4 typed-equivalence results from B-E/B-G.

---

# 21. Preservation Objectives can change without object identity changing

Funders/stakeholders/community needs can alter the preservation objective while the underlying object remains the same.

Therefore:

```text
ObjectIdentity
≠ PreservationObjectiveIdentity
```

ArchiveStanding includes future-oriented policies, not only properties of holdings.

---

# 22. Preservation planning ≠ preservation action

A repository can develop:

```text
migration plan
format strategy
community review plan
risk response plan
```

without yet executing the transformation.

Therefore:

```text
PreservationPlan
≠ PreservationAction
```

MF3 represents plans/policies; MF7 tracks state/dynamics; MF8 applies where action is genuinely agential/institutional.

---

# 23. Preservation action ≠ preservation success

Migration may be executed according to plan yet destroy an important significant property.

Thus:

```text
ActionPerformed
≠ ObjectiveSatisfied
```

Evaluation must be relative to Preservation Objectives and evidence.

No special Archive causal primitive is required.

---

# 24. Fixity ≠ authenticity

B-H already separated PREMIS fixity from preservation success.

OAIS additionally requires evidence supporting Authenticity and traceability to originally submitted Content Information.

Therefore:

```text
CurrentDigestMatches
≠ CompleteAuthenticityEvidence
```

Authenticity may require provenance, chain of custody, transformation history and identity criteria.

This remains MF3/MF7 + institutional evidence.

---

# 25. Authenticity evidence ≠ truth of content

A perfectly authentic historical record can contain false claims.

Therefore:

```text
AuthenticArchiveRecord
≠ TrueRepresentation
```

B-G's provenance/truth separation remains intact.

---

# 26. Access commitment ≠ unrestricted access

A crucial OAIS definition:

```text
Open
```

means the standards/reference-model development occurs in open forums; it **does not** imply unrestricted archive access.

An Archive can legitimately preserve restricted/confidential information while making it available only under governed conditions.

Therefore:

```text
ArchiveAccessCommitment
≠ PublicAccess
```

and B-D publicness must not be imported as an archival requirement.

---

# 27. Access commitment ≠ current availability

An Archive can temporarily lose service while retaining an ongoing obligation to restore access.

Conversely a public mirror can currently provide access while bearing no long-term obligation.

Thus:

```text
CurrentAvailability
≠ AccessCommitment
```

This cleanly distinguishes status/obligation from instantaneous system state.

---

# 28. Current availability ≠ discoverability

B-D already separated these.

OAIS adds Descriptive Information / finding aids because long-term holdings can be preserved yet unusable if consumers cannot locate them.

Therefore:

```text
Preserved
≠ Discoverable
```

but discoverability remains a derived access/selection/representation profile, not an Archive primitive.

---

# 29. Selection/appraisal ≠ preservation responsibility

Archives commonly select what enters the preservation boundary.

But:

```text
Appraisal/Selection
```

is a policy/action over candidates.

B-F already reduced generic selection/gatekeeping.

An Archive can accept responsibility for whatever its policy selects; selection itself is not the same relation as responsibility.

---

# 30. Retention policy ≠ persistence outcome

A policy may require retention for 20 years, forever, or until an event.

The bits might be lost earlier or accidentally survive longer.

Therefore:

```text
RetentionObligation
≠ ActualPersistenceDuration
```

Again Institution + MF6/MF7 handles the distinction.

---

# 31. Deletion can be archival policy-conformant

OAIS requires no ad-hoc deletion, not necessarily universal eternal retention of every object.

Deletion may be allowed under an approved preservation strategy/policy.

Therefore:

```text
ArchiveStanding
≠ NeverDeleteAnything
```

A preservation ontology must include governed disposition, not only indefinite accumulation.

---

# 32. Preservation responsibility can be distributed

An archive may depend on:

```text
external storage provider
format registry
partner archive
identity service
preservation network
rights holder
community reviewers
```

No one bearer must physically perform every preservation operation.

Thus:

```text
PreservationResponsibility
≠ centralized execution
```

This is analogous to distributed coordination lessons elsewhere in Ordivon.

---

# 33. Delegated preservation execution ≠ transferred responsibility

Organization O can delegate storage/migration/monitoring tasks to provider P while retaining contractual/institutional accountability.

Therefore:

```text
Executor(P)
≠ ResponsibleArchive(O)
```

unless the governing agreement transfers responsibility itself.

MF8/Host delegation/authority already covers this relation.

---

# 34. Responsibility can be transferred

An Archive may cease operation and transfer holdings/mission to a successor.

OAIS mandatory policy explicitly considers reasonable contingencies including demise of the Archive; security guidance notes successor identity and provenance-preserving transfer.

Therefore:

```text
ArchiveOrganizationIdentity
≠ PreservationMission/ResponsibilityContinuity
```

A responsibility lineage may continue across institutional succession.

MF7 successor/continuation + Institution responsibility transfer handles this.

---

# 35. Institutional continuity ≠ object continuity

The same institution can continue while holdings change.

The same holdings can continue while institutions change.

Thus:

```text
ArchiveBearerIdentity
≠ HoldingIdentity
```

No one-to-one ontology is defensible.

---

# 36. Preservation responsibility can begin before custody

A submission/deposit agreement can create future obligations before the complete information package has been ingested.

Therefore:

```text
ResponsibilityStanding
```

may be partly prospective.

It does not require current local possession of every object.

Institutional obligation precedes some physical transitions.

---

# 37. Custody can precede responsibility

A repository can temporarily hold data pending appraisal/acceptance without yet accepting long-term preservation responsibility.

Therefore:

```text
Possession
↛ AcceptedStewardship
```

This is the reverse dissociation.

---

# 38. Personal preservation pressures institutional essentialism

An individual can deliberately preserve family letters, media or research data for future descendants/researchers with real planning, migration and access intentions.

This may deserve broad `stewardship` language even when not an OAIS institution.

Therefore:

```text
PreservationResponsibility
```

need not require a large bureaucracy.

The minimal bearer may be an individual agent or small group.

But this pressure still maps to generic MF8 responsibility/agency + beneficiary scope + preservation objectives, not a Media primitive.

---

# 39. Non-agent storage cannot bear responsibility by itself

A disk array can persist data but cannot, merely by storing bits, hold normative responsibility.

If an automated repository is only a mechanism executing rules with no grounded agency/institution bearer, then responsibility lies elsewhere or is absent.

Thus:

```text
StorageMechanism
≠ ResponsibleSteward
```

Responsibility requires some admissible agency/institutional standing route.

---

# 40. Artificial agents can execute preservation without automatically owning responsibility

Agent-era systems can:

```text
monitor formats
migrate objects
repair replicas
validate fixity
update metadata
answer access requests
```

But operational AgencyStanding does not automatically confer social/legal preservation responsibility.

Thus:

```text
PreservationAgentExecutor
≠ PreservationResponsiblePrincipal
```

unless a practice/institution explicitly grounds that standing.

---

# 41. Artificial/collective bearer could in principle become responsible under a future regime

Ordivon must not hard-code `human institution only`.

If a future regime recognizes an autonomous/collective artificial bearer with:

```text
persistent identity
accepted obligations
authority/control
accountability interfaces
beneficiary commitments
resource continuity
```

then the same derived PreservationResponsibilityProfile could apply.

This confirms that the generic ontology is responsibility/authority standing, not a human-specific Archive substance.

---

# 42. Designated Community can include machine consumers

OAIS terminology historically assumes consumer communities, but Agent-era preservation can target:

```text
future software agents
scientific pipelines
machine-readable standards consumers
robotic/automated operators
human+agent communities
```

The deep requirement is not phenomenological human understanding.

It is sufficient Representation Information/capability for the declared consumer class to reconstruct/recruit the preserved information under preservation objectives.

This is an Agent-era extension of the role, not a new primitive.

---

# 43. Machine understandability ≠ human understandability

A binary scientific object can be machine-actionable with a schema while opaque to unaided humans.

Conversely a scan may be human-readable but not machine-parseable.

Therefore:

```text
UnderstandableTo(C)
```

must remain consumer-class relative.

MF0 recruitment + MF3 representation + Runtime/Harness capability profiles suffice.

---

# 44. Designated Community is not fixed forever

An archive may broaden from specialist researchers to public/agent consumers.

That can require new:

```text
schemas
documentation
translations
emulators
interfaces
finding aids
```

without changing the core historical information object.

Thus preservation targets evolve relationally.

---

# 45. Preservation Watch is monitoring/adaptation, not a primitive

OAIS v3 adds a Preservation Watch function within Preservation Planning.

Its role is to monitor changes relevant to long-term preservation and feed strategy/planning.

Structurally this is:

```text
observe environment/community/technology
→ detect threat/change
→ update preservation policy/plan
→ act/migrate/document
```

which is MF1 measurement + MF7 dynamics + MF8/Institution action.

No new Archive atom appears.

---

# 46. Preservation is reflexive and future-oriented

The archive changes representations to preserve future usability:

```text
migration
normalization
emulation
metadata augmentation
representation-information expansion
```

Thus preservation may intentionally change present bearer state to conserve a declared future relation.

This is a generic goal/constraint/action trajectory, not an ontologically unique causal form.

---

# 47. Trustworthiness ≠ preservation responsibility

A repository may accept preservation responsibility but be unreliable.

A trustworthy repository must provide evidence that its organization/processes/technical systems merit confidence.

Therefore:

```text
ResponsibilityStanding
≠ TrustworthinessAssessment
```

Trustworthiness is an epistemic/evaluative profile over stewardship performance/capability.

---

# 48. Certification ≠ underlying standing

CoreTrustSeal / ISO 16363-style certification evaluates whether a repository meets specified criteria.

Certification can be absent while real stewardship exists, or present and later become stale relative to current practice.

Therefore:

```text
Certified
≠ ArchiveStanding by identity
```

Certification is evidence/institutional recognition, not the primitive source of every stewardship relation.

---

# 49. Preservation level is not one universal scalar

CoreTrustSeal's curation/preservation-level work exists precisely because repositories provide different degrees/kinds of care.

A repository may preserve:

```text
bits only
format readability
semantic interpretability
provenance
discoverability
active transformation
specific significant properties
```

under different commitments.

Thus:

```text
PreservationLevel = one scalar
```

is unsafe without a declared capability/objective profile.

---

# 50. Rights constrain preservation but do not define it

PREMIS separately models Rights because an Archive may need permission to:

```text
copy
migrate
modify
provide access
```

Rights are enabling/limiting conditions.

Therefore:

```text
RightsStanding
≠ PreservationResponsibility
```

though insufficient rights may make an accepted objective unrealizable.

---

# 51. Capability ≠ authority

A repository might technically be able to copy/migrate an object but lack permission.

Conversely it might possess legal authority but lack technical capability/resources.

Therefore:

```text
CanPreserve
≠ AuthorizedToPreserve
≠ ObligatedToPreserve
```

This three-way separation is foundation-critical.

---

# 52. Obligation ≠ resource guarantee

An institution may remain obligated while underfunded or temporarily unable to meet all objectives.

Thus:

```text
PreservationObligation
≠ SufficientResources
```

Resource governance belongs to Institution/Finance/Host.

---

# 53. Resource capability ≠ obligation

A hyperscale storage provider can have enormous technical ability without accepting archival duty for arbitrary hosted objects beyond contract terms.

Thus:

```text
Capability
↛ StewardshipResponsibility
```

again defeating capability-based archive ontology.

---

# 54. Access benefit is community-relative, not necessarily public good

An archive may serve:

```text
classified government users
medical researchers
family descendants
scientific specialists
future autonomous systems
general public
```

Therefore archival obligation cannot be defined as universal publicness.

B-D remains separate.

---

# 55. Record status ≠ Archive responsibility

A document may be an institutional/legal record even before transfer to an archive.

A preservation archive may also hold non-record works/artifacts/data.

Therefore:

```text
RecordStanding
≠ ArchivedStanding
```

Recordkeeping/legal-evidence ontology remains Institution-specific.

---

# 56. Archive ≠ memory universally

Human/social memory can persist through oral tradition, ritual, practice and repeated performance without an archive institution.

An archive can hold objects nobody currently remembers.

Therefore:

```text
Archive ≠ Memory
```

Human/social memory remains Human-owned; archival systems can support it.

---

# 57. Archive ≠ history

Archival holdings are evidence/material from which historical claims can be constructed; they are not identical to historical truth.

Thus:

```text
ArchivedEvidence
≠ History
≠ Truth
```

World/Human epistemic disciplines remain distinct.

---

# 58. Archive ≠ canon

Selection into an archive can influence cultural canonization, but archival inclusion is not identical to aesthetic/social canonical status.

This protects ownership boundaries with Human/Culture/Institution and B-F selection.

---

# 59. Archive can preserve adversarial/false/harmful material

Preservation responsibility is compatible with content being:

```text
false
offensive
malware-like
fraudulent
politically contested
restricted
```

provided rights/security/policy conditions are met.

Therefore:

```text
WorthPreserving
```

is a selection/appraisal/institutional value judgment, not truth/quality identity.

---

# 60. Authenticity support requires traceability, not immutable original-only storage

OAIS requires dissemination that is a copy of, or traceable to, original submitted Content Information with evidence supporting authenticity.

This permits transformations/migrations while maintaining provenance.

Therefore:

```text
AuthenticPreservation
≠ NeverTransform
```

B-E/B-H typed continuation remains correct.

---

# 61. Archive can have multiple valid representations/derivatives

An AIP may have successors/migrated versions; access may produce transformed DIPs.

Thus:

```text
ArchivalObjectIdentity
```

cannot mean one immutable byte string.

MF7 lineage + MF3/MF4 equivalence already handles this.

---

# 62. Preservation package ≠ dissemination package

OAIS explicitly distinguishes:

```text
SIP — Submission Information Package
AIP — Archival Information Package
DIP — Dissemination Information Package
```

The package sent by producer, stored for preservation, and delivered to consumer need not be byte-identical.

Therefore:

```text
IngestRepresentation
≠ PreservationRepresentation
≠ AccessRepresentation
```

while lineage/traceability can be preserved.

This is another strong reduction to MF3/MF4/MF7.

---

# 63. Archival standing is scope-relative per holding/mission

An organization may accept preservation responsibility for collection X but not Y.

Therefore:

```text
ArchiveOrganization(O)
```

does not entail:

```text
PreservationResponsibility(O, every object it temporarily stores)
```

Responsibility must be object/collection/scope typed.

---

# 64. Multiple responsible archives can coexist

LOCKSS-like/federated/cooperative arrangements can distribute preservation obligations across organizations.

Thus one information object can have:

```text
Responsibility(O1,X)
Responsibility(O2,X)
...
```

simultaneously under different scopes/agreements.

There need not be one canonical archive owner.

---

# 65. Conflicting preservation objectives are possible

Different responsible institutions may prioritize:

```text
bit-level fidelity
original hardware behavior
public accessibility
privacy restrictions
research usability
legal evidentiary integrity
```

The objectives can conflict.

Therefore there is no universal PreservationUtility function intrinsic to the object.

Policy/Institution chooses the typed objective.

---

# 66. Preservation obligation can terminate lawfully

A mandate/contract may expire, collection may be deaccessioned under policy, or responsibility may transfer.

Thus:

```text
PreservationResponsibility
```

is temporally bounded and institutionally governed.

It is not necessarily eternal.

MF6/MF7 already provide temporal standing.

---

# 67. Failure to preserve can constitute breach without changing current object state

Suppose an institution is obligated to establish geographic redundancy by date T but has not done so; the object is still intact.

Then:

```text
CurrentObjectState = healthy
PreservationObligationPerformance = deficient
```

This demonstrates again that stewardship standing is normative/institutional, not reducible to object condition.

---

# 68. Same technical actions can have different stewardship standing

Two systems may run identical fixity checks/migrations.

One does so as part of accepted archival duty; the other performs the same operations for temporary operational reasons.

Therefore:

```text
PreservationTechniqueExecution
≠ PreservationResponsibility
```

Purpose/obligation/beneficiary standing matters.

---

# 69. Same responsibility can be realized through different technical architectures

One archive may use:

```text
local storage
```

another:

```text
cloud replication + partner format registry + emulation service
```

while both discharge equivalent obligations.

Thus:

```text
ArchiveResponsibilityIdentity
≠ TechnicalArchitectureIdentity
```

This strongly favors a derived responsibility profile over a Media substrate primitive.

---

# 70. Proposed `PreservationResponsibilityProfile`

No new Foundation is introduced.

```text
PreservationResponsibilityProfile(O, X | Σ) = <
  ResponsibleBearer O,
  Object/Collection Scope X,
  ResponsibilityStandingRoute,
  Acceptance/Charter/Agreement,
  DesignatedCommunity / Beneficiary Class,
  CommunityKnowledgeBase / Capability Assumptions,
  PreservationObjectives,
  TimeHorizon,
  SufficientControl / Authority,
  RightsConstraints,
  Custody/Execution Providers?,
  RepresentationInformation Requirements,
  Provenance/Authenticity Requirements,
  SignificantProperties / TransformationalProperties?,
  Retention/Disposition Policy,
  PreservationPlanning/Watch,
  Risk/Contingency Policy,
  Access/Dissemination Commitment,
  Successor/Transfer Plan?,
  Evidence/Audit Trail,
  Resource/Capability Assumptions,
  Current Performance State,
  Uncertainty,
  Scope
>
```

This is an institutional/operational standing profile, not a new ontological substance.

---

# 71. Proposed `IndependentUnderstandabilityProfile`

```text
IndependentUnderstandabilityProfile(X, C | t, Σ) = <
  ContentInformation,
  Consumer/DesignatedCommunity C,
  AssumedKnowledgeBase(C,t),
  RepresentationInformation Network,
  Required Software/Tools?,
  Required External Dependencies?,
  PreservationObjectives,
  Test/Evidence Method,
  Known Gaps,
  Current Understandability Assessment,
  Uncertainty,
  Scope
>
```

This preserves OAIS's powerful consumer-relative insight without treating `Understandable` as intrinsic.

---

# 72. Proposed `PreservationOutcomeProfile`

```text
PreservationOutcomeProfile(X, ObjectiveSet | t0→t1, Σ) = <
  Objective Set,
  Identity/Lineage Evidence,
  Bit/Fixity Evidence?,
  Representation/Content Preservation,
  SignificantProperty Preservation?,
  Provenance/Authenticity Evidence,
  Current Readability,
  Current Independent Understandability,
  Discoverability/Access State,
  Rights Compliance,
  Transformations Performed,
  Failures/Losses,
  Uncertainty,
  Scope
>
```

Responsibility and outcome must remain separate profiles.

---

# 73. Strongest irreducibility test

Construct A and B identical in:

```text
responsible bearer identity
object/collection scope
accepted obligation/charter
Designated Community
community Knowledge Base
preservation objectives
time horizon
authority/control
rights
custody/execution providers
representation information
provenance/authenticity requirements
retention/access policy
monitoring/planning
succession/transfer rules
resource commitments
evidence/audit state
```

and claim:

```text
Archive/PreservationResponsibilityStanding(A)
≠
Archive/PreservationResponsibilityStanding(B)
```

At the current frontier there is no grounded difference left.

Any attempted difference introduces an already-modelable change in:

```text
institutional obligation
beneficiary/community scope
authority
policy
state/history
representation requirements
execution/capability
provenance/evidence
```

No independent Archive atom survives.

---

# 74. Cheapest falsifier matrix

| Proposed universal claim | Cheapest counterexample | Result |
| --- | --- | --- |
| Archive = persistent storage | accidental long-lived mirror | falsified |
| Preservation responsibility = preservation success | responsible archive that fails | falsified |
| Preservation success = responsibility | accidental survival | falsified |
| Repository = Archive | storage/access repository without active long-term duty | falsified |
| Backup = Archive | recovery backup lacking long-term interpretability/community commitments | falsified |
| Custodian = responsible archive | outsourced cloud custody | falsified |
| Responsibility requires local custody | partner/external Representation Information/storage | falsified |
| Owner = responsible archive | licensed/deposited preservation | falsified |
| Full ownership required | sufficient-control agreements | falsified |
| Designated Community = current users | future/no-current-user community | falsified |
| Understandability is intrinsic | expert vs general-public Knowledge Base | falsified |
| Current expert understanding = independent understandability | single named expert dependency | falsified |
| Representation Information must be local | trusted partner archive | falsified |
| Understandability remains stable if bytes stable | community knowledge erosion | falsified |
| Preserved is one boolean | different Preservation Objectives | falsified |
| Plan = action = outcome | migration plan / failed migration | falsified |
| Fixity = authenticity | intact forged/misattributed object | falsified |
| Authenticity = truth | authentic false historical record | falsified |
| Archive access = unrestricted public access | restricted OAIS holdings | falsified |
| Current access = access commitment | temporary outage / public mirror | falsified |
| Preserved = discoverable | preserved but uncatalogued object | falsified |
| Appraisal = preservation responsibility | candidate selection vs accepted duty | falsified |
| Retention policy = persistence duration | loss/accidental over-retention | falsified |
| Archive means never delete | governed disposition | falsified |
| One central archive must execute all preservation | distributed/outsourced preservation | falsified |
| Executor = responsible principal | delegated preservation provider | falsified |
| Archive organization identity = mission continuity | successor transfer after demise | falsified |
| Responsibility requires current possession | prospective submission agreement | falsified |
| Possession implies accepted responsibility | temporary holding/pending appraisal | falsified |
| Large institution required | individual/small-group stewardship | falsified |
| Storage mechanism can bear responsibility by storage alone | passive disk array | falsified |
| Artificial preservation executor = responsible principal | delegated preservation agent | falsified |
| Human-only Designated Community required | machine/agent consumer class | falsified as deep ontology assumption |
| Trustworthiness = responsibility | responsible but unreliable repository | falsified |
| Certification = ArchiveStanding | uncertified real stewardship / stale certificate | falsified |
| Preservation level is one scalar | bit/semantic/access/property-specific commitments | falsified |
| Rights = responsibility | permission without duty / duty with scoped permission | falsified |
| Capability = authority = obligation | technically able but unauthorized/non-obligated system | falsified |
| RecordStanding = ArchiveStanding | active institutional record / non-record archival object | falsified |
| Archive = memory/history/canon | oral memory, false archives, uncatalogued holdings | falsified |
| Authentic preservation requires byte immutability | traceable migration | falsified |
| SIP = AIP = DIP | OAIS package transformation | falsified |
| One object has one responsible archive | cooperative/federated stewardship | falsified |
| Preservation responsibility is eternal | lawful termination/transfer | falsified |
| Technical preservation action establishes stewardship | same checks run for temporary ops | falsified |
| One technical architecture defines Archive | equivalent obligations across different architectures | falsified |

The survivor is a typed institutional responsibility/beneficiary/authority/objective relation—not a new Media foundation.

---

# 75. Irreducibility test

Question:

> Does Archive / Preservation Responsibility require a primitive absent from MF0–MF9 and adjacent owners?

Round B-J answer:

**No concrete Media-specific irreducible survivor.**

Reduction:

```text
Information/Representation          → MF3
Collection/package composition      → MF4
Temporal horizon                    → MF6
Persistence/identity/lineage        → MF7
Policy/objective/state              → MF3 + MF7
Preservation actions                → MF8 where agential
Institutional responsibility        → Institution/Host
Authority/control/delegation        → MF8 + Host/Institution
Designated Community                → Human/social/Institution role + MF4
Community Knowledge Base            → Human/Agent capability profile
Representation Information          → MF3 recursive representation
Fixity/integrity                    → B-H / MF7 evidence
Provenance/authenticity evidence    → MF3/MF7 + B-G
Rights                              → Institution/Law
Storage/execution                   → Runtime/Infrastructure
Networked/partner dependencies      → Network + Institution
Access/discoverability              → B-D/B-F + Network/Runtime
Preservation outcome                → derived evaluation profile
Trustworthiness/certification       → institutional/epistemic assessment
```

Therefore the candidate fails foundation-level irreducibility.

---

# 76. Ownership test

Media should retain derived operational concepts for:

```text
PreservationResponsibilityProfile
IndependentUnderstandabilityProfile
PreservationOutcomeProfile
ArchiveHoldingProfile
PreservationDependencyGraph
SuccessionTransferProfile
```

because preservation is central to Media persistence across time.

But generic ownership is distributed:

```text
MF3          information/representation/provenance/representation-information
MF4          holdings/packages/community/role composition
MF6          long-term horizon
MF7          persistence/state/policy/lineage
MF8          preservation action/delegation when agential
Human        human knowledge bases, cultural/community needs
Institution  stewardship duty, mandate, records law, access/retention obligations
Host         persistent responsibility/authority/delegation specializations
Runtime      storage/migration/execution mechanics
Network      distributed dependencies/access realization
World        physical degradation/environment risk
Finance      resource/funding sustainability where relevant
```

A separate universal Media Archive foundation would duplicate these owners.

---

# 77. Cross-regime test

Preservation responsibility appears across:

```text
family/personal archives
religious/scriptural stewardship
state records
libraries/manuscript repositories
museums
film/audio archives
scientific data repositories
software/net-art archives
institutional records systems
web archives
cloud/federated preservation networks
agent-managed knowledge stores
future machine-readable archives
```

The technical substrate varies radically.

The cross-regime invariant is approximately:

> **a bearer accepts a future-oriented, scoped obligation to maintain specified information/identity/use relations for a beneficiary/community under declared objectives, authority, policy and evidence conditions.**

That is a generic responsibility/institution relation specialized to preservation, not a Media-specific primitive.

---

# 78. Agent-era perturbation

Agent era intensifies:

```text
machine-targeted Representation Information
autonomous format monitoring
continuous migration
agent-maintained provenance graphs
selective machine forgetting/retention
self-updating access interfaces
machine consumers as Designated Communities
preservation agents delegated by institutions
rapidly changing model/tool dependencies
```

The main consequence is that archival profiles must become more explicit about:

```text
consumer capability
machine-readable schemas
software/model dependencies
authority/delegation
policy version
automated transformation evidence
responsible principal
```

But no Agent-era Archive primitive survives.

---

# 79. Important survivor — Audience / Public Formation

A Designated Community is a normative/beneficiary class defined for preservation objectives.

It is **not** the same thing as a socially constituted public/audience.

Thus B-J does not close:

```text
Audience / Public Formation
```

which remains primarily Human/social/Institutional.

---

# 80. Important survivor — Reflexive Mediation Ecology

Archives shape what remains available for later selection, historical memory, model training and cultural production; those later uses can alter future acquisition/preservation policy.

B-J supplies stewardship/preservation nodes but does not close the entire feedback ecology.

Keep:

```text
Reflexive Mediation Ecology
= unresolved cross-cutting referent
```

---

# 81. Important survivor — Translation / Remediation

Archive preservation often requires migration/transformation and may add Representation Information for new communities.

But B-J does not settle exactly which semantic/pragmatic/style/affordance relations are preserved across language/modality/carrier transformations.

Translation/Remediation remains open.

---

# 82. Important methodological result — Archive is an excellent derived institution

The reduction result should **not** be read as diminishing archive importance.

Archive is a particularly good example of a high-level institution that is real because many lower-level standings are jointly maintained:

```text
responsibility
authority
future beneficiary
representation
identity/persistence
policy
monitoring
access
provenance
resources
```

Its reality is relational/composite rather than primitive.

This pattern resembles earlier Ordivon findings about persistent purposive coordination: high-level reality need not be primitive to be operationally indispensable.

---

# 83. Foundation consequence test

Would a numbered Archive/Preservation Foundation create distinctions unavailable under current substrate?

Current answer: **no**.

It would risk collapsing:

```text
storage
persistence
stewardship obligation
custody
authority
rights
community
understandability
preservation objective
access
trustworthiness
```

into one overloaded noun.

Typed profiles expose the actual causal/normative structure much better.

---

# 84. Classification update

Canonical Round-B-J classification:

```text
Archive / Preservation Responsibility
= REDUCIBLE / CROSS-CUTTING / PRIMARILY INSTITUTION-OWNED
= NOT genuinely-new-foundation at current frontier
```

More specifically:

```text
Storage/fixity/persistence            → already-covered / B-H + MF7 + Runtime
Preservation responsibility           → derived Institution/Host responsibility profile
Designated Community                  → Human/social/Institution role profile
Independent Understandability        → MF3 + consumer/community capability profile
Representation Information            → already-covered / MF3 recursive representation
Preservation Objectives               → MF3 policy representation + MF7 evaluation/constraint
Preservation Planning/Watch           → MF1/MF7/MF8 + Institution
Rights/authority/control              → Institution/Law/Host
Authenticity/provenance               → MF3/MF7/B-G
Access/discoverability                 → B-D/B-F + Network/Runtime
Trustworthiness/certification          → institutional/epistemic assessment
Archive succession                    → MF7 continuation + Institution responsibility transfer
```

No MF10 is admitted.

---

# 85. FoundationReopen audit

No MF0–MF9 FoundationReopenCondition is triggered.

B-J instead validates:

```text
MF3 standing representation can persist inactive and recursively depend on Representation Information.
MF3 provenance/content remain distinct.
MF4 roles/collections/packages can be scope-relative.
MF6 long-term claims need explicit horizons.
MF7 persistence/status/policy/continuation remain distinct from obligation.
MF8 action and delegation do not collapse into responsibility.
```

No archival case falsified the frozen substrate.

Thus:

```text
MF0–MF9 = FROZEN
```

---

# 86. Research anchors used

Representative primary/authoritative comparison anchors:

- CCSDS 650.0-M-3, *Reference Model for an Open Archival Information System (OAIS)*, Issue 3, December 2024 — current OAIS model; normative mandatory responsibilities, Designated Community, Independent Understandability, Preservation Objectives, sufficient control, preservation policy, access and authenticity evidence.
- CCSDS 652.0-M-2, *Audit and Certification of Trustworthy Digital Repositories*, December 2024 — trustworthiness/certification as an audit layer rather than storage identity.
- CCSDS 653.0-M-1, *Information Preparation to Enable Long Term Use*, December 2024 — representation/information preparation for long-term use.
- Library of Congress PREMIS Data Dictionary v3.0 — preservation metadata model separating Objects, Events, Rights and Agents, with fixity, significant properties, preservation level and event/rights relations.
- CoreTrustSeal Requirements 2023–2025 and 2024 Curation & Preservation Levels position paper — certification scope requires active long-term preservation responsibility for a defined/designated user community; preservation/curation levels are not reducible to storage alone.
- MF3/MF4/MF6/MF7/MF8 frozen Ordivon foundations plus Round B-D/B-E/B-F/B-G/B-H/B-I.

These are comparison/falsification anchors rather than authorities that override Ordivon's ontology.

---

# 87. Round B-J closeout

```text
Round B-J target       = Archive / Preservation Responsibility
Result                 = REDUCIBLE / CROSS-CUTTING / PRIMARILY INSTITUTION-OWNED
New Media primitive    = NONE
MF10                    = UNKNOWN / NOT ADMITTED
FoundationReopen       = NONE
```

Deep result:

> **Archival reality survives the destruction of `archive = storage`, but it survives as an institutional responsibility relation rather than a Media primitive. The real difference between a long-lived repository and an archive is not bits or fixity: it is a future-oriented accepted obligation over scoped information, beneficiaries/Designated Communities, preservation objectives, sufficient authority/control, representation-information requirements, monitoring/planning, access commitments, provenance/authenticity evidence and succession contingencies. Responsibility is neither preservation success nor physical custody; understandability is community-relative; access need not be public; storage/execution can be delegated; and archival mission can survive institutional succession. These relations are fully reconstructible from MF3/MF4/MF6/MF7/MF8 plus Human/Institution/Host/Runtime/Network owners. Archive should therefore be retained as a high-value derived institutional concept, not admitted as MF10.**

The whole-domain search remains open. Surviving known residual pressure now includes:

```text
Audience / Public Formation
Reflexive Mediation Ecology
Translation / Remediation
unknown continents
```

No ordering is canonical and none is admitted as MF10.
