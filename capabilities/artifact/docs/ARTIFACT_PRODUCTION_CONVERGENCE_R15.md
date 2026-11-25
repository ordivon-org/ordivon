# Artifact R15 production convergence execution spec

Extends Standing R2.1 and R14 provider convergence (Host #32750). User explicitly
prioritizes canonical source catch-up; Host #32759 and #32776 record intent and
actual source/Python synchronization. Source cut ac8dba2cfb73f32a7398c28f8f416c4876e319c7.

## Thought modules and reusable capabilities
Git fast-forward/isolated worktrees (https://git-scm.com/docs/git-merge,
https://git-scm.com/docs/git-worktree), systemd service lifecycle
(https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html),
Temporal visibility/replay, Nix generations/GC roots, locked uv materialization,
OCI native provider and SLSA evidence identity. Reuse existing owner scripts,
Git, systemd and Temporal; no new release orchestrator or shared registry.

## Logical-to-capability mapping
| Logic | Existing capability | Boundary |
|---|---|---|
| Source authority | protected remote main, exact Git fetch | remote state is observed at one cut |
| Source admission | clean worktree, ancestry, ff-only/no-overwrite-ignore | never reset/force/stash/clean another owner |
| Live-consumer census | native process/unit paths, Temporal visibility | observed processes not exhaustive readset |
| Quiescence | existing service stop, visibility check | visibility alone is not a submission fence |
| Source materialization | native Git checkout/fast-forward | source synchronized != installed service |
| Runtime generation | existing artifact_python_environment.py | exact uv closure, atomic pointer, prior generation retained |
| Native method generation | artifact_openxml_environment.py, Nix, NuGet | frozen method corpus, exact output digest |
| Worker deployment | artifact_temporal_deploy.py/systemd | exact unit, SDK, service readback |
| Provider admission | Podman/Playwright, existing verify_web_local | explicit selection, no fallback |
| Evidence + standing | existing receipts/claim coverage | separate operational absence and content failure |
| Consumer readback | existing native activities/Workflow/OCI | local unsigned development never release |
| Rollback and retirement | existing generations and owner lifecycle | no automatic cross-owner restart or historical deletion |

## Formal transition
I=(remote cut, current local ref, observed source state, live consumer scope,
qualified generation recipe, profile); O=(source cut, installed generation,
loaded worker identity, bounded consumer receipt); S=existing Git refs,
generation symlinks, systemd state and Temporal durable history.
pre: ancestor-only, clean source, ignored collision protection, observed
quiescence; post: local HEAD equals fetched exact cut; installed and loaded
states independently read back; inv: no remote writes by sync, no unrelated
worktree mutation, no false release or fallback; eff: controlled fast-forward,
Artifact-only generation publication/restart; cost: observed delta and native
materialization, no inferred global downtime; epsilon: visibility is eventually
consistent, no global admission fence, no proof of other services' loaded cut;
prov: Git source IDs, native Job, binding, unit and receipt.

P0 actual source sync and Python deployment done #32776. P0 OpenXML managed
apply, frozen corpus, native consumer; P0 qualify pending #2767/#2773/#2824
normal protected queue, then exact provider candidate and real service
execution. P1 independent native test lanes, rich GLB closure, retire host-only
provider after actual migration. Future source updates must repeat bounded
fast-forward admission or use natural shared source deployment; do not add
a separate timer/service in this lane. Every owner independently qualifies
their own binaries/schema/consumer after shared source advances.

## Observed implementation receipt

- Canonical main actually advanced 5f0545cf6805 -> ac8dba2cfb73, 534 remote
  commits, clean tree, zero divergence at fetched cut. Job
  job-01a214b2-d883-74e9-abeb-d6b6d4dde6c8.
- Python generation 80b60f04b8b482b2810104b81e0f37b4ca8d6bf410fb462b52e76dad41bf1356,
  Python 3.15.2, Temporal SDK 1.37.0; exact unit deployed, Worker active
  PID 3574840.
- Actual canonical OpenXML generation
  3839bce8d30a5fe21e3ccd0913a9493d8bffa253b0e51126f435328f68186782,
  .NET 10.0.404, GC root registered, frozen corpus result
  sha256:3a0b9739903e4279e25528f3c5a52a4a7d0708ae2803436ffec57b684298b778.
  Job job-01a214b3-999d-7534-99cc-dbc15ff76374. This uses merged source,
  not pending #2824; canonical outside-Git staging produced the same output
  tree as the independent candidate but does not eliminate the recipe defect.
- Actual production worker local unsigned development workflow
  artifact-r15-production-local-development-20261126, run
  01a214b5-7d3a-7b38-bb28-62c7c422f8b4, completed 29 history events,
  27 exact output roles, four OCI referrers, three required gates PASS,
  replay PASS; history SHA
  0a748749f1a4ab930238d97912ad66df727071b140a047f6ea9f8583f7e43bd5.
  Job job-01a214b5-70c3-7366-a765-34fc3f518fa4. Retain real durable
  consumer state; releaseReady=false, external acceptance not evaluated.

Remaining source queue and explicit OCI provider activation are independent
release obligations. Do not imply all other owner services have been upgraded.
