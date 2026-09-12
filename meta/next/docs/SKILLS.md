# Skills

Ordivon Next does not maintain a private skill registry or trigger engine.

Project skills use the Agent Skills open format under `.agents/skills/`:

- discovery: compatible agents scan skill directories and load only `name` + `description`;
- activation: the agent loads the selected `SKILL.md` when the task matches;
- execution: the agent reads referenced files and invokes available tools/providers as needed.

Tool/provider discovery is deliberately separate. Skills describe procedural knowledge and proven compositions; executable capabilities come from the current harness, MCP, CLI/API environment, applications, or workflow systems.

Current skill:

- `.agents/skills/artifact-work/` — standards-first artifact creation and verification, with family-specific references loaded on demand.

The previous private `registry/` JSON experiment is retired. Its useful content was migrated into the Agent Skill and family references.
