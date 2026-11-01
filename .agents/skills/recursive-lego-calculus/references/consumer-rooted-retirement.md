# Consumer-rooted retirement: bounded witness, not a deletion oracle

Apply only when a real PR, source responsibility, remote branch or Runtime
Workspace is a retirement candidate and actual consumers/proofs are disputed.
Do not run a global audit merely because this reference exists.

## Mature theory and reuse

1. Knip's entrypoint-first reachability: missing dynamic/plugin/service roots
   produce false unused classifications. Test-only paths are separate.
   https://knip.dev/explanations/how-knip-works
2. Bazel Skyframe's reverse dependency graph and change pruning: invalidate
   affected readsets; reuse proof only under recorded input and assumption
   closure, not by a similar test name.
   https://bazel.googlesource.com/bazel/+/3b9ed6e9d3570a0c67e0d59e65b3785bbc1fad99/site/en/reference/skyframe.md
3. Immutable Git objects and protected merge queue: names of branches/PRs
   are mutable pointers, not evidence identity.
   https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches

REUSE tools/repo/convergence_plan.py as retirement candidate immutable Git
SourceCut prefilter, tools/repo/affected_owners.py for affected owner discovery,
the existing natural Owner CI and native Runtime Workspace/Job operations.
No new global registry, collector, custom dependency database or per-file LEGO.

## Representation: four independently typed objects

Carrier(repo, main_sha, candidate_sha, tree, path, mode, blob) is exact Git
source value evidence. Consumer(root, target, kind, observed_at, evidence)
distinguishes EXECUTED, INSTALLED, CONFIGURED, PRODUCTION, BUILD, CLI,
PUBLIC_API, TEST_ONLY, HISTORY_ONLY and UNKNOWN_DYNAMIC. Obligation(statement,
verifier, readset, assumptions, sourcecut, result) distinguishes LEAN_THEOREM,
TLC_FINITE_MODEL, IMPL_TEST, CODE_REFINEMENT, INSTALLED_CURRENT and
DOMAIN_ACCEPTANCE. Decision(action, sourcecut, covered_roots, unknown_roots,
negative_witness, effect, archive_or_rollback) authorizes exactly one effect.

Per claim use OBSERVED, FALSIFIED or UNKNOWN. An uninspected dynamic root
remains UNKNOWN, not an absent consumer. Decisions are KEEP, HOLD_UNKNOWN,
RETIRE_PR_ONLY, RETIRE_REMOTE_REF_AFTER_CAS or
RETIRE_SOURCE_AFTER_OWNER_VERIFY. Closing PR != removing deployed code;
closing detached Workspace != deleting its reachable Git commit.

## Existing method LEGO instance — full R2.1, not a new Skill/provider

ell = (I, O, S, pre, post, inv, eff, c, epsilon, prov, unfold)

- I: (RepoId, MainSha, CandidateSha, ChangeSet, RootSet, ObligationSet).
- O: RetirementDecision x Evidence x NegativeWitness x UnknownSet.
- S: immutable Git snapshot x observed installed/runtime snapshot x
  proof identity, no new persistent state store.
- pre: exact reachable Git objects, observed entry roots, scoped SourceCut,
  dynamic consumers enumerated or UNKNOWN, current effect authority checked.
- post: only the named effect authorized; equal Git blobs never by themselves
  authorize deletion of executable/installed consumers.
- inv: UNKNOWN != FALSE; test-only/history-only cycles do not prove terminal
  production value; model proof != code refinement != installed acceptance;
  archived pull ref != live mutable branch.
- eff: read-only assessment; optional explicitly authorized GitHub PR close,
  CAS remote ref delete, protected-queue source merge, native Runtime
  workspace.close(force=false), each independently.
- c: Git diff plus observed readset traversal O(changed_paths + |V| + |E|);
  external dynamic root discovery cost UNKNOWN.
- epsilon: scoped immutable Git path mode/blob equality exact; external
  consumer coverage and implementation behavioral error UNKNOWN.
- prov: exact main/candidate/branch SHA, Owner/native terminal Job ID,
  verified installed root, checker inputs/result and GitHub readback.
- unfold: full PR diff -> real loader/config/owner consumer -> downstream
  effects -> replacement and counterexample -> native Owner verification ->
  exact CAS operation -> terminal readback.

Any unobserved coordinate must be typed UNKNOWN(reason, scope, obligation),
not an invented zero. A declaration is not a theorem or current deployment.

## Independent counterexamples before retirement

- Hidden caller: a configured unit/dynamic import still calls the candidate
  despite no static import -> block source deletion.
- Self-test loop: only candidate-owned tests and old documents call it ->
  no independent production evidence; off-repo usage stays UNKNOWN.
- Proof mismatch: finite TLC checking is not a Lean kernel theorem, and
  neither alone proves real Python/Rust effect/refinement.
- SourceCut drift: main/head or referenced mode/blob changes while assessing
  -> recompute affected readset/consumer/proof closure.
- Active Job race: dirty or active-Job Workspace rejects force=false; never
  escalate to force=true merely to finish cleanup.
- Archive/ref split: close PR first; delete exact leased remote branch only
  after verifying no active checkout/open-PR consumer and intact pull/head
  archival ref. Re-read GitHub state after every mutation.

## Real owner execution and stop condition

Get exact GitHub main and PR headRefOid, inspect full Git diff and all named
production/configured/installed consumers, not just git grep. Existing
convergence_plan.py --retirement-candidate SHA --retirement-main SHA
qualifies only bounded immutable Git equality, not live consumer closure.
Run affected native Owner CI, at least one independent negative witness,
and any required source-to-model refinement/physical acceptance. No self-test
inserted by the candidate is independent evidence of candidate necessity.

Effects: GitHub PR close with scoped evidence; branch removal with Git
force-with-lease against exact HEAD after PR closed/archive preserved; Runtime
Workspace get then close(expectedSourceStateDigest, force=false); source
integration via protected GitHub merge queue only. Check current state
immediately before effect, then read actual terminal postcondition. Record
exact SourceCut, terminal Job, consumer boundaries and unresolved UNKNOWN
in the existing Host Space. Do not mistake a method note for authorization.
