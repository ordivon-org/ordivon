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
| `RECHECK_REQUIRED` | `RECHECK_NAMED_CONSUMER` | Suggest **only** the impacted verifier/consumer, no execution |
| `UNKNOWN` | `QUALIFY_DEPENDENCIES_NOT_RERUN` | Read source/Owner assumptions, never default to whole-suite run |
| `REUSE_CANDIDATE` with known proof ref | `READ_EXISTING_OWNER_PROOF` | Read/check original Owner evidence, **not** a new test |
| `REUSE_CANDIDATE` without ref | `LOCATE_PRIOR_OWNER_PROOF` | Locate natural Owner receipt, **not** a new test |

The output is a non-executing `ordivon.agent-host-verification-action-projection`.

The CLI result is checked by the existing Draft202012 validator against
`src/ordivon_composition/schemas/agent-host-verification-action-v1.schema.json`.
The strict schema refuses impossible impact-standing/Agent-decision pairs,
`proofVerifiedByProjection=true`, `wholeSuiteRecheckRequested=true`,
an eligible CAS with no legacy WorkSnapshot, or a caller asserting
`ownerCertifiedReadsetClosure=true`. This is a typed interface check, not
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
