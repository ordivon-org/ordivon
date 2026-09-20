# Runtime Workspace Reclaim - Authoritative Patterns Plan

## Goal

Harden the existing ordivon-runtime-reclaim path instead of introducing a second GC subsystem.

## External patterns adopted

1. Git worktree/remove: clean working tree is a mechanical deletion precondition, not proof that branch work is integrated.
2. Git patch identity: copied, rebased, or cherry-picked patches can be recognized independently of commit identity, but automatic reclaim uses patch-id --verbatim and rejects branch-exclusive merge topology because ordinary git cherry ignores whitespace and does not preserve merge topology.
3. Nix GC roots: semantic reachability and retention are distinct from physical materialization.
4. Kubernetes ownerReferences/finalizers: deletion is a gated lifecycle transition, not an age-only boolean.
5. Bazel/cache discipline: build materialization is reconstructible state and should not become source ownership.
6. Temporal durability: execution/history survives worker/workdir loss; retained history is not current execution substrate.

## Scope

- Extend the existing reclaim classifier with canonical Git integration evidence.
- Fail closed for clean Git-backed workspaces whose unique commits are not integrated.
- Bind workspace.close to a fresh workspace.get sourceStateDigest after checking the planned HEAD.
- Preserve Runtime/Host authority separation; Host claims remain an orchestration-layer finalizer, not a Runtime-owned truth.
- Preserve C9 law: retirement != reclamation; reclamation != historical erasure.

## TDD tasks

1. RED: unique clean commit is blocked_unintegrated.
2. RED: verbatim patch-equivalent clean branch is closable with PATCH_EQUIVALENT_IN_CANONICAL.
3. RED: whitespace-only patch differences remain blocked even though ordinary git cherry reports equivalence.
4. RED: branch-exclusive merge topology remains blocked.
5. RED: ancestor clean head is closable with HEAD_REACHABLE_FROM_CANONICAL.
6. RED: close obtains fresh workspace.get, verifies planned HEAD, and passes exact expectedSourceStateDigest.
7. GREEN: implement strict Git integration classifier and CAS close path.
8. Regression: run reclaim tests, lifecycle tests, operational-script tests, then the complete scripts test suite.
9. Live falsification: compare old and candidate classifiers against the same Runtime registry without apply.
10. Review: inspect authority boundaries; Host workStanding remains caller-authored continuity data and is not consumed as Runtime physical authority.
