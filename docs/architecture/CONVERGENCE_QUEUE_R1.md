# ADR — Multi-Agent Convergence Queue R1

Date: 2026-09-22

Status: **REMOTE CUTOVER ACCEPTED / GITHUB MERGE QUEUE CANONICAL FOR MAIN CONVERGENCE**

Base revision: `ab91b17aac661621425a72f171df7c812d5c6a30`

## 1. Decision

Ordivon will not build a private full merge-queue service.

R1 adopts the following ownership split:

```text
Git / GitHub
  owns candidate commits, synthetic merge-group commits, branch history and final queue publication

Ordivon repository mechanics
  owns deterministic owner/scope/dependency projections used to plan verification

Runtime / CI
  own mechanical execution evidence

Harness
  owns exact run/tool/source admission where applicable

Domain / Study owners
  own semantic acceptance

Host
  owns long-lived semantic continuity only when a convergence activity needs it
```

The intended architecture is therefore:

```text
parallel Agent workspaces
        |
        v
committed candidate revisions
        |
        v
Ordivon convergence projection
  changed paths
  -> direct owners
  -> conservative declared-seam closure
  -> verification scopes/tasks
        |
        v
provider merge queue / speculative checks
        |
        v
exact synthetic tree qualification
        |
        v
serialized canonical publication
        |
        v
main
```

R1 deliberately does **not** claim that the current owner/dependency projection proves semantic independence. Its machine-readable output says:

```text
independenceClaim = NOT_ESTABLISHED_BY_THIS_PROJECTION
```

## 2. External mature mechanisms

### GitHub Merge Queue — ADOPT as preferred publication substrate

The repository is hosted at `github.com:ordivon-org/ordivon`. GitHub Merge Queue already owns the mechanism Ordivon should not rebuild:

- ordered queued pull requests;
- synthetic `merge_group` revisions;
- required-check execution on the exact merge-group SHA;
- build-concurrency control;
- minimum/maximum merge-group size;
- status-check timeouts;
- final publication to the protected branch.

R1 now uses GitHub Merge Queue as the canonical remote-main convergence substrate. Repository ruleset main-convergence-queue-r1 (id 23819262) requires root-verification, enables merge_group qualification, and rejects non-fast-forward updates.

### GitLab Merge Trains — REJECT for this repository

Merge trains provide the right cumulative-validation model, but require a GitLab-hosted repository. They are not selected for a GitHub canonical repository.

### Zuul dependent pipeline — ADAPT mechanisms, do not operate Zuul yet

Zuul has the strongest mature model for dependency queues and speculative execution. Two mechanisms are retained as design references:

1. dependent queues that test future cumulative states in parallel;
2. TCP-like adaptive speculation windows: grow on success, shrink aggressively on failure.

Running a separate Zuul control plane is not justified while GitHub can own the final merge queue and Ordivon already owns repository/domain boundaries.

### Mergify / comparable smart queues — ADAPT mechanisms, no SaaS dependency yet

The useful mechanisms are:

- scope-aware parallel queues;
- dynamic batching;
- batch-failure splitting/bisection;
- two-step CI.

These become pressure-test patterns. A SaaS queue is activated only if measured GitHub-native throughput/cost is inadequate.

### Uber SubmitQueue research — DEFER predictive scheduling

Predicting build duration and limiting speculative work is justified at large monorepo scale. Ordivon R1 does not have enough clean convergence-history data to justify an ML/predictive scheduler. R1 must first record queue latency, invalidation, replay and verification-cost observations.

## 3. Queueing model

The system is not one queue. It contains four logical queues:

```text
Candidate Admission
        |
        v
Speculation / Verification
        |
        v
Promotion
        |
        v
serialized publish -> main

stale / failed / superseded
        |
        v
Reconciliation
        |
        +----> admission
```

The stability condition is operationally simple:

```text
long-run candidate arrival rate must not exceed sustainable convergence service rate
```

Little's Law is used only as an observation relation for stable periods:

```text
average WIP ~= arrival rate * average convergence latency
```

It is not a scheduling policy.

## 4. R1 LEGO graph

The machine-readable graph is:

`docs/architecture/convergence-queue-lego-r1.json`

Atomic responsibilities:

| id | kind | responsibility | natural authority |
|---|---|---|---|
| Q01 | SOURCE_TRIGGER | admit an immutable committed candidate | Git / Runtime Workspace |
| Q02 | TRANSFORM | derive exact source delta | Git |
| Q03 | TRANSFORM | project changed paths to direct owners | `owners.toml` |
| Q04 | TRANSFORM | project declared owner interaction closure | `dependency_contracts.toml` |
| Q05 | TRANSFORM | estimate verification cost | derived metrics; deferred R2 |
| Q06 | TRANSFORM | estimate conflict/failure risk | derived metrics; deferred R2 |
| Q07 | DECISION_ROUTER | apply admission/backpressure | queue provider / future scheduler |
| Q08 | DECISION_ROUTER | order candidates with fairness/age constraints | queue provider |
| Q09 | DECISION_ROUTER | choose speculative window | queue provider |
| Q10 | TRANSFORM | construct immutable future source cut | Git/provider |
| Q11 | TRANSFORM | compile verification plan | Ordivon projection |
| Q12 | EFFECT_EXECUTOR | execute checks | CI / Runtime |
| Q13 | VERIFIER_OBSERVER | verify mechanical checks | CI / Harness |
| Q14 | VERIFIER_OBSERVER | verify semantic outcome when required | Domain / Study |
| Q15 | RECONCILER | detect base/main drift | Git |
| Q16 | RECONCILER | invalidate dependent speculation | queue provider |
| Q17 | RECONCILER | replay intent on current main | Agent + Git Workspace |
| Q18 | RECONCILER | isolate failing batch/candidate | queue provider |
| Q19 | VERIFIER_OBSERVER | prove exact tree qualified for landing | queue provider + required checks |
| Q20 | EFFECT_EXECUTOR | publish canonical main transition | Git/GitHub or local CAS fallback |
| Q21 | VERIFIER_OBSERVER | read back final ref/tree | Git |
| Q22 | PROJECTION_SINK | expose latency/WIP/replay/invalidation metrics | rebuildable telemetry |

## 5. R1 implementation

R1 adds:

```text
tools/repo/convergence_plan.py
tools/repo/test_convergence_plan.py
```

The projection emits:

```text
baseRevision
headRevision
headTree
changedPaths
directOwners
verificationOwners
verifyTasks
queueVerifyTasks
scopeIds
crossCutting
ownerManifestDigest
dependencyContractDigest
```

Truth role:

```text
repository-convergence-projection-not-merge-or-domain-authority
```

### Conservative seam closure

`dependency_contracts.toml` preserves directional dependency policy.

The convergence projection intentionally treats those declared seams as an **undirected interaction graph** for verification planning. This can over-test but must not silently under-test based on an inferred direction.

Capital R2 adds a genuine public-package dependency on the Composition owner. Therefore Composition-connected changes may expand verification to Capital; this is intentional dependency truth rather than an optimization hint, and must not be removed merely to reduce CI fanout.

Examples on the current graph:

```text
runtime
  -> owner-component:runtime

security
  -> owner-component:harness+next+security+skills+web

media
  -> owner-component:artifact+distribution+game+media+workstation
```

A cross-cutting repository-mechanics change projects to all owners.

Absence of a declared edge is not promoted into a semantic-independence claim.

### Queue-portable verification vs. full owner acceptance

`verifyTasks` retains each owner's full verification contract. `queueVerifyTasks` is the mechanically portable gate executed on GitHub synthetic trees; it defaults to the full owner task and may narrow only environment-bound checks that cannot run on the queue provider. A queue PASS therefore proves the exact synthetic tree passed its admitted mechanical gate; it does not replace Domain/Study semantic acceptance or machine-bound owner acceptance.

R1.2 keeps two explicit provider-portability overrides, each narrower than the full owner contract. Next now uses its full `next:verify` task in the queue because the Browser Security cases are source-bound through the Harness locked environment. `harness:queue` omits only the physical realization probe for the Runtime target's exact `/bin/bash`, `/usr/bin/awk`, and `/usr/bin/rg` paths; source-level executable-contract tests remain. `artifact:queue` retains Artifact's portable unit/semantic suite and Ruff gate while excluding only node-local binding assertions that require exact workstation FreeCAD/OCCT/warcio/skopeo/sndfile or pinned local Python/Node materialization. All omitted checks remain in the corresponding full owner verify tasks.

## 6. GitHub queue compatibility

`.github/workflows/ci.yml` now accepts:

```yaml
merge_group:
  branches: [main]
  types: [checks_requested]
```

For a merge-group event, owner selection uses the exact:

```text
github.event.merge_group.base_sha
github.event.merge_group.head_sha
```

The workflow also emits a convergence projection into the GitHub job summary.

Queue runs are not canceled by the workflow's normal `cancel-in-progress` behavior.

R1 does **not**:

- enable the GitHub repository merge-queue ruleset;
- change branch-protection policy;
- enqueue existing branches;
- auto-open pull requests;
- replace `integrate-main.sh`;
- assert GitHub is currently the only publication path.

## 7. Existing local publication path

`tools/repo/migration/integrate-main.sh` remains the local/offline exact publication fallback:

```text
clean primary
+ integration flock
+ EXPECTED_MAIN fence
+ merge-tree qualification
+ late stale-ref fence
+ exact merge
+ post-readback
```

When GitHub Merge Queue becomes canonical, this script should remain recovery/local tooling rather than compete as a second normal queue authority.

## 8. Scheduling policy — deliberately not frozen in R1

R1 does not choose FIFO, SRPT, static priority, ML ranking or a custom scalar score.

Any later scheduler must preserve:

```text
dependency ordering
+ bounded starvation
+ candidate age
+ verification cost
+ failure/invalidation risk
+ available CI capacity
```

Pure SRPT is rejected as a default because it can starve expensive long-running convergence work.

A Zuul-style adaptive speculation window is the preferred first control-law experiment after telemetry exists:

```text
success -> additive/slow increase
failure -> multiplicative/fast decrease
floor <= active speculation <= ceiling
```

This is preferred before predictive ML because it is transparent, mature and needs much less data.

## 9. Graduation gates

Remote merge-queue cutover is not accepted until all are true:

1. `merge_group` workflow validates locally and in one real queue-created synthetic ref;
2. exact base/head projection is deterministic;
3. required checks are attached to the merge-group SHA;
4. stale/canceled merge groups do not produce publish claims;
5. owner/domain semantic gates remain outside GitHub's authority;
6. current branch rules are captured before mutation and independently read back after mutation;
7. a rollback path to the current local CAS integration process is retained;
8. at least one concurrent multi-Agent wave is replayed through the queue without broken main.

Advanced scheduling features require measured pressure:

- adaptive speculation window: queue contention or meaningful CI waste;
- batching/bisection: repeated high queue depth plus nontrivial per-build fixed cost;
- cost prediction: enough clean historical runs to validate prediction error;
- external smart-queue SaaS: GitHub-native queue demonstrably fails throughput/cost requirements.

## 10. R1 acceptance

Targeted current-main verification on 2026-09-22:

```text
affected-owner tests        18/18 PASS
convergence-plan tests       6/6 PASS
integrate-main smoke         PASS
GitHub workflow actionlint   PASS
git diff --check             PASS
```

The original checks proved only the R1 projection and queue-compatible carrier. Remote cutover was subsequently proven on 2026-09-22:

    ruleset                         main-convergence-queue-r1 / active
    first real merge_group          3425d361... / run 35721081039 / PASS
    two-producer synthetic wave     03a6e451... + 6be42de4... / PASS
    Harness portability merge_group ceba5910... / run 35725780805 / PASS
    real producer merge_group       06b93277... / run 35726560495 / PASS
    final main after producer       06b93277... / run 35726848574 / PASS

Canonical acceptance evidence lives in
GITHUB_MERGE_QUEUE_REMOTE_CUTOVER_ACCEPTANCE_R1.md and
HARNESS_QUEUE_PORTABILITY_R1.md.

Advanced scheduling is still deliberately not admitted. The observed queue
wave proves correctness and clean-runner portability, but does not establish
sustained queue contention, meaningful speculative CI waste, repeated high
queue depth, or enough historical runs to validate a cost predictor.

## 11. References checked for R1

- GitHub Docs — Managing a merge queue / rulesets / `merge_group` workflow event.
- GitLab Docs — Merge trains / merged results pipelines.
- Zuul Docs — dependent pipeline, project gating and adaptive pipeline window.
- Mergify Docs — scopes, parallel mode, batching and batch failure splitting.
- Uber SubmitQueue — predictive speculative execution for large monorepos, 2025.

External products remain replaceable. The architectural contracts above are the retained kernel.

Remote cutover is accepted only after the repository ruleset produces a real
merge_group synthetic revision and root-verification passes on that exact revision.
