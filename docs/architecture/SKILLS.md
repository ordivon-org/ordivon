# Skills

## One-sentence model

**Agent Skills package reusable procedural knowledge and supporting resources into task-activated folders that agents discover cheaply and load progressively only when relevant.**

Ordivon adopts the open Agent Skills format directly and does not maintain a private skill registry or trigger engine.

Project skills use the Agent Skills open format under `.agents/skills/`:

- discovery: compatible agents scan skill directories and load only `name` + `description`;
- activation: the agent loads the selected `SKILL.md` when the task matches;
- execution: the agent reads referenced files and invokes available tools/providers as needed.

Tool/provider discovery is deliberately separate. Skills describe procedural knowledge and proven compositions; executable capabilities come from the current harness, MCP, CLI/API environment, applications, or workflow systems. Credentials and execution authority stay with those natural providers.

Use repository-scoped instructions such as `AGENTS.md` for broadly applicable working rules; use Skills for optional procedures that should activate only for matching tasks; use MCP/tools/providers for executable capability.

Treat Skills as code-like trust inputs: audit third-party or repository-provided Skills before granting them access to powerful tools, and do not treat metadata such as experimental `allowed-tools` as a substitute for host-side permission enforcement.

## Scope and discovery: source tree is not a global catalogue

The canonical project Skill packages are the **actual** `.agents/skills/*/SKILL.md`
directories in the selected source checkout. The set changes with main and
must not be maintained as a second list in this document. Check the project's
current source and the [Skills MCP configuration format](../../extensions/chatgpt-skills-mcp/config/skills-mcp.example.json)
when using ChatGPT's connected Skills bridge.

The Skills MCP intentionally distinguishes globally visible user/vendor
sources from registered project workspaces. The installed project registration
observed on 2026-11-06 was `ordivon-next`: with that `workspaceId`,
`skills.search(query="finance")` returned the three project Finance
Skills, `skills.resolve` returned `project-ordivon-next/finance-paper-investment`,
and `skills.read` returned the exact Skill body. Without this project
context, a global search did not return the project Finance Skills.
A Runtime Workspace with a `ws-...` handle is a separate execution
identity, not an automatically registered Skills project.

Treat `ordivon-next` as an **observed deployment-specific registration**,
not a permanent global constant. Use current Skills Owner configuration or
the caller's registered project context instead of inventing new routing
code, duplicating packages into user scope, or disabling trust controls.
This is a discovery/read problem, not permission to perform effects.

`AGENTS.md` carries the small set of repository-wide rules that should apply before any optional Skill is activated, including external-authority-first, natural-owner, evidence-history and execution-vs-semantic-completion boundaries.

The previous private `registry/` JSON experiment is retired. Its useful content was migrated into standard Agent Skills and repository guidance.

See [the Agent Skills kernel lesson](../../catalogs/knowledge/lessons/agent-skills-kernel.md) for the extracted design rules, prototype boundary, and project-study acceptance record.
