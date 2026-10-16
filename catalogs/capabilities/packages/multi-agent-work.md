# Package: Multi-Agent Work Coordination

Last census: 2026-10-17
Standing: **READY_FOR_REAL_WORK**

## Outcome scope

Coordinate consequential work performed by multiple Agents across sessions without inventing a second task database, scheduler, workflow engine, or domain-acceptance authority.

This package is a task-local capability working set. It is not an Ordivon subsystem and does not define a universal organization lifecycle.

## Mature method and platform owners

Use the smallest mature owner that matches the actual pressure:

- GitHub owns public repository, Issue, Pull Request, review, CI-status, and maintainer-visible collaboration facts for GitHub-hosted projects.
- Repository-native CONTRIBUTING, SECURITY, CLA/DCO, test, release, and review rules govern contribution procedure for that repository.
- ECC team-agent-orchestration supplies team-shaping, isolated lanes, evidence, and merge-gate method.
- ECC parallel-execution-optimizer supplies dependency/lane decomposition and collision avoidance.
- Superpowers dispatching-parallel-agents supplies focused independent-agent dispatch discipline.
- Superpowers verification-before-completion supplies the universal evidence-before-claim completion gate.
- Matt triage contributes context gathering, redundancy checks, claim verification, and durable agent-ready briefs; maintainer-only tracker mutation semantics are not imported for external repositories.
- Matt codebase-design supplies the deep-module/deletion-test lens when a new coordination abstraction is proposed.
- Ordivon social-work-collaboration supplies the current Host Social Work Fabric procedure.
- Ordivon organizational-cybernetics is a diagnostic method for autonomy/coordination/control/intelligence/policy pressure; it does not prescribe five services.
- Temporal is an optional durable workflow owner when long timers, retries, waits, external events, or crash-resumable process semantics become recurrent.
- n8n is an optional integration edge for SaaS/API/webhook routing.
- Plane/OpenProject are optional work-management products only after measured human/project-management needs exceed the retained Host continuity surface.
- Microsoft Agent Framework/LangGraph-class orchestrators are optional when a real agentic stage needs richer graph/fan-in/handoff/checkpoint semantics than the current Harness/Agent Automation composition.

Do not activate optional platforms merely to make an architecture diagram look complete.

## Current local owner composition

| Responsibility | Natural owner | Truth boundary |
| --- | --- | --- |
| durable semantic frontier and re-entry | Host Social Work Fabric | Work/WorkSnapshot continuity only |
| collaboration/discussion/attention | Host Social Work Fabric | Space/Topic/Message/Subscription/Attention only |
| bounded Agent Run/cognition/provider-tool continuity | Harness | Agent Run truth only |
| ChatGPT occurrence/campaign materialization | Harness Agent Automation | provider occurrence lifecycle/effect fencing only |
| physical command execution | Runtime | Workspace/Job/Attempt/execution evidence only |
| repository bytes/history/branches | Git | source history only |
| public Issue/PR/review/CI collaboration | GitHub | provider-native public state |
| method/procedure | Skills | advisory procedure, no authority |
| concrete action | Tools/providers | only the effect surface they actually own |
| semantic acceptance | repository/domain owner or upstream maintainer | final domain/upstream decision |

Core law:

Host continuity != Harness run != Runtime execution != Git/GitHub truth != domain acceptance

## Thin operating profile

Long-running multi-Agent work uses the following composition only as needed:

RECOVER -> REVALIDATE -> ROUTE -> EXECUTE -> EVIDENCE -> DISTILL

- **RECOVER**: re-enter through Host Attention/Topic/Work continuity.
- **REVALIDATE**: refresh present-tense Git, GitHub, Runtime, provider, deployment, and domain facts at their natural owners.
- **ROUTE**: bind the current Plan/profile stage to the smallest applicable mature SOP/provider procedure and Skill set.
- **EXECUTE**: use the selected Agent/Harness and Tool through Runtime or the natural effect owner.
- **EVIDENCE**: retain exact execution/provider/repository evidence at its natural owner.
- **DISTILL**: commit a new WorkSnapshot only when the durable semantic frontier changed; use Host Messages for findings/questions/handoffs.

This is a composition profile, not a workflow engine.

## Work admission law

Do not mirror every external item into Host.

Create a durable Host Work only when at least one of these is true:

- the objective must survive multiple sessions;
- multiple actors require a shared semantic frontier;
- interruption/re-entry would otherwise lose consequential state;
- unresolved decisions/evidence must remain recoverable independently of one conversation;
- the case has become an active delegated contribution requiring continued coordination.

A repository census row, mined Issue candidate, one-shot API query, individual test, Runtime Job, PR comment, or transient wave lane is not automatically a Work.

Default hierarchy for campaign-shaped work:

- one Campaign Work for the long-lived objective;
- one collaboration Space linked to that Campaign Work when multi-actor discussion is needed;
- Topics for independently resumable waves or discussion axes;
- a Contribution/Case Work only after that case proves its own durable continuity need;
- GitHub Issues/PRs, Git commits, Runtime jobs, and artifacts remain references to their natural owners.

## Handoff and re-entry contract

A handoff must contain meaning, not copied logs:

- what was established;
- what remains unresolved;
- exact next action or stop condition;
- exact owner references for evidence.

Runtime stdout/stderr, CI logs, Git diffs, and provider payloads stay with their natural owners and are referenced from Host.

On re-entry:

1. recover Actor attention;
2. resume relevant Topic deltas;
3. read the current WorkSnapshot;
4. reconcile exact Harness/Runtime references where present;
5. revalidate mutable external facts such as GitHub Issue/PR/CI state;
6. only then resume reasoning or effects;
7. acknowledge Topic/Attention navigation after safe recovery.

Navigation acknowledgement is not semantic acceptance.

## Review and audit escalation law

Independent multi-Agent audit is **exception-driven, not a default ceremony**.

For ordinary bounded engineering work, the default path is:

one competent Agent -> applicable ECC/Matt/Superpowers methods -> owner-native verification -> completion

Do not spawn extra reviewers/falsifiers merely because multiple Agents are available.

Escalate to an independent Agent/reviewer only when the extra independence can materially change the decision, for example:

- the acting Agent has low confidence in diagnosis, semantics, or repair;
- the change has high blast radius, is hard to roll back, or crosses natural-owner truth boundaries;
- requirements or standards are ambiguous/conflicting;
- behavior is flaky, nondeterministic, concurrent, distributed, platform-specific, or otherwise hard to falsify locally;
- security, privacy, publication, money, destructive/external effects, or other consequential authority is involved;
- a large architectural/migration change has multiple plausible designs;
- owner-native verification is incomplete or cannot directly cover the risky claim;
- upstream/repository policy explicitly requires an independent review.

Use ECC, Matt Skills, and Superpowers directly for normal engineering. Multi-Agent review exists to reduce **material uncertainty or risk**, not to add process.

## Agent-team method

For a bounded wave, treat each Agent as a teammate with a narrow contract:

- scope/domain;
- allowed write surface;
- expected evidence;
- exit/kill conditions;
- handoff target;
- merge/review gate where code is produced.

Parallelize independent read/reproduction/review lanes. Isolate writes by repository/worktree/branch. Do not parallelize conflicting writes or let two Agents independently speak for one upstream contribution.

## Current standing

The local substrate is sufficient for real work:

- Host Social Work Fabric schema-10 surface is live;
- Runtime execution fabric is live;
- Harness Agent Automation exposes campaign registration/launch/inspection and conversation lifecycle surfaces;
- the current Skills supply includes ECC, Matt, Superpowers, Spec Kit, Ordivon methods, REA, and native tool Skills;
- Git/GitHub CLI and common engineering toolchains are available.

No generic Organization Service, Task Service, Board Service, scheduler, global priority engine, or new organization ontology is justified.

## Task-triggered escalation

Activate additional mature platforms only after measured pressure:

- Temporal: durable timers/retries/waits/event-driven continuation become recurrent.
- n8n: recurring external webhook/API integration becomes a real edge.
- Plane/OpenProject: human-facing portfolio/project management needs exceed Host continuity.
- MAF/LangGraph-class orchestrator: an agentic stage requires richer durable graph semantics not already supplied by Harness/Agent Automation.
- message bus: independently deployed producers/consumers require durable asynchronous delivery/replay.

Until then, keep the composition thin.

## Acceptance workload

The GitHub Top-1000 OSS contribution campaign is the first acceptance workload.

Success requires a fresh Agent to be able to:

1. recover the Campaign Work and relevant Topic from Host;
2. revalidate the exact current GitHub/Git/Runtime state rather than trusting historical prose;
3. select the current campaign stage and required Skills/procedures;
4. execute in an isolated Runtime workspace;
5. publish a typed Host finding/handoff with exact evidence references;
6. advance the WorkSnapshot only when the semantic frontier changes;
7. avoid creating duplicate Work/Task/Board state;
8. preserve upstream maintainer authority over merge/acceptance.
