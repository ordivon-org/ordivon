# Long-Running Multi-Agent Work Operating Profile R1

Date: 2026-10-17
Status: CURRENT COMPOSITION PROFILE

## Decision

Long-running multi-Agent work in Ordivon is a composition of existing natural owners, not a new organization subsystem.

The stable interface is deliberately small:

RECOVER -> REVALIDATE -> ROUTE -> EXECUTE -> EVIDENCE -> DISTILL

Deleting this profile would force each long-running campaign to rediscover the same owner boundaries, re-entry law, and Work-admission rule. The profile therefore earns its keep as a thin reusable module. It must not grow into a pass-through service that re-exports Host, Runtime, Harness, GitHub, or Skills.

## 1. System of interest

The system of interest is a long-running objective pursued by multiple human/Agent actors across interruptions, independent execution lanes, external systems, and changing evidence.

Whole-system outcome:

> A fresh authorized actor can recover the exact semantic frontier, revalidate current reality, execute the next bounded action through natural owners, and leave evidence plus a durable handoff without creating competing truth stores.

External environment includes Git/GitHub or other forges, CI, package ecosystems, upstream maintainers, external providers, and domain-specific acceptance authorities.

## 2. Owner map

| Question | Owner |
| --- | --- |
| What durable objective/frontier should actors recover? | Host Work/WorkSnapshot |
| What discussions/handoffs changed while an actor was away? | Host Space/Topic/Message/Attention |
| What bounded Agent Run occurred? | Harness |
| What provider occurrence/campaign was materialized? | Harness Agent Automation |
| What command physically ran and what evidence did it produce? | Runtime |
| What source/history/branch exists? | Git |
| What public Issue/PR/review/CI state exists? | GitHub/provider |
| How should this stage be performed professionally? | selected mature procedure + Skill |
| What action can actually be performed? | Tool/provider with effect authority |
| Is the result semantically accepted? | repository/domain/upstream authority |

References connect owners; they never transfer truth.

## 3. Domain terms

- **Campaign**: one long-lived objective whose semantic frontier must survive multiple waves/sessions.
- **Wave**: a bounded batch of independent or mostly independent lanes used to discover, reproduce, repair, or review cases. A Wave is not a Work by default.
- **Case**: one external candidate whose evidence may mature into durable coordinated work.
- **Stage marker**: a profile/Plan progress label stored in semantic frontier text when useful. It is not a new Host lifecycle enum.
- **Finding**: a typed Host Message containing a bounded observed conclusion plus references to natural-owner evidence.
- **Handoff**: a typed Host Message that says what another actor should recover and do next.
- **Evidence reference**: an exact identifier pointing to a natural owner; the reference is navigation, not copied authority.

These terms are specialized by domain profiles such as the OSS contribution profile.

## 4. Work admission and topology

Use the smallest durable object set.

Default campaign topology:

- 1 Campaign Work when the objective truly needs durable semantic continuity;
- 1 collaboration Space only when multi-actor social coordination is needed;
- 1..N Topics for independently resumable discussion/wave axes;
- 0..N Case Works, created only when a Case independently meets Work-admission criteria.

Never create:

- one Work per repository merely because it exists;
- one Work per mined Issue;
- one Host row per Runtime Job/test/CI run;
- a Board/Task mirror of GitHub;
- a second scheduler or priority database.

Host Work lifecycle remains Host-native: open/completed/abandoned. Domain/profile stages belong in the Campaign/Case semantic frontier, not in a new global Work enum.

## 5. Re-entry protocol

A returning actor uses:

1. attention.reentry(actorRef) to discover relevant changed owner records;
2. topic.resume(...) for relevant Topic deltas and relations;
3. work.get(...) for the current complete semantic frontier;
4. exact Harness reattachment when a bound Harness Run exists;
5. Runtime exact-reference reconciliation for Runtime references;
6. owner-native revalidation for mutable external references such as GitHub Issue/PR/CI/Git state;
7. reasoning/effects only after those checks;
8. topic.cursor.ack and attention.ack after the referenced state has been safely recovered.

Do not infer effect replay permission from recovery. Existing continuation law keeps redispatch false unless separately authorized.

## 6. Procedure routing

Three layers must remain distinct:

- **SOP/provider procedure**: mature external/repository procedure that defines required ordering/gates, such as repository CONTRIBUTING, SECURITY, CLA/DCO, GitHub PR review flow, or a mature debugging/testing discipline.
- **Plan/Operating Profile**: task/campaign-specific composition that selects stages, kill conditions, owners, and procedure bindings.
- **Skill**: executable procedural knowledge for an Agent at one stage.

A Plan must not be promoted into an “industry SOP” merely because it repeats successfully.

Tools are below those layers: they perform concrete reads/effects; they do not choose the method or own the semantic decision.

## 7. Agent operating loop

For one admitted action:

1. Recover current semantic frontier.
2. Revalidate facts that may have changed.
3. Determine the current Plan/profile stage.
4. Resolve the smallest applicable Skills and mature procedure.
5. Bind exact inputs, source revision, scope, allowed effects, and done/kill conditions.
6. Execute through the natural Tool/Runtime owner.
7. Verify through owner-native checks.
8. Post finding, question, warning, or handoff messages as appropriate.
9. Commit a WorkSnapshot only if the durable semantic frontier changed.
10. Stop rather than manufacture additional work when a kill condition is met.

## 8. Parallel organization

Use ECC/Superpowers parallel methods to shape independent lanes, not to create another board.

Parallel-safe examples:

- repository/policy scans;
- Issue mining and live dedupe;
- independent reproduction on isolated source cuts;
- independent review/falsification;
- cross-platform read-only verification.

Sequential/gated examples:

- two Agents editing the same patch surface;
- multiple Agents posting conflicting upstream comments;
- two PRs for the same admitted Case;
- destructive/provider effects sharing one authority;
- integration before independent verification.

Runtime workspaces/worktrees/branches isolate physical writes. Host records the semantic relationship only when it matters for re-entry.

## 9. Organizational-cybernetics diagnostic

Use these as questions, not service names:

- Operations: Scouts, Reproducers, Patch Agents, Reviewers, Integrators.
- Coordination: Host social continuity plus lane-isolation method.
- Control: controller decisions, Runtime capacity/admission, merge/effect gates.
- Intelligence: external currentness/mining/maintainer-feedback sensing.
- Policy/Identity: Campaign purpose, repository rules, security rules, effect authority, Actor identity.

Escalate the organization only when observed variety/coordination pressure exceeds the current composition.

## 10. Promotion gates for optional platforms

Do not add a provider because it exists.

- Temporal requires repeated durable timer/retry/wait/event pressure.
- Plane/OpenProject requires repeated human/project portfolio views not adequately served by Host continuity.
- MAF/LangGraph-class orchestration requires a real agentic stage with graph/checkpoint semantics not supplied by current Harness/Agent Automation.
- n8n requires recurring integration-edge pressure.
- NATS/message-bus class infrastructure requires independently deployed asynchronous delivery/replay pressure.

Every promotion needs a real workload, substitution comparison, and acceptance test.

## 11. Anti-patterns

- **Agent soup**: many actors with no narrow contract or evidence gate.
- **Board theater**: duplicating external state into an internal board without decision value.
- **Invisible work**: results exist only in chat text.
- **Log dumping into Host**: execution payloads copied instead of referenced.
- **Historical-truth drift**: treating a WorkSnapshot as current GitHub/Git/Runtime truth.
- **Skill authority leak**: a Skill is treated as permission or acceptance.
- **Execution authority leak**: Runtime exit 0 is treated as semantic success.
- **Profile inflation**: campaign-specific states become global Host schema.
- **Premature platform activation**: Plane/Temporal/MAF/n8n started for diagram completeness.

## 12. Acceptance

The profile is sufficient when a real multi-Agent campaign proves:

- cold re-entry from Host without reading prior chat history;
- current-world revalidation before action;
- isolated Runtime execution with exact evidence references;
- sparse durable Work topology;
- independent Agent lanes without conflicting writes;
- procedure/Skill/Tool/authority separation;
- domain/upstream acceptance remains at the natural owner.

The first designated workload is profiles/oss-contribution/.
