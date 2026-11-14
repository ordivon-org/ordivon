# Incremental Evidence Validity R1 — Exact-Check Consumer

Status: SOURCE IMPLEMENTED, LIVE GITHUB CHECK READBACK OBSERVED, cross-SHA proof
reuse NOT implemented. Source date: 2026-11-14. Natural facts remain owned
by Git, GitHub Actions, the existing repository SourceCut selector and native
verification owners. No new database, Registry, Gateway MCP, Runner, Scheduler,
or agent was created.

## Actual business consumer

An Agent often launches Gateway/Runtime replay or TLA+ checks on its next turn
even though an accepted GitHub Actions Check Run already finished for the
unchanged exact source SHA. Do not repeat a successful exact-SHA check simply
because a new conversation/Agent turn started.

Minimal read-only interface:

    python3 tools/repo/evidence_validity.py --current-sha FULL_GIT_SHA --check-name root-verification

For historical comparison add --prior-sha FULL_ANCESTOR_SHA. The entrypoint
reuses ci_telemetry.Gh for original GitHub Check Run transport,
convergence_plan.build_plan for existing Owner verification selection, and
source_history_legos.require_ancestral_source_cuts for native Git ancestry.
It does not initiate verification, dispatch CI, or mutate Host Work/Runtime.

## Distinct evidence and truth scopes

- A GitHub Actions Check Run at an exact SHA, with its original Check Run ID,
  app, name and completed/success result, may be reused as evidence that
  THAT CHECK finished successfully. It is NOT a theorem about every
  consumer, a production installation, an actual Agent task, or a
  different SHA.
- A missing, failed, skipped or still-running current Check Run cannot be
  replaced with an older successful Check Run. Query the current existing
  provider result first; do not dispatch a duplicate.
- When the requested exact SHA has no accepted check, optional prior
  ancestor evidence may be read. The existing native convergence plan
  reports changed paths and affected verification Owner tasks, but does
  not grant formal proof reuse or close dynamic/non-Git assumptions.
- A changed SourceCut with no known affected Owner remains
  UNKNOWN_CROSS_CUT_READSET; a sibling-tip comparison or unavailable
  provider is UNKNOWN, not a PASS or a failure.
- The source consumer intentionally separates
  existingCheckReceiptReusable=true from proofReuseAdmissible=false.
  Existing LEGO graph impact projections also keep
  proofReuseAdmissible=false until real proof readset closure is
  independently established.

## Native Formal declared source-readset consumer (R2)

For a question about WHICH Formal source inputs changed (rather than
whether a proof remains valid), opt in to the independent read-only
source comparison:

    python3 tools/repo/evidence_validity.py --current-sha FULL_CURRENT_SHA --prior-sha FULL_ANCESTOR_SHA --formal-source-delta

The comparison reads the historical Formal producer's SOURCE_FILES
declaration at BOTH immutable Git cuts using static Python AST parsing,
never historical Python execution. It reuses the native Git ancestry
and Git tree object-membership reader. Each file must be a regular Git
blob where declared. Added/deleted proof files and modified mode/blob
objects are genuine changes, not a guess from path names.

The independent formalDeclaredSourceDelta is one of:
- UNCHANGED_DECLARED_SOURCE_INPUTS: exact set and mode/blob identity;
- CHANGED_DECLARED_SOURCE_INPUTS: declaration or member changed;
- UNKNOWN_DECLARED_SOURCE_INPUTS: native source relationship or declaration
  cannot be qualified.

An unknown Formal delta must not erase an independently qualified
GitHub Check Run PASS. The field declaredSourceReadsetComparisonComplete
means ONLY declared Git input equality, not closed proof/toolchain
dependencies. proofReuseAdmissible stays false in ALL branches.

Real Git observations (no solver/verification Job):
- two adjacent general-code commits: 36/36 declared Formal Git path
  mode/blob pairs unchanged; source readset Green.
- a genuine historical Formal verifier change: the declared input
  set expanded from 33 to 36 members and two tracked Git member
  identities changed; source readset Red.
Neither source comparison claims a prior formal result can be
reused without its original trusted execution/tool/environment receipt.
The existing Formal producer itself already emits sourceBlobs, toolBinaries,
Alloy resources, observed Z3 ELF dependencies, and 21 proof probes with
pre/post checking. Its CI consumer separately validates that exact
receipt. Keep these natural producer and consumer capabilities; do not
create a competing proof source.

To qualify a prior formal proof across commits still requires the
ORIGINAL trusted proof receipt, verifier/toolchain/resources, formal
assumptions and real implementation/consumer readset closure. Static
source comparison alone is NOT a proof-reuse grant.

Harness consumer: Generic Harness Agent Run and Runtime ToolBridge
carry nonverification work such as compilation, research experiments
and browser actions. Do not string-match or silently skip generic
workspace.exec actions based on this report. A verification-specific
Caller-admitted exact Tool/Task scope and original evidence identity
would be necessary for safe automated no-dispatch; it is not yet built.
For now, this read-only query is source evidence for Agent cognition
and scoped verification planning.

## Status contract

| Disposition | Consequence |
| --- | --- |
| REUSE_CURRENT_RECEIPT | Reuse same-SHA named GitHub Check Run outcome; no repeat run |
| OBSERVE_EXISTING_RUN | Current check is already in flight; do not start another |
| INVESTIGATE_EXISTING_RESULT | Current check completed without PASS; read that result |
| SOURCE_AFFECTED | Native Owner selector identifies affected tasks; inspect real new obligations |
| UNKNOWN_CROSS_CUT_READSET | No affected native task, but no cross-SHA proof-readset closure |
| UNKNOWN_SOURCE_RELATION | Git ancestry / source delta cannot be qualified |
| UNKNOWN_NO_ACCEPTED_EVIDENCE | No qualified current or prior successful result |
| UNKNOWN_PROVIDER_OR_SOURCE | GitHub provider or exact native Git identity unavailable |

## Nonfictional consumer evidence

On actual GitHub source commit
9df78f24899eac718d563e5686d973a9bbb398c6,
the read-only CLI observed GitHub Check Run 132064192546:
root-verification, app github-actions, completed/success.
Disposition was REUSE_CURRENT_RECEIPT. No CI or test replay occurred.

The new bounded tests exercise provider paging, exact SHA/app identity,
pending and failed Check Runs overriding earlier PASS, unrelated commits,
unknown/empty readsets, immutable ancestor ordering, malformed provider
output, and finite decision-state combinations. These are part of the
existing repository CI pytest collection, not a new test framework.

## Remaining P0 / P1 capabilities

P0: Produce exact proof readset + verifier config + dependency/consumer
closure + external assumption receipts at the natural verifier Owner.
GitHub metadata alone cannot authorize reuse across commits.

P0: Harness Agent verification-task selector must consume this existing
read-only decision before scheduling a replay. The CLI and Agent guidance
do not yet enforce remote Harness/Runtime scheduling.

P1: Mature red-green incremental calculation with scoped dependency
closure and a proof-evidence argument (GSN/Assume-Guarantee) on only
those new source/business consumers that need cross-SHA reuse.

P1: Strict source/model/implementation/consumer refinement when changing
the actual semantics, using existing formal tools. Unchanged formal
models should not be rechecked every Agent turn.

P2: Empirically measure duplicate checks avoided and false positive
reuse as real Agent consumer metrics. Do not invent a percentage from
synthetic test counts.


## R4: Real PR merge-SourceCut consumer correction (2026-11-14)

Actual user-facing failure observed on existing PR #2182: GitHub Actions
root-verification Check Run 132147168403 on PR Head
ef001b0d3e111721bcca856be960a6027737bb77 was SUCCESS and
workflow 43499713609 published Artifact 14073198750. The published
Artifact name and its original 21-probe/36-source/8-tool report instead
bind GitHub's actual checkout/verification SourceCut
72d97e758f22383cf0a464a3ea5e08d5f9f0aad5. This is the synthetic
PR merge commit with parent 1 equal to exact Base
5f6a0d1f93024c8992a5d78d61771ad5a0fbbf5a and parent 2 equal to
exact PR Head. Previously the consumer guessed Artifact name and
report sourceCut from the Check Run Head, so it failed to find
a successful original proof.

The repaired read-only consumer follows the actual GitHub:
Check Run -> original Workflow Run -> complete original Artifact list.
It requires one unexpired matching Formal Artifact, exact workflow
identity, canonical repository, bounded Artifact size, digest metadata,
and exact original Git commit identity. If the Artifact SourceCut differs
from Workflow Head, an explicitly sourced PR event and exact Git
two-parent merge relation must establish the difference. A rejected,
missing, duplicate, expired, unrelated or forged Artifact is UNKNOWN,
never a pretext for rerun or proof admission.

The execution-input-versus-candidate comparison deliberately reads
the actual report execution SourceCut and the candidate Git commit as
TWO IMMUTABLE SOURCE SNAPSHOTS, without making an ancestral-history
claim. The old --formal-source-delta is still a separate ancestral
change-history query; when the PR actually verified a synthetic merge,
the two comparators answer different questions. The actual PR readback
returns UNCHANGED_DECLARED_SOURCE_INPUTS for all 36 native Formal
source inputs between merge and PR Head, but
proofReuseAdmissible=false, because dynamic/toolchain/real consumer
closure and cross-run evidence validity are not established.

Historical Formal SOURCE_FILES is now read with native
--no-replace-objects so local Git refs/replace cannot substitute the
historical declaration for an otherwise immutable Git object tree.
The existing original blob/mode membership reader and graft-free
Git native ancestry protections remain reused rather than copied.

This is concrete evidence identity interoperability, NOT a new
Harness permission gate, mathematical proof, or false current deployed
status. For a verified Agent business/task claim, its natural owner
must still define exact applicability and consumption.

## R3: retain the original Formal verification receipt (2026-11-14)

Problem: tools/formal/verify.py already emits a complete bounded report
covering pre/post sourceBlobs, qualified toolBinaries, Alloy/JVM resources,
observed Z3 ELF dependency snapshot and actual positive/negative probes.
The original GitHub CI validates it, but used to leave the evidence under
RUNNER_TEMP. Future Agents could only see an opaque PASS check and often
reran the proof unnecessarily.

Delivery: CI now uploads the already validated report using pinned official
actions/upload-artifact, named ordivon-core-formal-<workflow SHA>, after the
existing Formal receipt validator succeeds. It runs only when native
Formal was genuinely selected. Retention is 30 days; no new solver pass.

Optional read-only Agent consumer:
    python3 tools/repo/evidence_validity.py --current-sha CURRENT_SHA --prior-sha PRIOR_FORMAL_SHA --formal-source-delta --fetch-historical-formal-report

This resolves the official prior root-verification Check Run, checks the
linked GitHub workflow run repository and exact source SHA, then invokes
mature gh run download into a disposable directory. The reader compares
the historical report sourceCut/SOURCE_FILES set and Git blob modes/OIDs,
PASS probe inventory and tool entrypoint record shapes without executing
it. A caller-supplied local file may alternatively be examined with
--historical-formal-report PATH, but remains untrusted local evidence.

Standing CONTENT_MATCHES_DECLARED_GIT_SOURCE does NOT imply toolchain
identity is currently unchanged. Dynamic dlopen/loader and non-Git input
closure, original artifact-to-CI cryptographic linkage, installed status,
implementation refinement and real consumer success all remain UNKNOWN.
proofReuseAdmissible remains false. Unavailable or expired artifacts
do not trigger a solver rerun.

Harness architecture: this bounded verification-only evidence query is
Agent/caller cognition. Generic workspace.exec also runs compilation,
experiments, browser and physical tasks; it must not be silently suppressed
by a historic proof success. A future strict no-dispatch admission requires
one exact caller-declared verification intent and its natural owner.
