# Skills

## One-sentence model

**Agent Skills package reusable procedural knowledge and supporting resources into task-activated folders that agents discover cheaply and load progressively only when relevant.**

Ordivon Next adopts the open Agent Skills format directly and does not maintain a private skill registry or trigger engine.

Project skills use the Agent Skills open format under `.agents/skills/`:

- discovery: compatible agents scan skill directories and load only `name` + `description`;
- activation: the agent loads the selected `SKILL.md` when the task matches;
- execution: the agent reads referenced files and invokes available tools/providers as needed.

Tool/provider discovery is deliberately separate. Skills describe procedural knowledge and proven compositions; executable capabilities come from the current harness, MCP, CLI/API environment, applications, or workflow systems. Credentials and execution authority stay with those natural providers.

Use repository-scoped instructions such as `AGENTS.md` for broadly applicable working rules; use Skills for optional procedures that should activate only for matching tasks; use MCP/tools/providers for executable capability.

Treat Skills as code-like trust inputs: audit third-party or repository-provided Skills before granting them access to powerful tools, and do not treat metadata such as experimental `allowed-tools` as a substitute for host-side permission enforcement.

Current skill:

- `.agents/skills/artifact-work/` — standards-first artifact creation and verification, with family-specific references loaded on demand.

The previous private `registry/` JSON experiment is retired. Its useful content was migrated into the Agent Skill and family references.

See `knowledge/lessons/agent-skills-kernel.md` for the extracted design rules, prototype boundary, and project-study acceptance record.
