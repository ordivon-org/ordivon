# GitHub Merge Queue Remote Cutover Acceptance R1

Date: 2026-09-22
Status: ACCEPTED

The repository-level convergence boundary for main is now GitHub Merge Queue,
not direct multi-producer pushes.

## Accepted remote controls

- Repository ruleset: main-convergence-queue-r1
- Ruleset id: 23819262
- Enforcement: active
- Target: refs/heads/main
- Required check: root-verification
- Merge queue: ALLGREEN, build concurrency 2, merge group size 1,
  merge method MERGE, required-check timeout 30 minutes
- Non-fast-forward updates are rejected.
- The required workflow listens to pull_request, merge_group, and push.

## Remote evidence

The first fully green protected-main prerequisite was GitHub Actions run
35720348956 on 411b3bc56769f8bb78d3e3318a73ef04add5e5ad.

Dedicated queue dogfood PR #16 produced merge-group synthetic revision
3425d361f678ae688d5ac81863ea33095b62411b. Run 35721081039 reported
root-verification=success on that exact revision. The queue then merged that
same synthetic revision into main, and post-merge push run 35721225774
also passed.

The first two-producer queue wave used PRs #17 and #18. GitHub dispatched
two merge-group builds concurrently:

- PR #17: 03a6e451b0bb8aa5e346cce52c091758d2b71edb, run 35721556672, success.
- PR #18: 6be42de4c698b658fbc10cc34b06b8a122074470, run 35721558190, success.

The second synthetic revision was based on the first, so the queue verified the
serialized composition rather than two isolated branch heads. Both entries
merged through the queue, and final protected-main push run 35721673056
passed on 6be42de4c698b658fbc10cc34b06b8a122074470.

## Authority boundary

GitHub Merge Queue owns repository convergence ordering only. It does not own
Runtime jobs, Host continuity, Domain semantic success, Study scientific
authority, or Agent workflow semantics.

Parallel producers may continue independently. Their convergence path is now:

producer branch -> pull_request -> root-verification -> merge_group -> main

The local CAS integrator remains recovery and pre-cutover evidence; it is no
longer the default remote-main convergence path.
