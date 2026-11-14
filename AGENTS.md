# Ordivon Monorepo Agent Rules

**Linux PG Runtime Workspace lifecycle:** On workspace.open, read the returned
retentionNotice. The hourly native cleanup can reclaim a clean, mainline-integrated
Workspace after at least **4 hours of inactivity since its latest Runtime Job**
once the last Job succeeds and no active/held consumer remains. Persist results
to Git or Artifact storage; a Workspace is not durable evidence. This is a
minimum quiet period, not a guaranteed four-hour reservation. Do not force-close
dirty/unmerged Workspaces.

First session in this repository? Use
[Agent first verified task](docs/start/agent-first-run.md) and
[task/owner navigation](docs/start/tasks.md) to find one real consumer. These
are optional onboarding pointers, not new execution authority or an additional
mandatory workflow. The rules below govern consequential changes.


1. Work inside the natural owner directory.
2. Read prior exact-SourceCut verification receipts and the affected consumer/change scope BEFORE rerunning tests. Reuse existing scoped PASS evidence when its assumptions and inputs remain qualified. Run affected Owner-native verification only for newly required, invalidated or missing claims; distinguish reused PASS from a freshly executed PASS.
3. Do not import another owner's internals merely because they are in the same Git tree.
4. Cross-owner effects use the producing/consuming owners' explicit contracts.
5. Root tooling may orchestrate checks but may not redefine owner truth.
6. Do not unify lockfiles, environments, databases, releases, or scientific state as a repository-cleanup shortcut.
7. Keep source relocation separate from semantic refactoring.
8. For a consequential testing-method or test-template choice, consult `docs/architecture/TESTING_UPSTREAM_ADOPTION_R1.md`; prefer existing Owner-native tools and mature Skills. Do not impose that read on routine edits. SKIP, NOT_RUN and ENV_BLOCKED are not PASS.
9. For a nontrivial test or debugging task, discover the relevant current Skill only if it can change the method; use the Owner's actual `mise tasks ls` and focused native verification where applicable. An isolated test PASS is not whole-Owner or domain acceptance.
10. In user-facing replies, reports, and handoffs, state the decision, result, or next action directly. Do not add generic disclaimers, defensive qualifications, obvious warnings, patronizing reminders, or repeated caveats after a clear answer. Explain uncertainty or a constraint only when it materially changes the decision or work; keep it precise and integrated into the answer. Give deeper analysis when requested.
    For material second opinions, scoped Chinese prose editing, concrete error correction, or evidence-backed manuscript framing, discover only the relevant existing method Skill: evidence-calibrated-dialogue, natural-chinese-writing, feedback-grounded-repair, or research-claim-framing under .agents/skills/. They are optional advisory thinking methods, not global activation, effect permission or replacements for Owner-native verification.

11. **Agent vocabulary / conceptual boundaries (on demand):** when Tool, Skill, Agent, Harness, Runtime, Workflow, Memory, MCP/A2A, Formal or LEGO distinctions affect work, read `docs/architecture/AGENT_CONCEPTS_FORMAL_LEGO_RESEARCH_20261024.md`. It is a scoped vocabulary reference, not a new owner or a permission source. Reuse the actual owner API and current evidence; do not claim a Task is complete merely because a model Run or Runtime Job finished. Skip this read for routine tasks where the roles are already clear.

12. **Implementation languages:** prefer Rust, Python and TypeScript, chosen by the natural Owner and real consumer; use pnpm for TypeScript package work. Specialized specification/policy/data languages (Lean, TLA+, SMT-LIB, Rego, SQL, etc.) are allowed for their actual purpose. Keep current stable dependencies and Owner lockfiles in sync with affected consumer tests; never rewrite a working provider solely to enforce language purity.
13. **Representation / LEGO:** start with the goal, SourceCut, real consumer and best adequate representation. Prefer DELETE unnecessary custom work, then REUSE mature native/external capabilities, then COMPOSE, and create only for an unmet evidenced contract. A LEGO is an independently contractable, replaceable semantic responsibility, not each file, Skill, Tool or Agent. For a formally DECLARED or ADMITTED LEGO, use the complete typed R2.1 `ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)` contract from `.agents/skills/recursive-lego-calculus/SKILL.md`; use scoped typed UNKNOWN instead of invented values. Do not build another registry, calculus, Broker or runtime.
14. **Proof and tests:** first state the property, assumptions, failure modes, current source/implementation and affected consumer. Select only relevant formal/model checking, implementation refinement, property/state-machine, differential/consumer-contract, integration/read-back, fault-injection/replay and Agent trajectory/holdout evaluations. Match tools to the Owner, not a universal checklist; see the testing guide. A model PASS does not prove code refinement; a test PASS does not prove universal correctness; a Runtime/Agent success does not establish domain completion.
15. **Agent decision evidence:** distinguish OBSERVED, DECLARED, DERIVED, VERIFIED, UNKNOWN and FALSIFIED with provenance and currentness. Treat hypotheses and predictions as candidates; consider rival explanations and value of further evidence where material. A model belief, Skill read, evidence graph or Tool discovery never confers effect authority. Finish real work with implementation or justified subtraction, actual execution/observation, affected verification and repair; report explicit remaining UNKNOWN rather than fictitious success.
16. **Integration discipline:** compare current main, relevant branches/PRs and actual consumers before retaining changes. For cross-Owner or PR-sized work, exchange evidence and counterexamples in the existing Space when useful; a message or Owner opinion is not a proof or a permission gate. Prefer the smallest verified contribution and retire superseded code rather than accumulating parallel implementations.

## Evidence-reuse / incremental verification admission

**A new Agent turn is not a new verification obligation.** First identify the
claim, formal/consumer scope, source revision, verifier/toolchain, environment
assumptions and previous accepted receipt. A status question or conceptual
design task does not by itself authorize re-running proof, replay or CI.

- REUSE_SCOPED: a prior accepted PASS covers the same immutable SourceCut,
  exact claim, verifier and assumptions. Read the receipt and keep its
  original evidence date. Installed/external facts require separately
  qualified generation, principal and currentness; source equality alone
  never certifies current production behavior.
- AFFECTED_RECHECK: changed inputs, contracts, owner APIs, verifier
  assumptions or actual consumers intersect the proof's qualified
  dependency/readset. Select the minimum new obligation, not every historic
  test. Use the existing tools/repo/convergence_plan.py for Owner/CI queue
  and check_architecture_docs.py --agent-impact for declared LEGO impact.
- UNKNOWN_DEPENDENCY: missing evidence, unresolved dynamic/non-Git consumers,
  incomplete proof readset, or a non-ancestral comparison. Investigate the
  missing edge first. The existing declared source impact always reports
  proofReuseAdmissible=false; NO_DECLARED_HIT is NOT a proof reuse grant.
- FALSIFIED: a scoped counterexample changes the standing of the affected
  claim; unrelated verified claims remain available.

The repository already has affected_owners.py, convergence_plan.py,
ci_owner_shards.py and GitHub Owner CI checks. Reuse them instead of building
a competing selector or database. A prior CI PASS on another SHA is not
automatically equivalent to a PASS on this SHA. Do not rerun unchanged
TLA+ models/negative controls without affected inputs, and do not equate
formal source proof with installed/physical effect evidence.

For concrete GitHub Actions Check Run results use the already existing
GitHub CLI and the bounded read-only native consumer first:

    python3 tools/repo/evidence_validity.py --current-sha FULL_SHA --check-name root-verification

Add --prior-sha FULL_ANCESTOR_SHA only when the current check is absent and
changed-source impact would change the decision. For Formal Git input changes,
add --formal-source-delta with two ancestral commits to compare the existing
Formal producer's historical SOURCE_FILES modes/blobs without executing a
proof.
To inspect a historical Formal proof's ORIGINAL validated CI report, do not
rerun the solvers. Opt in to the existing GitHub Check Run and pinned native
artifact consumer with --prior-sha FULL_FORMAL_ANCESTOR_SHA,
--formal-source-delta and --fetch-historical-formal-report. The exact
root-verification Check Run and workflow SHA must be qualified. The artifact
exists only for runs that actually selected Formal, succeeded and uploaded it
(30-day retention). Missing artifacts are UNKNOWN, not authorization for
generic Harness ToolBridge redispatch or cross-version proof reuse.
 This is source input equivalence only; a toolchain/assumption/real
consumer proof reuse or arbitrary Harness workspace.exec no-dispatch remains
unqualified. The check-receipt decision can reuse a same-SHA check outcome
without replay. It never asserts formal
or installed proof reuse across Git commits. Do not create a second CI
scheduler or run another verification Job after a same-SHA accepted receipt.

In handoffs report REUSED_EXISTING_EVIDENCE separately from NEWLY_VERIFIED,
UNKNOWN and FALSIFIED. Prioritize new business/consumer capabilities over
repeated verification of unchanged claims.

Before reusing a CI Formal receipt on a PR, distinguish the
GitHub Check Run's PR Head SHA from the actual verified synthetic merge
SourceCut. Read historicalFormalReceipt.verifiedExecutionSourceCut,
sourceRelationship, and executionInputsVsCandidate; a two-snapshot
input equality is neither temporal ancestry nor full proof reuse.
The evidence consumer must validate the original PR base/head parents;
do not copy the PR Head into the historical proof as if it had executed.
No separate Harness execution-dispatch authority is implied.

A local Git candidate that has not yet been pushed can return
UNKNOWN_CURRENT_CHECK_PROVIDER while independent prior Formal Artifact
and immutable Git input comparison still succeed. Do not let current
provider unavailability erase previously qualified historical evidence
or trigger automatic solver re-execution. The existing Runtime
agent_evidence_admission.py already consumes exact GitHub CI
for the named natural Owner. It is read-only, not an enforced
Harness ToolBridge no-redispatch gate.

For the actual bounded Formal declared-Git-input Claim, reuse
tools/repo/evidence_validity.py with exact --current-sha,
original --prior-sha, --fetch-historical-formal-report and
--claim-kind BOTH. One original artifact read returns both
FORMAL_DECLARED_GIT_INPUTS_EQUAL (only the agent:formal-declared-source-impact
consumer may receive scoped support) and FORMAL_PROOF_APPLICABLE_TO_TARGET
(UNKNOWN until dynamic/toolchain/implementation/consumer assumptions
are closed). Neither result authorizes any Runtime Job or generic Harness
workspace.exec, nor does it establish installed currentness.
See docs/architecture/EVIDENCE_VALIDITY_KERNEL_R1.md.

## Evidence-backed detailed reporting and handoffs

When a user requests a detailed progress/completion report, or when handing off a
consequential multi-Owner or production change, report against **the actual
consumer and acceptance authority**, not the amount of Agent activity.
Keep routine replies concise; do not require every section for a trivial edit.

- **Decision and standing:** lead with what is complete, what is not, and the
  real consumer consequence. State the exact scope and the as-of time.
- **Source and change identity:** record the exact Git revision/PR and
  changed or retired responsibilities, distinguishing proposal, committed
  branch, merged main and deployed source. Link the original evidence.
- **Independent realization:** distinguish, when relevant, `SOURCE`,
  `MERGED`, `INSTALLED`, `LOADED`, `EXECUTED` and `CONSUMED`.
  Use owner-native exact readback (bytes, process/generation, kernel or
  external provider) and the consumer's real acceptance, not job exit alone.
- **Verification and falsification:** name the native commands, observed
  results, tested assumptions and relevant negative controls. Mark failed,
  skipped, unavailable and not-run checks distinctly; never inflate a
  model, static source, CI, or service-health PASS into domain success.
- **Open work:** give only consequential `UNKNOWN` or `FALSIFIED`
  properties, their actual blocker or competing explanation, natural Owner,
  next executable action and observable closure condition. Do not invent a
  completion percentage, ETA, approval, deployment or ongoing monitoring.
- **Incident mode only:** when an incident actually occurred, add observed
  impact, chronological events, contributing causes and tracked mitigation
  and prevention actions. Do not turn every engineering report into a
  postmortem.

This is a **presentation and handoff contract**, not a new status database,
runtime, universal report generator or mandatory Skill. Reuse existing Host
Work/Topic, GitHub PR/checks, Owner-native verification and domain receipts.
Follow the scoped Owner Agent guide for concrete evidence (Network example:
`platform/network/docs/AGENT_GUIDE.md`); use
`.agents/skills/task-space-reentry/SKILL.md` only when a real Work/Space
handoff is required.

## Practical consumer routing

### Live local-tool discovery

- For local executables, start at [Workstation inventory](platform/workstation/inventory/README.md); probe the **actual node and Runtime execution identity** on demand, not a dated machine snapshot or another user's PATH.
- Classify the needed capability via [Capability Catalog](catalogs/capabilities/README.md), then read the selected Owner's README, closer AGENTS.md (if present), and relevant Skill; see [Agent first-run](docs/start/agent-first-run.md).
- Resolve callable operations from live MCP tool definitions, Owner-native CLI help or `mise tasks ls`; do not reconstruct interfaces from prose. A trusted Skill, installed application, discovered command and authorized domain effect are distinct evidence.
- Do not copy tool inventory into this file or create a second tool registry. Verify actual provider readback and the final consuming task.

- Use the Human and Agent owner navigation in README.md, mechanically backed by tools/repo/owners.toml. Choose the Owner by the actual **fact or effect**, not where a helper happens to live. Nearest scoped AGENTS.md instructions take precedence for local methods, not Owner authority.
- Method-first discovery: the existing .agents/skills/method-router/SKILL.md; select only the relevant trusted method or supplier. Use design-structure-matrix for evidenced dependency clustering, skill-supply-chain-audit for external candidates, recursive-lego-calculus for a real R2.1 contract. Do not create one file per LEGO or a second capability registry.
- **External Learning & Evolution (ELE):** For material external facts, research results, counterexamples or changed standards, activate `.agents/skills/external-world-evidence-review/SKILL.md`; for upstream projects, tools, algorithms or Skills, activate `.agents/skills/external-capability-evaluation/SKILL.md`. Bind the natural Owner and actual consumer before adoption; keep discovery, qualification, Owner acceptance, Git merge, installation and consumer read-back distinct. Without a qualified consumer, retain discovery only. Detailed methods belong in the two Skills, not a new ELE Owner, registry or workflow engine.
- Execution and retirement: check the active Job, exact Git branch/PR/installed SHA, current Host Work Snapshot, cross-Topic Message references, subscriptions, cursors and replay receipts as applicable; no age-only or mere-reference-only deletion. Prefer native Runtime workspace.close, Git worktree remove/prune, PostgreSQL transaction/Alembic or package manager prune.
- Reuse owner-specific source checks and mature tools. Verify the affected user/domain consumer and report merged, installed and executed states separately. Close only your own fully integrated, clean Workspace; leave concurrent Agents untouched.
