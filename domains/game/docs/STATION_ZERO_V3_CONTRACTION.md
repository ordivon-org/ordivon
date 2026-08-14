---
schema_version: 1
id: game.station-zero-v3.contraction
title: Station Zero v3 — Contraction and Reopen Record
type: decision
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - builder
  - agent
updated: 2026-08-15
summary: Compact owner-local record of structures deliberately removed, retained below the semantic waist, or left as outer potential after the cross-project contraction round. It preserves negative knowledge and reopen conditions without duplicating Computing's cross-project research.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.authority
  - game.product.station-zero-v3
  - game.development-model
---
# Station Zero v3 — Contraction and Reopen Record

## Boundary

This document owns only **Game-local contraction decisions and reopen conditions**.

The cross-project theory that motivated the round belongs to Ordivon Computing. The revision-bound reference study is `ordivon-computing/studies/2026-cross-project-convergence/README.md`, first integrated at Computing commit `81b1d124973cf5b1023b22629fc9588d263bca51`.

Game keeps the consumed result, not a second copy of the theory.

The governing shape is:

```text
CORE
  thin + hard
  only non-bypassable Game truth/consequence/recovery responsibilities

OUTER
  high potential
  experiments, Providers, content grammar, production tools, future mechanics
  replaceable / removable / reopenable
```

Code size is not the criterion. A large lower-level implementation may remain outside the semantic core when it has a real owner-local job. A tiny field may be removed when no current consequence consumes it.

---

## Hard Game core

Current v3 core responsibility is intentionally narrow:

```text
Authoritative World
→ bounded Faction Knowledge
→ legal Candidate / Intent admission
→ Commander Order
→ sealed Plan Preview
→ explicit Commit
→ canonical simultaneous Turn Batch
→ deterministic World consequence
→ retained Turn Receipt / replay evidence
→ exact recovery / re-observation
→ bounded player Aftermath
```

These relations protect real inequalities:

```text
knowledge ≠ hidden World truth
proposal ≠ legal action
Preview ≠ Commit
Commit ≠ consequence
process return ≠ retained Turn evidence
retained evidence ≠ invented semantic success
```

Further contraction must preserve those inequalities or prove a smaller invariant protects the same product value.

---

## GC1 — dormant research surfaces: removed

Removed from current v3:

- `resource-egress.ts`;
- `message-issuance.ts`;
- `entity-departure.ts`;
- optional `agent-action-admission.ts` machinery;
- their dedicated tests and public exports.

Reason:

```text
implemented + tested
but no current PlayService/API/browser/product consumer
```

The three cross-World modules had already been identified as zero-current-consumer future primitives in historical commit `22aa1ac` (`game: purge zero-causal Station Zero surface`). Later lineage reconciliation reintroduced them without a new playable consumer. GC1 restored the owner-local decision after revalidating the current graph.

### Reopen condition

Reopen only when a **current playable Game consumer** requires the capability and a simpler ordinary World/Turn fact cannot represent it. Historical or hypothetical multi-World usefulness is not sufficient.

---

## GC2 — duplicate v3 Embedded Host semantics: removed

The v3-local Host transcript and semantic aliases were removed from Planning/Turn execution:

```text
taskId
goalId
effectId
dispatchId
```

They were deterministic aliases of Game-owned Run/Planning/Turn identities and had no independent owner or consequence.

Retained Game evidence is enough:

```text
runId
planningId
turnBatchId
World Event
Turn Record
Turn Receipt
state / record digests
```

Response-loss recovery still re-observes the original Turn identity and never redelivers an uncertain Turn under a fresh identity.

Four legacy SQLite compatibility columns remain physically present in the unregistered v3 schema because introducing a migration framework solely to delete dead columns would cost more than it clarifies. They have no semantic role.

### Reopen condition

Reopen Host-like semantic state only if Game acquires a real cross-session/cross-executor semantic-work continuity problem that cannot be represented by current Game Planning/Turn evidence. Do not reopen merely because Host exists elsewhere in Ordivon.

---

## GC3 — DeepSeek multi-credential machinery: outer, retained locally

`deepseek-provider.ts` and `deepseek-credentials.ts` are **not Game product meaning**, but the current local implementation has a real equipment responsibility:

- hot credential discovery/reload;
- weighted credential selection;
- per-credential concurrency;
- 429 cooldown;
- 401 quarantine;
- retry/pool evidence.

Harness Provider continuity and Workstation credential/network authority do not currently own this exact multi-credential pool semantics. No second materially different consumer requires a shared extraction.

Decision:

```text
KEEP LOCAL BELOW SEMANTIC WAIST
```

### Reopen condition

Extract only when a second real consumer reproduces the same responsibility or maintenance friction proves a lower owner would reduce total system cost.

---

## GC4 — `agent-planning.ts`: outer implementation, no evidence-based split

The file is physically large, but change history did not show stable false coupling among Candidate generation, Context/decision admission, fixture policy, Commander Order/catalog, and Plan assembly.

Decision:

```text
KEEP CO-LOCATED
```

Physical line count is not an architecture boundary.

### Reopen condition

Split only after repeated G5 production changes show that one planning responsibility cannot evolve without unrelated source/test blast radius.

---

## GC5 — contraction retained only after product/recovery equivalence

The accepted GC1/GC2 contraction retained the current product evidence:

```text
repository suite:        PASS
registered v2 E2E:      PASS
v3 20-Turn E2E:         PASS
G3 strategy signatures: unchanged
G4 calibration:         PASS
Product Value:          PASS
live Provider boundary: verified
```

The exact historical receipts live in Git/Host evidence. This document does not duplicate their full metric tables.

---

## GC6 — design history leaves runtime core

The former `StationZeroP0Contract` mixed executable facts with design derivation:

```text
runtime-relevant:
  encounter Turn budget

non-runtime design history:
  product form prose
  player / Agent responsibility prose
  genre influence lists
  retained / rejected mechanic lists
  route/meta deferral declarations
  non-goals
```

No external repository consumed that runtime object. Current Game runtime read only the Turn limit.

GC6 therefore removes `StationZeroP0Contract` and `StationZeroDesignInfluence` from `src/` and retains only:

```text
STATION_ZERO_V3_TURN_LIMIT = 20
```

alongside the already authoritative scenario/ruleset/phase constants.

Product form, design influences, responsibilities, non-goals, and future possibilities remain in `STATION_ZERO_V3_PRODUCT.md` and `STATION_ZERO_V3_P0.md`, where they can evolve without pretending to be executable World state.

### Reopen condition

Promote a design field back into runtime only when current executable behavior consumes it and a simpler constant/type cannot preserve the required invariant.

### GC6 acceptance

The thinner core retained current product and outer-capability value:

```text
repository suite:             296 / 296 PASS
registered v2 browser E2E:   PASS
v3 20-Turn browser E2E:      PASS; worldRevision 20; browserErrors []
G3 strategy matrix:           Rescue 3/6; Core 1/6; Hive 6/6; Pareto 8; signatures 3
G4 calibration:               25 / 25 PASS; 0 critical/major failures
Product Value:                PASS; retained contextual/control/information/pressure/identity results
live Provider preflight:      3 / 3 bounded Runs verified
live Provider calls:          15 / 15 successful; 0 retries; 0 hidden references
Provider latency p50 / p95:   1494 / 1725 ms
Preview latency p50 / p95:    1635 / 1777 ms
```

The acceptance claim is deliberately narrow: removing research/design metadata did not change current Game consequence, recovery, product behavior, or live Agent realization.

---

## Negative-knowledge fence

A removed region is not a constitutional ban. It is a compact burden-of-proof record:

```text
region
reason
historical/current evidence
reopen condition
```

Current hard negative regions:

| Region | Current reason | Reopen condition |
|---|---|---|
| Resource Egress | no playable consumer | current cross-World gameplay requires it |
| Message Issuance | no playable consumer | current cross-World gameplay requires it |
| Entity Departure | no playable consumer | current cross-World gameplay requires it |
| optional Agent Action Admission | no production caller | current subject/cognition provenance failure appears |
| v3 Embedded Host transcript | duplicates Game Turn evidence | real semantic-work continuity exceeds Game evidence |
| P0 design-history runtime object | runtime consumed only Turn limit | executable behavior requires a promoted field |

The regression test protects only silent resurrection. A deliberate future reopen updates the decision and the fence together.

---

## Outer potential remains intentionally broad

G5-P2 has promoted one exact topology treatment, `junction-bottleneck`, into a durable Scenario Case without changing the hard core. That admission does **not** promote topology mutation machinery: the exact Case is content; the wider topology search space remains outer.

None of the contractions prohibit future exploration of:

- additional topology/choke geometry;
- enemy doctrine/objective packages;
- alternate systemic pressure profiles;
- new specialist loadouts;
- additional Providers or model families;
- richer expression/media production;
- later multi-encounter structure;
- later cross-World mechanics;
- later social/character systems.

Those are **outer hypotheses**, not current core obligations.

The admission rule is:

```text
outer experiment
→ current consequence evidence
→ smallest owner-local mechanism
→ only then consider promotion
```

This preserves high potential without making the core pay permanent complexity tax for every plausible future.

---

## Stop rule

Contraction stops when the remaining structure has:

1. a named Game responsibility;
2. a current consumer;
3. a relevant failure if removed;
4. a smaller semantic surface than the mechanism it replaced;
5. no cheaper existing owner that preserves the same truth.

At that boundary, further deletion is not simplicity; it is loss of product truth.

The current v3 architecture satisfies that stop rule closely enough to resume bounded G5 Content Grammar research from a thinner core.
