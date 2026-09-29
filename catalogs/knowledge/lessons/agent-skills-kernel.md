# Agent Skills Kernel — extracted standard and design lessons

Status: **REGISTERED / PROTOTYPE-READY**  
Registered: 2026-09-14

## One-sentence model

**Agent Skills package procedural knowledge and supporting resources into discoverable folders whose metadata is cheap to advertise and whose full instructions, references, scripts and assets are loaded only when the agent decides they are relevant.**

## Authority and source

Agent Skills is an open format originally developed by Anthropic and now maintained as an open standard at `agentskills.io` / `agentskills/agentskills`.

Anthropic's `anthropics/skills` repository is primarily a production/example collection and implementation reference. It is not the sole definition of the standard. Individual example-skill licensing must be checked: many examples are Apache-2.0, while some production document skills are source-available under different terms.

## Minimal format

A skill is a directory containing at minimum:

```text
my-skill/
├── SKILL.md
├── scripts/       # optional
├── references/    # optional
└── assets/        # optional
```

`SKILL.md` contains YAML frontmatter plus Markdown instructions.

The only required metadata fields are:

- `name` — stable skill identifier;
- `description` — what the skill does **and when it should be used**.

Useful optional standard fields include `license`, `compatibility`, arbitrary string `metadata`, and experimental `allowed-tools`.

## Core mechanism: progressive disclosure

The important mechanism is not the folder convention by itself. It is the three-tier context-loading model:

1. **Discovery** — load only each skill's `name` and `description` into the available-skill catalog;
2. **Activation** — when the model judges a skill relevant, load the full `SKILL.md`;
3. **Execution/resources** — load referenced files, scripts or assets only when the active procedure actually needs them.

This allows many skills to remain available without paying the context cost of all instructions on every turn.

## Activation model

Default activation should be model-driven rather than a private trigger engine.

Conceptually:

```text
installed skills
    ↓ scan metadata
skill catalog
    ↓ shown to model
current task
    ↓ model selects relevant skill
read SKILL.md
    ↓
load references/scripts/assets as needed
```

If an agent already has filesystem access, ordinary file-read capability is enough to activate a skill. A dedicated `activate_skill(name)` tool is only necessary when the runtime cannot expose files directly or when stronger mediation is desired.

The `description` therefore carries most of the routing burden. It must be specific enough to trigger on relevant work but narrow enough not to activate on unrelated tasks.

## What belongs in a Skill

Put in a Skill what the model would not reliably know or reproduce without task-local procedural context:

- organization/project-specific procedures;
- mature domain workflows and decision rules;
- non-obvious edge cases and failure handling;
- instructions for composing known tools/providers;
- reusable verification procedures;
- small deterministic scripts that remove repeated reasoning;
- reference material and templates that are useful only for that capability.

Do not use Skills to restate generic knowledge the model already possesses.

## Boundary with tools / MCP / providers

A Skill is **procedural knowledge**, not execution authority.

```text
Skill = how/when to use capabilities
Tool/MCP/API/CLI = executable capability
Credential/provider = authority to perform effects
```

A skill may tell an agent to call a tool, run a script or inspect a provider, but it does not make that tool exist and it should not own provider credentials.

Tool discovery and Skill discovery therefore remain separate concerns.

## Boundary with AGENTS.md / repository instructions

Use repository/project instructions such as `AGENTS.md` for broad rules that apply while working in a directory or repository.

Use a Skill for an optional capability/procedure that should activate only for matching tasks.

A rough distinction:

```text
AGENTS.md -> always-applicable scoped working rules
Skill     -> task-activated procedural capability
MCP/tool  -> executable operation surface
```

Do not convert every repository rule into a Skill, and do not encode every Skill permanently into the system prompt.

## Context discipline

Keep `SKILL.md` as the minimum always-needed procedure for an activated skill. The standard recommends keeping it below roughly 500 lines / 5,000 tokens.

Move detailed content to focused reference files and state **when** each reference should be read. Avoid deep reference chains.

This is directly compatible with Ordivon's task-local working-set principle.

## Scripts and deterministic work

Use `scripts/` when a repeated operation is better expressed deterministically than repeatedly reasoned about by the model.

A script should be self-contained or state dependencies clearly, produce useful errors, and handle expected edge cases.

The presence of scripts does not turn a Skill into a sandbox or security authority. Execution still follows the host agent's permission/tool policy.

## Trust boundary

Skills are agent instructions and executable/resource packages. Treat third-party or repository-provided Skills as code-like trust inputs.

A malicious or compromised Skill can influence an agent to invoke powerful tools or read/send data. Therefore:

- trust/audit the source before installing or mounting Skills;
- pin/review important Skill revisions when reproducibility matters;
- keep provider/tool permissions independently constrained;
- do not interpret `allowed-tools` as a universal security enforcement mechanism; it is currently experimental and client support varies;
- credentials remain outside the Skill.

## Ordivon use

Ordivon should adopt the standard directly rather than maintain a private Skill schema, registry or trigger engine.

Use Agent Skills for reusable `Knowledge -> Action` mappings that are procedural and task-activated, for example:

- Artifact family production and verification;
- a repeatable research procedure;
- a repository/tool-specific engineering procedure;
- a provider-specific operational playbook;
- a narrow domain workflow that composes mature external tools.

Do **not** force every Capability Package into one Skill. A package is a task-local working set; Skills are one way to package reusable procedures inside that set.

## Minimal client prototype

A Skill-compatible agent can be prototyped with very little machinery:

1. scan configured project/user skill directories;
2. parse YAML frontmatter from each `SKILL.md`;
3. validate `name` and `description`;
4. inject an available-skills catalog containing name, description and location;
5. let the model choose a relevant Skill;
6. expose a normal file-read tool or `activate_skill` tool to load `SKILL.md`;
7. let the model follow relative references and invoke scripts/assets through existing host capabilities;
8. keep execution permission and credentials in the host/provider, not in the Skill loader.

This is sufficient for a working Agent Skills prototype. A registry service, database, package manager, embedding search or custom trigger classifier is not required.

## Extracted rules

1. Package reusable **procedural knowledge**, not another agent runtime.
2. Advertise only lightweight metadata globally; load procedures just in time.
3. Make `description` encode both capability and activation conditions.
4. Prefer model-driven activation before building a trigger engine.
5. Keep detailed references/scripts/assets behind progressive disclosure.
6. Put deterministic repeated operations in scripts rather than prompts when appropriate.
7. Keep Skill knowledge separate from Tool execution and Credential authority.
8. Treat Skills as a trust boundary comparable to executable/project instructions.
9. Reuse the open standard directly; avoid private Ordivon Skill semantics.
10. Validate real task performance; the existence of a Skill does not prove it improves outcomes.

## Project-study acceptance

### One-sentence test

PASS: Agent Skills are progressively disclosed, task-activated packages of procedural knowledge plus optional scripts/references/assets.

### Prototype test

PASS: discovery, catalog injection, activation, resource loading and execution-authority boundaries are explicit enough to implement a compatible loader in a small prototype.

## Verdict

**PASS — ADOPT STANDARD + USE ECOSYSTEM + EXTRACT DESIGN RULES.**

Further investigation should be demand-driven: individual production Skills should be studied only when Ordivon needs that specific capability.
