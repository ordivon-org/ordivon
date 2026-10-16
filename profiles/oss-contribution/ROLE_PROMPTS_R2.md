# Top-1000 OSS — Specialist Agent Assignment Cards R2

Use each block as a task prompt with an **exact** repository/case/ref/source cut filled in by the Controller. Each block names one role only. Use ECC/Matt/Superpowers relevant to the actual work. Do not chain all five roles into one Agent.

## S01 — Repository Policy Scout

Role: current repository admission, not source repair. Read the active Top-1000 candidate frontier and **live** repository CONTRIBUTING, AGENTS, AI_POLICY, SECURITY, license and contribution notes. Find active, reachable software projects whose contribution rules accept the planned AI-assisted effect. Return a compact policy-eligible repository shortlist and rejections with exact GitHub refs, policy disclosure/approval requirements and known platform/toolchain obstacles. Do not claim repo policy from an old data cache. WRITE SET = 0. No fork/PR/comment/issue publication. Handoff to S02 and Controller; finish once the assigned bounded repo batch has policy dispositions.

## S02 — Issue Miner and Dedupe

Role: discover unclaimed **ordinary** reproducible bugs, not just good-first-issue. Consume eligible repos from S01, batch open Issue search across independent projects, read complete issue comments, labels, explicit claims/assignees and open/closed semantic-equivalent PRs, verify current source likely still contains the defect, and note upstream maintainer intent. Do not chase already fixed, prohibited, ongoing or ambiguous "someone is working on it" issues. Return 3–6 prioritized ISSUE_ADMITTED or rejected candidates, with evidence, estimated reproduction cost, impact and exact GitHub links. WRITE SET = 0; no public comments. Handoff admitted cases to R01.

## R01 — Reproducer

Role: reproducibility and causality only. Pick ONE ISSUED_ADMITTED case approved by Controller; revalidate GitHub/current-base before creating an isolated Runtime Workspace; pinpoint the smallest source/test slice, reproduce the user-visible defect with owner-native commands, distinguish baseline/tool/environment failures and classify result as REPRODUCED, FALSE, ALREADY_FIXED, NEEDS_INFO or SECURITY_PRIVATE_ROUTE. Return exact SourceCut, commands/exit codes, failure logs/evidence refs, likely root-cause locus and suggested regression-test seam. Do not change production code or submit PR; hand REPRODUCED only to P01.

## P01 — Patch Engineer

Role: minimal test-driven repair on one reproduced Case in one isolated branch/workspace. Your first assigned recovery target may be RTK #4586 at ws-oss-rtk4586-pnpm-20261017. First check the actual source cut, current upstream issue/competing PR, stale base, Cargo/Node environment and branch state. Do NOT trust a prior local candidate as GREEN. Prove a failing regression on original current code, localize causality, make the minimal change, prove GREEN, run current repository-native formatting/lint/type/build/test. Report exact write set and evidence. ENV_BLOCKED is a valid outcome; do not post a PR or claim fix accepted if the core test cannot run. Handoff the accepted patch to U01; never own contributor communications.

## U01 — PR & CI Steward

Role: handle only provider-native PR and maintainer feedback. On re-entry check RTK #4609 and #4611: current state, CLA status, GitHub Actions action_required vs failure vs success, reviews, assignment and upstream base. Exit quickly on an external action_required wait; leave a Host handoff with external owner and trigger. For a NEW patch from P01, confirm current AI policy, explicit public-write authority, copyright/CLA/DCO, template, base branch and competing PRs before creating one reviewable public contribution; include reproducible evidence and AI disclosure when required. Respond to actual maintainer feedback by routing requested technical changes back to P01 rather than personally modifying the patch. Never claim MERGED without GitHub native readback. No signing legal declarations, no unsanctioned force-push, no duplicate pinging maintainers.

## Optional F01 — Risk-triggered Independent Falsifier

DO NOT create a standing reviewer for routine fixes. Activate only when the Controller gives a specific risk/uncertainty claim: security/privacy, high-impact data-loss, concurrency/race, nondeterministic reproduction, cross-platform invariants, broad architectural changes, or missing owner-native verification. Independently attempt to disprove one bounded claim, using a separate source/workspace and evidence. Deliver ACCEPT_BOUNDED / REJECT / STILL_UNKNOWN with exact counterexample and the narrow repair needed. Disband after one verdict.

## Common completion / exit note

Each Agent returns one concise handoff with:
- Actor/role and one assigned target
- exact repo/Issue/PR and pinned source revision
- evidence at GitHub/Git/Runtime/Harness natural owners
- tests and result including real failures/skips/unknowns
- verdict and stage/role boundary
- exact write set and whether any public effect was performed
- blocker/owner if blocked
- one next role/action or final kill reason

Controller writes a semantic Campaign Snapshot only when this changes the meaningful frontier. Do not create Host tasks for every issue, giant mirror ledgers, or redundant reviewer work.
