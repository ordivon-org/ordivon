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

Current project skills:

- `.agents/skills/artifact-work/` — standards-first artifact creation and verification, with family-specific references loaded on demand.
- `.agents/skills/enterprise-work/` — consequential multi-step/customer/business/cross-domain work composition: current external authority, bounded quality/delivery planning, natural owner/provider selection, risk/authorization, domain-native V&V and bounded acceptance. It deliberately stays dormant for trivial low-risk edits.
- `.agents/skills/mobile-app-security/` — evidence-first authorized mobile application analysis spanning APK/AAB classification, static/native reconstruction, runtime compatibility, instrumentation, hybrid bridges, and application-generated network behavior.
- `.agents/skills/skill-supply-chain-audit/` — third-party Skill intake and supply-chain review that keeps package scanning, source approval, instruction authority, and effect authorization separate; optionally consumes SkillSpector evidence.

`AGENTS.md` carries the small set of repository-wide rules that should apply before any optional Skill is activated, including external-authority-first, natural-owner, evidence-history and execution-vs-semantic-completion boundaries.

The previous private `registry/` JSON experiment is retired. Its useful content was migrated into standard Agent Skills and repository guidance.

See `knowledge/lessons/agent-skills-kernel.md` for the extracted design rules, prototype boundary, and project-study acceptance record.
