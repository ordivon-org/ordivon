# Ordivon Media Deep Foundations — Round B-C: Convention / Protocol / Interoperability Reducibility

**Date:** 2026-08-18  
**Continuity Task:** `task:media-foundations-mf2h-20260817`  
**Parent:** `media-whole-domain-round-b-b-encounter-exposure-reducibility-20260818.md`  
**Status:** **destructive reducibility / ownership audit only; no MF10 admitted**

---

# 0. Question

Round A identified a previously undernamed residual:

```text
Convention / Protocol / Interoperability
```

Round B-A then increased its pressure because machine/Agent communication can operate across opaque independent systems only when some shared public protocol standing survives.

Round B-C asks:

> **Is Convention / Protocol / Interoperability one Media-specific irreducible foundation, or is it a family of derived relations over Representation, Composition, State/Dynamics, Agency, Institution, Network and Runtime?**

The attack must separate at least:

```text
Convention
Specification
Schema / Grammar / Vocabulary
Protocol
Rule / Constraint
Conformance
Capability
Compatibility
Interoperability
Negotiation
Translation / Gateway
Version / Evolution
Standardization / Registration
```

No one term is allowed to inherit the others by definition.

---

# 1. Internal frozen substrate already covers much of the apparent core

MF3 explicitly froze:

```text
RFV1-04  conventional/public grounding is a valid representation route
RFV1-09  public convention/institution can stabilize representation
RFV1-22  content can survive byte/code/format transformation under typed equivalence
RFV1-27  schema/protocol/context/namespace can be constitutive of public/computational token content
RFV1-34  content ≠ code ≠ format ≠ geometry ≠ coordinates
RFV1-35  representation equivalence is typed
RFV1-38  standing type/specification roles can exist without current use
RFV1-39  type-level assigned content can pre-exist token instantiation
```

MF3 also established:

```text
Schema can represent constraints/types/roles.
The same schema can descriptively represent structure and normatively constrain future tokens.
Protocol codepoints can possess type-level standing before any token occurrence.
```

MF4 provides composition/part-whole and non-arbitrary joint-organization standing.

MF7 provides configuration, admissible-continuation, constraint and state-transition standing.

MF8 provides action, policy, choice, delegation and institutional/collective agency where genuine agency exists.

Therefore a new foundation must survive a very strong reduction base.

---

# 2. First correction — convention ≠ specification ≠ protocol

## Convention

A convention is a stabilized relation/practice under which forms, roles or actions acquire repeatable standing for participants or a system.

It may be:

```text
explicit or tacit
formal or informal
local or public
human or machine-maintained
short-lived or intergenerational
institutionally ratified or merely reproduced
```

Natural language, gesture, notation, genre and local social practice show that convention does not require one explicit specification artifact.

## Specification

A specification is a representation of declared types, rules, constraints, semantics, interfaces or expected behavior.

Thus:

```text
SpecificationStanding → MF3 Representation
```

A specification can exist while nobody currently conforms to it.

## Protocol

A protocol is stronger than a static specification when its represented constraints/roles are recruited as rules governing admissible interaction/continuation among participants or components.

Candidate derived decomposition:

```text
ProtocolProfile(P | Σ) =
  Specification/Convention Standing
+ Participant/Role Standing
+ Message/Action Type Standing
+ Admissibility / Constraint Structure
+ State/Continuation Semantics where stateful
+ Error/Failure Semantics
+ Version/Extension Scope
+ Realization/Transport Binding where applicable
+ Authority/Institution Standing where applicable
+ Provenance
+ Uncertainty
```

No new atom is visible in this decomposition.

---

# 3. Explicit specification is not necessary for convention

Cheap falsifiers:

```text
spoken slang
locally stabilized gesture
tacit conversational turn-taking
musical performance practice
genre convention
ad-hoc shared shorthand
```

These can stabilize interpretation/action without a formal written specification.

Therefore:

```text
Convention ≠ Specification
Convention does not require formal institution universally
```

Generic human convention formation is largely Human/social territory.

Media consumes the resulting standing when conventions ground representations or interactions.

---

# 4. Public consensus is not necessary for protocol standing

Consider two internally designed software components whose creator defines a private schema and message sequence.

The protocol can possess perfectly determinate operational standing even if:

```text
no public community exists
no standards body exists
no negotiated social consensus exists
```

Its grounding route can be:

```text
design + implementation + operational recruitment
```

already admissible under MF3.

Thus:

```text
PublicConvention ≠ universal requirement for Protocol
Institution ≠ universal requirement for Protocol
```

---

# 5. Protocol is not necessary for all Media

Oral performance, an image viewed directly, an environmental sign or a simple analog alarm can instantiate Media/Signal/Representation standing without any rich interaction protocol.

Even where a carrier has physical compatibility conditions, these need not constitute a protocol in the representational/normative sense.

Therefore:

```text
Protocol ≠ constituent of Media universally
```

This alone prevents Convention/Protocol from becoming a universal higher Media essence.

---

# 6. HTTP hard case — semantics ≠ wire syntax

HTTP provides a strong technical falsifier.

Current HTTP semantics are intentionally shared across HTTP/1.1, HTTP/2 and HTTP/3 while their transport/messaging realizations differ.

The standards explicitly separate core semantics from version-specific wire expression.

Therefore:

```text
ProtocolSemanticIdentity
≠ WireFormatIdentity
≠ TransportIdentity
```

This directly confirms MF3's existing typed-equivalence firewall.

Two implementations can preserve request-method/status/resource semantics across distinct wire realizations.

Thus `same protocol` is itself typed and scope-dependent.

---

# 7. Conformance ≠ interoperability

HTTP defines conformance relative to the roles an implementation performs and requires both syntax and semantic behavior.

But the standard also gives the key failure form:

```text
implementation claims conformance
+ does not implement required recipient behavior
→ failure to interoperate with peers relying on that claim
```

RFC 6838 makes the separation even clearer for media types:

```text
registration/specification standing
≠ universal interoperability
```

Known problems may arise from:

```text
version differences
byte ordering
gateway behavior
platform assumptions
```

Therefore:

```text
SpecificationStanding ≠ ConformanceStanding
ConformanceStanding ≠ InteroperabilityStanding
```

and neither identity can be used to found a primitive.

---

# 8. Interoperability is not conformance plus one boolean

Candidate:

```text
InteroperabilityStanding(A,B,T | Σ)
```

should be read as a relation:

> Under scope Σ and task/profile T, systems/components A and B can compose through available interfaces/transformations so that the distinctions, semantics, admissible operations and outcomes required by T survive sufficiently for joint operation.

This is not a universal scalar.

A pair can be interoperable for:

```text
plain text
```

but not:

```text
rich attachments
streaming
push notifications
cryptographic extensions
new vocabulary fields
```

Hence interoperability is:

```text
task-relative
capability-relative
version-relative
profile-relative
transformation-relative
```

rather than a natural binary property of two systems.

---

# 9. A2A hard case — same protocol family, unequal capabilities

The current A2A protocol exposes this structure directly.

Independent opaque agents can communicate without sharing internal state, memory, tools or implementation details, but the protocol explicitly models:

```text
protocol version
AgentCard
optional capabilities
extensions
required extension support
operation support
context/task/message semantics
```

A client is expected to inspect capabilities before invoking optional operations.

An agent can support the same core protocol while not supporting:

```text
streaming
push notifications
extended cards
particular extensions
```

Therefore:

```text
SameProtocolFamily
≠ SameCapabilityProfile
≠ UniversalInteroperability
```

The protocol also uses extension and unknown-field rules to preserve forward compatibility where possible.

This is a realization of a generic compatibility profile, not a new ontological primitive.

---

# 10. Version identity is typed

HTTP, MIME, Unicode and A2A expose different version strategies.

## HTTP

Core semantics can remain shared while incompatible wire-format changes increment major versions.

## MIME

`MIME-Version` asserts conformance to a message-body format standard, while media-format versions may have their own independent versioning conventions.

## Unicode

The standard preserves character/code-point identity across versions and uses stability guarantees to make later conformant implementations continue interpreting older data coherently while allowing additive repertoire growth.

## A2A

Major/minor protocol version participates in compatibility negotiation; patch releases do not define protocol compatibility.

Therefore there is no universal metaphysics of `Version` specific to protocol.

It decomposes into:

```text
MF7 identity/persistence/successor relation
+ MF3 specification/content identity
+ declared compatibility/equivalence rules
```

No new Foundation is required.

---

# 11. Same syntax is not sufficient

Construct two implementations that parse identical JSON fields but assign different meanings to one field.

```text
SyntaxCompatible = yes
SemanticCompatible = no
```

MF3 already predicts this because:

```text
Code/Format ≠ Content
```

Therefore syntax matching alone cannot ground interoperability.

---

# 12. Same semantics is not sufficient

Construct two implementations that agree fully on an operation's abstract semantics but encode messages in mutually unreadable wire formats.

Without a translator/gateway:

```text
SemanticCompatibility = yes
DirectOperationalInteroperability = no
```

Again:

```text
ContentIdentity ≠ FormatIdentity ≠ ReadoutCompatibility
```

already frozen in MF3.

---

# 13. Direct common protocol is not necessary

HTTP explicitly supports intermediaries/gateways that translate between non-HTTP or differently realized systems.

More generally:

```text
A speaks format/protocol X
Gateway maps X↔Y
B speaks Y
```

can permit task-level interoperability without A and B sharing one native syntax/protocol implementation.

Therefore:

```text
Interoperability ≠ direct shared protocol universally
```

Translation becomes a typed transformation whose validity depends on preserved semantics/actions/effects.

MF1/MF3 already provide transformation and equivalence machinery; Runtime/Network own realization where computational/networked.

---

# 14. Shared standard is not necessary

Two parties can develop a local bilateral protocol, or one side can adapt to an undocumented de facto interface through a stable operational mapping.

This may be fragile, poorly governed or hard to scale, but interoperability can exist without a recognized standards organization.

Therefore:

```text
Standardization ≠ ProtocolStanding
Standardization ≠ Interoperability
```

Standards bodies supply an institutional grounding/coordination route, not the universal ontology.

---

# 15. Standardization does not guarantee interoperability

RFC 6838 explicitly requires registrants to document interoperability considerations because even formally specified media types can encounter incompatibilities.

Thus:

```text
RegisteredName
+ PublishedSpecification
+ InstitutionalStanding
↛ UniversalInteroperation
```

This is a decisive anti-collapse rule.

---

# 16. ActivityPub hard case — conformance is role-scoped

ActivityPub defines distinct conformance classes for:

```text
client
server
federated server
```

and implementations may support client-to-server, server-to-server federation, or both.

It also depends on ActivityStreams vocabulary, HTTP behaviors, media types, addressing and side-effect semantics.

Therefore even within one named protocol:

```text
ProtocolMembership
≠ one homogeneous implementation profile
```

Role standing and supported layers matter.

This maps naturally to:

```text
MF4 composition/roles
MF3 representation/schema semantics
MF7 state/side effects
Network transport
Institutional/public specification standing
```

No new primitive appears.

---

# 17. Unicode hard case — stable identity enables compatibility without frozen implementation

Unicode demonstrates that interoperability can depend on **stability constraints on meaning/identity across evolution**, not on keeping implementations or data versions identical.

Key strategy:

```text
new repertoire may be added
existing characters are not removed/reassigned incompatibly
unknown future code points must be handled safely
```

This is well described by:

```text
MF7 persistence / identity rules
+ MF3 type/content standing
+ compatibility policy
```

It does not require a Protocol primitive beyond those structures.

---

# 18. Natural-language and notation hard cases

Language, musical notation, mathematical notation and sign systems expose a different regime.

Participants can share substantial conventional meaning while differing in:

```text
dialect
vocabulary
notation extensions
interpretive practice
historical version
local convention
```

Interoperability may be partial and repairable rather than binary.

Translation, explanation and contextual adaptation can increase it.

Thus:

```text
ConventionStanding
≠ CompleteSharedSemantics
```

and:

```text
PartialInteroperability is ordinary
```

Generic human convention/interpretation belongs largely to Human/social/linguistic research; Media consumes the conventional representational standing through MF3.

---

# 19. Protocol without rich semantics

Some protocols primarily constrain sequencing, timing, turn-taking or admissible operations rather than denoting a rich external referent.

For example:

```text
handshake order
acknowledgement rule
retry state
framing delimiter
request/response turn structure
```

This pressure does not reopen MF3 because the protocol artifact can represent/direct the rule while the enacted interaction belongs to:

```text
MF7 state/dynamics/continuation constraints
```

The representational rule and enacted dynamics remain distinct.

Therefore:

```text
ProtocolSpecification ≠ ProtocolExecution
```

---

# 20. Protocol execution without agency

A deterministic finite-state machine can conform to and execute a protocol without satisfying rich AgencyStanding.

Therefore:

```text
ProtocolParticipation ≠ Agency universally
```

MF7 can represent formal/operational state transition and continuation standing without MF8.

MF8 enters only when participant action/choice/evaluation/authority genuinely has AgencyStanding.

---

# 21. Protocol negotiation is not constitutive

Some protocols negotiate:

```text
version
media type
encoding
capability
extension
language
security mechanism
```

Others use a fixed profile with no negotiation.

Hence:

```text
Negotiation ≠ Protocol universally
```

Where present, negotiation decomposes into:

```text
MF3 representation of capabilities/options
MF7 state transition
MF8 action/selection when agential
Network/Runtime realization
```

---

# 22. Compatibility is not one relation

At minimum distinguish:

```text
SyntacticCompatibility
SemanticCompatibility
RepresentationalCompatibility
VersionCompatibility
CapabilityCompatibility
TransportCompatibility
TemporalCompatibility
SecurityCompatibility
Authority/PermissionCompatibility
Behavioral/ProtocolCompatibility
TaskCompatibility
```

A system pair may satisfy some and fail others.

Thus a global scalar:

```text
Compatible = true/false
```

is usually underspecified.

Compatibility is a typed profile over requirements.

---

# 23. Interoperability is realized composition, not protocol identity

A useful derived definition is:

```text
InteroperabilityProfile(A,B,T | Σ) = <
  Participant/Role Standing,
  Required Task/Outcome Profile T,
  Shared or Translatable Representation Standing,
  Syntax/Format Compatibility,
  Semantic Compatibility,
  Capability Intersection,
  Admissible Interaction/State Composition,
  Transport/Execution Route,
  Version/Extension Profile,
  Error/Recovery Semantics,
  Security/Authority Compatibility,
  Timing/Ordering Compatibility,
  Observed Joint-Operation Evidence,
  Provenance,
  Uncertainty,
  Scope
>
```

This is a derived composition profile.

It does not require a new primitive.

---

# 24. Conformance as satisfaction relation

A useful derived relation is:

```text
ConformanceStanding(I,S,R,V | Σ)
```

where implementation/artifact `I` satisfies the requirements of specification `S` for declared role `R` and version/profile `V` under scope `Σ`.

This requires:

```text
SpecificationStanding            → MF3
Implementation/Bearer Standing   → MF4/MF7/Runtime as relevant
Requirement/constraint semantics → MF3 + MF7
Typed evaluation/satisfaction    → already admissible under MF3
Evidence                         → test/observation layer
```

Again, no missing primitive.

---

# 25. Convention formation is an adjacent owner, not a missing Media atom

The remaining apparently deep question is:

> How does a convention become socially/systemically established rather than merely analyst-imputed?

MF3 already requires non-arbitrary standing and allows convention/public/institutional grounding.

The **formation dynamics** of social convention may involve:

```text
repetition
coordination equilibria
learning
imitation
network diffusion
sanction/norm
institutional ratification
power
path dependence
```

Those mechanisms are largely Human / Game / Host-Institution / Network / MF7 dynamics territory.

Media should consume their result when it grounds representation or protocol standing.

Thus convention formation does not currently justify a Media Foundation.

---

# 26. Institutional authority is optional but changes standing

A standard can be:

```text
de facto
de jure
vendor-specific
community-governed
bilateral
private/internal
```

Institutional authority may affect:

```text
who may revise it
what counts as official conformance
registry identity
jurisdiction
certification
adoption incentives
```

but not the basic possibility of convention/protocol standing.

Therefore institutional status is a profile/grounding route owned largely by the broader Institution/Governance/Law work.

---

# 27. Agent-era perturbation

Agent-era systems intensify four things:

```text
1. machine-readable capability description
2. explicit version/extension negotiation
3. runtime protocol adaptation
4. machine-to-machine protocol ecosystems with no human reader in the loop
```

A2A is a clean example: independent opaque agents advertise capabilities, negotiate supported interaction patterns and retain protocol compatibility through version/extension rules.

But these map to:

```text
MF3   public protocol/capability representation
MF7   task/context/version state
MF8   delegated agent action where genuine agency exists
Network transport
Runtime/Harness execution and adaptation
Institution/security authority as applicable
```

No Agent-era primitive survives reduction.

---

# 28. Emergent agent languages / self-evolving protocols

A harder future case is agents developing a locally efficient protocol not predeclared by humans.

Even there, the decomposition remains available:

```text
new stable token/action relation emerges
→ systemic use provides grounding
→ MF3 RepresentationStanding can arise without public human convention

interaction rules stabilize
→ MF7 continuation/constraint profile

participants adapt
→ MF8 learning/action if agents

protocol persists/changes
→ MF7 identity/version profile
```

A later case would reopen this conclusion only if a genuine shared protocol cannot be represented as grounded use/convention plus state/constraint structure.

No such counterexample is presently known.

---

# 29. Cheapest falsifier matrix

| Proposed universal claim | Cheapest counterexample | Result |
| --- | --- | --- |
| Convention requires explicit specification | slang / tacit gesture / performance practice | falsified |
| Protocol requires public convention | private internal schema/protocol | falsified |
| Protocol is necessary for all Media | static image / direct oral sign | falsified |
| Same syntax is sufficient for interoperability | identical JSON, conflicting field meaning | falsified |
| Same semantics is sufficient for direct interoperability | incompatible wire formats without translator | falsified |
| Conformance is sufficient for interoperability | optional capability/profile mismatch; RFC interoperability caveats | falsified |
| Interoperability requires one identical version | backward-compatible versions / stable Unicode evolution | falsified |
| Interoperability requires one direct shared protocol | gateway/translator | falsified |
| Standardization guarantees interoperability | registered media types with known version/platform issues | falsified |
| Standardization is necessary | bilateral/de facto protocol | falsified |
| Institution is necessary | private/ad-hoc protocol | falsified |
| Agency is necessary | deterministic protocol state machine | falsified |
| Negotiation is necessary | fixed-profile protocols | falsified |
| Human semantics are necessary | machine/Agent protocol | falsified |
| Compatibility is one scalar | feature/version/security/task-specific compatibility | falsified |

The survivor is a family of typed standing/constraint/composition relations, not one new atom.

---

# 30. Irreducibility test

Question:

> Does Convention / Protocol / Interoperability require a primitive absent from MF0–MF9 and adjacent owners?

Round B-C answer:

**No concrete irreducible survivor.**

Reduction:

```text
Convention grounding        → MF3 + Human/Institution/systemic-use routes
Specification               → MF3
Schema/Vocabulary           → MF3
Protocol rule representation→ MF3
Admissible interaction      → MF7
Role composition            → MF4
Protocol execution          → MF7 + Runtime/Network
Agency/negotiation          → MF8 where genuine
Version/persistence         → MF7 + MF3 identity/equivalence
Conformance                 → derived satisfaction relation
Compatibility               → typed relational profile
Interoperability            → realized composition profile
Standardization/registry    → Institution/Governance
Transport                   → Network
Execution machinery         → Runtime/Harness
```

Therefore the candidate fails the foundation-level irreducibility test.

---

# 31. Ownership test

No single Media-owned core survives.

Media legitimately needs:

```text
representation convention profiles
format/schema/protocol context
media-type/version compatibility
consumer/producer interoperability profiles
```

But generic foundations distribute as:

```text
MF3                  representation/convention/schema semantics
MF4                  composition/roles
MF7                  state/constraint/version/continuation
MF8                  agential negotiation/action
Human                natural-language/social convention formation
Host/Institution     standards authority/registry/governance
Network              transport/protocol realization
Runtime/Harness      execution/capability/adaptation machinery
```

A broad Media `Protocol Foundation` would duplicate these owners.

---

# 32. Cross-regime test

Convention and interoperability phenomena survive across:

```text
oral language
manuscript conventions
print notation
telegraph codes
telephone signaling
broadcast standards
recording/file formats
network protocols
social federation
mobile/immersive systems
Agent protocols
```

But the common denominator is not a new physical or social essence.

It is approximately:

> **grounded repeatable type/use/constraint standing plus participant-relative capability to preserve required distinctions/actions across composition.**

Those terms are already expressible by MF3/MF4/MF7.

Cross-regime persistence therefore supports importance, not independence.

---

# 33. Foundation consequence test

Would a numbered Convention/Protocol/Interoperability foundation enable classifications unavailable under the frozen substrate?

Current answer: **no**.

The main practical consequences are better represented by explicit derived profiles:

```text
ConformanceProfile
CompatibilityProfile
InteroperabilityProfile
ProtocolVersionProfile
CapabilityProfile
TranslationProfile
```

A monolithic Foundation would obscure exactly the distinctions standards engineering has learned to preserve.

---

# 34. Classification update

Canonical Round-B-C classification:

```text
Convention / Protocol / Interoperability
= REDUCIBLE / CROSS-CUTTING
= NOT genuinely-new-foundation at current frontier
```

More specifically:

```text
Convention                  → MF3 grounding + adjacent social/institutional formation
Specification               → already-covered / MF3
Protocol semantics          → MF3 + MF7
Protocol execution          → MF7 + Network/Runtime
Conformance                 → derived satisfaction profile
Compatibility               → derived typed relation
Interoperability            → derived composition/realization profile
Version evolution           → MF7 + MF3
Standardization/registry    → owned-elsewhere / Institution
Agent protocol negotiation  → cross-cutting / MF3+MF7+MF8+Runtime/Harness
```

No MF10 is admitted.

---

# 35. What survives B-C

Reducing this candidate increases pressure on adjacent residuals rather than eliminating the overall unexplored space.

## S1 — Selection / Gatekeeping / Visibility Allocation

B-B already raised this. Protocol reduction does not absorb it.

## S2 — Publicness / Addressability / Publication Standing

Standards/protocols can define addressing, but the status of `public`, publication, audience eligibility and discoverability remains separate.

ActivityPub itself provides a clean example: a special Public collection participates in addressing semantics but is not a normal inbox that receives actual activities. This reinforces rather than closes the Publicness distinction.

## S3 — Artifact / Work / Edition identity

Protocol/version analysis sharpens, but does not solve, work identity under revisions, performances, editions and continuously generative artifacts.

## S4 — Meaning / Pragmatics / Context Integrity

Shared code/protocol standing does not guarantee identical contextual interpretation or pragmatic force.

## S5 — Translation / Remediation

Translation did not survive as a primitive here, but semantic-preservation profiles across carriers/languages/modalities may remain a valuable operational reconstruction problem.

---

# 36. FoundationReopen audit

No MF0–MF9 FoundationReopenCondition is triggered.

In fact B-C strongly validates existing MF3 distinctions:

```text
content ≠ code ≠ format
schema/protocol can constitute token content
public convention can ground standing
representation equivalence is typed
content can survive format transformation
standing type/spec can exist without current token/use
```

MF7 also survives protocol state/constraint/version hard cases without requiring syntax to become ontology.

Thus:

```text
MF0–MF9 = FROZEN
```

---

# 37. Research anchors used

Representative primary/authoritative comparison anchors:

- RFC 9110, *HTTP Semantics* — shared core semantics across HTTP versions; conformance is role-, syntax- and semantics-sensitive; interoperability can fail when required recipient behavior is absent; gateways/intermediaries are explicit.
- RFC 6838, *Media Type Specifications and Registration Procedures* — public registration/specification supports interoperability but universal interoperability is not required; known version/platform/gateway issues must be considered.
- RFC 2045, *MIME Part One* — MIME-Version asserts conformance to the message-body format while media formats can maintain independent version conventions.
- Unicode Standard versioning/conformance/stability documentation — stable code-point identity and forward/backward compatibility discipline across standard evolution.
- W3C ActivityPub Recommendation — separate client/server/federated-server conformance classes; ActivityStreams vocabulary, addressing and HTTP/media-type semantics compose into the protocol.
- A2A Protocol Specification v1.0.0 — independent opaque agents, explicit protocol versioning, capability declarations, extension support and compatibility rules.
- MF3 Representation Foundations v1 — conventional/public grounding, schema/protocol context, typed equivalence and type-level standing.

These are falsification/comparison anchors, not external replacements for Ordivon's ontology.

---

# 38. Round B-C closeout

```text
Round B-C target       = Convention / Protocol / Interoperability
Result                 = REDUCIBLE / CROSS-CUTTING
New Media primitive    = NONE
MF10                    = UNKNOWN / NOT ADMITTED
FoundationReopen       = NONE
```

Deep result:

> **Convention, protocol, conformance, compatibility and interoperability are real but distinct standings. Convention supplies one grounding route; specifications represent rules/types; protocols recruit represented constraints into interaction; conformance is a role/version-scoped satisfaction relation; compatibility is typed possibility of composition; interoperability is realized task-relative composition across semantics, capabilities, versions and execution routes. None currently requires a new Media primitive beyond MF3/MF4/MF7 plus adjacent owners.**

The whole-domain search remains open. The next destructive round must select another unresolved residual by cheapest falsifier, not by inheriting a roadmap or by promoting the latest surviving term.
