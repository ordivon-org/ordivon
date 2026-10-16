# Top-1000 OSS Controller R2 Handoff Implementation Plan

> For agentic workers: use the already adopted OSS Operating Profile and the installed ECC team-agent-orchestration, Matt codebase-design and Superpowers verification-before-completion. The implementation tasks below are completed by the current Controller; the new Controller begins the first real specialist wave.

**Goal:** Close out the serial bootstrap, retain exact upstream/current-source evidence, and hand one recoverable Campaign to a new multi-Agent Main Controller.

**Architecture:** Keep the current Host Campaign Work/Space/Topics and live GitHub as owner. Launch distinct specialist Agents through the native Harness/Agent Automation carrier; isolated Runtime workspaces carry code/testing; public writes remain GitHub/provider effects. No new Task, Scheduler, Review Registry or Board service.

**Tech Stack:** Ordivon Host/Runtime/Harness/Skill, git, GitHub CLI/API, Python/pytest for profile conformance, repository-native testing.

**Spec:** profiles/oss-contribution/README.md

## Global Constraints

- Keep the existing Campaign Work: work:oss:top1000-contribution-campaign-r1:20261017.
- Never turn Host semantic snapshots into GitHub/Runtime truth.
- Do not create a Work per repo/Issue or an independent reviewer for routine changes.
- AI-contribution policy, CLA/DCO, PR template and security disclosure are repository-native authorities.
- #4586 is an unverified local repair candidate, not a green PR.
- Distinguish GitHub action_required from failing CI, CLA pending from signed, and user action from maintainer approval.

## Completed delivery tasks

- [x] Revalidate Host Campaign Work and Runtime candidate reference; read current PR #4609 and #4611 statuses from GitHub.
- [x] Write a standalone new-controller prompt with stable re-entry refs and currentness gates.
- [x] Write narrow specialist Agent prompts for S01, S02, R01, P01 and U01; conditionally add F01.
- [x] Add focused conformance assertions on role separation, upstream-effect policy, old-work recovery and risk-driven review.
- [x] Verify with native tests and adopt the isolated artifact commit only when current canonical source has not moved.
- [x] Publish durable handoff into Host and update Campaign Work to the next wave; old wave stops here.

## First specialist wave execution (new Controller)

- [ ] Preflight actual Harness/Agent Automation model-backed execution provider and real slots; recover Host Attention/Topic/Work.
- [ ] Start S01 repo-policy scout and S02 issue-dedupe scout with disjoint repo reads; link S02 to newly admitted S01 sources after early results.
- [ ] Start R01 on one admitted reproducible non-RTK case, P01 on the existing #4586 candidate, and U01 on the two RTK PRs.
- [ ] Reconcile real Agent Runs, Runtime job evidence and upstream GitHub readbacks; move only source-backed cases across stage gates.
- [ ] Scale only when enough independent admitted cases and native verification capacity justify extra parallelism.

## Handoff acceptance

- Controller Prompt and role cards are complete, discoverable under profiles/oss-contribution.
- Profile conformance tests PASS on the adopted canonical revision.
- GitHub and Runtime facts are listed as last-observed with fresh-read obligations.
- Host snapshot/message actually records the new Controller's first wave and unresolved exact blockers; no false multi-Agent run claim.
