# Ordivon Media Deep Foundations — Round B-D: Publicness / Addressability / Publication Reducibility

**Date:** 2026-08-18  
**Continuity Task:** `task:media-foundations-mf2h-20260817`  
**Parent:** `media-whole-domain-round-b-c-convention-protocol-interoperability-reducibility-20260818.md`  
**Status:** **destructive reducibility / ownership audit only; no MF10 admitted**

---

# 0. Question

Round B-A showed:

```text
public communication ≠ known current receiver
```

Round B-B showed:

```text
public availability ≠ encounter / exposure
```

Round B-C showed:

```text
public addressing ≠ delivery
```

The residual therefore deserves direct attack.

Round B-D asks:

> **Do Publicness, Addressability, Visibility and Publication require a Media-specific irreducible standing beyond MF0–MF9 plus Institution/Law, Network and Human/social ownership?**

The candidate must first be decomposed. We must not treat the everyday word `public` as one ontology.

---

# 1. Term separation

At minimum distinguish:

```text
Private / Restricted Standing
Audience Scope
Recipient Eligibility
Addressability
Reachability
Availability
Access Permission
Discoverability
Indexability
Visibility / Presentation Opportunity
Exposure / Encounter
Publication Standing
Public Display / Performance
Broadcast / One-to-many Transmission
Public Record / Official Disclosure
Public Domain / Rights Status
Public Sphere / Public Formation
Common Knowledge / Public Knowledge
```

These are not synonyms.

The first candidate failure is therefore semantic compression:

```text
public = open = published = visible = addressed = broadcast = widely seen
```

is false across multiple regimes.

---

# 2. Internal frozen substrate already has most lower machinery

MF0 provides MediaRole, Coupling, Recruitment, Agent/System, Context and Time.

MF1 provides signal/channel/observation structure.

MF2 provides perception/attention rather than public status.

MF3 already allows:

```text
public/conventional/institutional grounding
standing external representation without current consumer use
schema/protocol/context/namespace constituting public token content
standing vs active-use separation
```

MF4 provides composition, role, collection and boundary standing.

MF5/MF6 provide spatial and temporal scope.

MF7 provides status/configuration standing and state transition.

MF8 provides publication/disclosure/addressing acts when genuinely agential.

MF9 covers experience when relevant, never publicness itself.

Generic institution/law work owns:

```text
status functions
rights
permission
jurisdiction
authority
legal publication
public records
licensing
```

Network owns generic reachability/delivery.

Therefore B-D must find something more than one of these profiles.

---

# 3. First destructive result — `public` is not one audience-size predicate

Large audience does not by itself imply public standing.

Examples:

```text
large invite-only organization channel
large private conference under access restriction
restricted mailing list with many members
```

may remain bounded/private under the governing practice.

Conversely, a small event in a genuinely open public venue can have public standing even if few people actually attend.

Thus:

```text
AudienceCardinality ≠ Publicness
```

Publicness depends on typed membership/access/status relations, not merely count.

This points toward MF4 boundary/role + institutional/access standing rather than a new Media atom.

---

# 4. Publicness is not actual audience occurrence

A public object can remain entirely unencountered.

Examples:

```text
public web page with zero visits
public notice posted where nobody passes
published book never purchased/read
public archive object never retrieved
```

Round B-B already reduced actual exposure/encounter.

Therefore:

```text
PublicStanding ≠ AudienceOccurrence
PublicStanding ≠ Exposure
```

Publicness, if retained, must be a standing/capacity/status relation rather than an encounter event.

---

# 5. Same bytes, different access-status falsifier

Construct:

## World A

```text
object bytes = X
representation standing = R
network host = H
URL = U
access policy = owner-only
```

## World B

Everything is identical except:

```text
access policy = unauthenticated/all eligible requesters
```

The object becomes publicly accessible under the local system's policy without changing bytes, content or representational identity.

The difference is expressible as:

```text
MF7 access/status configuration
+ represented policy/rule under MF3
+ audience/eligibility boundary under MF4
+ Institution/authority standing where policy is normative
+ Network route where access is realized
```

No new Media primitive is necessary.

---

# 6. Public access ≠ discoverability

Cheap web falsifier:

```text
public unauthenticated URL
but no incoming links
no index registration
no search-engine discovery
no feed listing
no known identifier among target consumers
```

The resource is publicly accessible in one sense but practically undiscoverable.

Therefore:

```text
PublicAccess ≠ Discoverability
```

Discoverability requires additional relations such as:

```text
index membership
reference/link structure
searchability
identifier knowledge
catalog placement
ranking/selection
consumer search capability
```

These are composed from MF3/MF4/MF7 plus Network/Harness/Human and the still-open Selection/Visibility-Allocation residual.

---

# 7. Discoverability ≠ accessibility

The reverse dissociation is equally easy.

A catalog, search result, citation or metadata record can reveal that an object exists while the object itself remains:

```text
paywalled
permission-restricted
offline
physically inaccessible
removed from current storage
available only to another institution
```

Thus:

```text
Discoverable(Object) ≠ Accessible(Object)
```

This prevents `Visibility` from silently collapsing into Publicness.

---

# 8. Addressability ≠ publicness

A private direct message is maximally addressable to one recipient while remaining non-public.

A restricted group post can be addressed to a named collection while remaining non-public.

Therefore:

```text
Addressability ≠ Publicness
```

Addressability is better reconstructed as:

```text
AddressabilityProfile(M,R | Σ)
= a grounded ability to designate R (entity/role/group/class/collection)
  as a target/relevant audience for M under a representation/protocol/practice
  with enough resolution to support subsequent routing, access or interpretation operations.
```

Components:

```text
recipient identity/type representation → MF3
recipient/group composition            → MF4
address/status state                   → MF7
selection/addressing act               → MF8 where agential
resolution/routing realization         → Network
institutional eligibility              → Institution where applicable
```

Thus Addressability is a derived relation.

---

# 9. Publicness ≠ addressability

ActivityPub provides an unusually clean hard case.

The protocol defines a special `Public` collection identifier.

Activities addressed to it are to be accessible to all users without authentication, but implementations must **not deliver to the Public collection itself**, because that collection cannot receive actual activities.

Therefore one real protocol supports:

```text
PublicAddressingStanding = yes
PublicAccessibilityStanding = yes
DeliveryToPublicCollection = no
```

This decisively falsifies:

```text
Public = a recipient endpoint
Publicness = broadcast delivery
Addressing = delivery
```

The relation decomposes into MF3 public collection representation + MF4 audience/collection role + protocol/institution rules + Network delivery to concrete actor endpoints.

---

# 10. Audience targeting ≠ delivery guarantee

ActivityStreams/ActivityPub also distinguishes intent/audience metadata from realized delivery.

Fields such as:

```text
to
cc
bto
bcc
audience
```

represent audience/targeting relations, while ActivityPub separately defines recipient resolution and delivery to actor inboxes.

The ActivityStreams audience concept is itself an intended/relevant population relation, not proof that every audience member was reached.

Thus:

```text
AudienceRepresentation
≠ RecipientResolution
≠ Delivery
≠ Exposure
```

Again the residual is stage structure, not a new primitive.

---

# 11. Public availability ≠ publication — legal hard case

United States copyright law supplies a powerful institutional falsifier.

Under 17 U.S.C. §101, `publication` has a technical distribution-based meaning concerning copies/phonorecords.

The same statute explicitly states that a **public performance or public display does not by itself constitute publication**.

Therefore a work can have:

```text
PublicPerformance/DisplayStanding = yes
PublicationStanding = no
```

within one mature legal regime.

This proves:

```text
Publicness ≠ Publication
```

and also shows that `Publication` is at least partly an institutionally constituted status transition rather than a universal natural Media event.

---

# 12. Publication ≠ actual broad distribution

The same legal definition also treats an **offer** to distribute copies/phonorecords to a group for further distribution/public performance/public display as publication.

Therefore actual mass encounter or completed downstream distribution is not required under that regime.

So:

```text
PublicationStanding ≠ MassExposure
PublicationStanding ≠ CompletedDeliveryToPublic
```

Publication is a status/action classification under declared institutional rules.

---

# 13. Publication is regime-relative

`Publication` has different practical meanings in:

```text
copyright law
academic publishing
journalism
book trade
web platforms
archives
software/package releases
broadcasting
social posting
```

Sometimes it means institutional acceptance/release.
Sometimes it means distribution of copies.
Sometimes it means making an object externally available.
Sometimes it means a specific legal event.

Therefore no unqualified universal:

```text
Publication = X
```

is defensible at whole-Media foundation level.

A better derived profile is scope-relative.

---

# 14. Derived PublicationProfile

```text
PublicationProfile(W | Regime, Σ) = <
  Work/Object Identity,
  Publisher/Actor Standing,
  Publication Act/Event?,
  Release/Distribution Route,
  Intended Audience Scope,
  Access/Availability Standing,
  Copy/Performance/Display Mode,
  Institutional/Legal Recognition,
  Effective Date/Time,
  Edition/Version,
  Rights/License Status,
  Provenance/Authority,
  Discoverability/Indexing?,
  Exposure Evidence?,
  Scope,
  Uncertainty
>
```

Fields after `?` are not universally constitutive.

This is a derived institutional/media profile rather than a new primitive.

---

# 15. Public performance without persistent artifact

Oral/live regimes are essential.

A public speech, live improvisation or ritual can occur before an open audience without creating a persistent artifact or distributing copies.

Therefore:

```text
Publicness does not require Fixation
Publicness does not require Artifact persistence
Publicness does not require Publication in copy-distribution sense
```

This preserves Round A's oral/live falsifier and prevents a print-centric ontology.

---

# 16. Publication without current publicness

A historically published work can later become practically unavailable:

```text
all copies lost
archive closed
website removed
service discontinued
access restricted by later policy
```

Its historical publication event remains true even when current public accessibility is false.

Therefore:

```text
HistoricalPublicationStanding
≠ CurrentPublicAccessibility
```

This decomposes naturally into MF6/MF7 time/status plus institutional provenance.

---

# 17. Public domain ≠ public access

Copyright terminology provides another anti-collapse case.

`Public domain` concerns copyright protection/permission status, not whether the work is actually reachable, discoverable or exposed.

A public-domain work may be physically lost or inaccessible.

A copyrighted work may be freely viewable on a public website while retaining copyright protection.

Thus:

```text
PublicDomainRightsStatus
≠ PublicAccessStatus
```

This is strong evidence that the word `public` spans independent legal and media relations.

Rights status belongs to Law/Institution, not Media ontology proper.

---

# 18. Broadcast ≠ publication

Broadcasting can instantiate:

```text
one-to-many transmission
public performance/display
large audience potential
```

without satisfying every regime's publication criterion.

From Ordivon's perspective:

```text
signal distribution     → MF1 + Network
public audience scope   → MF4 + Institution/social standing
exposure                → reduced in B-B
publication status      → regime-specific Institution/Law profile
```

Broadcast therefore does not unify the candidate.

---

# 19. Public place ≠ public audience relation universally

Architecture and spatial practice add another ambiguity.

A display may be physically located in a public place but:

```text
face away from pedestrian routes
be illegible
require credentials/device to decode
be visible only at particular times
be legally restricted despite physical exposure
```

Conversely, a transmission can address the public while recipients are spatially dispersed in private homes.

Thus:

```text
PublicPlaceStanding
≠ PublicAudienceStanding
```

MF5 handles place/position; Institution handles legal/public-space status; Media handles coupling/presentation profiles.

---

# 20. Public knowledge ≠ public availability

A fact can be widely or commonly known through many channels even if no one current artifact is publicly available.

Conversely, a public notice can be publicly available while almost nobody knows its content.

Therefore:

```text
PublicKnowledge
≠ PublicAvailability
```

Common/public knowledge belongs primarily to epistemic/social/Human foundations, not a Media primitive.

---

# 21. Public sphere ≠ public access

Pre-Agent social theory gives an important conceptual boundary.

Habermas's public sphere is not merely a set of publicly readable artifacts or a broadcast audience. It is a social/institutional communicative formation in which participants assemble/discourse around matters of general concern, generating public opinion and mediating between private life/civil society and political authority.

Later public-sphere work also permits multiple intersecting publics rather than one universal audience.

Therefore:

```text
PublicSphereStanding
≠ PublicAccessStanding
≠ BroadcastAudienceStanding
```

The ontology of publics/public spheres belongs primarily to Human/Social/Institution/Political foundations, with Media as constitutive infrastructure/mediation in many regimes.

This is an ownership result, not a denial of Media importance.

---

# 22. A public is not merely a stored recipient list

Human publics can emerge through:

```text
shared issue attention
recursive discourse
common references
institutional membership
collective identity
public controversy
repeated circulation
```

while machine protocol recipient sets may be explicit collections.

Thus a single `AudienceSet` representation cannot define all public formation.

However this does not create a Media primitive.

Instead:

```text
AudienceSetRepresentation → MF3/MF4
PublicFormation           → Human/social/institutional dynamics
Media circulation         → Media/Network specialization
```

Audience/Public Formation therefore remains an adjacent cross-cutting continent, not absorbed by B-D.

---

# 23. Private communication can become public without content change

Take exact same bytes:

```text
private letter X
```

Later:

```text
recipient posts X publicly
archive releases X
court record makes X public
leak exposes X widely
```

The bytes can remain identical while:

```text
access status
provenance
publisher/authority standing
audience scope
context/pragmatic standing
rights status
```

change.

MF3 already permits standing changes with unchanged bytes via changed grounding/practice history.

MF7 can represent the status transition.

Institution/Law owns authorization/legal consequences.

B-D therefore does not trigger MF3 reopen.

---

# 24. Authorized publication ≠ unauthorized disclosure

Two acts may produce identical public accessibility:

```text
A: author/publisher intentionally releases document
B: attacker/leaker exposes identical document
```

Yet provenance, authority, legality and pragmatic standing differ.

Therefore:

```text
CurrentPublicAvailability
≠ AuthorizedPublicationStanding
```

This is precisely why PublicationProfile needs provenance/authority fields rather than a primitive public flag.

---

# 25. Public access can be machine-only in practice

Agent-era case:

```text
machine-readable endpoint
no authentication required
stable public identifier
no human-oriented UI
consumed entirely by agents/indexers
```

Public accessibility does not require a human audience.

The relation decomposes into:

```text
public eligibility/access policy  → MF7 + Institution/Runtime
address/identifier representation → MF3
network reachability               → Network
machine consumption                → MF0 + Runtime/Harness
```

Thus:

```text
HumanAudience ≠ necessary for minimal access-publicness
```

---

# 26. Agent-targeted publicness can be capability-scoped

A supposedly public machine endpoint can still require:

```text
specific protocol
specific cryptographic mechanism
specific representation format
rate limits
resource budgets
```

It may be legally/openly available to anyone while only capable systems can use it.

Therefore:

```text
EligibilityToAccess
≠ CapabilityToUse
```

This mirrors B-B accessibility/exposure results and further weakens a monolithic Publicness primitive.

---

# 27. Addressability can be symbolic, extensional or intensional

Recipient targets can be represented as:

```text
one named individual
explicit list
role
followers collection
geographic region
subscription class
public special collection
query/predicate-defined audience
future unknown members of a class
```

Thus addressability does not require enumerating current recipients.

It only requires a grounded audience-target relation sufficient for the surrounding system/practice.

That is already representational/compositional standing.

---

# 28. Publicness can be nested and partial

Real systems contain nested scopes:

```text
private to one bearer
team-visible
organization-visible
subscriber-visible
community-visible
federation-visible
Internet-readable
physically public
legally public record
public-domain rights status
```

These dimensions are not one total order.

Example:

```text
legally public record
but operationally difficult to retrieve
```

or:

```text
Internet-readable copyrighted material
but not public-domain material
```

Therefore a scalar:

```text
Publicness = 0..1
```

is not foundation-safe without a declared dimension.

---

# 29. Visibility is also overloaded

At least distinguish:

```text
GeometricVisibility       → MF5 + MF1/MF2
InterfacePresentation     → MF0/MF5/MF6
AlgorithmicVisibility     → Selection/Ranking residual
InstitutionalVisibility   → disclosure/public-record status
SocialVisibility          → Human/social audience relation
SearchDiscoverability     → indexing/search profile
ObservedExposure          → reduced B-B profile
```

Thus `Visibility` is not a single remaining primitive after Publicness decomposition.

The algorithmic-selection component remains unresolved and should not be silently discarded.

---

# 30. Publicness state transition

A generic public-release event can be represented as:

```text
RestrictedStatus
    --[authorized/unauthorized disclosure or release action]-->
BroaderEligibility/AvailabilityStatus
```

The transition requires no new ontological category:

```text
state/status alternatives   → MF7
release/disclosure action    → MF8 when agential
object/content identity      → MF3/MF7
recipient-scope change       → MF4
rules/authority              → Institution/Law
transport realization        → Network
```

Publication is one regime-specific subtype of such status transitions.

---

# 31. Cheapest falsifier matrix

| Proposed universal claim | Cheapest counterexample | Result |
| --- | --- | --- |
| Public = large audience | large invite-only restricted group | falsified |
| Public = actual audience | public zero-visit page | falsified |
| Public access = discoverable | unlinked unauthenticated URL | falsified |
| Discoverable = accessible | catalog/search result for restricted object | falsified |
| Addressable = public | private direct message | falsified |
| Public = addressable recipient endpoint | ActivityPub Public collection cannot receive actual activities | falsified |
| Audience targeting = delivery | ActivityStreams target metadata vs ActivityPub delivery resolution | falsified |
| Public display/performance = publication | 17 U.S.C. §101 explicitly separates them | falsified |
| Publication = mass encounter | legal publication can occur without actual mass exposure | falsified |
| Publication = current public access | historically published but now inaccessible work | falsified |
| Publicness requires fixation | public oral/live performance | falsified |
| Public place = public audience | dispersed public transmission / inaccessible public-place display | falsified |
| Public knowledge = public availability | public notice nobody knows / widely known fact without current artifact | falsified |
| Public domain = public access | rights status independent of availability | falsified |
| Human audience required | public machine endpoint | falsified |
| Publicness = one scalar | independent access/legal/discoverability/audience dimensions | falsified |

No universal primitive survives this matrix.

---

# 32. Irreducibility test

Question:

> Do Publicness / Addressability / Publication require a primitive absent from MF0–MF9 and adjacent owners?

Round B-D answer:

**No concrete irreducible survivor.**

Reduction:

```text
Audience/recipient representation → MF3
Audience/group boundary            → MF4
Addressability                     → MF3+MF4 + Network resolution
Access/public eligibility          → MF7 status + Institution/policy
Reachability/delivery              → Network
Discoverability/indexing           → MF3/MF4/MF7 + Selection/Harness/Network
Presentation/exposure              → reduced B-B profile
Publication act                    → MF8 action where agential
Publication status                 → MF7 + Institution/Law + provenance
Public display/performance         → MF0/MF1/MF5/MF6 + Institution when legally typed
Rights/public-domain status        → Law/Institution
Public sphere/public formation     → Human/social/Institution
```

Therefore the candidate fails the foundation-level irreducibility test.

---

# 33. Ownership test

Media owns important specializations:

```text
AudienceScopeProfile
AddressabilityProfile
PublicAccessProfile
PublicationProfile
DiscoverabilityProfile
VisibilityProfile
```

but not a new generic publicness primitive.

Owner boundaries:

```text
MF3             object/audience/policy representation
MF4             audience/group/collection boundary
MF7             public/private/access/publication status and transitions
MF8             release/addressing/disclosure acts
Network         reachability/delivery
Human           human audience/public formation/public knowledge
Institution/Law rights, authority, public record, legal publication
Runtime/Harness machine access/context/discovery realization
```

A broad Media Publicness Foundation would duplicate these owners.

---

# 34. Cross-regime test

The public/private distinction appears across:

```text
oral assembly
manuscript circulation
print publication
public signage
telegraph/news service
telephone conference
broadcast
cinema/performance
networked web
social/federated platforms
mobile feeds
immersive shared spaces
agent-readable endpoints
```

But the invariant is not one new primitive.

What persists is roughly:

> **scope-relative standing about which bearers/classes may access, receive, discover, participate in or be relevant to a mediated object/event under a governing practice/system.**

That is a composite of boundary, representation, status, policy and realization.

Cross-regime persistence supports operational importance, not ontological independence.

---

# 35. Agent-era perturbation

Agent-era media intensifies:

```text
machine-public endpoints
capability-scoped publics
agent-generated audience sets
algorithmically assembled publics
per-recipient generated variants
public/private state changing at machine speed
policy-enforced selective disclosure
```

But these still map to:

```text
MF3 recipient/policy representation
MF4 dynamic audience composition
MF7 visibility/access state
MF8 selection/disclosure action
Runtime/Harness enforcement
Network delivery
Institution authority
```

No Agent-era Publicness primitive is currently justified.

---

# 36. Important survivor — Public Formation

B-D reduces `public access/status` but **does not close the ontology of publics as social formations**.

A public may arise through recursive circulation, mutual awareness, issue orientation, identity and participation rather than merely because an object has open access.

This should remain classified:

```text
Audience / Public Formation
= CROSS-CUTTING / OWNED-ELSEWHERE-CANDIDATE / still unresolved at whole-domain level
```

Likely owners are Human + Institution + Communication-derived structures, with Media supplying circulation/representation/exposure conditions.

Do not silently call this solved merely because Publicness reduced.

---

# 37. Important survivor — Selection / Gatekeeping / Visibility Allocation

A public object can remain effectively invisible because a selector does not surface it.

A restricted object can be made highly visible within a bounded audience.

Therefore:

```text
Publicness ≠ VisibilityAllocation
```

B-D further strengthens the still-open question:

> Given the same candidate set and access rules, what determines which mediated objects are surfaced to which consumers/publics?

This remains an unresolved destructive target.

---

# 38. Important survivor — Context Integrity / Recontextualization

The same bytes can move:

```text
private letter
→ leaked public post
→ newspaper quotation
→ court exhibit
→ archival record
→ model training corpus
```

while content bytes remain fixed but provenance, audience scope, authority and pragmatic/evidential force change.

B-D can represent the public/private status changes, but whether **context integrity / recontextualization** has a Media-specific irreducible remainder remains unresolved.

Do not infer closure.

---

# 39. Foundation consequence test

Would adding a numbered Publicness/Publication foundation make distinctions unavailable under the current stack?

Current answer: **no**.

It would likely collapse multiple independent dimensions:

```text
access
recipient scope
discoverability
publication
rights
public record
exposure
public formation
```

into one overloaded term.

Derived typed profiles provide higher explanatory resolution.

---

# 40. Classification update

Canonical Round-B-D classification:

```text
Publicness / Addressability / Publication as one Media Foundation
= REDUCIBLE / CROSS-CUTTING
= NOT genuinely-new-foundation at current frontier
```

More specifically:

```text
Public Access / Eligibility       → reducible / cross-cutting
Addressability                    → reducible / cross-cutting
Reachability / Delivery           → owned-elsewhere / Network
Discoverability                   → cross-cutting / partly unresolved through Selection
Visibility                        → overloaded; split across MF5/MF2/B-B/Selection/Institution
Publication Standing             → cross-cutting / owned-elsewhere / Institution-Law
Public Display / Performance      → composite profile
Public Domain / Rights Status     → owned-elsewhere / Law
Public Sphere / Public Formation  → cross-cutting / owned-elsewhere-candidate; NOT closed
```

No MF10 is admitted.

---

# 41. FoundationReopen audit

No MF0–MF9 FoundationReopenCondition is triggered.

B-D instead validates:

```text
MF3 standing can change while bytes remain fixed
MF3 public/institutional grounding is typed
MF4 boundaries/collections can carry operational/institutional standing
MF7 state/status claims are scope-relative
MF8 action must remain distinct from institutional consequence
```

No frozen claim was falsified.

Thus:

```text
MF0–MF9 = FROZEN
```

---

# 42. Research anchors used

Representative authoritative/comparison anchors:

- W3C ActivityPub Recommendation — special `Public` collection, public accessibility without authentication, explicit separation between public addressing and actual delivery; recipient targeting and inbox delivery remain distinct.
- W3C ActivityStreams 2.0 Core/Vocabulary — explicit audience-targeting metadata and audience/object relations.
- 17 U.S.C. §101 / U.S. Copyright Office — technical publication definition; public performance/display does not itself constitute publication; `publicly` and `publication` are legally distinct standings.
- U.S. Copyright Office public-domain guidance — public-domain status concerns copyright protection/permission, not physical or network availability.
- Habermas public-sphere tradition as summarized by the Stanford Encyclopedia of Philosophy — a public sphere is a social/institutional communicative formation, not mere open access or a large recipient set.
- MF3/MF4/MF7/MF8 frozen internal foundations — public/institutional grounding, audience/collection organization, status transition and agential release/action distinctions.

These are falsification/comparison anchors rather than external authority over Ordivon's ontology.

---

# 43. Round B-D closeout

```text
Round B-D target       = Publicness / Addressability / Publication
Result                 = REDUCIBLE / CROSS-CUTTING
New Media primitive    = NONE
MF10                    = UNKNOWN / NOT ADMITTED
FoundationReopen       = NONE
```

Deep result:

> **`Public` is not one Media ontological property. Public access, audience scope, addressability, discoverability, delivery, exposure, publication, public performance, public-domain rights and public-sphere formation are distinct standings. Public access reduces to audience/eligibility/status relations; addressability reduces to represented target/group standing plus resolution; publication is a regime-specific institutional status/action profile; public formation belongs primarily to Human/social/Institutional ontology. Media should retain typed publicness/publication profiles, not promote the overloaded word `public` into a new foundation.**

The whole-domain search remains open. Residual pressure now concentrates on:

```text
Artifact / Work / Edition / Performance / Generative Identity
Selection / Gatekeeping / Visibility Allocation
Meaning / Pragmatics / Context Integrity
Audience / Public Formation (adjacent-owner question)
Translation / Remediation profiles
Inscription / Fixation / Materialization
unknown continents
```

The ordering above is not a roadmap and does not imply any candidate is MF10.
