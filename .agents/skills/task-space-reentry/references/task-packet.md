# Ordivon capability task-space packet / bounded index

General task intake Space: `space:ordivon-task-control-r1:20261101` (canonical cross-domain priority and deduplication).
Specialist proof/capability execution Space: `space:ordivon-capability-task-forum-r1:20261101`.
Hard-kernel task normal form discussion: `message:ordivon-hardkernel:task-lego-normal-form-r1:20261101`.
Do not treat the two Spaces as competing task managers or assign tasks from their presence.
**No task is assigned by Space participation.**

## Discover the current execution anchor

Use an explicit current WorkRef from the caller or a verified handoff when available.
Otherwise use the existing Host `work.list` (open state, bounded pages; follow
its returned cursor when necessary), and compare objectives with the actual
consumer and task. Read the selected candidate's exact current `work.get`
snapshot; the list is a locator, not priority or assignment. For historical
evidence, query the named terminal Work or exact revision separately. A native `NOT_FOUND` is
`HISTORICAL_REFERENCE_ONLY` for the missing pointer, not proof of absent
successors. An incomplete discovery or transport error remains `UNKNOWN`.
If no unique, relevant Work can be verified, keep the task coordinate UNKNOWN
and ask the natural owner via the existing Task Control Topic. Do not recreate
a missing Work, substitute a similarly named Work, infer authority from
participation, or silently skip an unresolved obligation.

## Receiver handoff packet: use the current Work and owner facts

```text
taskRef: exact Host WorkRef + revision (never inferred)
problemRef: named source-backed problem or typed UNKNOWN
goal/consumer: actual observable acceptance, not a file or owner title
sourceCut/readset: Git commit, dependencies/tool/environment digests or UNKNOWN
preconditions: exact authority, capabilities, stale proof/installed checks
inputs/outputs: typed, including errors/timeouts and side effects
dependency/verification graph: typed edges + UNKNOWN dynamic edges
proposed solution: DELETE / REUSE / COMPOSE / EXTEND / CREATE, with reason
proof obligations: specification vs checker vs code vs installed vs consumer
negative oracle: what MUST fail if implementation/assumptions are broken
next executable delta: one concrete native tool/test/action, no speculative PR
result: evidence IDs, unchanged consumers, residual UNKNOWN, reopen triggers
```

## R2.1 auxiliary method LEGO profile (DECLARED_CANDIDATE, not a new calculus)

`ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`:

- I: typed SpaceRef, WorkRef, optional ActorRef/cursor, authorized Skill catalog view.
- O: bounded TaskPacket or explicit UNKNOWN/BLOCKED; never execution success.
- S: Host Work/Topic/cursor *read-only projections* plus versioned Skill view; helper owns no durable database.
- pre: valid refs and permitted Host/Skill reads; fresh versions must be checked.
- post: packet points to present Work/Topic and required owner readbacks; missing facts remain UNKNOWN.
- inv: social membership is never IAM, assignment, or domain authority; Skill prose never grants tool permissions.
- eff: permitted reads and optional, separately authorized Work/Topic updates after verification; no implicit execution.
- c: bounded tool calls/messages/bytes, measured cost otherwise typed UNKNOWN.
- epsilon: packet summary is not semantics-equivalent to owner truth; omitted edges are UNKNOWN and block proof reuse.
- prov: exact Work revision, Skill instruction/package/snapshot digests, native source/build/Job evidence pointers.
- unfold: Level-0 task context -> Level-1 selected Skill body -> Level-2 named references -> Level-3 owner-native execution evidence on demand.

This is a consumer-grounded draft profile for the method Skill, **not** proof of runtime hooks or automatic entry injection.

## Cold-agent acceptance

Positive: task forum entry retrieves current root and selects only needed Skill, produces an actionable packet with exact source and no false deployment claim.

Negative: no matching work, unavailable Skills, stale Skill digest, changed SourceCut, missing dynamic consumer, or Host participation with no authorization must remain UNKNOWN/BLOCKED. No explicit Agent task -> no task assignment and no automatic write.

Do not batch read every Topic or every Skill; use bounded Host pagination and native Skill progressive disclosure.

## Cross-Agent Spec composition (on shared source or physical resource)

Use the existing Work revision and Topic, not a second registry. Publish a
bounded advisory claim with the property/subject, exact SourceCut and Spec
identity, semantic read/write/effect sets (including offline/recovery roots),
real consumer, assumptions, verifier and next action. Overlapping writes or
effects, or a write invalidating another readset, require coordination;
a message is neither an exclusive lease nor effect authorization.

A donor handoff references its exact base/head/tree, changed property,
native positive and negative evidence (Job/receipt refs), limits and
unresolved obligations. The receiving Agent independently re-reads that
subject and records acknowledgement or rejection against that exact message;
use existing message relations to reference or supersede old candidates.
Keep one agreed integration head per overlapping effect and recheck affected
assumptions if the cut changes. Preserve independent tests, do not promote
isolated green results as composed acceptance. Native merge, installation
and real consumer acceptance are distinct. Advance Work with revision CAS,
never overwrite intervening findings; a processed Topic cursor is not
acceptance. Release the physical carrier only after its unique source and
artifacts are durable and the native owner confirms release. Unknown
readsets or consumers remain UNKNOWN; do not infer them absent from silence.

## Terminal Work obligation transport (only when closing or superseding Work)

Do **not** treat `completed` or `abandoned` as a proof that all entries of
`unresolved` vanished. A successor WorkRef in `referenceRefs` is navigation,
not proof that each old obligation was received.

For a named *terminal* Work and each target *open* Work, obtain exact `work.get`
snapshots and record their `workRef`, integer `revision`, `state`, and
`unresolved` arrays. For every original unresolved item, attach a human-reviewed,
exact string mapping to an active successor's unresolved item. Run the
read-only optional helper `scripts/check_obligation_handoff.py` with one JSON
object on stdin:

```json
{"source":{"workRef":"work:old","revision":2,"state":"completed","unresolved":["verify consumer"]},"successors":[{"workRef":"work:new","revision":4,"state":"open","unresolved":["verify consumer end-to-end"]}],"links":[{"sourceObligation":"verify consumer","sourceRevision":2,"successorRef":"work:new","successorRevision":4,"successorObligation":"verify consumer end-to-end"}]}
```

The wire input has unique JSON object members at every depth, rejects
non-JSON numeric constants and uses positive Host bigint revisions (at most
9223372036854775807). Duplicate member names, even identical values, are
ambiguous before typed navigation assessment; never silently select a winner.

The helper accepts UTF-8 JSON without BOM. Work references and obligation
strings must be representable in the native Host Work input/PG text domain:
3–1024 trimmed identifier characters without C0 controls, at most 128
nonempty trimmed obligations, no NUL or unpaired surrogate in snapshot text.
Keep exact Unicode scalar text (do not normalize distinct strings).
Successful navigation still does not attest the existence of either Work.

Helper success means only **NAVIGATION_COVERED** for the caller-supplied versions.
It **does not verify semantic equivalence** between the strings, current
versions at the Host, permission, source identity, implementation proof, or
technical completion. Re-read native Host versions before using the result;
if a receiver changed, re-evaluate and report `UNKNOWN`.

For separately verified **resolved** or **superseded** obligations, cite the
actual owner-qualified receipt and explicit disposition in the *current*
receiving Work/Topic; do not manufacture a synthetic receiving obligation
solely to turn the helper green. Leave any unmapped or contested item
`UNKNOWN` and post a bounded handoff into the existing canonical Task Control
Topic. This does not reopen a terminal Work or create another task registry.

Negative controls: missing old obligation, stale receiver revision,
receiver already terminal, duplicate mapping, self-referential successor,
out-of-scope task and missing owner receipt must never be reported as
semantically complete. This procedure is advisory and never authorizes
an external effect.

If an actual Host Work lists the same unresolved text more than once, it is
**not** a set: the list preserves distinct occurrence positions. For any link
whose source text repeats, include zero-based `sourceIndex`; for any repeated
receiving text, include zero-based `successorIndex`. Each index must refer to
an exact matching string at the observed Work revision. No index is required
for unique text (backward-compatible); duplicate text without an index is
ambiguous and rejected. `coveredIndices`, `missingIndices` and
`invalidIndices` are position-aware navigation witnesses, **not** evidence
of semantic discharge. Never silently deduplicate a Host Work obligation.
