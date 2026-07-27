# M3 implementation plan

> **Superseded historical plan.** Do not implement PR1–PR7 from this document. The cross-stack correction in [`M30-DESIGN.md`](M30-DESIGN.md) and revised sequence in [`M30-PLAN.md`](M30-PLAN.md) replace this plan.

Issue: #5 — multi-Agent team, communication, and authority
Design: [`M3-DESIGN.md`](M3-DESIGN.md)

## Strategy

Implement M3 as seven reviewable PRs. Preserve Scenario v1, Ruleset v1/v2, the single-Agent M2 facade, all frozen receipts, and the 95/90/95 coverage gates throughout.

The sequence intentionally builds deterministic team semantics before live multi-model evaluation.

## PR1 — Generalize Host identity and Team projections

### Scope

- remove `engineer-01` literal types from Goal, Task, Attempt, Effect, and Context contracts;
- add Team Goal, Agent Profile, Team Task, Task Edge, Wait Record, and Team Projection types;
- add M3 projection tables and independent Host Journal events;
- keep `AgentHost` as a backward-compatible one-actor facade over generalized storage;
- define Team configuration and provider mapping per actor;
- no World rule changes and no new Provider calls.

### Acceptance

- old single-Agent fixture and receipts remain byte-stable;
- three Profiles can persist in one Run without identity collision;
- multiple Tasks and Attempts survive a fresh process;
- invalid Task cycles, duplicate actor IDs, and incompatible assignments fail closed;
- one Agent can be marked waiting while another Task remains ready.

## PR2 — Scenario v2 specialists and Ruleset v3

### Scope

- register `station-zero@2` and `station-zero-core@3`;
- add Engineer, Medic, and Security World actors;
- add `security-post`;
- add `treat_agent` and `contain_hazard` Commands;
- add hazard containment state and battery cost;
- make breach control an OR success condition;
- generalize environmental damage across Agents;
- make individual incapacitation non-terminal and full Team incapacitation terminal;
- add Facts and Verification for treatment, containment, and specialist incapacitation.

### Acceptance

- each specialist has an exclusive capability;
- wrong-specialist Commands reject atomically;
- Engineer seal and Security containment both satisfy breach control;
- containment and sealing produce different resource/event traces;
- one Agent may become incapacitated while other legal actions remain;
- Scenario v1 and Ruleset v2 digests remain unchanged.

## PR3 — Actor-scoped Observation and typed communication

### Scope

- add Observation Policies for Engineer, Medic, and Security;
- compile `AgentContext v3` per actor under the 16 KiB limit;
- add Team Message schema, persistence, Host events, and delivery engine;
- implement local and station-radio channels;
- enforce one message per actor per round, 512-byte payload, eight-message Context tail, and four-Tick TTL;
- expose delivered immutable Fact/Artifact references, not shared transcripts;
- add deterministic Fixture communication policies.

### Acceptance

- each actor receives materially different Context from the same World revision;
- private or undelivered information is absent;
- same-room local delivery succeeds while remote radio is unavailable;
- queued messages deliver after communications restoration or expire deterministically;
- communication connectivity changes at least one deterministic Team outcome;
- Context size remains bounded at every evaluated state.

## PR4 — Team Task DAG and authority

### Scope

- implement deterministic Team Task compiler and AND/OR dependency validation;
- add claimable Task frontier by capability;
- add Authority Level lattice and Operation requirements;
- add player-configured `autoApproveThrough` per actor;
- persist Authority Requests and single-use Grants;
- bind Grants to proposal, Context, World digest, and expiry;
- add `awaiting_authority`, `blocked_dependency`, and related Wait Records;
- add approval/denial engineering APIs.

### Acceptance

- Task cycles and impossible capability assignments fail closed;
- breach control exposes Engineer and Security alternative Tasks;
- restricted containment waits under a lower threshold;
- unrelated Tasks continue while approval is pending;
- approved proposal executes once;
- denied or stale Grant cannot authorize a Dispatch;
- changing player threshold changes the admitted plan.

## PR5 — Proposals, conflict graph, and interleavable Skills

### Scope

- retain Agent Proposals separately from Decisions;
- compile deterministic Resource Claims;
- build typed Proposal conflict graph;
- implement public priority tuple and deterministic maximal independent set;
- persist conflict sets and waiting evidence;
- replace exact linear revision Skill freshness with Plan Dependency Sets;
- allow unrelated World changes between Skill steps;
- force replan on relevant target, resource, route, Task, or authority drift;
- implement fair one-command-per-Tick Team Scheduler.

### Acceptance

- duplicate and opposite target proposals conflict explicitly;
- unrelated Medic and Engineer proposals are admitted together;
- loser waits with blocker evidence and later resumes or becomes unnecessary;
- unrelated interleaving does not stale a Skill;
- relevant resource consumption forces replan;
- no actor monopolizes more than two consecutive steps when another ready non-conflicting Attempt exists;
- no multi-intent World mutation is introduced.

## PR6 — Persistent Team Host and control APIs

### Scope

- add TeamHost initialize, round, step, and bounded run loop;
- allow up to three bounded concurrent Provider calls per Coordination Round;
- persist all Decisions before conflict resolution;
- integrate message delivery, Task refresh, authority, conflicts, scheduler, execution, and verification;
- add Team state, Task, Message, conflict, and authority APIs;
- extend engineering browser panel with specialist cards, waiting reasons, messages, and approvals;
- add interruption fault points across round, message, authority, conflict, and interleaved execution boundaries.

### Acceptance

- one specialist progresses while another waits for authority or communication;
- fresh process resumes unresolved rounds, queued Messages, Grants, conflicts, and active Attempts;
- after-World-commit interruption creates no duplicate effect;
- one Provider may fail without erasing other specialists' progress;
- TeamHost remains bounded and reaches terminal/blocked/step-budget state synchronously;
- M2 single-Agent APIs remain functional.

## PR7 — Evaluation, receipt, and Issue #5 closeout

### Scope

- deterministic Team Fixture baseline;
- alternative breach-plan comparison;
- connected/disconnected communication comparison;
- authority auto-approve/deny comparison;
- one-specialist-incapacitation run;
- live all-Codex and mixed Codex/Hermes Team runs;
- mid-run Provider replacement;
- normalized machine-readable evidence and M3 receipt;
- exact clean-main acceptance;
- update Program Issue and M4 entry contract.

### Acceptance

- at least two different valid plans reach verified victory on the same seed;
- restricted action requires authority in the evidence trace;
- communication limits materially change coordination or outcome;
- one Agent progresses while another waits or fails;
- all World Effects remain unique and replay exact;
- Host Journal verifies Task, Message, authority, conflict, and wait evidence;
- no hidden manager model or Fixture correction changes valid live Decisions;
- Issue #5 closes only after merged-main clean acceptance.

## Cross-cutting gates

Every PR must run:

```text
pnpm install --frozen-lockfile
pnpm check
pnpm receipt
pnpm measure
```

Additional M3 gates:

- Scenario v1 and M2/M2.1 evidence tests remain green;
- Scenario v2 Team evidence has deterministic digests;
- new source remains above global 95% lines, 90% branches, 95% functions;
- Contexts remain at or below 16 KiB;
- Message payloads remain at or below 512 bytes;
- conflict resolver output is deterministic under input permutation;
- authority Grants are single-use and stale-sensitive;
- no background scheduler is introduced;
- runtime dependencies remain zero unless a concrete measured need justifies one.

## Recommended execution order

```text
PR1 identity/storage
  ↓
PR2 specialist World
  ↓
PR3 observation/communication
  ↓
PR4 Task DAG/authority
  ↓
PR5 conflict/interleaving
  ↓
PR6 TeamHost/API/recovery
  ↓
PR7 live evaluation/receipt
```

PR3 and PR4 may be developed in parallel after PR2 contracts freeze, but PR5 must consume both final schemas.

## Main risks

### R1 — Over-modeling communication

Mitigation: two channels, eight message kinds, one message per round, no general dialogue runtime.

### R2 — Hidden central planning

Mitigation: deterministic Task compiler and conflict resolver expose semantics but never replace a valid Provider choice.

### R3 — Interleaving invalidates M2 Skill assumptions

Mitigation: implement Plan Dependency Sets before TeamHost execution; never weaken stale checks globally.

### R4 — Authority becomes UI-only decoration

Mitigation: admission requires a bound Grant and evaluation compares approval configurations.

### R5 — Specialist loss creates implicit instant failure

Mitigation: individual incapacitation is non-terminal; remaining work proceeds until ordinary terminal rules resolve the mission.

### R6 — Multi-Agent costs expand uncontrollably

Mitigation: maximum three Provider calls per round, bounded Contexts/messages, deterministic Fixtures first, and live evaluation only after recovery gates pass.

### R7 — Same-Tick simultaneity pressure

Mitigation: preserve serial World commits in M3. Reconsider true multi-intent Tick only after M3 measurements demonstrate a gameplay requirement that interleaving cannot satisfy.
