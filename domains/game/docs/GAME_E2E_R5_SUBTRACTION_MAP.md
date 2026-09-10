---
schema_version: 1
id: game.e2e.r5.subtraction-map
title: Ordivon Game E2E R5 — Semantic Subtraction Map
profile: engineering
lifecycle: active
source_role: migration-map
visibility: public
owners:
  - ordivon-game
updated: 2026-09-10
evidence_status: first-verdict-frozen
readiness: PARTIAL
---
# Game E2E R5 — Semantic Subtraction Map

## 0. Classification law

Classify by **semantic authority**, not file or directory name.

```text
KEEP   = irreducible Game/product/apparatus semantics
DERIVE = thin projection over existing Game authority
MOVE   = generic concern with a stronger external Ordivon/mature owner
SPLIT  = file/module mixes Game semantics with generic machinery
DELETE = allowed only after lossless substitution + dual-game replay
HISTORY = retained historical/regression evidence, no current authority promotion
```

No classification authorizes broad deletion by itself.

## 1. Current first-pass module map

| Surface | R5 disposition | Reason / target |
| --- | --- | --- |
| `research/core/*`, frozen GDF docs | KEEP | Game foundation/domain semantics and owner boundaries |
| `docs/GAME_DEVELOPMENT_CORE.md` | KEEP / DERIVED | D1–D8 responsibility projection; explicitly not services |
| `docs/GAME_PLAYER_EVIDENCE_PROGRAMME.md` | KEEP / DERIVED | Game claim/evidence ecology; research execution moves to Research E2E |
| `src/model.ts`, `src/world.ts`, `src/facts.ts`, `src/scenario.ts`, `src/scenario-cases.ts` | KEEP | authoritative Station Zero world/game semantics |
| `src/registry.ts` | KEEP | despite generic name, resolves Station Zero scenario/ruleset domain contracts |
| `src/station-zero-v3/*` | KEEP as PRODUCT/APPARATUS | exact Station Zero v3 world/planning/product semantics; do not generalize into platform |
| `web-v3/*`, product/player projections | KEEP as PRODUCT/APPARATUS | player-facing product evidence; not generic UI framework |
| `experiments/veilwild-r1/*` | HISTORY / REGRESSION | R1–R4 historical dogfood and falsification corpus |
| `src/host-contract/*` | MOVE → DELETE after substitution | duplicates generic Host task/context/decision/dispatch/observation/verification/outcome lifecycle |
| `src/build.ts` | SPLIT / MOVE | game build selection may remain local; generic build identity/provenance belongs Artifact/Engineering |
| `src/digest.ts` | MOVE where generic | generic hashing/canonicalization should not become Game semantic authority |
| `src/storage.ts` | SPLIT | Station Zero authoritative world history/recovery is Game-owned; generic SQLite durability/error/persistence mechanics are implementation/substrate |
| `src/replay/*` | SPLIT | Game world replay/diagnosis semantics remain; generic evidence/provenance graph mechanics move or stay implementation-local without semantic authority |
| `src/team/*` | SPLIT | Game faction/team planning semantics may remain; provider execution/session/orchestration belongs Runtime/Host/Provider owners |
| `src/deployment/*` | SPLIT / MOVE | Game deployment comparison/constraints may remain as domain projection; generic release/deployment lifecycle belongs Engineering/Distribution/Operations |
| `src/mission-control/*` | KEEP where player/product projection | product-facing experience/projection semantics; no second state authority |
| `src/casefile/*` | KEEP as APPARATUS | retained epistemic/game research treatment, not generic evidence platform |
| `src/comparison/*` | KEEP if Game-relative judgment | move only generic statistical/artifact mechanics if substitution exists |
| `.github/workflows/ci.yml` | MOVE-SEMANTICS | CI is Engineering infrastructure; repo may retain configuration without Game ownership |
| `test/*` | RECLASSIFY | game-specific oracles/failure fixtures KEEP; generic infra contract tests migrate with owner or become adapter tests |

## 2. `src/host-contract` first verdict

`src/host-contract/model.ts` currently defines generic objects including:

```text
TaskDescriptor
CompiledContextEnvelope
ModelInvocationIntent
ModelDecision
AdmittedDecision
DispatchEnvelope
ObservationEnvelope
VerificationReceipt
TaskOutcome
```

These are not Game semantics. They overlap current Host/Runtime responsibilities and are therefore the strongest first substitution target.

Migration rule:

```text
no direct delete
→ identify every current Game consumer
→ bind consumer to current Host/Runtime interface
→ replay exact current product + failure tests
→ quarantine old adapter
→ delete only after no action/judgment loss
```

## 3. `src/storage.ts` decomposition

The file currently mixes:

### Game-owned semantics

- Run identity tied to scenario/ruleset/world state;
- authoritative World command/event sequence;
- replay of exact Game rules;
- Game world invariant validation;
- world revision and mission status;
- Game-specific recovery consequence.

### Generic/implementation mechanics

- SQLite schema/materialization;
- WAL/busy/synchronous settings;
- generic storage error mapping;
- record hash-chain implementation;
- snapshot retention mechanics;
- file-system directory creation.

R5 does **not** move authoritative World history to Host/Runtime. It separates semantic ownership from persistence implementation.

## 4. `src/replay/*` decomposition

KEEP when replay answers a Game question such as:

- what Game world state existed at revision N?
- which player/game decision caused the outcome?
- did hidden information leak?
- which challenge/failure/recovery path occurred?

MOVE/implementation-only when the surface is merely:

- generic evidence graph transport;
- generic provenance identity;
- generic artifact retention;
- generic workflow/job reconstruction.

## 5. `src/team/*` decomposition

KEEP:

- faction/team planning semantics;
- Game-owned candidate/action admission;
- player-visible/sealed-information rules;
- deterministic low-cost policy semantics when they are gameplay behavior.

MOVE:

- model/provider session lifecycle;
- provider retry/recovery;
- generic execution records;
- generic task/session/context continuity.

A Provider or Agent does not own actor identity, Game state or task truth merely because it generated a plan.

## 6. Deletion admission rule

A generic Game-local module earns deletion only when all are true:

```text
1. exact replacement owner is current and observable;
2. all current consumers are enumerated;
3. no Game semantic authority is lost;
4. Station Zero replay passes;
5. Veilwild R4 failure replay still catches the historical class;
6. source/artifact/currentness identity remains exact;
7. response-loss/recovery behavior is not weakened;
8. independent destroyer fails to find a false green;
```

Until then the disposition is MOVE/SPLIT/QUARANTINE, not DELETE.


## 7. M6 current subtraction verdict

M6 supersedes the first-pass disposition for `src/host-contract/*`. The generic embedded Host workload/lifecycle implementation has now been physically removed from the current candidate after a derived-state experiment preserved the relevant Game judgments.

Current disposition:

```text
DELETE completed:
  host task/workload object model
  embedded Host authority state machine
  Host effect/dispatch/observation/verification duplication
  GameWorldExecutor compatibility executor
  Host protocol validation/store layer

KEEP as bounded implementation residual:
  LocalEvidenceJournal
  GameEvidencePort adapter
  DerivedTeamCommitmentView
```

The residual local journal is not a Host replacement and is not semantic authority. It remains because current Station Zero durability requires Game projection updates and retained local evidence to commit in one SQLite transaction. Full external substitution remains `NOT_ADMITTED` until another owner can preserve that invariant or a proven outbox/receiver topology replaces it without action or judgment loss.

Measured current generic-ish LOC is 552 versus 2,123 immediately before true subtraction (~74% reduction). The M6 full post-delete repository check is 386/386 PASS and the post-delete targeted boundary/recovery suite is 45/45 PASS. Veilwild final strict dynamic replay also passes after explicit import, while the cold no-cache failure remains detectable.

This satisfies deletion rules 2–7 for the retired duplicate lifecycle. Rule 1 is intentionally split: no external owner replaces the local atomic evidence carrier, so that carrier was **not** deleted. The duplicate Host lifecycle did not require such an external replacement because M6 proved it was derivable from existing Game-owned authoritative facts rather than an independent owner.
