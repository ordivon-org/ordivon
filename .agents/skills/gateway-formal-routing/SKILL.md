---
name: gateway-formal-routing
description: Verify and refactor Ordivon Gateway as a thin Owner-routing MCP adapter through route identity, TLA+ safety properties, Python conformance, and native consumer evidence.
compatibility: Needs Ordivon checkout and Gateway Python dependencies. TLC needs Java 11+ and a digest-verified pinned JAR.
license: MIT
---

# Gateway Routing Formal Verification — R2.1 thought/ability LEGO

Use for Gateway routing changes, capability discovery, execution forwarding,
SourceCut/Owner boundary, formal-verification migration and obsolete-worker cleanup.

## Contract
I: operator route map, requested capability and verified ingress.
O: exact routed Owner operation or rejection.
S: lookup, validate, route and reject.
pre: each map key equals the CapabilityRoute.capability of its value.
post: forwarded capability identity equals the declared route identity;
the selected Owner equals the exact route Owner.
inv: ForwardedImpliesExactRoute and RejectedNeverForwards.
eff: owner RPC is outside the routing model; Job/Host authority never moves.
c: finite explored state count; real runtime resource cost UNKNOWN.
epsilon: full model-to-Python refinement UNKNOWN; installed behavior UNKNOWN
without exact installed consumer evidence.
prov: pinned Git commit, TLC output, bounded Python check, native readback.
unfold: specification -> TLA+ model -> model check/negative controls ->
source conformance -> real consumer -> installed candidate proof.

## Agent procedure
1. Bind the intended property, natural consumer, current Git SourceCut and
   previous evidence receipt including its verifier/toolchain and assumptions.
   Read exact PR head SHA and already completed native CI/Owner/Formal checks.
   Before manually rerunning a completed GitHub check, query
   tools/repo/evidence_validity.py with the exact --current-sha and
   --check-name root-verification. The actual GitHub Check Run metadata
   plus existing native Owner source impact are reusable evidence inputs.
   existingCheckReceiptReusable is strictly same-SHA Check Run outcome;
   proofReuseAdmissible remains false for broader formal/external claims.
   If the decision specifically needs an original Formal execution receipt,
   pass --prior-sha ORIGINAL_FORMAL_SHA --formal-source-delta
   --fetch-historical-formal-report. It uses original GitHub Check Run
   and official gh run download, verifies the original Git members and
   retains UNKNOWN for dynamic/toolchain/installation assumptions.
   No automatic solver rerun is triggered by missing/expired artifacts.

   For specific Formal source-input impact, add --prior-sha
   FULL_ANCESTOR_SHA --formal-source-delta to compare both historical
   declared SOURCE_FILES sets and exact Git modes/blobs without executing
   old Python or a proof. An unchanged declared input set does not close
   solver/toolchain, dynamic environment or real consumer assumptions.

   Do NOT execute a verifier merely because another Agent turn began.
2. Use the existing tools/repo/convergence_plan.py changed-source Owner
   selection and check_architecture_docs.py --agent-impact to locate affected
   declared consumers. Neither projection alone admits formal proof reuse:
   partial/dynamic readsets and non-Git assumptions retain UNKNOWN.
3. If source, proof scope and assumptions still match the accepted receipt,
   report REUSED_SCOPED_EVIDENCE without rerunning. If a proof dependency,
   model, checker, assumption or novel consumer obligation changed, run only
   the affected formal/model check and relevant negative control. The\n   unchanged Formal models actually PRESENT at the selected SourceCut\n   require no new TLC replay.
4. Run bounded Python route conformance and the relevant native Gateway
   consumer tests only for impacted implementation/readset or an explicit
   fresh release gate. Run full gateway:verify when Gateway behavior
   changed and the existing CI source selection has not yet qualified it;
   do not duplicate an exact completed CI PASS.
5. Require live installed Gateway -> Runtime/Host readback only when the
   decision involves actual installed generation, identity, external
   assumptions or physical effects. An older real observation remains
   historical evidence, not automatically current state.
6. Report REUSED_SCOPED_EVIDENCE, NEWLY_VERIFIED, AFFECTED_RECHECK,
   UNKNOWN_DEPENDENCY and FALSIFIED separately. No Git-only source delta,
   missing consumer observation, or no-hit result can authorize false proof
   reuse. Retire redundant tests only when a stronger validated refinement
   covers the same actual consumer claim.

## Human
Review the claim/evidence ledger before using a candidate release. Reuse
TLA+, CrossHair (pure Python only), static typing and existing release scripts.
Do not invent a second policy decision or rollout framework.

## B03 Owner observation: strict truth contract

Pure Owner observation contract: Runtime status fields configured and available
must be literal booleans. available=True requires configured=True. A truthy
string, integer, missing field, or contradictory pair is not positive evidence
and must carry an observation error. Gateway retains its non-authoritative
boundary; malformed observations are UNKNOWN, not proof Runtime is down.

Agents: run uv run python formal/check_owner_status_contract.py through the
existing Gateway verification target. The checker enumerates 100 adversarial
status pairs through execution and Artifact projections. Compare with live
runtime.describe and Gateway capability.describe; synthetic enumeration is
not a physical RPC success.

Humans: inspect capability_projection.py and capability_catalog.py for the
implementation; read observation errors before classifying Runtime unavailable.
Retain real MCP consumer readback and native Windows identity and PG integration
checks where appropriate.

## R04 Transport composition LEGO (capability + reasoning)
Gateway upstream transport owns only HTTP sockets and is explicitly scoped to
McpOwnerCaller. Prefer upstream MCP SDK Client protocol negotiation and
httpx2 connection pooling; do not replace SDK with a custom JSON-RPC client.
Auth material is read on each request through OwnerEndpointAuth, including
when a connection is reused. MCPServer lifespan must close pooled clients.
Validate exact Owner semantics through independent real loopback RPCs, not
only mocked connector calls; do not infer production latency from loopback.
Preserve long-running Runtime Jobs on HTTP cancellation; never blindly replay
an execution submission after uncertain delivery.


### PR synthetic merge and original Formal identity

For a pull_request workflow, GitHub reports the Check Run at PR Head
while Formal executes the synthetic merge SourceCut. Query the existing
--fetch-historical-formal-report consumer and use
verifiedExecutionSourceCut, sourceRelationship and
executionInputsVsCandidate. Only an exact two-parent native Git match
allows the source label distinction; ordinary previous/current
--formal-source-delta requires ancestor history. Neither static
comparison proves solver/toolchain continuity or real Owner acceptance.


### Typed Claim applicability at the exact Git SourceCut

To avoid evaluating the same original Formal Artifact twice, pass
--claim-kind BOTH with exact --current-sha, original --prior-sha
and --fetch-historical-formal-report to the existing repo consumer.
FORMAL_DECLARED_GIT_INPUTS_EQUAL can be supported only for the
declared source-input comparison consumer. The much stronger
FORMAL_PROOF_APPLICABLE_TO_TARGET remains UNKNOWN until toolchain,
dynamic dependency and model-to-real-consumer obligations close.
Do not treat the GatewayToolVisibility model on separate unmerged
PR #2174 as if it were already present in a different SourceCut.
This Skill grants no Harness or Runtime execution authority.


### Optional selected-tool observation, not another proof run

When the precise missing premise concerns the actual selected
toolchain, pass --compare-current-formal-tool-inputs together with
the existing --fetch-historical-formal-report and exact Git cuts.
This calls the original Formal producer's read-only mise, Alloy
and Z3 helper functions, never the solver main(). Inspect
changedObservedFields to distinguish path-only drift from SHA.
Even identical selected bytes do NOT close Lean OLEAN imports,
dlopen/plugins, runtime time/environment or installed consumer
scope. Ordinary Gateway requests need not run this optional query.


When selected tool inputs differ, the stronger Typed Claim emits
AFFECTED_PROOF_TOOL_INPUTS with an exact
INSPECT_CHANGED_SELECTED_FORMAL_TOOL_INPUTS obligation. This is an
inspection instruction, NOT permission to dispatch a verification Job;
the runtime/caller identity and existing check receipts remain separate.


### A new contained Z3 consumer, not the original multi-solver proof

When the specific Media Loudness IEEE-754 SMT model needs a new
verification, tools/formal/contained_z3.py can execute the original
Git-bound model under Bubblewrap with a selected immutable
Z3/ELF input bundle and no host filesystem except those bound
files. It requires SAT/UNSAT/SAT and negative guest denial of
host /etc/passwd. This is a narrow new consumer, never a proof
that original historical Lean/Alloy/Z3 results can be reused.
Do not generalize or dispatch it for unrelated Claims.
