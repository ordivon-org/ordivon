# Hermes + Obsidian Workflow

Hermes now runs as a project-scoped runtime and uses this vault as its working knowledge base.

## Current Vault Path

- `/home/dev/Documents/Obsidian Vault`

## Current Hermes Runtime

- project path: `/home/dev/projects/hermes-runtime`
- state path: `/home/dev/state/hermes`
- enter runtime: `cd /home/dev/projects/hermes-runtime && direnv allow`
- CLI check: `./bin/hermes-runtime --version`
- optional extras: `./bin/bootstrap-node`

## Operating Model

- vault content is durable knowledge and workflow documentation
- Hermes runtime stays project-scoped and is not installed globally
- state is separated from the repo so runtime data does not pollute the project tree
- optional browser and messaging dependencies remain opt-in
- runtime entry should follow the project flake via `.envrc`

## Stable Docs

- [[03 Systems/Tools/Tools Index]]
- [[03 Systems/Tools/Hermes Runtime]]
- [[03 Systems/Tools/Obsidian Vault]]
- [[03 Systems/Tools/Research Wiki]]
- [[03 Systems/Workflows/Hermes + Obsidian + Wiki Workflow]]

## Recommended Workflow

1. Drop messy inputs into `01 Research/raw/`.
2. Ask Hermes to summarize them into `01 Research/wiki/`.
3. Promote trading-relevant ideas into `02 Trading/`.
4. Use `03 Systems/` for operating rules, agent prompts, and workflows.
5. When Hermes operating rules change, update `99 Rules/` and `03 Systems/` before changing habits.

## Reconnection Checklist

- treat `/home/dev/Documents/Obsidian Vault` as the canonical vault
- do not use `/home/dev/Obsidian Vault` as the working vault
- document Hermes procedures in `03 Systems/`
- document machine policy in `99 Rules/`
- add high-value reusable workflows as skills only after the wiki version is stable

## Example Prompts

- Summarize this source into the research wiki and link related notes.
- Create a dossier note for a token and include drivers, risks, and monitoring items.
- Turn today's market notes into a post-trade review template.
- Compare two narratives and identify conflicting assumptions.

## Rule of Thumb

- Raw notes are allowed to be messy.
- Wiki notes should be stable.
- Trading notes should be actionable.
- Runtime decisions should follow the projectized Hermes policy.
