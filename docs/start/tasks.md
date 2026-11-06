# Find the Ordivon owner for your task

**Choose by outcome and authoritative fact**, not by a technology name.
The paths below are discovery aids. Capability deployment and consumer
qualification must be checked with the real owner.

| I want to... | First owner entry | First evidence to request |
| --- | --- | --- |
| Run a verifiable task and read its artifacts | [Runtime](../../services/runtime/README.md) | Workspace/Job/Attempt plus artifact/result state |
| Continue an Agent collaboration, Work or discussion | [Host](../../services/host/README.md) | Work/Space/Topic/Message authority and exact revision |
| Build an Agent invocation or tool session | [Harness](../../services/harness/README.md) | Agent run/tool effects and owned trace |
| Route a remote authenticated tool operation | [Gateway](../../services/gateway/README.md) | Deployed route and downstream owner readiness |
| Run an investment research/simulation study | [Capital / Finance](../../domains/capital/README.md) | Source digests, read-only replay and independent research status |
| Inspect a network/VPN/DNS failure | [Network](../../platform/network/README.md) | Observed route, nameserver and exit-path evidence |
| Review auth, credentials or effect boundaries | [Security](../../platform/security/README.md) | The applicable Security owner contract |
| Create or inspect application-facing browser behavior | [Web](../../apps/web/README.md) | Canary/browser acceptance; production eligibility separately |
| Work on media | [Media capability](../../capabilities/media/README.md) | Actual active consumer and native owner tests; see owner-native documentation |
| Design or review a research workflow | [Research capability package](../../catalogs/capabilities/packages/research.md) | Resolve the study/experiment owner and actual consumer; no monolithic Research service is implied |
| Work on a playable game | [Game](../../domains/game/README.md) | Playable build and actual Agent/human game loop |

**Where is Skills?** Canonical in-repo procedural packages live under
[Agent Skills](../../.agents/skills/), with
[method-router](../../.agents/skills/method-router/SKILL.md) for tasks where
method selection is genuinely uncertain. Skill discovery, authority and runtime
effects are different boundaries.

**When no owner entry exists:** inspect the source and current deployment
rather than treating a missing README as proof a capability is absent.
A separate owner onboarding page should be added when a real consumer and
setup path can be demonstrated; do not generate boilerplate READMEs for
empty or retired owners.
