# M5 plan — Station Zero first playable release

Status: implementation in progress; M5.0 and verified point-in-time World replay are complete
Tracking: Issues #1 and #7
Release target: `v0.1.0-alpha.1` source-playable developer Alpha

## 1. Release contract

M5 now optimizes for one exact player loop rather than treating every research question as a release blocker:

```text
deploy
→ play one bounded Station Zero mission
→ reach a verified terminal outcome
→ replay any retained revision
→ inspect evidence-linked diagnosis
→ clone and change one deployment input
→ run again
→ compare compatible Runs
→ verify the exact source release from a clean directory
```

The default release journey uses Fixture cognition. Codex and Hermes remain optional live Providers and receive release-candidate compatibility dogfood, but their installation, network access, output variance, or cost cannot determine whether the deterministic source release is playable.

## 2. Critical path

```text
R0 release contract and issue graph                   complete in first implementation PR
 ↓
R1 derived Run Evidence Graph + Replay Frames
 ├───────────────┐
 ↓               ↓
R2 curves, key turns, diagnosis   R3 deployment manifests, profiles, comparison
 └───────────────┬────────────────┘
                 ↓
R4 Replay / Diagnosis / Compare Web + Chromium E2E
                 ↓
R5 release archive, clean verification, tag, closeout
```

R2 and R3 may proceed in parallel only after R1 types and API contracts are merged. Every other stage remains sequential to avoid projection drift and false release evidence.

## 3. Completed entry contracts

### M5.0

Implemented:

- deterministic Scenario Cases and Genesis digests;
- truthful package/evaluated-input identity;
- backend product catalog;
- legacy Run migration;
- true World-revision timeline paging;
- timestamp metadata separated from authority order.

### Point-in-time replay

Implemented:

- exact `stateAtRevision()` from retained Snapshots, Commands, and Events;
- Snapshot-as-cache semantics;
- full sequence/hash/digest verification;
- read-only `/api/replay/state`;
- complete Genesis-to-terminal reconstruction tests.

## 4. R1 — Evidence Graph and Replay Frames

### Goal

Join retained World, Team, player-control, Message, authority, Context, Provider, Effect, Dispatch, Observation, and Verification evidence in one deterministic read-only projection. Do not persist a second graph authority.

### Files

```text
src/replay/model.ts
src/replay/evidence.ts
src/replay/frames.ts
src/server.ts
test/replay-graph.test.ts
```

### Deliverables

- typed `RunEvidenceGraph`;
- stable evidence node/edge identities;
- graph digest independent of timestamps and query order;
- one bounded `ReplayFrame` per World revision;
- summary, paged frames, and single-frame APIs;
- fail-closed dangling required identity handling;
- zero semantic writes from reads.

### Exit gate

- every revision has an exact Frame whose World digest equals `stateAtRevision()`;
- every edge references an existing node;
- repeated graph/frame reads append zero World, Host, Team, Artifact, or player records;
- revision paging is gap-free and duplicate-free;
- one Frame is <=64 KiB, with raw Context/Artifact bodies left behind explicit detail APIs.

## 5. R2 — Curves, key turns, and diagnosis

### Goal

Turn replay into deterministic explanation without model-generated causes.

### Evidence classes

```text
VERIFIED_DIRECT
VERIFIED_CONTRIBUTOR
COUNTERFACTUAL_SENSITIVE
CONTEXT_ONLY
```

Every non-context statement references retained evidence IDs. A contributor is never presented as the unique cause. Counterfactual statements are bounded deterministic sensitivity tests, not statistical or philosophical causality.

### Deliverables

- battery, oxygen, heat, Actor/crew health, system, item, and Objective curves;
- deterministic key turns;
- terminal/victory explainers;
- contributor rules for resource ownership, communication delay, waiting, authority, redundant work, and Provider failure;
- bounded one-step legal-alternative sensitivity;
- diagnosis and summary APIs.

### Exit gate

- known victory and failure traces produce evidence-linked explanations;
- curves contain exactly one point per World revision;
- key turns are deterministic and bounded to 12;
- evaluation timeout is never diagnosed as a Game mission failure;
- no model call is required.

## 6. R3 — Immutable deployment and comparison

### Goal

Create the verified failure/change/re-run/compare loop while conserving finite World resources.

### Deliverables

- immutable content-addressed deployment manifest;
- Scenario Case, loadout, Provider order, authority mode, coordination profile, evaluated-input digest;
- bounded typed loadout/coordination profiles only when measurement proves a trade-off;
- exact same-Case comparison;
- descriptive-only cross-Case comparison;
- one deterministic configuration change that converts failure to victory or materially improves a verified outcome.

### Exit gate

- manifest cannot mutate after cognition or World execution begins;
- every profile conserves item totals;
- restart restores the exact manifest;
- incompatible ruleset comparisons fail closed;
- missing Provider cost/token data remains `null`/unknown;
- two retained Runs compare through one pure API.

## 7. R4 — Player Web and Chromium release journey

### Goal

Expose Replay, Diagnosis, Compare, and redeployment through the existing dependency-free player Web.

### Product navigation

```text
Mission
Replay
Diagnosis
Compare
Deploy Again
```

### Deliverables

- revision scrubber and key-turn navigation;
- station state at selected revision;
- plain SVG curves;
- proposals, admitted intents, verified facts, authority, player, Message, and Provider evidence;
- diagnosis evidence-class labels;
- compatible Run comparison and clone-deployment action;
- Provider preflight and readable fail-closed errors;
- Playwright as a dev-only dependency;
- one real Chromium journey using Fixture cognition and persisted SQLite.

### Browser gate

```text
open deployment
→ start baseline Run
→ perform one player intervention
→ reach terminal
→ open Replay and select an earlier revision
→ inspect Diagnosis
→ clone deployment and change one profile
→ complete second Run
→ compare input and outcome differences
→ reload and restore the same Run
```

## 8. R5 — Exact release artifact and closeout

### Version

`v0.1.0-alpha.1`

### Required artifacts

```text
ordivon-game-station-zero-v0.1.0-alpha.1.tar.gz
SHA256SUMS
docs/M5-EVALUATION.json
docs/M5-RELEASE.json
docs/M5-RECEIPT.md
evaluated-inputs.json
```

### Verification

The archive is unpacked into a fresh directory and must pass:

```text
pnpm install --frozen-lockfile
pnpm check
pnpm e2e
pnpm receipt
pnpm measure
pnpm release:verify
```

The release workflow builds and verifies the same bytes it uploads. Commit/tree metadata and optional GitHub attestations are additional provenance, not the sole release identity.

### Closeout

- merge release PR;
- verify post-merge `main` CI;
- create tag;
- verify tag release CI;
- download and reverify uploaded archive;
- close #7 and #1;
- delete release branch and Workspaces.

## 9. Unified gates

Every implementation PR must pass:

```text
pnpm typecheck
pnpm webcheck
pnpm coverage
pnpm receipt
pnpm measure
pnpm release:inputs
git diff --check
```

Coverage remains at least 95% lines, 90% branches, and 95% functions. Runtime dependency count remains zero.

## 10. Explicit post-alpha work

These remain valuable but do not block `v0.1.0-alpha.1`:

- #40 equal-budget single-Agent/multi-Agent ablations;
- Runtime experiment-cell execution and <=16-cell matrix;
- #39/#41 final embedded Host convergence and compatibility deletion;
- general Hermes structured-output repair/fallback;
- additional Scenarios, second game, hosting, accounts, multiplayer, 3D, modding, or a generic game platform.

Any later claim that multi-Agent architecture is superior must complete #40 first. Any second game or platform extraction must complete Host convergence first.

## 11. Stop conditions

Stop and revisit design when:

- Evidence Graph starts requiring synchronized truth tables or recovery ownership;
- diagnosis requires a model to invent or upgrade causality;
- profiles grow into a generic configuration DSL;
- Web framework migration becomes larger than the player value it unlocks;
- release verification depends on undeclared global tools, caches, credentials, or retained local databases;
- Host convergence and release would require simultaneous authority migration.
