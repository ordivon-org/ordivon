# OSS Contribution Campaign Operating Profile R1

Date: 2026-10-17
Standing: FIRST REAL-WORK ACCEPTANCE PROFILE

## Purpose

Operate a long-running, multi-Agent upstream contribution campaign over a large repository universe while preserving GitHub/upstream truth, repository-native contribution rules, independent defect evidence, and sparse Ordivon continuity state.

This is an Ordivon **Operating Profile / Plan composition**, not an industry SOP and not a workflow engine.

Mature procedures remain external/repository-native: GitHub contribution/PR mechanics, each repository's CONTRIBUTING/SECURITY/CLA/DCO rules, language/toolchain-native testing, systematic debugging, TDD, and code review.

## System boundary

Ordivon may:

- discover and rank repositories/issues;
- read public contribution policy and GitHub state;
- clone/fetch source;
- reproduce defects;
- create local/fork candidate branches when authorized;
- test, review, falsify, and prepare PR material;
- retain internal semantic continuity and evidence references.

Ordivon does not own:

- GitHub Issue/PR/review truth;
- repository semantic conventions;
- upstream roadmap;
- maintainer acceptance/merge decisions;
- security disclosure policy;
- CLA/DCO/legal meaning.

External GitHub writes remain effect-authority gated. A local PR_READY result is not permission to publish.

## Campaign topology

Default durable shape:

- one Campaign Work for the Top-1000 contribution objective;
- one collaboration Space when multiple actors participate;
- one Topic per independently resumable wave or shared policy/review axis;
- repository/Issue census remains dataset/artifact state, not Host Work;
- a Contribution Case becomes its own Work only after durable multi-session/multi-actor continuity is genuinely needed.

Do not create 1,000 repository Works or thousands of Issue Tasks.

## Campaign stage model

Stage markers are profile-level semantic labels. They do not extend Host's Work lifecycle.

Primary path:

UNIVERSE -> REPOSITORY_ADMITTED -> ISSUE_CANDIDATE -> ISSUE_ADMITTED -> REPRODUCING -> REPRODUCED -> ROOT_CAUSED -> RED_PROVEN -> PATCHED -> GREEN -> FALSIFIED_OK -> OWNER_VERIFIED -> PR_READY -> PR_OPEN -> REVIEW_LOOP -> MERGED

Terminal/side dispositions:

- REPOSITORY_REJECTED
- ISSUE_REJECTED
- DUPLICATE_OR_ASSIGNED
- FALSE
- ALREADY_FIXED
- NEEDS_INFO
- SECURITY_PRIVATE_ROUTE
- SUPERSEDED
- REJECTED_UPSTREAM
- ABANDONED_WITH_REASON

A disposition is evidence-backed. Killing a bad/duplicate/already-fixed candidate is successful campaign work.

## Stage gates and method bindings

| Stage | Required evidence/gate | Preferred procedure/Skill | Natural truth owner |
| --- | --- | --- | --- |
| Universe | ranked/current repository dataset | batched GitHub/API collection; ECC search/parallel methods as needed | GitHub + retained dataset |
| Repository admission | software/activity/openness/reachability evidence | ECC GitHub ops + campaign policy | GitHub/repository |
| Contribution-policy check | current contribution/security/test/CLA-DCO rules | repository-native docs; ECC GitHub ops | repository/GitHub/legal owner |
| Issue mining | plausible actionable candidate | batched local/API mining | GitHub |
| Live dedupe | current Issue, assignee, linked/open PR, current-main check | ECC GitHub ops; Matt triage read-only subset | GitHub/Git |
| Issue admission | bounded value/repro/cost decision | Matt triage context/redundancy/claim-verification subset | Campaign decision |
| Brownfield slice | bounded code/test perimeter, not whole-repo onboarding | ECC brownfield-retrospective | repository source |
| Reproduction | current source + exact environment + repeatable result | Superpowers systematic-debugging; Matt diagnosing-bugs as complement | Runtime + source |
| Root cause | causal code/invariant explanation supported by evidence | systematic-debugging | source + Runtime evidence |
| RED | regression test fails for the claimed defect | Superpowers TDD | repository-native test runner |
| Minimal repair | smallest behavior change needed by the admitted defect | stack-specific Skill as needed | candidate Git branch |
| GREEN | same regression test now passes | repository-native test runner | Runtime/test owner |
| Conditional independent falsifier | when escalation triggers fire, adversarial inputs/assumptions fail to disprove repair | independent Agent + review/debug methods | independent evidence |
| Owner-native verification | full applicable lint/type/build/test/security gates | Superpowers verification-before-completion; ECC verification-loop when broad gate helps | repository-native tooling/CI |
| Exact contribution contract | PR template, CLA/DCO, changelog/newsfragment, base/branch rules | repository-native docs + ECC GitHub ops | repository/provider |
| Pre-PR live dedupe | no newly competing fix/assignment/mainline repair | GitHub/Git revalidation | GitHub/Git |
| PR preparation | reviewable problem/repro/root-cause/fix/test evidence | Matt code-review + Superpowers review discipline | candidate branch |
| PR open/review | provider accepted PR and current reviews/checks | GitHub provider procedure | GitHub |
| Maintainer loop | requested revisions answered and reverified | same engineering loop on exact requested change | upstream maintainer + repo |
| Closure | merged/rejected/superseded outcome observed | provider readback + Campaign distillation | GitHub/upstream |

## Reproduction result contract

An admitted Issue may leave reproduction as exactly one of:

- REPRODUCED: the reported defect exists on the pinned current source/environment with retained evidence;
- FALSE: the admitted claim does not hold under the tested current conditions;
- ALREADY_FIXED: current source no longer exhibits the reported defect;
- NEEDS_INFO: available evidence cannot establish or falsify the claim;
- SECURITY_PRIVATE_ROUTE: public investigation would violate repository security/disclosure policy.

Do not patch a FALSE, ALREADY_FIXED, or NEEDS_INFO case merely to produce activity.

## Minimal repair law

After REPRODUCED:

1. localize root cause before proposing a fix;
2. encode the missing invariant/behavior in a regression test;
3. observe RED before changing production behavior;
4. make the smallest repair that satisfies the admitted behavior;
5. observe GREEN;
6. if the review-escalation policy is triggered, run an independent falsifier; otherwise do not add one ceremonially;
7. run all applicable owner-native verification before PR_READY.

A broad refactor, dependency upgrade, architecture rewrite, or cleanup is a separate candidate unless the root cause makes it necessary.

## Review escalation for contribution cases

Do **not** assign an independent falsifier/reviewer to every ordinary Issue or patch.

The default contribution repair path is one capable Agent using the relevant ECC/Matt/Superpowers methods plus repository-native verification. Add an independent reviewer only when it is decision-relevant, especially for low-confidence root cause/fix reasoning, risky or hard-to-reverse changes, broad/cross-owner changes, concurrency/platform-specific behavior, security/privacy concerns, ambiguous repository policy/specification, flaky evidence, or verification gaps.

A small, well-bounded bug with a clear reproduction, clear root cause, RED/GREEN regression test, minimal diff, and complete owner-native verification does not need a second Agent merely for ceremony.

## Multi-Agent wave shape

A normal bounded wave may use:

- Scouts: repository/policy/Issue discovery and live dedupe;
- Reproducers: independent current-source reproduction;
- Patch Agents: only after reproduction/root-cause admission;
- Falsifiers/Reviewers: conditional independent adversarial/spec/standards review only when confidence/risk triggers justify it;
- Integrator/Controller: selects transitions, prevents collisions, and distills durable frontier.

Use ECC parallel-execution-optimizer to create a lane matrix. Use Superpowers dispatching-parallel-agents only for genuinely independent domains. Use ECC team-agent-orchestration method for narrow role contracts, evidence, and merge gates.

Do not run two Patch Agents against the same write surface unless explicitly conducting isolated competing designs. Never let multiple Agents independently post conflicting upstream comments/PRs for one Case.

## Host usage

Host stores meaning and re-entry state, not logs.

Use:

- WorkSnapshot: current objective/frontier/established/unresolved/rejected/constraints/nextActions/referenceRefs;
- Topic: resumable Wave/policy/review discussion axis;
- finding: verified bounded result;
- question: missing evidence/request for decision;
- warning: material blocker/risk;
- handoff: exact recovery/next-action note.

Reference Runtime/Git/GitHub/Harness evidence rather than copying it into Host.

Commit a new WorkSnapshot only when the semantic frontier changes.

## Cold re-entry recipe

A returning Agent:

1. re-enters Host Attention;
2. resumes the relevant Topic;
3. loads the Campaign/Case WorkSnapshot;
4. resolves exact source/reference identities;
5. revalidates GitHub Issue/PR/assignment/CI and Git currentness;
6. reconciles Runtime/Harness references where relevant;
7. resolves the stage's required mature procedure and Skills;
8. executes only the bounded next action;
9. verifies fresh evidence;
10. posts a finding/question/warning/handoff;
11. updates WorkSnapshot only if semantic state changed;
12. acknowledges Topic/Attention cursors after safe recovery.

Prior chat prose is not a recovery authority.

## Work promotion rule for Contribution Cases

A mined Issue stays a dataset row until there is active durable work.

Promote a Case to its own Work only when one or more applies:

- reproduction/repair spans multiple sessions;
- multiple actors need a shared case frontier;
- maintainer review creates a continuing revision loop;
- unresolved external evidence must survive interruption;
- a patch/PR has become a consequential delegated objective.

Close/abandon the Case Work when its durable objective ends; retain GitHub/Git evidence at natural owners.

## Public-write and security law

Read-only discovery/reproduction is separate from public effects.

Before any GitHub comment, Issue, fork push, PR creation, review response, close/reopen, label mutation, or other external write:

- revalidate the exact target and current state;
- confirm repository procedure;
- confirm the action is within the user's effect authority;
- ensure only one campaign lane is speaking for the Case.

Security-signaled candidates default to repository SECURITY procedure/private disclosure. They do not enter the ordinary public PR path merely because a technical fix is available.

## Contribution ledger

Do not create a second authoritative ledger database by default.

The campaign ledger is a derived/reporting view assembled from:

- Campaign/Case WorkSnapshot semantic outcomes;
- GitHub Issue/PR/review/merge state;
- Git commit/source identities;
- Runtime/Harness evidence references.

A generated JSON/CSV reporting artifact is acceptable for analysis, but it remains a projection over natural owners.

Useful derived fields include repository, Issue, admitted source cut, reproduction disposition, root-cause evidence, patch commit, verification evidence, PR identity, maintainer disposition, merge/release identity, and timestamps.

## Escalation

Do not add Temporal/Plane/MAF/n8n by default.

Escalate only when measured campaign pressure proves:

- Temporal: large recurring timers/retries/waits/event-driven wakeups;
- n8n: recurring webhook/API integration edges;
- Plane/OpenProject: human portfolio/project views become necessary;
- MAF/LangGraph-class orchestrator: a stage needs richer agent graph/checkpoint semantics than Harness/Agent Automation provides.

## First acceptance experiment

Use one bounded Wave, not the whole Top-1000 frontier.

The acceptance experiment should prove:

- one fresh Agent can cold-recover campaign state from Host;
- at least two independent read/reproduction lanes can run without shared-state collision;
- one Case can terminate early (FALSE, ALREADY_FIXED, duplicate, or needs-info) without spawning repair work;
- one genuinely reproduced Case, if available, can progress RED -> repair -> GREEN -> conditional falsifier when justified -> owner-native verification;
- no GitHub public write occurs without explicit effect authority;
- all durable claims can be reconstructed from Host semantics plus natural-owner evidence refs.

Only after that experiment should we automate more of the campaign.
