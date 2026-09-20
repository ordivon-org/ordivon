# Agent Security LEGO — Cross-Domain Destroyer R1

Date: 2026-09-18
Status: CROSS-DOMAIN VALIDATION COMPLETE
Parent:
- knowledge/lessons/agent-security-lego-r1.md
- knowledge/lessons/agent-security-cross-system-destroyer-r1.md

Domains:
1. Browser automation / Agent Birth
2. Artifact Build & Delivery
3. Market Capital read-only / staged effect admission
4. Game / Station Zero multi-agent execution
5. Connected Apps: Gmail + Google Calendar tool surfaces

## 1. Purpose

The previous destroyer showed that Agent Security LEGO survives across six coding-agent products. That result could still be domain overfit.

This round deliberately tests unrelated effect and persistence regimes:
- browser/provider interaction;
- digital artifact production and publication;
- financial observation and external-write admission;
- deterministic multi-agent game execution;
- OAuth-backed connected SaaS actions.

The question is not whether every AS node appears as the same component. The question is whether omitting the concept causes material loss of authority, information-flow, persistence, or control semantics.

## 2. Source boundary

### Browser / Agent Birth
Local canonical evidence:
- knowledge/lessons/ordivon-agent-birth-lego-r1.md
- knowledge/graphs/ordivon-agent-birth-r1.json
- knowledge/lessons/cloudflare-provider-security-boundary-r1.md
- user-agents/web-provider-routing Skill

### Artifact
Source authority:
- /root/projects/ordivon-artifact-v2
- docs/artifact-build-delivery-e2e-v1.md
- docs/artifact-build-delivery-e2e-toolchain-v1.md
- artifact-work Skill

### Market Capital
Source authority:
- /root/projects/ordivon-market-capital-next
- revision 4aaaa8e175cf3d8689aa8097894f830a596350c3
- README.md
- docs/ARCHITECTURE.md

### Game
Source authority:
- /root/projects/ordivon-game
- README.md
- docs/ARCHITECTURE.md
- docs/STATION_ZERO_V3_P3.md

### Connected Apps
Evidence boundary:
- current ChatGPT Gmail and Google Calendar tool contracts available to this session.
- No mailbox, calendar, message, event, or other user content was read for this study.
- The analysis uses only tool/action schemas and their documented effect semantics.

## 3. Domain A — Browser automation / Agent Birth

### Security regime identity

The same logical task may route through:
- native connector/API;
- direct public HTTP;
- deterministic Playwright;
- adaptive Browser Use;
- desktop Computer Use;
- dedicated ChatGPT Agent Birth carriers.

The current web-provider-routing law chooses the thinnest admitted provider and explicitly forbids treating provider success as domain completion.

This validates XAS13 SECURITY_REGIME_IDENTITY:
a browser task's authority and observability depend on the chosen carrier/control regime, not on the user-visible task label.

### Trigger / authority / effect boundary

Agent Birth separates:
- role/campaign identity;
- provider carrier lease;
- provider preflight;
- durable effect fence;
- SEND;
- exact-turn provider observation;
- reconciliation.

The central non-idempotent effect is SEND.

This yields an explicit commit point:

```text
intent
-> provider preflight
-> durable UNKNOWN/effect fence
-> SEND
-> provider observation
-> reconcile
```

A retry after ambiguous SEND is not automatically authorized.

### Persistence

Distinct classes include:
- browser profile/session state;
- task/effect ledger;
- provider conversation state;
- local recovery evidence;
- challenge/admission observations.

This validates XAS16 PERSISTENCE_CLASS_VECTOR.

### Binding time

Carrier selection, carrier lease, preflight state, and effect fence bind before provider effect.
Changing a route after the effect fence cannot retroactively make the prior effect safe to resend.

This validates XAS14 POLICY_BINDING_TIME.

### Reconciliation

Provider-visible exact-turn observation is separate from transport/process success.

This exposes a stronger primitive:
XAS18 EFFECT_RECONCILIATION_ORACLE.

## 4. Domain B — Artifact Build & Delivery

Artifact is deliberately not an agent-security product, making it a useful destroyer.

### Regime identity

Artifact outcomes depend on:
- artifact family/profile;
- authoring authority mode;
- selected target renderer;
- target OS/application;
- validator set;
- delivery destination;
- trust/signing mode.

A PPTX that passes structural validation but has not reached PowerPoint Desktop target acceptance is a different regime from one that has.

This validates XAS13 outside agent execution.

### Capture / derivation

READ SET:
- native source materials;
- templates;
- images/data;
- exact immutable input authorities.

DERIVE SET:
- PPTX/DOCX/XLSX/PDF/HTML;
- render PNGs;
- PDF companions;
- verification summaries;
- provenance;
- OCI package/referrer material.

This validates AS03/AS04 independently of model context.

### Egress and external publication

The Artifact Skill explicitly separates:
- create/transform/verify/package;
from
- upload/publish/provider effect.

Publication belongs to Distribution/provider authority.

Thus:
```text
artifact bytes exist
!=
artifact published
```

### Persistence classes

Distinct classes include:
- source material;
- generated artifact;
- render evidence;
- verification evidence;
- package/OCI material;
- provenance/attestation;
- destination copy.

A destination copy is not equivalent to the local build artifact.

### Effect commit point

Artifact's publication/delivery step is a commit boundary.
The R1 contract requires destination read-back plus SHA-256 equality.

This validates:

XAS17 EFFECT_COMMIT_POINT / REVERSIBILITY CLASS.

### Reconciliation oracle

```text
write/upload
-> provider destination
-> read back exact object
-> digest equality
```

A successful local process or upload command is insufficient.

This strongly validates XAS18 EFFECT_RECONCILIATION_ORACLE.

### Policy binding time

Trust/signing configuration and production activation are explicitly separate.
A local signing config intentionally avoids external transparency-log effects; public/keyless signing is a later explicit operational action.

Policy/effect mode must therefore be known at the point the release/publication action is admitted.

## 5. Domain C — Market Capital

Market Capital is a destructive test because it distinguishes observation, economic semantics, and external financial effect.

Canonical flow:

```text
Evidence
-> Decision
-> ExecutionIntent
-> Authority
-> External Effect
-> Reality
-> Reconciliation
-> Evidence
```

### Security regime identity

Current regimes include:
- public credential-free market observation;
- mechanics-only local simulation;
- private read-only reality;
- demo/testnet preflight;
- live-endpoint qualification;
- production/live write authority.

These regimes must not be collapsed.

Example:
an endpoint may be technically LIVE while production trading remains false.

XAS13 survives strongly.

### Authority vector

Market Capital separates:
- scientific truth;
- economic truth;
- capital truth;
- effect authority;
- external financial write admission;
- provider account/order reality.

This is a non-agent example of authority being a vector, not a single permission level.

### Policy binding time

External financial write admission is evaluated before execution begins.
Current runners cross the in-repository effect boundary before LEAN starts.

Future market data may not rewrite the already-frozen decision/precommit.

Therefore binding time matters twice:
1. decision-time evidence freezes before future observations;
2. effect authority must be valid before external execution.

XAS14 survives strongly.

### Delegation/inheritance

LEAN, Nautilus, QuickFIX/n, TigerBeetle, Network v2, venue APIs, and Market Capital each own different semantics.

No mature provider inherits Market Capital's semantic authority merely because it executes mechanics.

This generalizes XAS15 from parent/subagent inheritance to:
AUTHORITY DELEGATION / PROPAGATION ACROSS COMPOSED EXECUTORS.

### Persistence vector

Classes include:
- decision artifact;
- intent;
- provider-order/execution history;
- reservation/accounting mechanics;
- normalized account reality;
- monitoring evidence;
- reconciliation state.

TigerBeetle provider state cannot resurrect terminal Market Capital history.

XAS16 survives.

### Effect commit point

Market Capital gives the clearest formulation:

```text
Decision != ExecutionIntent != EffectAuthority != External Effect
```

A FIX message, engine fill, workflow success, or process exit is not capital truth.

XAS17 survives strongly.

### Reconciliation oracle

```text
authorized effect
-> broker/venue receipt or execution
-> authoritative account/order reality
-> reconciliation
```

Broad snapshot absence is not proof of no effect.

XAS18 survives strongly.

## 6. Domain D — Game / Station Zero

Game is a strong destroyer because its effects are local and deterministic rather than remote/SaaS.

### Regime identity

Station Zero distinguishes:
- current registered v2 product;
- v3 research preview;
- deterministic fixture provider;
- live external cognition provider;
- research surfaces enabled/disabled.

Product/research standing and effect authority differ by regime.

XAS13 survives without cloud/network dependence.

### Capture scope / information flow

Each high-fidelity Agent receives a bounded Agent Context.

It explicitly excludes:
- hidden enemy positions;
- exact hidden health;
- enemy inventories;
- opposing Commander Orders;
- other faction plans;
- direct World mutation capability.

This validates AS03 and existing Wave 2 information-flow reasoning.

### Derivation

```text
World + faction knowledge + Commander Order
-> bounded Context
-> admitted Candidate
-> Agent Decision
-> Faction Plan
-> Preview
```

The Provider returns Candidate identity only; free-form prose does not become privileged operation.

AS04 survives.

### Persistence classes

Distinct durable classes:
- Commander Order revisions;
- Preview;
- Faction Plans;
- Batch identity;
- World/Event/Record heads;
- replay/recovery evidence;
- SQLite product state.

XAS16 survives strongly.

### Policy binding time

Order is mutable until a durable Faction Plan is submitted.
After the first durable plan, Order/Preview become immutable.

Thus policy/intent mutability has an explicit temporal boundary.

XAS14 survives strongly.

### Delegation

Player, Agent Provider, deterministic policy, P2 execution layer, and World each own distinct authority.

Agent Provider choice explicitly does not imply Game action authority.

This validates XAS15 outside infrastructure/security software.

### Effect commit point

The architecture explicitly separates:

```text
Commander Order
!=
Plan Preview
!=
Commit
!=
World state transition
```

Only explicit Commit enters P2 canonical Batch execution.

This is an exceptionally clean XAS17 case.

### Reconciliation oracle

After restart or response loss:
- recover exact history;
- verify selected Preview;
- reuse retained plans;
- resume exact prepared Batch;
- observe exact World result before opening another Planning Head.

This validates XAS18 even though no external provider write is required for the World effect.

## 7. Domain E — Connected Apps: Gmail + Google Calendar

This domain uses current connected-app action contracts only. No personal mailbox/calendar content was read.

### Security regime identity

The operative regime depends on:
- installed/authorized connector;
- authenticated provider account;
- read versus mutation tool;
- target mailbox/calendar;
- object identity returned by the provider;
- action semantics such as draft, send, trash, event-create, update scope.

XAS13 survives.

### Capture/read scope

Gmail search returns message IDs; reading the body is a separate action.
Attachments are read through another exact message/attachment boundary.

Calendar search can be bounded by explicit time window and calendar ID; full event detail uses an exact event read.

This strongly validates progressive capture scope:
discovery identity != full content read.

### Derivation

Examples:
- message body -> outgoing draft/reply;
- attachment -> extracted representation;
- event state -> updated event proposal;
- user text -> Calendar event/Meet request.

AS04 survives.

### Persistence classes

Gmail:
- source message;
- draft;
- sent message;
- thread;
- Trash state;
- attachment/provider object.

Calendar:
- event;
- recurring-series master/instance;
- attendees' copies/notifications;
- conference provisioning state.

XAS16 survives strongly.

### Effect commit point

Gmail explicitly distinguishes:
```text
draft != send
```

Deleting an email through the available action means:
```text
move to Trash != permanent delete
```

Calendar distinguishes:
```text
search/read != create/update/delete
```

and recurring updates have explicit scopes:
- this instance;
- entire series;
- this and following.

XAS17 survives strongly.

### Policy binding time

The user's explicit request binds mutation authority at the action boundary.
Calendar update scope must be chosen before mutation.
A created event's downstream attendee/conference effects cannot be reinterpreted afterward as a different scope.

XAS14 survives.

### Delegation / provider authority

The connector acts on behalf of the authenticated account, but provider-native IDs and provider state remain authoritative.
The model does not own Gmail message identity or Calendar event truth.

XAS15 survives as delegated provider authority, though the OAuth token mechanics themselves remain client/provider-owned.

### Reconciliation oracle

Gmail send returns provider message/thread IDs.

Calendar create/update returns provider event state, but Google Meet creation can remain pending; the current tool contract explicitly instructs a later re-read when finalized conference details matter.

Thus:
```text
mutation accepted
!=
all downstream provider state finalized
```

XAS18 survives.

## 8. Cross-domain matrix

Legend:
- STRONG = omission loses material architecture/control truth.
- PRESENT = concept exists but is less central.
- CONDITIONAL = only applicable for some regimes.

| Primitive | Browser/Birth | Artifact | Market | Game | Connected Apps | Cross-domain standing |
| --- | --- | --- | --- | --- | --- | --- |
| AS01 Identity Authority | STRONG | PRESENT | STRONG | STRONG | STRONG | STABLE |
| AS02 Trigger | STRONG | STRONG | STRONG | STRONG | STRONG | STABLE |
| AS03 Capture/Read Scope | STRONG | STRONG | STRONG | STRONG | STRONG | STABLE |
| AS04 Derivation | STRONG | STRONG | STRONG | STRONG | STRONG | STABLE |
| AS05 Local Persistence | STRONG | STRONG | STRONG | STRONG | CONDITIONAL | STABLE |
| AS06 Egress Path | STRONG | STRONG | STRONG | CONDITIONAL | STRONG | STABLE, regime-dependent |
| AS07 Remote Persistence | STRONG | STRONG on delivery | STRONG on providers | CONDITIONAL | STRONG | STABLE, conditional |
| AS08 Key Authority | CONDITIONAL | CONDITIONAL | CONDITIONAL | LOW | provider-owned | CONDITIONAL LENS |
| AS09 Capability Actuator | STRONG | STRONG | STRONG | STRONG | STRONG | STABLE |
| AS10 Side-effect Observation | STRONG | STRONG | STRONG | STRONG | STRONG | STABLE |
| AS11 Retention/Delete | STRONG | STRONG | STRONG | STRONG | STRONG | STABLE |
| AS12 Disclosure Alignment | STRONG | STRONG | STRONG | PRESENT | STRONG | STABLE META-LENS |
| XAS13 Security Regime Identity | STRONG | STRONG | STRONG | STRONG | STRONG | CROSS-DOMAIN STABLE |
| XAS14 Policy Binding Time | STRONG | STRONG | STRONG | STRONG | STRONG | CROSS-DOMAIN STABLE |
| XAS15 Authority Delegation/Inheritance | STRONG | STRONG composition | STRONG composition | STRONG | STRONG provider delegation | CROSS-DOMAIN STABLE, broaden name |
| XAS16 Persistence Class Vector | STRONG | STRONG | STRONG | STRONG | STRONG | CROSS-DOMAIN STABLE |
| XAS17 Effect Commit Point / Reversibility | STRONG | STRONG | STRONG | STRONG | STRONG | NEW CROSS-DOMAIN STABLE |
| XAS18 Effect Reconciliation Oracle | STRONG | STRONG | STRONG | STRONG | STRONG | NEW CROSS-DOMAIN STABLE |

## 9. Two new primitives from the cross-domain destroyer

### XAS17 — Effect Commit Point / Reversibility Class

Every consequential workflow needs to identify where a proposal becomes an effect.

Examples:
- Browser: SEND.
- Artifact: publish/deliver to external destination.
- Market: admitted external financial write.
- Game: explicit Turn Commit into canonical Batch.
- Gmail: send rather than draft.
- Calendar: create/update/delete provider event.

Required questions:
- what is the last freely reversible state?
- what operation crosses the commit boundary?
- is the effect idempotent?
- if not, what exact identity fences replay?
- what compensation/reversal exists, if any?

This sharpens the optional IRREVERSIBLE EFFECT SET already suggested in Agent Security LEGO R1.

### XAS18 — Effect Reconciliation Oracle

Observation and process success are insufficient when an effect can be ambiguous or asynchronously finalized.

Required questions:
- what authority can establish the external/authoritative result?
- what exact identity is queried?
- what evidence distinguishes pending, committed, absent, failed, or unknown?
- can an UNKNOWN safely converge without repeating the effect?

Examples:
- Browser exact-turn provider read-back.
- Artifact destination read-back + digest equality.
- Market authoritative venue/account reality.
- Game exact World/Batch recovery.
- Gmail provider message/thread identity.
- Calendar event re-read for pending conference materialization.

## 10. Cross-domain laws

### CD-S1 — Claims Are Regime-Bound

A claim such as "network is disabled", "read-only", "sandboxed", "published", or "live" is incomplete without exact regime identity.

### CD-S2 — Policy Has a Binding Event

Every policy/control must state when it becomes effective.
A correct rule applied after commit cannot retroactively constrain the committed effect.

### CD-S3 — Authority Propagation Must Be Explicit

Whenever one actor/component invokes another, record whether authority is:
- delegated;
- attenuated;
- independent;
- clamped;
- escalatable.

Do not infer inheritance from topology.

### CD-S4 — Persistence Is Object-Class Specific

Do not assign one retention/deletion statement to a heterogeneous system.
Name each persisted object class and owner.

### CD-S5 — Intent Is Not Commit

Plan, prompt, draft, decision, preview, package, or intent is not automatically an effect.

### CD-S6 — Commit Is Not Reality

An admitted/sent/committed operation is not automatically authoritative domain truth.

### CD-S7 — External/Authoritative Reality Requires Reconciliation

For consequential or ambiguous effects, completion requires an owner-native read-back/reconciliation oracle.

### CD-S8 — Deletion/Reversal Follows the Descendant Graph

Trash, archive, local delete, undo, release, void, cancellation, and remote deletion are distinct transitions.

## 11. Relationship to existing LEGO Theory

### Information Flow Wave 2

Do not duplicate it.

Existing Wave 2 already owns:
source -> transform -> store -> channel -> sink/observer -> declassification.

Agent Security LEGO consumes that lens for AS03/AS04/AS06/AS12.

### Feedback Control / STPA

AS09 and XAS14 are actuator/control-timing applications.
Unsafe placement/timing remains a control-structure problem.

### FMEA / FTA

XAS17/XAS18 expose failure paths around ambiguous effects:
- commit succeeded but response lost;
- provider accepted request but downstream state pending;
- local success but remote read-back mismatch;
- retry risks duplicate effect.

### Compositional Contracts

XAS15 asks whether composed components preserve required authority/effect guarantees rather than merely sharing an API.

## 12. Promotion decision

The cross-domain evidence is now sufficient to promote several concepts from "coding-agent candidates" to shared LEGO Theory analytical laws.

Promote as SHARED ANALYTICAL LAWS, not mandatory schema fields:

1. REGIME_BOUND_CLAIMS
2. POLICY_BINDING_EVENT
3. EXPLICIT_AUTHORITY_PROPAGATION
4. PERSISTENCE_CLASS_SEPARATION
5. EFFECT_COMMIT_POINT
6. EFFECT_RECONCILIATION_ORACLE

Do NOT add AS01-AS18 as universal project-plan fields.

Reason:
the existing LEGO node/typed-edge model can represent them when activated. Mandatory fields would create ontology pressure on projects that do not need the lens.

## 13. Shared-kernel relationship

Several cross-domain findings reinforce laws already present in the Agent Architecture LEGO catalog:

Existing:
- intent_not_authority;
- task_not_execution;
- attempt_before_effect_when_durable;
- observation_not_semantic_success;
- unknown_external_outcome_is_first_class.

New cross-domain laws extend rather than replace them:

```text
intent_not_authority
  + EFFECT_COMMIT_POINT

observation_not_semantic_success
  + EFFECT_RECONCILIATION_ORACLE

unknown_external_outcome_is_first_class
  + POLICY_BINDING_EVENT
  + PERSISTENCE_CLASS_SEPARATION
```

The promotion target should therefore be LEGO Theory law text and reusable lens procedure, not schema expansion.

## 14. Ordivon architecture consequences

### Runtime / Host / Agent Service
- bind every consequential Job/effect to a regime identity;
- record policy generation/binding event;
- preserve exact effect identity across recovery;
- expose reconciliation instead of blind retry.

### Security
- retain AS01-AS18 as the rich security analysis vocabulary;
- consume Wave 2 information-flow rather than duplicating it.

### Artifact
- keep publication external to build acceptance;
- retain destination read-back as effect reconciliation.

### Market Capital
- continue separating read-only reality, non-live mechanics, demo/live endpoints, and production effect authority.

### Game
- preserve Order -> Preview -> Commit -> World authority split;
- do not let Provider choice become action authority.

### Connected Apps
- prefer staged/reversible states such as drafts when user intent calls for review;
- treat send/create/update/delete as provider effects with owner-native identities;
- model Trash separately from permanent deletion.

## 15. Result

Agent Security LEGO has now survived:
- six coding-agent products;
- five unrelated execution/effect domains.

The surviving abstraction is no longer "AI IDE security."

It is a general control/data/effect model for systems where:

```text
identity
+ trigger
+ scoped information
+ derivation
+ authority propagation
+ policy timing
+ persistence
+ commit boundary
+ observation
+ reconciliation
```

jointly determine what the system can actually do and what can later be proven about it.
