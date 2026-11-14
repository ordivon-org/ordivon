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


## R5: unpublished candidate / current provider independence (2026-11-14)

A local exact Git candidate SHA may not yet exist in the GitHub API.
Its current Check Run is UNKNOWN_CURRENT_CHECK_PROVIDER. That is neither
a known CI failure nor reason to rerun the old proof. For that
read-only case the candidate's original local Git identity is qualified
first, and independent historical source/Artifact consumers are still
permitted to inspect original evidence.

Actual readback (before publishing the candidate): PR #2182's
original GitHub root Check Run 132147168403 and Formal execution
SourceCut 72d97e758f22383cf0a464a3ea5e08d5f9f0aad5 were retrieved
while the candidate commit ec21eb7acce3b608ba0b126045888ec8722c6a54
had no GitHub check. Native Git snapshot comparison found
UNCHANGED_DECLARED_SOURCE_INPUTS for all 36 producer-declared Formal
source inputs. The local-current provider remained UNKNOWN and
proofReuseAdmissible was FALSE. No solver and no duplicate CI/Runtime
Job were launched.

A separate natural Owner consumer is already present on main:
services/runtime/scripts/agent_evidence_admission.py. Its real read-only
query on original PR #2182/Head ef001b0d3e111721bcca856be960a6027737bb77
returned EXACT_CUT_CI_OBSERVED with advice
REUSE_OFFICIAL_SOURCE_CI_RESULT_AT_THIS_CUT_NO_DUPLICATE_RUN.
That is an exact-commit CI result and does not supersede a separate
Formal input/toolchain/consumer proof. Harness archived claim
currentness is independently owned by
services/harness/scripts/check_evidence.py. Do not create an
alternative Harness authority or treat this query as a physical
Runtime no-dispatch fence.

The remaining P0 boundary is caller-specific verification intent:
the caller must identify exact claim, natural Owner, relevant
verified producer/consumer scope and accepted evidence before
a task-specific no-redispatch decision can be enforced. Generic
Harness ToolBridge/workspace.exec is also used for compilation,
research, browser and real external actions, and must not be
globally disabled on the basis of old source CI proof.

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


## R6: Typed Claim / Consumer Golden Road (2026-11-14)

### Evidence is not a generic theorem

The actual accepted PR #2182 Check Run and its original Formal Artifact
support a **narrow typed proposition**: the declared native Formal Git
input set, modes and Blob OIDs on its original execution SourceCut equal
those of a requested candidate SourceCut. They do NOT automatically prove
that a theorem applies to new toolchains, installations or consumers.

The existing read-only tools/repo/evidence_validity.py includes one
small pure Claim-to-Evidence projection, not another registry or
scheduler. The source-bound producer is still original GitHub Actions
plus the native Formal report and immutable Git tree comparator.

The finite typed contract has:

- claimKind = FORMAL_DECLARED_GIT_INPUTS_EQUAL or
  FORMAL_PROOF_APPLICABLE_TO_TARGET.
- consumerRef = agent:formal-declared-source-impact for this narrow
  scope. Any other consumer stays UNKNOWN.
- targetSourceCut = exact full Git SHA, never a mutable branch alias.
- historicalFormalReceipt = the original qualified GitHub workflow
  and Artifact plus the immutable pairwise native Formal source
  comparison, NOT arbitrary caller-controlled local JSON.
- outputs: claimSupported, evidenceRefs, nextOperation, named
  unresolvedObligations, proofReuseAdmissible=false,
  physicalExecutionAuthorized=false, verificationTaskDispatched=false.

| Requested Claim | Evidence / change observation | Decision |
| --- | --- | --- |
| Declared Git inputs equal | Original official evidence + same declared Git members and modes | SUPPORTED_SCOPED_SOURCE_INPUT_FACT |
| Declared Git inputs equal | Actual changed declared path | CONTRADICTED_SCOPED_SOURCE_INPUT_FACT; inspect only changed paths |
| Declared Git inputs equal | Missing/wrong consumer/forged or contradictory evidence | UNKNOWN with specific missing qualification |
| Formal proof applicable to target | Same declared Git inputs, but dynamic/toolchain/consumer closure not established | UNKNOWN_UNCLOSED_PROOF_ASSUMPTIONS |
| Formal proof applicable to target | Declared Git inputs changed | AFFECTED_PROOF_SOURCE_INPUTS; inspect change and missing assumptions |

Query BOTH Claim grades from ONE original GitHub Artifact download:

    python3 tools/repo/evidence_validity.py --current-sha FULL_TARGET_SHA --prior-sha FULL_ORIGINAL_PR_HEAD_SHA --fetch-historical-formal-report --claim-kind BOTH

The stronger Claim never becomes true based merely on a static source
comparison. An arbitrary installed Gateway or Domain consumer cannot
reuse this source-input-only evidence through a scope substitution.

### Actual live consumer on prior PR #2182

Prior PR Head: 06407a629e74e1782513a0a1cde00a008b2911a0.
Original Formal execution Git merge:
d841a022afd09fe9b214c91041db9baf6da8063f.
Official GitHub Check Run and original Artifact returned
CONTENT_MATCHES_DECLARED_GIT_SOURCE and
UNCHANGED_DECLARED_SOURCE_INPUTS for 36 declared Git members.
The source-equality Claim was SUPPORTED_SCOPED_SOURCE_INPUT_FACT;
the stronger proof-applicability Claim was
UNKNOWN_UNCLOSED_PROOF_ASSUMPTIONS, with two missing obligations:
qualify toolchain/dynamic dependencies and
qualify model/implementation/consumer refinement.
No additional solver or duplicate verification Job was executed.
Earlier valid same-SHA official CI results remain reusable as their
original Check Run outcome only.

### Recursive LEGO R2.1 representation

I = typed Claim, consumerRef, target SourceCut, original Formal evidence.
O = scoped result, evidenceRefs and minimal unresolved proof obligations.
S = absent, mismatched, unchanged, changed and unclosed input premises.
pre = original GitHub/Artifact/Git binding qualified, else UNKNOWN.
post = source input equality supported only with valid declared readset.
inv = claimSupported for source equality NEVER grants broader
proofReuseAdmissible, production acceptance or physical Job admission.
eff = none; the evaluator has no execution effects.
c = original Artifact read once plus bounded pure Claim projection;
real resource savings require real measured consumers.
epsilon = toolchain, OLEAN/loader and dynamic non-Git dependencies,
model-to-implementation and installed consumer remain UNKNOWN.
prov = qualified source commit, original GitHub Artifact/Run and
focus-scoped native tests with negative controls.
unfold = original SourceCut -> readset comparison -> typed Claim ->
missing obligations -> caller-specific decision.

### Remaining P0 and P1

P0: A caller-specific VerificationIntent must bind exact Claim,
consumer, SourceCut, natural Owner and existing Runtime Job identity,
with a true atomic admission boundary. The existing read-only
Runtime agent_evidence_admission.py and Harness check_evidence.py
are separate natural consumers, not physical no-dispatch gates.

P0: Proof dynamic/toolchain/assumption closure and
model-to-implementation/consumer refinement are still UNKNOWN.
Source equality cannot replace those obligations.

P1: Only for real consumers, refine this bounded decision against
formal properties and independently falsify implementation
conformance. Do not delete unrelated tests before stronger evidence
covers their exact Claim.


## R7: Original Formal selected-tool comparison without proof replay

R6 proves only declared Git input consistency. R7 exposes the original
Formal producer's selected tool-input observations for an explicitly
requested toolchain premise, instead of repeating its expensive
mathematical solvers.

The official historical GitHub Formal report already has 8 selected
mise executables (path/version/SHA256), Alloy JAR and JVM resource
paths/SHA256 and Z3 loader scope, interpreter, and resolved libraries.
R7 reuses the existing native Formal verify.py read-only functions
qualified_source_cut, qualified_tool_binaries,
qualified_alloy_runtime_resources and
observed_z3_elf_dependencies at the exact local target SourceCut.
No second scanner, proof engine, evidence registry, or scheduler.

For one exact PR Head and candidate checked-out SourceCut:

    python3 tools/repo/evidence_validity.py --prior-sha ORIGINAL_PR_HEAD --current-sha CURRENT_EXACT_SHA --fetch-historical-formal-report --claim-kind BOTH --compare-current-formal-tool-inputs

This invokes one original GitHub Artifact fetch and *only*
read-only current tool observations. It never runs a solver.
formalToolInputComparison has the following bounded outcomes:

- MATCHED_SCOPED_TOOL_OBSERVATIONS: all declared selected
  original/current paths, versions, entrypoint SHA, Alloy resources,
  and scoped Z3 loader observation fields match.
- CHANGED_SCOPED_TOOL_OBSERVATIONS: changedObservedFields isolates
  exact path, version, sha256, interpreter, or resolved-library
  difference; path changes do not by themselves prove byte changes.
- UNKNOWN_TOOL_INPUT_OBSERVATION / UNKNOWN_CURRENT_TOOL_OBSERVATION:
  original or current evidence is insufficient. No automatic retry.

Even if observed tool digests agree, the record is NOT a full readset.
It does not cover Lean OLEAN, dlopen, plugins, arbitrary subprocess
inputs, environment/time, cross-host semantics, or the actual
model-to-implementation-to-consumer refinement. Both
fullReadsetClosed and proofReuseAdmissible always remain false.

Actual initial consumer at the R10 #2182 Head
b633ae7003497dddf558ae6a156e658780d0ac85 found
CHANGED_SCOPED_TOOL_OBSERVATIONS for all 8 tool entrypoint records,
Alloy JAR/JVM resource records and Z3 loader path/libraries.
Each record may differ only in path; R7 now outputs per-field
differences to prevent conflating location and changed executable
bytes. Historic original GitHub CI PASS and synthetic merge
SourceCut are not the currently installed server state.

Recursive LEGO R2.1: I=(official prior Artifact, target current
SourceCut, existing formal producer); O=(scoped tool field diffs and
remaining assumptions); S=(MATCHED/CHANGED/UNKNOWN);
pre=(official original receipt and current native producer Git binding);
post=(only those selected tool observations);
inv=(never mathematical proof reuse, full readset, or physical admission);
eff=(read-only tool binary/loader observations);
c=(selected tool hashes/finite loader inputs, no solver runtime);
epsilon=(unclosed imports, plugin/dlopen, temporal/currentness,
model/consumer refinement); prov=(GitHub Run/Artifact, native mise);
unfold=(original evidence→current snapshot→changed fields→next obligation).

Still P0: closed non-Git dynamic readsets via real hermetic
execution assumptions; Caller-level VerificationIntent + native
PostgreSQL atomic Job admission (do not reimplement Runtime).


### R7 real obligation-planner consumer (not a proof executor)

On the same original official #2182 GitHub Artifact, a later local
candidate (source snapshot df50d7ca80a41b97c1c2bf989337eac881dd3c46)
had identical 36 declared Git Formal inputs to execution SourceCut
f40a5b85d0b674435ab393802aad7889f3a4bbde.
The selected tool differences were field-qualified: all eight entrypoint
records changed absolute path; Kani alone also changed executable
SHA256, the seven other selected executable SHA256 values were equal;
both Alloy resource digests were equal despite path drift; and Z3
interpreter path/resolved library map changed. These are specific
cross-environment observations, not mathematical counterexamples.

When the actual optional comparison is available to the same Typed Claim
call, the stronger FORMAL_PROOF_APPLICABLE_TO_TARGET decision becomes
AFFECTED_PROOF_TOOL_INPUTS, with obligation
INSPECT_CHANGED_SELECTED_FORMAL_TOOL_INPUTS and its exact observed field
map. If the Git Formal source inputs also change, the decision becomes
AFFECTED_PROOF_SOURCE_AND_TOOL_INPUTS. In both cases the unresolved
toolchain/dynamic and model/consumer assumptions remain present;
no PG Job is dispatched, no other Claim is promoted, and full proof
reuse still remains FALSE/unknown. Missing or unqualified observations
fail closed and preserve the previous UNKNOWN path.
