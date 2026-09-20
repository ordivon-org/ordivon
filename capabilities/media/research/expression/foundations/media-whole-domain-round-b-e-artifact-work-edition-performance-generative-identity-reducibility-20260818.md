# Ordivon Media Deep Foundations — Round B-E: Artifact / Work / Edition / Performance / Generative Identity Reducibility

**Date:** 2026-08-18  
**Continuity Task:** `task:media-foundations-mf2h-20260817`  
**Parent:** `media-whole-domain-round-b-d-publicness-addressability-publication-reducibility-20260818.md`  
**Status:** **destructive reducibility / ownership audit only; no MF10 admitted**

---

# 0. Question

Round A left one of the strongest residuals:

```text
Artifact / Work / Edition / Performance / Generative Identity
```

because traditional media practice repeatedly distinguishes:

```text
work
expression / realization
manifestation / edition
copy / item
performance
documentation
recording
revision
adaptation
fork
restoration
iteration
```

while oral, live, software and generative media make any fixed artifact-centric model unstable.

Round B-E asks:

> **Is there a Media-specific `WorkStanding` or `ArtifactIdentity` primitive that cannot be reconstructed from MF3 Representation + MF4 Composition + MF7 Identity/Persistence/Lineage, with Agency/Institution/Human/Runtime specializations where needed?**

The strongest irreducibility test is deliberately severe:

> Construct two cases identical in token/type/content/organization/history/provenance/institutional standing and all declared identity criteria, yet still genuinely different in work identity. If that cannot be done without smuggling in an unmodeled criterion, `WorkStanding` is not an independent primitive.

---

# 1. Term separation

Do not collapse:

```text
Physical Object
Carrier
Artifact
Representation Token
Representation Type
Composition Specification
Composition Token
Active Performance / Execution
Work
Expression / Realization
Manifestation / Edition
Copy / Item
Recording
Documentation
Revision
Version
Variant
Derivative Work
Adaptation
Remix
Fork
Restoration
Migration
Emulation
Iteration
Tradition / Practice
Corpus / Collection
```

The ordinary word `work` mixes intellectual, artistic, legal, cataloguing, institutional, historical and practical identity regimes.

A universal ontology must therefore survive these regime differences rather than adopting one tradition's vocabulary as primitive.

---

# 2. Frozen substrate already contains unusually strong identity machinery

## MF3 Representation

MF3 already froze:

```text
Token continuity
≠ Type continuity
≠ Content continuity
≠ Provenance continuity
```

and:

```text
Physical Identity
≠ Information Identity
≠ Functional Identity
≠ Content Identity
≠ Provenance Identity
```

It also states that content can survive byte/material/code/format transformation under a declared typed equivalence relation.

## MF4 Composition

MF4 already separates:

```text
CompositionSpecification / Type
≠ CompositionToken / Realization
≠ ActiveCompositionEpisode
≠ CompositionIntegrity
```

A score can exist unperformed; a token can remain historically/type-continuous while degraded; identity thresholds are history/profile dependent rather than universally scalar.

## MF7 Identity / Persistence

MF7 already provides:

```text
ContinuationStanding(B_i,B_j | IdentityCriterion, StandingRoute, Scope)
```

and freezes:

```text
StateSimilarity ≠ TokenIdentity
RadicalStateChange ≠ IdentityTermination
StrictIdentity ≠ BroaderContinuation
Continuation may branch/merge
Persistence = identity-preserving continuation under branch/fusion/termination rules
```

This substrate was explicitly tested against `fork()` / `exec()` and branching lineages.

Therefore B-E must find more than multiple copies, versions, branches or changing state.

---

# 3. Bibliographic models are useful evidence, not universal ontology

Bibliographic traditions strongly confirm that one physical item is not enough to model creative identity.

Classical FRBR/RDA-style modelling distinguishes approximately:

```text
Work
→ Expression
→ Manifestation
→ Item
```

while Library of Congress BIBFRAME 2.0 deliberately uses:

```text
Work
→ Instance
→ Item
```

and its training material explains that BIBFRAME Work roughly combines the RDA Work and Expression levels, while Instance corresponds roughly to Manifestation.

This disagreement is productive evidence.

It shows:

```text
Work/Expression boundary is modelling-purpose relative
```

rather than proof of one mandatory natural four-level hierarchy.

### B-E result 1

Bibliographic `Work`, `Expression`, `Manifestation`, `Item` are strong operational abstractions but do not by themselves establish four Media primitives.

They can be reconstructed as typed identity/realization layers.

---

# 4. Artifact ≠ Work

A physical or digital artifact can exist without being one complete work.

Examples:

```text
anthology containing many works
album containing multiple songs/recordings
server containing many net artworks
manuscript containing several texts
archive box containing unrelated records
```

Conversely, one work can span multiple artifacts.

Thus:

```text
ArtifactBoundary ≠ WorkBoundary
```

MF4 already allows one token/composition to support several layered organization profiles and multiple valid decompositions under different scopes.

No Work primitive is needed to explain boundary nonidentity.

---

# 5. One artifact can participate in multiple work standings

The same carrier/token can simultaneously instantiate:

```text
one anthology work
several contained literary works
paratext/editorial work
illustration works
translation/adaptation relations
```

A recording medium can likewise contain several recordings and an album-level collective composition.

Therefore:

```text
PhysicalToken → one Work
```

is false.

The appropriate model is many typed standing relations over one carrier/composition.

This is already supported by MF3 role multiplicity + MF4 layered composition.

---

# 6. One work can have many tokens without token identity

Copies of a book, score, image or file can be distinct physical/digital tokens while being treated as realizations/copies of one work under a practice.

MF3 already directly proves:

```text
same content ≠ same physical token
```

Thus multiple realization is not evidence for a new primitive.

A `WorkIdentityProfile` may group or relate tokens under a declared practice/history/equivalence criterion without making them numerically identical objects.

---

# 7. Musical work ≠ score ≠ performance ≠ sound recording

Music provides a powerful hard case.

U.S. Copyright Office practice distinguishes the underlying musical composition from a particular sound recording.

The same musical composition may be embodied as:

```text
notated sheet music
or
phonorecord / audio embodiment
```

while a particular recording of a performance is treated as a separate sound-recording work.

Thus even one mature legal/practical regime requires:

```text
MusicalWork
≠ NotatedCopy
≠ PerformanceOccurrence
≠ SoundRecordingWork
```

This does not establish copyright categories as metaphysical truth.

It establishes the falsifier:

> physical embodiment, performed occurrence and work-level identity cannot be collapsed.

Ordivon already handles the separation:

```text
score/specification representation → MF3 + MF4 specification
performance occurrence             → MF6/MF7 + MF8 where agential
recorded signal/artifact           → MF1/MF3/MF4
work continuity                    → MF7 identity criterion + practice/provenance
```

---

# 8. Score ≠ work universally

A musical work may be transmitted orally, improvised from tradition, realized through recordings or created without canonical notation.

A score can also specify a work that is never performed.

Therefore:

```text
Work does not require Score
Score does not require realized Performance
```

MF4 already uses the unperformed score as a canonical falsifier for:

```text
Specification ≠ Realization
```

No new Work ontology is forced.

---

# 9. Performance ≠ mere token of a fixed work universally

Some performances realize a strongly pre-existing work.

Others involve:

```text
improvisation
open-form composition
participant interaction
site-specific adaptation
live coding
ritual variation
```

where the performance may partly create the relevant organization during the episode.

MF4 already permits spontaneous organization with no pre-existing type/specification.

Therefore:

```text
EveryPerformance requires PreexistingWorkType
```

is false.

A performance can be:

```text
realization of a standing type
+ novel derivative realization
+ unique work/event
+ manifestation of a broader practice/tradition
```

under different grounded regimes.

`Performance` itself does not decide which identity relation applies.

---

# 10. Oral/living traditions destroy fixed-token essentialism

UNESCO's intangible-cultural-heritage framework explicitly treats oral traditions, performing arts and social practices as living heritage that is transmitted while being continuously recreated.

UNESCO notes that manifestations of the same practice/expression need not be identical and that oral retellings mix reproduction, improvisation and creation.

This gives a strong counterexample to:

```text
Persistent WorkIdentity requires fixed canonical token
Persistent WorkIdentity requires byte/content equality
Persistent cultural identity requires frozen manifestation
```

But this pressure does not create a Media Work primitive.

The persistence is better represented as:

```text
practice/tradition bearer + community standing     → Human/social/Institution
manifestation episodes                             → MF6/MF7/MF8
organization/content profiles                      → MF3/MF4
lineage/transmission                               → MF7
identity/equivalence criteria                      → practice-relative MF7 profile
```

Living heritage is therefore also an ownership warning: not every repeated cultural expression is fundamentally a Media `Work`.

---

# 11. Edition ≠ copy

An edition is not merely another physical copy.

Many copies can instantiate one edition.

An edition may differ from another through:

```text
editorial revision
layout/format
paratext
translation
critical apparatus
corrected errors
added/removed material
publisher/date/production context
```

The identity relation is profile-dependent.

Thus:

```text
EditionIdentity ≠ ItemIdentity
```

Bibliographic models already treat edition/instance-level characteristics separately from item/copy identity.

Ordivon maps this to:

```text
edition specification/content profile → MF3/MF4
instance/copy token                   → MF4
edition lineage/version               → MF7
publication/institution profile       → B-D / Institution
```

---

# 12. Revision ≠ automatically same work or new work

There is no universal amount of change at which `revision` becomes `new work`.

Examples:

```text
typo correction
new chapter
abridgment
translation
critical edition
remaster
colorization
new software build
substantial rewrite
```

Different legal, cataloguing, artistic and social practices draw different boundaries.

Thus:

```text
DifferenceMagnitude → WorkIdentity
```

cannot be one universal scalar rule.

MF4 already states there is no universal damage/identity threshold; MF7 requires an explicit identity criterion and standing route.

### B-E result 2

`Same work after revision` is a typed continuity claim, not a primitive fact derivable from percentage similarity alone.

---

# 13. Derivative work / adaptation / remix ≠ simple versioning

Copyright practice provides a useful boundary case: translations, abridgments, musical arrangements and other recast/transformed/adapted forms may be derivative works, with protection attaching to new authorship rather than erasing the pre-existing material.

This produces overlapping identity:

```text
pre-existing work lineage continues
new derivative work standing can also arise
```

Therefore:

```text
Derivative ≠ pure same-work version
Derivative ≠ complete unrelated new object
```

MF7 branching lineage + MF3/MF4 content/organization profiles handle this naturally.

No new `DerivativeIdentity` atom is needed.

---

# 14. Forks expose lineage without strict identity

Software/media projects make branching explicit:

```text
common ancestor
→ branch A
→ branch B
```

The branches can share most bytes/content/history initially while already being distinct lineage tokens.

Later they may diverge strongly, merge, cherry-pick or be rebased/transformed.

Git's own history model visibly represents divergent branch histories rather than treating similarity as numerical identity.

MF7 was already built for exactly this shape:

```text
StrictIdentity ≠ Continuation
Continuation may branch/merge
```

Thus `fork` is evidence for lineage graphs, not a new Media foundation.

---

# 15. Copy ≠ fork ≠ edition ≠ derivative

These relations differ because their declared identity criteria differ.

```text
Copy        → new token under preserved type/content relation
Edition     → grouped manifestation/version profile
Fork        → branching lineage with autonomous continuation
Derivative  → lineage relation + new transformed authorship/content standing
```

No single generic `VersionOf` edge is sufficient for serious modelling.

But this supports **typed relations**, not a new primitive substrate.

---

# 16. Restoration can change material while preserving work standing

Traditional conservation already distinguishes material intervention from complete identity destruction.

Variable/time-based media make this explicit.

Guggenheim preservation practice may use:

```text
migration
emulation
virtualization
replica computers
replacement components
```

while evaluating whether intended behavior/aesthetics/function and the artwork's integrity remain acceptably preserved.

Therefore:

```text
MaterialIdentity ≠ WorkIdentity
```

and:

```text
ChangedComponent ≠ automatically NewWork
```

This is exactly MF3 typed equivalence + MF4 integrity + MF7 continuity.

---

# 17. Migration can preserve some profiles and destroy others

A film migrated to video may preserve image sequence while changing:

```text
projection mechanism
brightness
texture
noise
frame/scan characteristics
installation behavior
```

Guggenheim case studies explicitly evaluate which medium changes are acceptable and may retain one medium as preferred while allowing another only under exceptional circumstances.

Thus:

```text
MigrationSuccess
```

must always name the preserved profile.

This mirrors MF3:

```text
representation preservation under transformation is typed
```

and MF4:

```text
robustness/invariance names a preserved profile, not total identity
```

No new work atom emerges.

---

# 18. Emulation falsifies hardware identity

An obsolete interactive/digital work can sometimes be re-presented through emulation on entirely different hardware.

Guggenheim's Variable Media work explicitly compares original and emulated versions to test whether the work's integrity survives.

Therefore:

```text
HardwareIdentity ≠ WorkIdentity universally
```

The relevant relation is:

```text
preserved behavior/appearance/interaction/content profile
+ authorized/practice-grounded identity criterion
+ provenance of transformation
```

already expressible in MF3/MF4/MF7.

---

# 19. Time-based media identity is iteration-relative

Guggenheim's computer-based-art conservation explicitly documents `Identity Reports` and `Iteration Reports`, and notes that each installation can be considered a different representation of an artwork.

This is a strong real-world analogue of Ordivon's distinction:

```text
Standing Work/Profile
≠ Iteration Token
≠ Active Installation Episode
```

The museum also tracks which changes are acceptable without compromising integrity.

Again:

```text
Work identity = practice-grounded continuation under declared significant properties
```

rather than material sameness.

---

# 20. Rhizome net-art variants falsify one canonical file assumption

Rhizome ArtBase explicitly treats net art as dependent on alignments among:

```text
hardware
software environment
network protocols
user interaction
```

and records multiple `variants` produced by creator changes, preservation intervention or structural software/network change.

Historically, ArtBase also distinguished cloned objects stored by Rhizome from linked works remaining under artist stewardship.

Therefore:

```text
Work = one canonical hosted file
```

is false for a major class of digital media.

But the required machinery remains:

```text
component composition       → MF4
representation/content      → MF3
dependencies/state          → MF7 + Runtime/Network
variant lineage             → MF7
institutional stewardship   → Institution/Archive
```

---

# 21. Software source ≠ executable ≠ runtime episode ≠ artwork

For software-based art:

```text
source code
compiled executable
assets
configuration
dependencies
operating system
hardware
network services
runtime state
interaction history
```

can all contribute to realization.

No one component universally equals the work.

A bit-identical executable under a changed dependency/environment may behave differently.

Different code after migration may intentionally preserve the artwork's behavior.

Therefore:

```text
SourceIdentity ≠ BinaryIdentity ≠ RuntimeBehaviorIdentity ≠ WorkIdentity
```

This is a compositional/runtime identity problem, not evidence for a new Media primitive.

---

# 22. Generative work may have no canonical output token

Consider a generative artwork:

```text
program/rules = stable
seed/input/environment = variable
outputs = potentially unbounded
```

No single output need be `the work`.

Possible identity standing can attach to:

```text
generative system / rule composition
admissible behavior/output family
interaction regime
artist-authorized parameter envelope
installation practice
lineage/provenance
```

Outputs become realization tokens/episodes.

This maps cleanly to:

```text
MF4 CompositionSpecification / Token / ActiveEpisode
MF7 Dynamics + identity/persistence
MF3 represented rules/content where applicable
Runtime execution
MF8 creator/participant agency where applicable
```

Thus generativity does not force a `Work` primitive.

---

# 23. Same generator ≠ same work universally

Two artists could intentionally use identical source code but establish two separately authored/project-grounded works through different histories, titles, contexts or institutional acts.

Conversely, one artist can migrate source code extensively while preserving one work's continuity.

Therefore source-code equality is neither sufficient nor necessary for work identity.

The difference is already representable through:

```text
provenance/history/authority   → MF3/MF7/Institution
identity criterion             → MF7
composition/content profiles   → MF3/MF4
```

No unexplained residual remains.

---

# 24. Adaptive / self-modifying / agentic works

Agent-era systems can alter:

```text
model parameters
prompts
memory
policy
code
assets
tool graph
audience-specific output
```

over time.

A work might therefore continue while its implementation changes continuously.

But the ontological problem is still typed persistence:

```text
What bearer is claimed to continue?
Which transformations are identity-preserving?
Which branches are successors versus copies/new works?
Which behavior/content/provenance constraints matter?
Who/what has authority to revise the criterion?
```

MF7 already requires exactly these questions.

Agent-era change increases the frequency and automation of identity transitions; it does not create a new primitive by itself.

---

# 25. A work may intentionally have multiple simultaneous realizations

Networked, installation and performance works can have several active realizations at once.

This falsifies:

```text
Work = one persistent bearer token
```

Instead:

```text
one work-level standing
→ several realization/iteration tokens
```

is a typed one-to-many relation under a practice.

MF4 composition type/token and MF7 lineage/equivalence already support this.

---

# 26. A realization may instantiate several work relations simultaneously

A performance may:

```text
realize composition A
quote work B
adapt work C
create recording-work D
participate in ritual/tradition E
```

Therefore:

```text
RealizationToken → exactly one Work
```

is false.

Work relation is many-to-many and typed.

This is another reason not to reify `Work` as the object's singular essence.

---

# 27. Broken work tokens / incomplete realizations

A damaged book, corrupted digital installation or incomplete performance can remain historically attributable to a work even while failing full integrity.

MF4 already directly separates:

```text
CompositionStanding
CompositionRealization
CompositionIntegrity
```

and rejects immediate identity destruction on damage.

Therefore:

```text
PerfectInstantiation ≠ WorkMembership requirement
```

Work identity can be retained with an integrity profile.

---

# 28. Restoration can overshoot and destroy identity

The opposite problem matters.

A restoration/migration may alter so many identity-defining properties that the result should no longer count as an authorized/continuous realization.

There is no universal percentage threshold.

The decision depends on:

```text
identity criterion
significant properties
artist/practice/institution standing
transformation provenance
scope
```

This is exactly the typed identity framework rather than a missing primitive.

---

# 29. Authenticity ≠ work identity

An unauthorized counterfeit copy can be recognizably a copy/representation of a work while failing authenticity/provenance.

An authorized later realization may materially differ yet remain authentic under the relevant practice.

Thus:

```text
WorkRelation
≠ Authenticity
≠ Authorization
```

MF3 already freezes semantic/content and provenance/authenticity identity as separate.

Institution/Law owns many authority consequences.

---

# 30. Legal work identity ≠ cataloguing work identity ≠ artistic work identity

Copyright, library cataloguing, musicology, museum conservation and artist practice may classify the same transformation differently.

For example:

```text
translation
arrangement
remix
restoration
new edition
software port
```

may be one work, new expression, derivative work, new edition, new iteration or new legal work depending the governing regime/question.

Therefore:

```text
WorkIdentity is always scope/criterion/standing-route typed.
```

There is no foundation-safe universal answer to `same work?` without specifying the identity question.

---

# 31. Work as equivalence class is still too simple

An equivalence-class model suggests symmetric/transitive sameness.

But work ecosystems often require asymmetric/branching relations:

```text
translation-of
derivative-of
forked-from
restoration-of
performance-of
recording-of
edition-of
inspired-by
successor-to
```

Thus serious modelling needs a **typed lineage graph**, not only an equivalence class.

MF7 already distinguishes strict identity from successor/continuation and allows branching/merging.

---

# 32. Proposed derived WorkIdentityProfile

No new Foundation is introduced.

A useful profile is:

```text
WorkIdentityProfile(W | Regime, Σ) = <
  Claimed Work Bearer / Abstract Standing,
  Standing Route,
  Constitutive / Significant Organization Profile,
  Content Profile?,
  Representation Profile?,
  Creator / Author / Community Provenance?,
  Identity-Preserving Transformation Rules,
  Realization / Expression Relations,
  Manifestation / Edition Relations,
  Token / Item Relations,
  Performance / Execution Relations,
  Derivation / Fork / Successor Relations,
  Integrity Criteria,
  Authenticity / Authorization Profile,
  Institutional / Legal Status?,
  Temporal Scope,
  Provenance,
  Uncertainty
>
```

Not every work uses every field.

The critical rule is:

```text
WorkIdentityProfile ≠ universal Work substance
```

It records the grounded criterion under which a practice treats changing realizations as one work, successors, derivatives or distinct works.

---

# 33. Minimal reconstruction of `WorkStanding`

If the word `WorkStanding` is retained operationally, the weakest defensible reconstruction is:

> A scope-relative, practice/history-grounded identity standing over an organized expressive/operative creation or family of realizations, under declared criteria specifying which content/organization/provenance/behavior transformations preserve identity and which create successor/derivative/new-work relations.

This decomposes into:

```text
scope/practice grounding         → MF3/MF4 + Institution/Human
organized creation profile       → MF4
content/representation profile   → MF3 when present
continuity/branching             → MF7
identity criteria                → MF7
realization occurrences          → MF6/MF7
agency/authorship                → MF8 when relevant
execution                        → Runtime/Harness when computational
```

No irreducible constituent remains.

---

# 34. Strongest irreducibility test

Try to construct:

```text
Case A and Case B
```

with identical:

```text
physical/material profile
information/content profile
composition/organization profile
functional/behavioral profile
provenance/history/lineage
creator/authority standing
institutional/legal standing
identity criteria
scope/practice
```

while asserting:

```text
WorkIdentity(A) ≠ WorkIdentity(B)
```

At current frontier this can only be done by introducing an additional distinction such as:

```text
different originating act
new title/designation
new creator/project intention
new institutional accession
new practice-level identity declaration
new lineage relation
```

But each of those is precisely a difference in provenance, authority, history, agency or standing route already representable by the substrate.

Therefore no independent Work atom survives.

---

# 35. Cheapest falsifier matrix

| Proposed universal claim | Cheapest counterexample | Result |
| --- | --- | --- |
| Work = physical artifact | many copies / one work | falsified |
| One artifact = one work | anthology / album | falsified |
| Work requires fixed canonical token | oral/living tradition | falsified |
| Work requires score/specification | oral/improvised work | falsified |
| Performance requires pre-existing fixed work | improvisation / live coding | falsified |
| Same bytes imply same work identity | separately grounded/provenanced projects | falsified |
| Same content implies same token | ordinary copying | falsified |
| Same source code implies same artwork | separately grounded works / contexts | falsified |
| Same work requires same material | migration/emulation | falsified |
| Same work requires same behavior exactly | authorized variable installations / permissible variation | falsified |
| Same behavior implies same work | independently created equivalent systems | falsified |
| Revision amount determines identity | edition/adaptation thresholds differ by regime | falsified |
| Version relation is always linear | forks/branches/merges | falsified |
| Derivative is merely same work | legal/artistic derivative work cases | falsified |
| Derivative is completely unrelated | preserved lineage/pre-existing material | falsified |
| Authenticity = work membership | forgery vs authorized transformed realization | falsified |
| Work identity is one equivalence class | asymmetric derivation/performance/fork relations | insufficient |
| Generative work requires canonical output | unbounded output family | falsified |
| Human author is necessary | autonomous/systemic generative cases as pressure cases | not universal |

What survives is typed identity/lineage standing under a practice—not a new Media atom.

---

# 36. Irreducibility test

Question:

> Does Artifact / Work / Edition / Performance / Generative identity require a primitive absent from MF0–MF9 and adjacent owners?

Round B-E answer:

**No concrete irreducible survivor.**

Reduction:

```text
Artifact/carrier token             → MF0/MF1/MF4
Representational identity          → MF3
Composition type/token/iteration   → MF4
Performance occurrence             → MF6/MF7 (+ MF8 if agential)
Persistence/continuation            → MF7
Edition/version                     → MF3/MF4/MF7 + Institution
Copy/item identity                  → MF4/MF7
Derivation/fork/lineage             → MF7 + MF3/MF4 profiles
Authenticity/provenance             → MF3/MF7 + Institution
Restoration/migration/emulation     → typed transformation/equivalence via MF3/MF4/MF7
Software realization                → Runtime + MF4/MF7
Generative/adaptive realization     → MF4 specification/dynamics + MF7 + Runtime/Harness
Authorship/creation                  → MF8 + Human/Institution
Living tradition/community identity → Human/social/Institution + MF7 lineage
```

Therefore the candidate fails the foundation-level irreducibility test.

---

# 37. Ownership test

Media should retain operational profiles for:

```text
WorkIdentityProfile
EditionProfile
RealizationProfile
VariantProfile
DerivationProfile
PreservationIdentityProfile
```

But the generic substrate is distributed:

```text
MF3              content/type/provenance/representation identity
MF4              artifact/work organization and type/token/active distinctions
MF7              persistence, lineage, branching, identity criteria
MF8              creation/revision actions when agential
Human            cultural practice, tradition, authorship interpretation
Institution/Law  official work/edition/rights/authenticity status
Archive          stewardship/preservation obligations
Runtime/Harness  computational realization, migration, adaptive execution
Network          dependency realization for network works
```

A broad independent Media Work foundation would duplicate this machinery.

---

# 38. Cross-regime test

The practical need for work/realization identity survives across:

```text
oral tradition
manuscript
print
music notation/performance
recording
cinema
broadcast
software/net art
interactive installation
immersive work
generative systems
agentic/adaptive works
```

But no universal material/type/token structure survives.

The robust cross-regime core is approximately:

> **grounded identity/lineage criteria over changing organized realizations under a declared practice/scope.**

That is MF4 + MF7 standing, optionally enriched by MF3 and adjacent owners.

Cross-regime persistence therefore supports a major operational concept, not a new foundation.

---

# 39. Agent-era perturbation

Agent-era media intensifies:

```text
continuous generation
personalized realization
self-modification
runtime learning
model/version replacement
recursive derivation
forking by autonomous agents
multi-agent co-authorship
works with no fixed final artifact
```

But every pressure case still asks generic identity questions:

```text
what continues?
which transformations preserve identity?
what branches?
what is merely a new realization?
what creates a derivative successor?
who/what grounds or revises the criterion?
what provenance survives?
```

Those are precisely MF7/MF4 questions.

No Agent-era `GenerativeWork` primitive is admitted.

---

# 40. Foundation consequence test

Would a numbered Artifact/Work foundation provide classifications unavailable under the frozen substrate?

Current answer: **no**.

It would risk collapsing:

```text
artifact identity
representational identity
composition identity
work identity
edition identity
copy identity
performance identity
provenance/authenticity
lineage
legal/institutional status
```

into one noun.

Typed profiles and relations are more explanatory and more falsifiable.

---

# 41. Classification update

Canonical Round-B-E classification:

```text
Artifact / Work / Edition / Performance / Generative Identity
= REDUCIBLE / CROSS-CUTTING
= NOT genuinely-new-foundation at current frontier
```

More specifically:

```text
Artifact identity            → already-covered / MF4+MF7
Token/type/content identity  → already-covered / MF3+MF4
Work identity                → derived practice-grounded identity profile
Edition/version              → derived MF3+MF4+MF7 profile
Performance realization      → cross-cutting MF4+MF6+MF7+MF8
Copy/item                     → derived token/lineage profile
Derivative/remix/fork        → derived lineage relation
Restoration/migration        → typed equivalence/preservation profile
Generative work              → derived MF4+MF7+Runtime profile
Living tradition             → owned-elsewhere / cross-cutting Human+Institution+MF7
```

No MF10 is admitted.

---

# 42. What survives B-E

Reducing Work identity does **not** close several neighboring questions.

## S1 — Selection / Gatekeeping / Visibility Allocation

Unaffected and still strongly unresolved.

## S2 — Meaning / Pragmatics / Context Integrity

Work identity can be preserved while contextual meaning/pragmatic force changes; conversely recontextualization may create a distinct work-standing in some regimes. The boundary still needs direct attack.

## S3 — Inscription / Fixation / Materialization

B-E strongly weakens fixation as a universal requirement, but the event/status transition by which an ephemeral process becomes a durable manipulable token still deserves its own reducibility test.

## S4 — Authorship / Creation / Attribution

Work identity does not solve authorship, especially under collective, anonymous, traditional, generative and agentic production. Likely MF8/Human/Institution-owned but not directly closed here.

## S5 — Archive / Preservation responsibility

B-E solves much of identity mechanics but not designated-community, stewardship, access and preservation-obligation ontology. Those remain institutional/archive specializations.

## S6 — Audience / Public Formation

Still an adjacent-owner question, unaffected by Work reduction.

---

# 43. FoundationReopen audit

No MF0–MF9 FoundationReopenCondition is triggered.

B-E instead strongly validates existing frozen claims:

```text
MF3 token/type/content/provenance identities are distinct
MF3 transformation preservation is typed
MF4 specification/token/active/integrity distinctions are necessary
MF4 robustness ≠ total identity
MF7 state similarity ≠ bearer identity
MF7 strict identity ≠ continuation
MF7 branching/fusion lineage is necessary
```

No tested work/performance/generative case requires changing those definitions.

Thus:

```text
MF0–MF9 = FROZEN
```

---

# 44. Research anchors used

Representative authoritative/comparison anchors:

- IFLA Library Reference Model and FRBR tradition — bibliographic Work/Expression/Manifestation/Item abstractions as a strong operational identity model.
- Library of Congress BIBFRAME 2.0 — Work/Instance/Item model; BIBFRAME intentionally chooses a different abstraction boundary from RDA/FRBR, demonstrating model-purpose-sensitive granularity.
- U.S. Copyright Office musical-work/sound-recording guidance — underlying musical composition and a recording of a particular performance are distinct works; musical composition may be embodied in notation or phonorecord.
- U.S. Copyright Office derivative-work guidance — translations, arrangements, abridgments and other transformed works can retain relation to pre-existing material while adding new protected authorship.
- UNESCO Intangible Cultural Heritage Convention/guidance — oral/performance traditions are continually recreated and transmitted; manifestations need not be identical and safeguarding should not freeze living practices.
- Guggenheim Variable Media / Conserving Computer-Based Art — artworks may survive migration, emulation and changing installations through documented identity/significant-property criteria; each installation can be a distinct representation/iteration.
- MoMA media/performance conservation — time-based/performance works may be replicated, migrated or emulated to continue existence, with documentation essential to identity/integrity decisions.
- Rhizome ArtBase — net art may have multiple variants across software/hardware/network change and preservation interventions rather than one canonical stored object.
- Git branching model — explicit branch divergence provides an engineering hard case for lineage ≠ strict identity.
- MF3/MF4/MF7 frozen Ordivon foundations — typed representation identity, composition type/token/active/integrity, and branch-aware continuation/persistence.

These sources are falsification/comparison anchors rather than external authority over Ordivon's ontology.

---

# 45. Round B-E closeout

```text
Round B-E target       = Artifact / Work / Edition / Performance / Generative Identity
Result                 = REDUCIBLE / CROSS-CUTTING
New Media primitive    = NONE
MF10                    = UNKNOWN / NOT ADMITTED
FoundationReopen       = NONE
```

Deep result:

> **A `work` is not a special substance sitting above artifacts. It is best reconstructed as a scope- and practice-grounded identity/lineage standing over organized realizations, under declared criteria specifying which transformations preserve one work, which instantiate it, and which create variants, successors or derivatives. Bibliographic Works, musical compositions, performances, editions, restored time-based media, software variants, oral traditions and generative systems use different identity granularity, but all tested cases remain expressible through MF3 typed representation identity + MF4 specification/token/active/integrity organization + MF7 branch-aware continuation, with Human/Institution/Runtime specializations where required.**

The whole-domain search remains open. No ordering of surviving residuals is canonical and none is admitted as MF10.
