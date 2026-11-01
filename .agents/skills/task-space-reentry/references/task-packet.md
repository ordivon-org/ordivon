# Ordivon capability task-space packet / bounded index

Entry Space: `space:ordivon-capability-task-forum-r1:20261101`.
Coordination root: `work:ordivon:capability-program-root-r1:20261101`.
Get its newest revision: these references are navigation, not current Work content. **No task is assigned by Space participation.**

## Existing execution anchors to reuse
- Linux PG actual production gate: `work:ordivon:linux-runtime-pg-cutover-p0:20261031`.
- Windows PG actual production gate: `work:ordivon:windows-pg-first-native-runtime-cutover-r1:20261026`.
- Formal kernel: `work:ordivon:systemwide-formal-lego-audit-r1:20261026`.
- Source/consumer proof graph: `work:ordivon:capability-program:proof-graph-r1:20261101`.
- Release truth and rollback: `work:ordivon:capability-program:release-currentness-r1:20261101`.
- R2.1 domain decomposition: `work:ordivon:capability-program:domain-lego-r1:20261101`.
- Safe cleanup: `work:ordivon:capability-program:cleanup-r1:20261101`.
- Problem LEGO case library: `work:ordivon:capability-program:problem-legos-r1:20261101`.

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
