# Host Owner — Agent navigation

This file is a **scoped navigation pointer**, not a new policy registry, database authority, MCP tool surface, or release gate. Follow the repository-level `AGENTS.md` and the current Host source.

## Start with current facts

- Actual interface inventory: [mcp-surface.json](mcp-surface.json). Discover the installed MCP `tools/list` before use; a source manifest does not prove installed currentness.
- Current Host contract and operator guidance: [README](README.md) and [Human/Agent Owner Guide](docs/HOST_OWNER_GUIDE.md).
- Formal scope: [Social Work Fabric R2 Specification](docs/SOCIAL_WORK_FABRIC_R2_SPEC.md) and [implementation receipts](docs/SOCIAL_WORK_FABRIC_R2_IMPLEMENTATION.md).
- Owner decomposition: [LEGO R3 plan](planning/lego-plan-r3.json); repository graph verifier currently also consumes [R1 graph carrier](planning/lego-plan-r1.json). The plan is source evidence, not installed truth.

## Locate the actual owner

- **Work semantic state:** `src/ordivon_host_v2/work_store.py` (CAS), `work_queries.py` (reads), `work_relation_commands.py` (internal DAG relation mutation).
- **Message search:** Native GIN array_ops on Unicode codepoint 3-grams for 3+ CJK, with exact strpos post-filter; short CJK still uses strpos and other terms FTS. See migrations/versions/0013_unicode_substring_gin.py and the Owner Guide.
- **Collaboration:** `social_store.py` composes `social_space_*`, `social_topic_*`, `social_message_*` and `coordination_intent_commands.py`.
- **Attention:** `attention_store.py` (subscriptions/acks), `attention_projections.py` and `attention_sql.py` (rebuildable navigation).
- **MCP:** `mcp_server.py`, `mcp_tool_registration.py`, `mcp_*_tools.py`; do not invent additional northbound tools.
- **Schema/release:** `migrations/versions/` via Alembic; `packaging/` handles immutable release and systemd.
- **Validation:** `mise run verify` for source gate, `mise run test:postgres:disposable` for isolated real PostgreSQL 18, and `mise run formal:reply-source` (Python PEP316 obligations) and `mise run formal:work-graph` (bounded Z3 DAG model and negative control); run `mise run formal:dag-theorem` for the axiom-free general Lean DAG theorem using the repo's pinned Lean toolchain for the scoped pure source obligations. For Unicode-gram candidate soundness, run `mise run formal:unicode-search` (axiom-free Lean theorem), then verify PostgreSQL `host_unicode_ngrams3` refinement with `mise run test:postgres:disposable`; neither proof alone proves installed behavior. A skip is not a database PASS.

## Before another verification run: consume existing proof applicability

The repeated Rust/PG18/Gateway regressions are **not** automatic Agent work.
Check the existing Host Work.current `established` / `unresolved` /
`referenceRefs` first, then use Composition's existing C04
`select_impacted_obligations` (via read-only `agent-host-actions`
CLI), or the **native Git/readset route** `agent-host-source-actions` when
Git owns the immutable scoped path delta; the latter re-queries the actual
Git SourceCut rather than trusting a caller's changedRefs JSON. Both routes
use C04's **same** selector and Agent action renderer. Unchanged inputs generate **existing
Owner-proof lookup**, unknown dependencies generate **qualification**, and
actual changed dependencies generate **only scoped recheck candidates**. Even if a dependency changed, read a matching **already-updated** Owner receipt from current Work before invoking a verifier again; `QUALIFY_EXISTING_IMPACTED_PROOF_FIRST` records this alternative without declaring PASS.
The projection may propose an eight-field legacy `work.snapshot.commit`
CAS payload which embeds next Agent actions; no Host schema/table is added.
Composition now validates both Agent action CLI outputs using a strict Draft202012
JSON Schema; impossible status→action pairs and false verifier-PASS claims are rejected.
Never promote `REUSE_CANDIDATE` to VERIFIED or trust unauthenticated proof
references. No new Runtime Job is needed for an unchanged Owner receipt.
Source: [Composition consumer R1](../../packages/composition/docs/HOST_AGENT_VERIFICATION_APPLICABILITY_R1.md).
**This source bridge is not yet an installed Gateway tool.**

## Real GitHub Owner workflow evidence and Justification (source-only R4)

For a GitHub workflow completion at one exact Git SHA, the Composition
agent-host-github-justifications consumer reads natural gh run view records
for evidence references **already present** in current Work. It evaluates
AND/OR support paths under current SourceCut and workflow identity.
A prior successful run on an older SHA does not substitute for a new run;
an independently complete path may prevent an unnecessary rerun.
This is a narrow evidence-requirement qualification, not a domain VERIFIED,
full dependency closure, installed policy or Agent authorization claim.
Only a separately authenticated Work CAS may record generated nextActions.
See packages/composition/docs/HOST_AGENT_VERIFICATION_APPLICABILITY_R1.md.

## Host Agent R5: exact workflow reuse is NOT domain proof

The same Composition `agent-host-github-justifications` CLI accepts an
optional exact native Git two-cut delta and caller-declared positive source
readsets. Native Git is requalified independently before C04 computes
impact. Claim IDs must bind the matching readset obligation.
A current GitHub workflow may have completed successfully *even though*
C04 reports RECHECK_REQUIRED, so do not schedule that same workflow
again merely because the source changed. Instead qualify missing
domain and negative/dynamic dependency evidence with its natural Owner.
An unchanged positive readset is not full dependency closure when new
Git members were added; keep UNKNOWN.
This is source-only; no native Harness pre-dispatch admission is installed.

## R6: green GitHub workflow is not proof a required step ran

Agent must not replace a required Job/Step result with a successful
parent GitHub workflow conclusion. The existing Composition
`agent-host-github-justifications` interface optionally accepts
`requiredJobs:[{name,requiredSteps}]` on each evidence edge.
Use original `gh run view --json jobs` Owner observations to
distinguish a uniquely completed/successful required step from a
`skipped`, missing or ambiguous one. On run 43578313957 at c24,
the Formal preflight step was actually skipped despite parent success.
This is an evidence scope boundary, not necessarily a broken workflow.
`conclusion=success` is post-continue-on-error, not raw exit outcome.
Never assert domain proof, full dependency closure or installed
Harness enforcement based on this scope.

## Agent re-entry and effects

Use `work.get → attention.reentry → topic.resume → owner-native reference readback → work.snapshot.commit → cursor acknowledgment` as needed. Attention change sequence and per-topic Message sequence differ. Host never grants authentication/authorization, assigns work, schedules Jobs, or proves domain completion; Runtime, Git, Security and domain Owners retain their own truths.

For a change or cleanup, inspect the *exact real consumers*, PostgreSQL dependencies, active Work/Topic/Subscription references, source cut and installed release. Do not delete business rows because they are old or appear redundant. Prefer an existing PostgreSQL/MCP/Alembic/Pydantic capability before implementing a custom one; add no duplicate registry or event bus. Keep code reshaping separate from contract changes, and publish verification outcomes accurately.

## HTTP Host workload identity (source boundary)

**Human:** Host's native Streamable HTTP endpoint now uses the official
MCP/Starlette bearer middleware. Configure
\`ORDIVON_HOST_V2_OWNER_BEARER_TOKEN_FILE\` as a private absolute credential file;
configure Gateway's \`ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE\` with the
same credential bytes before activating the candidate. A systemd
\`LoadCredentialEncrypted\` source is preferred over copying a secret into a
repo or environment. The HTTP listener fails before bind when the Host
credential is absent or invalid. Never treat a loopback IP as authentication.
Run the real SDK consumer \`tests/test_http_identity.py\`, followed by
\`mise run host:verify\` and Gateway's native consumer tests. STDIO is a
different operator-local trust boundary and remains unchanged.

**Agent:** Authentication proves only the Gateway workload token; it
does not establish a human/agent Principal, a Host Actor delegation, or
resource-level policy authorization. Host remains the natural Owner of
Work/Space/Topic/Message state. Inspect Gateway upstream service credential
configuration, the actual installed Host HTTP app, and live rejected/accepted
request outcomes before promoting \`HTTP_AUTHENTICATED\`. Until a real
Security decision is bound to Host object/actor/effect, leave
\`HOST_OBJECT_AUTHORIZATION=UNKNOWN\`. Do not advertise a fictitious OAuth
issuer for the operator-local service token; for real federated OAuth use
the upstream SDK's \`AuthSettings\` and IdP-backed verifier.

## Host workload-credential FD continuity

**Human:** the Host HTTP bearer credential is acquired from the service-private
operator/systemd credential directory. Token verification re-reads the exact
opened file descriptor per request with POSIX no-follow and nonblocking flags;
regular-file mode, size and same-inode metadata continuity must hold before
the native MCP/Starlette bearer middleware authenticates the Gateway workload.
An unexpected FIFO or in-place mutation fails closed. This is M2M transport
authentication only, never Human/Agent identity or object-level Actor/Grant
authorization. The trusted credential directory is configured by the OS.

**Agent:** exercise test_http_identity.py with the actual TokenVerifier and
native Host HTTP app, then run host:verify. Rejection of substituted FIFO,
mutable credential bytes and wrong service bearer must not be downgraded by
an outer Gateway ALLOW. Distinguish Linux verified source behavior, unrun
Windows source behavior (Host HTTP remains POSIX only), installed service
credentials and authoritative Actor resource policy. Do not leak credential
values into evidence.
