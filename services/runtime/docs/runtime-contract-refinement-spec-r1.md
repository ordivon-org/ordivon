# Runtime R2.1 Formal Refinement & Consumer Acceptance — Spec R1

Status: DECLARED, not model-proved or installed. Owner: services/runtime. Git basis: PR #1983, commit 15ac1ee0a6fc1c1891984627558e805d0367ecbd. Original remote main has moved; re-evaluate before merge.

## Problem Statement

An implementation can pass local checks while violating its consumer contract: conservative retention never reclaims eligible Workspaces; a new canonical release artifact changes the deployer's set but the release workflow asserts the previous cardinality; and model-level safety is reported as if it proved real code. PR #1983 has concrete mandatory CI failures; CodeQL passed, repo-mechanics failed due to release artifact cardinality drift (13 vs 14).

The outcome is an independently falsifiable Runtime lifecycle guarantee: no unjustified closure AND eventual closure of continuously eligible Workspaces under explicit fairness, with exact implementation/installed evidence and no new Agent governance runtime.

## Existing Ordivon thought LEGOs and Owners

Reuse .agents/skills/recursive-lego-calculus/SKILL.md and its formal-model, formal-thinking-legos-human-agent, consumer-rooted-retirement references, plus .agents/skills/compositional-contracts/SKILL.md. They already adopt typed R2.1, assume–guarantee reasoning, stuttering refinement, non-vacuity, CEGAR, and scoped UNKNOWN. No replacement calculus, per-file LEGO or second registry.

Runtime owns physical Workspace/Job/Attempt closure, PG owns durable execution facts, Git owns source persistence, OS/systemd owns actual processes, GitHub owns merging and release verification, and Host/domain consumers own semantic acceptance. A caller's consumerReleased assertion is not an independently observed Host lease.

## Independent capability LEGO: Runtime Workspace Reclamation

Declare only this independently consumer-relevant responsibility:
ell = (I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)

- I: typed Git SourceCut, Registry Workspace/Job projection, current Runtime Workspace, OS process evidence, owner-controlled configuration, native close request.
- O: eligible/skip/UNKNOWN reason, close receipt, release manifest and installed consumer observation.
- S: abstract open/closed with bounded fresh/expired/Job/reference states; physical PG/Git/systemd source must be separately related to model.
- pre: committed retention expires, no active/held Job or observed process, clean worktree, durable Git source reference, readable current Runtime identity and authorization.
- post: any reported closed disposition is backed by a matching native workspace.close of identical workspaceId and expected source digest. Job failure is not domain failure.
- inv: live/held process and unique source cannot be silently disposed; UNKNOWN input cannot imply closure; physical closure must not invent semantic success.
- eff: exact Runtime close may physically remove a worktree. Git and Artifacts are durable repositories with distinct lifecycle.
- c: typed UNKNOWN measured CPU/PG/API/latency cost; no invented 0.
- epsilon: typed UNKNOWN empirical failure bounds; finite state model PASS is not a probabilistic error rate.
- prov: Git commit/digest, formal version/config, native test results, release receipt and installed/consumer witness (each separately qualified).
- unfold: scripts/ordivon-runtime-pg-reclaim, Runtime MCP workspace.get/close, PG Job/readback, Git, Rust close code, systemd Unit, native deployment manifest.

Formal declaration is not evidence that the implementation already satisfies the contract.

## Formal and mathematical obligations

1. **Hoare/DbC**: {pre} close {post}. The effect authority must actually establish pre, not accept self-serving Agent assertions. Different evidence predicates are never collapsed into boolean success.
2. **Assume–Guarantee**: express assumptions and guarantees on one observable alphabet. A replacement cannot strengthen previously qualified consumer assumptions or weaken required guarantees. Local behavior refinement is not sufficient for an arbitrary composition without side conditions.
3. **Transition refinement**: map real state to abstract state and preserve initial relation and each observable transition (allow justified stuttering). Invariant satisfiability alone does not prove preservation. Source-level Python tests do not prove TLA+ refinement automatically.
4. **Safety**: always (closed => no active Job, no unpreserved Git dependency). This is scoped to the modeled truth channels.
5. **Conditional liveness**: always ((eligible AND no future competing Job/ref AND fair Close scheduler) => eventually closed). Unconditional real-world closure is unprovable if the environment can infinitely recreate activity or providers remain offline.
6. **Concurrency/linearizability**: a PG query is not atomic with physical deletion. Re-read PG activity, require exact Workspace and source-state CAS, delegate final operation to native Runtime close. If native lock/PG admission coupling is not demonstrated, full end-to-end linearizability stays UNKNOWN.
7. **CEGAR and falsifiability**: require a reachable eligible Close, a counterexample without the fairness assumption, and a safety-invariant counterexample for an unsafe Close transition. Do not equate a model syntax PASS or empty state-space with success.
8. **Evidence hierarchy**: MODEL_CHECKED, SOURCE_VERIFIED, MERGED, INSTALLED, EXECUTED, CONSUMER_ACCEPTED are independent standing; UNKNOWN blocks only dependent claims, not unrelated implementation work.

## Adopted mature theory and original sources

- Lamport, Specifying Systems: https://lamport.azurewebsites.net/tla/book.html
- Lamport, Refinement and Temporal Logic of Actions: https://lamport.azurewebsites.net/tla/papers.html
- Herlihy and Wing, Linearizability (1990): https://doi.org/10.1145/78969.78972
- Clarke et al., CEGAR (2000): https://web.stanford.edu/class/cs357/cegar.pdf
- AWS industrial formal method use: https://lamport.azurewebsites.net/tla/amazon.html
- Kubernetes TTL and owner reference / finalizers: https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/ and https://kubernetes.io/docs/concepts/architecture/garbage-collection/
- Matt to-spec / to-tickets / tdd / code-review: https://github.com/mattpocock/skills
- ECC verification-loop (continuous-learning v1 deprecated): https://github.com/affaan-m/ECC
- Superpowers writing-plans / executing-plans / verification-before-completion: https://github.com/obra/superpowers

## Acceptance seams and independent negative controls

A. Formal: existing services/runtime/formal/WorkspaceConsumerCloseR1.tla, pinned TLC and scripts/tla-formal. Preserve safety, add conditional progress and weak-fair Close; remove fairness as a liveness falsifier; retain existing closed-unreachable and unsafe close falsifiers.

B. Real implementation: current public PG reclaim CLI with PG/RUNTIME MCP/Git seams. Terminal failed/lost/no-Job can reclaim; active/held/dirty/recent/unanchored/revision-drift/UNKNOWN cannot; changed Job projection must veto closure.

C. Tagged release: canonical native deployer defines the set of artifacts, GitHub workflow uses the manifest rather than independent fixed count. Missing, extra, duplicate, digest or mode mismatch fails. A legitimate additive artifact does not require synchronized magic constants in unrelated owners.

D. Owner verification: real repo mechanics, Runtime formal, Runtime native tests and exact installed readback. Scope claims to executed checks.

E. Cross-owner evidence: R2.1 provenance records exact SourceCut, model/config checker digest, native result, release/install digests and actual consumer. Do not add a second evidence database.

## Non-goals and exit criteria

No weak-model trials. No new workflow engine, Agent governance platform, LEGO registry, approval gate, generic formal language, arbitrary database migration or early Windows SQLite deletion. Do not assume closed-source backend linearizability from a mocked Python response.

Exit SOURCE: native failing-before/green-after tests, TLC safety+conditional liveness+falsifiers and release manifest identity tests pass.
Exit MERGED: PR #1983 actual required GitHub checks and merge queue pass.
Exit INSTALLED: installed script and loaded systemd Unit digests and release origin verified.
Exit CONSUMED: actual eligible Workspace closure and preserved Git/Artifact state observed. Unfinished exits remain UNKNOWN.
