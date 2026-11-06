# Tutorial: an Agent's first evidence-backed Ordivon task

**Audience:** a coding or operations Agent working in an Ordivon source
workspace with its assigned tools. The path below is intentionally read-only.
It does not need production credentials or permission to change an owner.

## 1. Discover before acting

Read the root [AGENTS.md](../../AGENTS.md) once, then choose the natural owner
by the fact or external effect you must inspect. For this exercise, use
[Capital](../../domains/capital/README.md). Check any nearer scoped
`AGENTS.md` and the owner's native verification task.

The model's familiarity with a package or old documentation is not evidence
that its deployment, data source, release or consumer is current.

## 2. Discover a project Skill without confusing Workspace identities

When the Ordivon Skills MCP is connected, project Skills are deliberately
**not** visible through an unscoped global inventory. Supply the **registered
Skills project-workspace name**, not the ephemeral Runtime execution
`ws-...` handle. An observed example in the installed 2026-11-06
deployment is `ordivon-next` (other deployments may differ):

```text
skills.search(query="finance", workspaceId="ordivon-next")
skills.resolve(ref="finance-paper-investment", workspaceId="ordivon-next")
skills.read(skillId="project-ordivon-next/finance-paper-investment",
            workspaceId="ordivon-next")
```

The `skillId` above is an example of an actual qualified Skills Owner
resolution; always use the exact returned ID, revisions and source currentness
when available. The live test found all three project Finance procedures
(`finance-paper-investment`, `finance-experiment-review` and
`finance-paper-risk-review`) with that project context, and successfully
read the first Skill. A global query returning no Finance results does not
imply missing project packages.

The named project registrations belong to the existing
[Skills owner](../architecture/SKILLS.md). Check its active configuration
rather than installing duplicate Skills, creating a second registry or
passing a Runtime Job workspace ID as if it were a Skills project key.
Skill activation supplies instructions only; real tools/effects are still
owned by their natural providers.

## 3. Complete one concrete, bounded task

Using an already allocated isolated Workspace (or a separate Git worktree
when the Runtime owner is not available), from the repository root:

```sh
cd domains/capital
scripts/run-strategic-contribution-brief < examples/strategic_contribution_r1.json
mise tasks ls
```

Inspect the JSON output. Require `standing=READ_ONLY_PROJECTION`,
`executionAuthorized=false`, and `cashAfterMinor=40000` for the supplied
sample. If this is a code change, follow with the focused consumer test and
`mise run verify` from `domains/capital` before claiming Owner acceptance.

## 4. Distinguish kinds of evidence

| Observation | What it supports | What it does not prove |
| --- | --- | --- |
| CLI returns JSON | The exercised consumer completed this input | The whole domain or public service works |
| Owner tests pass | Covered native contracts survived the tests | All cases, deployments or provider truth |
| Runtime Job succeeds | A committed execution reached its terminal outcome | The requested financial/research objective succeeded |
| Frozen candidate produces a digest | Exact bytes/declared identity can be rechecked | The data was truly available at historical freeze time |

When a task requires an external effect, obtain that owner's currently
accepted effect contract and identity; never infer approval from an Agent Skill
or a read-only analysis. Domain success needs a relevant consumer readback or
independent acceptance evidence.

## 5. Report and hand off

Record the natural owner, exact source revision, input/evidence identity,
executed command or Job, actual output, checked tests, and the single most
material remaining UNKNOWN. Link to the real PR/artifact when one exists.
Do not fabricate production currentness, a completed customer outcome, or a
generic `SUCCESS` status.

## Next paths

- [Find an owner by task](tasks.md).
- For new research methods, use only the relevant
  [method-router Skill](../../.agents/skills/method-router/SKILL.md).
- For Finance experiments, use
  [finance-experiment-review](../../.agents/skills/finance-experiment-review/SKILL.md).
- For core concepts, consult
  [Agent/LEGO vocabulary](../architecture/AGENT_CONCEPTS_FORMAL_LEGO_RESEARCH_20261024.md).
- For an actual code contribution, follow
  [CONTRIBUTING](../../CONTRIBUTING.md) and the owner's tests.

This page is a starting tutorial, **not** a second mandatory global workflow
or a new Agent authority.
