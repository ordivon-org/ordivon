# Host Agent verification knowledge — task-local R1 consumer

Status: **source-only non-authoritative composition / no installed or owner-proof claim**.
Source owner: Composition's existing `select_impacted_obligations`.
Direct consumer: an Agent/Harness reading **Host's current WorkSnapshot**.
This is deliberately **not** a new Host tool, proof registry, verification executor,
database table, job scheduler, cache server, or identity service.

## The business defect

A Host Work currently holds human-readable `established`, `unresolved`,
`nextActions` and `referenceRefs`. Those fields do not encode proof
dependency closure. After a new Git SourceCut or Agent conversation, repeating
every Host/Rust/PG18 test feels safe but wastes time, and it does not establish
foreign-owner live/current validity. An old proof statement alone never proves
the current target still matches its preconditions.

The existing Composition C04 selector already computes:
`RECHECK_REQUIRED / UNKNOWN / REUSE_CANDIDATE`.
Do **not** create a competing invalidation engine.

## R1 Agent read-only bridge (still supported)

`project_host_agent_verification_actions` accepts the current native Host
`work.get` response, the exact **task-local** Composition proof graph, a
changedRefs/unknownRefs delta, optional previous graph, and optional proofRefs
that **must already be in** the Work's current `referenceRefs`.

It calls the existing selector, never trusts a caller-supplied impact status:

| Composition finding | Agent decision | Side effect |
| --- | --- | --- |
| `RECHECK_REQUIRED` with a current Work proof reference | `QUALIFY_EXISTING_IMPACTED_PROOF_FIRST` | First ask the original Owner whether the changed subject has **already** passed an applicable check; only if not, recheck the affected obligation |
| `RECHECK_REQUIRED` without proof reference | `RECHECK_NAMED_CONSUMER` | Search for an Owner proof first; otherwise propose only the impacted verifier/consumer, no execution |
| `UNKNOWN` | `QUALIFY_DEPENDENCIES_NOT_RERUN` | Read source/Owner assumptions, never default to whole-suite run |
| `REUSE_CANDIDATE` with known proof ref | `READ_EXISTING_OWNER_PROOF` | Read/check original Owner evidence, **not** a new test |
| `REUSE_CANDIDATE` without ref | `LOCATE_PRIOR_OWNER_PROOF` | Locate natural Owner receipt, **not** a new test |

The output is a non-executing `ordivon.agent-host-verification-action-projection`.

The CLI result is checked by the existing Draft202012 validator against
`src/ordivon_composition/schemas/agent-host-verification-action-v1.schema.json`.
The strict schema refuses impossible impact-standing/Agent-decision pairs,
`proofVerifiedByProjection=true`, `wholeSuiteRecheckRequested=true`,
an eligible CAS with no legacy WorkSnapshot, or a caller asserting
`ownerCertifiedReadsetClosure=true`. Any old or new Owner reference is an **address**, not proof of the changed source. `RECHECK_REQUIRED` says the old *dependencies* were affected; it does not mean a verifier has not already run since the change. Only a qualified Owner result with exact changed subject, acceptance, provenance and covered readset can suppress the recheck. This avoids repeated tests after another Agent already supplied the new receipt.

This is a typed interface check, not
a proof that the natural Owner's dependencies or historical receipt are valid.
It has `workRef`, exact `expectedRevision`, inherited impact `basisDigest`,
per-proof action, summary and **an optional canonical eight-field legacy
`proposedWorkSnapshot`**. That proposal replaces *only* prior
`verification-impact:` prefixed `nextActions`, preserves established and
unresolved claims, keeps existing proof references, and adds one bounded
"prior evidence lookup — don't rerun" summary for unaffected candidates.
A subsequent Agent can read these actions via ordinary `work.get`.

The caller may, *separately*, supply the proposed snapshot to the existing
`work.snapshot.commit` CAS tool with authenticated ActorRef and
clientRequestId. This bridge does not write any Host state and never builds a
second durable proof store. Terminal Works, Rust Engagement snapshots and
unrepresentable legacy shapes get **no** commit proposal.

### R2: native Git source/readset → Agent action (no hand-built middle graph)

The existing Git source authority `tools/repo/source_history_legos.py` can
produce an immutable two-SourceCut, path-scoped `git-source-membership-delta`.
Composition already has `select_source_readset_impacts`; it cross-checks
a positive Owner source readset against that delta, then delegates to the
original C04 three-valued worklist. The **R2 connection does not invent or
reimplement proof graph propagation**.

`project_host_agent_source_readset_actions` directly accepts the native Git
delta and the Owner readset statement, reuses the exact C04 selection and
converts it to the **same** Agent action format as R1. The public CLI also
reexecutes the already-existing `_requalify_git_source_delta` native Git
query first, rejecting a forged changedRefs set, invalid SourceCut or altered
scoped Git membership. The optional `--proof-refs` must still address only
references already in current Host Work.

```bash
# First obtain the delta from the existing Git owner, with exact immutable
# source cuts and the smallest consumer-relevant --impact-prefix.
python tools/repo/source_history_legos.py \
  --repo /path/to/repo --left PREVIOUS_COMMIT --right CURRENT_COMMIT \
  --impact-prefix packages/composition/ > /path/to/git-delta.json

# Owner's readset statement is separate and may remain unqualified.
cd packages/composition
uv run python -m ordivon_composition.verification_obligation_r1 \
  agent-host-source-actions /path/to/host-work-get.json \
  /path/to/git-delta.json /path/to/owner-readset.json \
  --repo /path/to/repo --proof-refs /path/to/existing-proof-refs.json
```

**Negative dependency fence (R2 refinement).** An exact Git membership
change (added/removed file under the scoped prefix) cannot be discharged by
an old **positive** `sourcePaths` list. The existing C04 worklist now receives
one unresolved membership-closure obligation and propagates `UNKNOWN` to
unaffected candidate proofs. Known directly changed obligations remain
`RECHECK_REQUIRED`. The Agent should qualify glob/dynamic/directory
consumers first, **not** blindly replay a whole suite. Even when membership
does not change, caller-asserted `dependenciesComplete=true` is still NOT
a natural Owner certification.

Output includes the precise `sourceReadsetScope` (SourceCut, scoped Git
authority, native Git requalification via the **CLI**), and explicitly says
`ownerCertifiedReadsetClosure=false`. Native Git proves **which committed
paths differ**, not whether all dynamic/env/negative prerequisites were
observed or whether a historical verifier PASS is still valid. No current
Security Grant or external Runtime effect can be certified by this tool.

The original `agent-host-actions` graph mode remains available for non-Git
changes and typed environment/effect observations. R2 shares its one
renderer: it is a **second input route**, not a second algorithm or state
store. The previous 9 targeted R1 tests are retained; only four new
R2 scenarios plus one strict typed-output negative test (including actual Git CLI and tampered source) are added.

### Existing CLI

From `packages/composition` using the already-installed native environment:

```bash
uv run python -m ordivon_composition.verification_obligation_r1 \
  agent-host-actions /path/to/work-get.json /path/to/task-local-graph.json \
  /path/to/changed-refs.json \
  --unknown-refs /path/to/unknown-refs.json \
  --proof-refs /path/to/work-existing-proof-refs.json
```

The CLI only reads files and prints JSON; **do not launch a Runtime Job merely
to read a file**. Use the existing Harness/Runtime capability when a real task
requires running this computation. For an authenticated production workflow,
the natural Owner must supply and qualify Work, SourceCut, dependency readsets,
prior proof receipts and any live/currentness witnesses. This adapter cannot
authenticate caller-supplied JSON or certify an installed binary by itself.

## R4: natural GitHub Owner justification with finite AND/OR support

R4 is a narrow **workflow completion** consumer, not a full domain-proof
registry. The source module github_justification_r1.py reads Git HEAD and
native GitHub Actions run records with the installed gh CLI; it **never**
accepts caller-authored PASS as Owner evidence or schedules a workflow.

A task-local contract identifies the exact GitHub owner/repository, current
immutable Git HEAD, and nonempty Claims. Each Claim binds to the existing
Host WorkRef and has an **OR of alternative Justifications**, each containing
an **AND of required GitHub run IDs and exact workflow names**. Every run
reference must already be in current Work referenceRefs.

- A path supports a narrow workflow-result requirement only when every
  required run has matching repository, run ID, Git SHA, workflow name and
  completed/success Owner result.
- A stale successful run on an old Git SHA is SOURCE_MISMATCH. A separate
  valid alternative can still support the same workflow requirement.
- A failed, unavailable, unfinished, or mismatched Owner record is UNKNOWN
  as support for the requested workflow-completion claim; it is NOT evidence
  that a domain Claim is false.
- The result always says domainClaimVerified=false and creates zero new
  GitHub/Runtime verification Jobs. It does not prove full dynamic/negative
  readset closure, installation, Security authorization or Research quality.
- It emits an optional unchanged eight-field Host WorkSnapshot proposal,
  replacing only previous verification-justification-prefixed nextActions.
  The native Host CAS update, if needed, is **a separate authenticated act**.

The existing Composition command is:

    uv run python -m ordivon_composition.verification_obligation_r1 \
      agent-host-github-justifications /path/to/host-work.json \
      /path/to/justification-contract.json --git-repo /path/to/git/repo

The contract has kind=ordivon.github-workflow-justification-contract,
repo=owner/repo, targetSourceCut=EXACT_HEAD, and claims with id,
consumerRef, anyOf paths (each with id and allOf edges of evidenceRef
github:run:RUNID plus workflowName). This mode deliberately does not infer
arbitrary domain truth from the caller's chosen proof formula.

**Real consumer receipt.** On PR #2185 exact head
c9daf823040b2a9bd7f5543b778a68cd937bbd07, native GitHub Owner reads
returned old Monorepo Required 43490396164 as SOURCE_MISMATCH; current
Monorepo Required 43567631728 and Monorepo CodeQL 43567631871 were
completed/success for the exact current SHA. One OR Claim used the new
alternative, while a separate AND Claim required both current runs.
Both workflow-result evidence requirements were satisfied, domain claims
remained unverified and no new verification Job was started. The actual Host
Work was committed rev4 -> rev5 by native CAS and independently read back
by Gateway with matching Snapshot digest. This is semantic handoff, NOT
an independently authenticated second Agent.

The new strict Draft202012 JSON Schema prevents false domain PASS, fake
execution counts, ambiguous status/action pairs and malformed identity tokens.
The abstract axiom-free Lean support calculus at formal/GitHubJustification.lean
proves five properties: support requires one all-matched path, a valid
alternative suffices, an unmatched dependency in every path blocks support,
adding matched evidence preserves support, and an empty OR has no support.
Those abstract theorems do **not** prove Python/GitHub API/Host CAS refinement.

**Thought modules:** Truth Maintenance System (Justification support),
Build Systems a la Carte verifying traces, in-toto/SLSA subject separation,
Pact exact consumer-version compatibility, formal-first and CQRS.

**Logical modules:** current Consumer Claim -> OR paths -> AND required Owner
evidence -> exact SHA/workflow qualification -> narrow workflow-result
support -> non-executing Agent nextAction -> Host Work current reentry.

**Capabilities:** reuse native Git and gh CLI; new bounded source-only Python
AND/OR projection + strict schema; five Lean theorems and targeted tests;
reuse existing Host WorkSnapshot CAS and Gateway read path. No second
evidence database, no new Host MCP tool or Runtime scheduling responsibility.


## R5: Join verified workflow evidence to exact C04 consumer impact

**Use case:** after a changed Git SourceCut, the Agent has a new completed
GitHub run but also an incomplete, caller-declared dependency readset. Does
it rerun CI, or can it reuse the workflow result without overclaiming
application/domain correctness?

The R5 mode extends the **same** existing
\`agent-host-github-justifications\` command; it adds two optional,
all-or-nothing inputs and reuses the existing native Git delta
requalification and existing C04 \`select_source_readset_impacts\`.
There is no new dependency selector, fact registry, execution policy or
Host MCP tool.

\`\`\`bash
cd packages/composition
uv run python -m ordivon_composition.verification_obligation_r1 \
  agent-host-github-justifications \
  /path/to/current-host-work.json \
  /path/to/task-local-gh-workflow-justifications.json \
  --git-repo /path/to/repo \
  --git-source-delta /path/to/native-git-scoped-two-cut-delta.json \
  --source-readset-evidence /path/to/owner-readsets.json
\`\`\`

The \`source-readset-evidence.items[].id\` set must be identical to the
Justification \`claims[].id\` set, not guessed from textual similarity.
Each readset is bound to the exact current Git SHA and scoped paths.
The CLI independently recomputes the claimed Git delta before impact
selection and still reads live GitHub run records through \`gh run view\`.
However, readset \`dependenciesComplete=true\` is **only caller input**:
positive readsets never become Owner-certified negative/dynamic/environment
dependency closure.

The output distinguishes three separate dimensions:

1. **Owner workflow status:** exact completed/successful SHA and workflow
   means \`EVIDENCE_REQUIREMENTS_SATISFIED\`, *only for that workflow fact*
2. **C04 source impact:** \`RECHECK_REQUIRED\`, \`REUSE_CANDIDATE\`, or
   \`UNKNOWN\`; Git file additions create the known negative-membership
   \`UNKNOWN\` fence for otherwise apparently unchanged positive readsets
3. **Domain Proof:** always \`UNKNOWN_NOT_OWNER_CERTIFIED\`; no domain PASS,
   no claim of full readset closure or new verifier execution

The action logic is intentionally bounded. A matching current Owner
workflow with changed input means
\`CURRENT_WORKFLOW_ALREADY_CHECKED_QUALIFY_DOMAIN\`: do not repeat that
identical workflow just because something changed; qualify separate
domain/source assumptions first. A matching workflow with an \`UNKNOWN\`
readset instead yields \`CURRENT_WORKFLOW_KNOWN_READSET_UNKNOWN\`.
An unchanged candidate similarly remains domain unqualified. A missing,
failed or incomplete Owner result yields
\`LOCATE_CURRENT_OWNER_RESULT_BEFORE_SCOPED_RECHECK\`, never an automatic Job.

**Real consumer evidence (Git c9daf823 → 73d649fd).** The actual Git
diff in packages/composition added four files. At the exact newer commit,
native GitHub Required run 43575031656 and CodeQL run 43575031634 each
completed successfully; older run 43567631728 belongs to c9daf823 and
was correctly rejected for the current target. Two claims had changed
positive source inputs and became \`RECHECK_REQUIRED\` yet had already
completed their exact current Owner workflows. A third claim referenced
an unchanged positive source path, but the new-membership negative
dependency fence made its impact \`UNKNOWN\`. All three **domain proof
applicabilities remained UNKNOWN**, and **zero** verifier Jobs were
created by this projection. The actual Host Work
\`work:ordivon:host-agent-proof-applicability-r3:20261114\` was
separately updated by normal Work CAS from revision 7 to 8 and Gateway
read back the same current snapshot.

Strict Draft202012 type checks now reject impossible combinations of
Owner standing, C04 impact, decision, and domain authority, as well as any
fabricated \`ownerCertifiedReadsetClosure=true\` or
\`wholeSuiteRerunRequested=true\`. The existing Lean file now contains
additional abstract *no domain reuse without independently closed
readset and domain Owner proof* obligations; this **does not prove**
Python-API or installed Harness refinement. R5 did not establish
post-deploy currentness, a second authenticated Agent Principal, or
cross-domain proof applicability.

**Thought LEGOs:** TMS reason maintenance, Bazel/Build Systems à la
Carte incrementality, Assume–Guarantee scope, in-toto provenance,
three-valued conservative reasoning, CQRS. **Logical LEGOs:**
Claim-ID ↔ existing C04 obligation; immutable Git delta;
native Owner workflow result; justification AND/OR; source impact;
domain-closedness unknown; Agent action; Work.current handoff.
**Capability LEGOs:** Existing Git provider and C04, existing GitHub
Owner read, reused \`agent-host-github-justifications\` interface,
stricter JSON Schema, Lean abstraction/refinement tests, actual Host
CAS and Gateway readback.


## LEGO 2.1 and thought modules

`ell = (I, O, S, pre, post, inv, eff, c, epsilon, prov, unfold)`

- **I:** current typed Work response, finite task-local authority/proof graph,
  changed/unknown refs, existing Work proof references, optional prior graph.
- **O:** per-proof Agent decision + summary + optional CAS snapshot proposal,
  never a proof admission or verifier pass.
- **S:** immutable caller input; Host current Work and Git/CI/Owner receipts
  remain under their natural sources.
- **pre:** exact Work shape/revision, typed graph identities and prior proof refs
  only from current Work; owner-certified completeness remains an independent
  precondition **not** asserted here.
- **post:** changed obligations yield scoped recheck candidates; unknowns
  yield qualification; other candidates yield existing-proof lookup.
- **inv:** `REUSE_CANDIDATE != VERIFIED`;
  `UNKNOWN != FALSE`; `automaticVerifierExecution == false`;
  only `verification-impact:` action entries may be replaced;
  established evidence and existing references are preserved.
- **eff:** no external effect, no Host write, no verification run.
- **c:** bounded O(|vertices|+|edges|) Composition existing worklist plus
  O(number of Host actions); runtime/Token metrics not measured.
- **epsilon:** `UNKNOWN` for missing Owner closure, dynamics, installation
  and live state; no unfounded global success rate.
- **prov:** exact source path, Git SourceCut and task-local impact basis;
  natural Owner proof references still require authenticated readback.
- **unfold:** Agent reads Work → retrieves owner-qualified Git/Verifier
  evidence → Composition C04 impact selector → pure action projection
  → optional existing Host CAS → next Agent reads Work current state.

**Thought LEGO:** incremental build/task affected inputs (Nx/Bazel), evidence
applicability and provenance (in-toto), design by contract, assume–guarantee,
three-valued reasoning, CQRS/current state, natural-owner authority.

**Logic LEGO:** Claim → dependency closure → change propagation → impact
standing → Agent action/knowledge projection → Work current snapshot.

**Capability LEGO:** Composition C04 selector (reused unchanged), existing
verification-obligation CLI (extended), Host WorkSnapshot CAS (reused
unchanged), task-local Python adapter (new), focused tests (new).

## Explicitly incomplete

1. `REUSE_CANDIDATE` still requires a real Owner verifier outcome and
   preconditions before anyone says VERIFIED/NO_RECHECK in an authoritative
   sense. Fake proofRefs and a caller's `dependenciesComplete=true` do not
   satisfy that requirement.
2. This is **not installed through Gateway**. Actual Agent/Harness consumers
   and a peer-reviewed SourceCut remain necessary before claiming real
   deployment reuse.
3. Native Git readsets can be incomplete (dynamic imports, environment,
   negative dependencies), so only the **known** affected set is selected.
4. Source proof applicability and live Security authorization are distinct.
   Never infer present-day Grant status from an old identical digest.
5. Terminal/Rust Engagement Work must not be overwritten through the Python
   legacy WorkSnapshot commit API. Read-only action rows still work.
6. Existing CI can retain broad mandatory publish gates; this feature changes
   **Agent discretionary re-verification demand**, not GitHub branch policy.

## Bounded acceptance — no repeated full validation

Only run `uv run pytest -q tests/test_host_agent_verification_actions.py`
and targeted `ruff`/JSON/architecture contracts after a change limited
to this adapter. Existing C04/PG18/Security/Rust proofs remain **prior
evidence** unless their own relevant readsets change.

Cases required: unrelated change → zero verifier runs; affected leaf →
only leaf and downstream consumer selected; unknown/unindexed source →
qualification not automatic verification; provenance ref outside Host
Work → reject; repeated projection → no duplicate Work nextActions;
terminal/Rust Engagement Work → no unsafe CAS proposal; actual CLI
produces the same projection.
