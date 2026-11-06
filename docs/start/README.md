# Start with Ordivon

Ordivon is an evolving, human-directed and Agent-assisted engineering system.
It combines specialized owners for execution, coordination, security, methods,
and practical work such as research, finance analysis, media and software.
The goal is **verified outcomes from reusable capabilities**, not a second
universal task manager, a single AI model, or a promise that every possible
workflow is already available.

**Current product posture:** Ordivon has working operator/developer-facing
Runtime and Host services and independently testable domain workflows. Its
web application has a tested human/Agent security canary but explicitly remains
**not production eligible**. A functioning source command is not proof of a
publicly hosted customer product. Check the owning component's live state
before making availability claims.

## Pick a first journey

| Who are you? | Start here | Expected first outcome |
| --- | --- | --- |
| Curious user or researcher | [Run a read-only Finance example](human-first-run.md) | Get and interpret a deterministic result without brokerage access |
| Coding Agent or engineering contributor | [Agent's first verified task](agent-first-run.md) | Locate the natural owner, run its actual consumer, record evidence |
| Someone looking for a specific capability | [Find the right task owner](tasks.md) | Reach the owner-specific entry and confirm readiness |
| Architecture reader | [Current architecture projection](../architecture/CURRENT_ARCHITECTURE.md) | Understand the owner boundaries and source-vs-deployment caveat |

These paths are complementary. **Human documentation explains an outcome and
how to achieve it; Agent documentation adds discovery, source control, testing
and effect boundaries.** The same owner source and executable consumers back
both. This index is navigation, not another Capability or Skill registry.

## How to read existing documentation

- **Tutorials**: start with the two runnable experiences above.
- **How-to guides**: follow one owner README or the exact linked command for
  the outcome you need.
- **Reference**: inspect the owner's native API, schema, CLI and tests.
- **Explanation**: consult architecture/decision documents only when you
  need the reasoning behind a boundary.

This is the Diátaxis distinction between learning, achieving a task, looking
up exact information and understanding design trade-offs.

## Source, deployment and claims

The root repository describes source ownership; it does not certify the
current health of a remote service. The dated
[architecture projection](../architecture/CURRENT_ARCHITECTURE.md) explicitly
states that it is non-authoritative and must be reconciled with live owners,
their release evidence and real consumers. The planned physical directory
layout is not necessarily deployed.

Do not translate a passing unit test into an available service, a model result
into domain acceptance, or a research simulation into financial authority.
For a specific source tree, start at [the repository overview](../../README.md)
and [the agent rules](../../AGENTS.md) if the work is being done by an Agent.

External documentation precedents:
[Diátaxis](https://diataxis.fr/),
[AGENTS.md](https://agents.md/),
[Agent Skills](https://agentskills.io/),
and [Google's prescriptive documentation guidance](https://developers.google.com/style/prescriptive-documentation).
