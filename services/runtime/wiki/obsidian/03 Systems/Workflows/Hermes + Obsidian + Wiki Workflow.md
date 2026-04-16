# Hermes + Obsidian + Wiki Workflow

This is the stable operating workflow for the current environment.

## Division Of Labor

- Hermes: execution, summarization, transformation, maintenance
- Obsidian: browsing, editing, linking, reviewing
- wiki: durable markdown knowledge

## Standard Workflow

1. Capture incoming material in `00 Inbox/`, `01 Research/raw/`, or `01 Research/sources/`
2. Use Hermes to summarize or restructure the material
3. Save durable knowledge into `01 Research/wiki/`
4. Promote market-specific conclusions into `02 Trading/`
5. Promote repeatable operating knowledge into `03 Systems/`
6. Update `99 Rules/` when machine or environment policy changes

## When To Use Which Layer

Use `01 Research/raw/` when:

- the input is new
- the source is messy
- no durable conclusion has been written yet

Use `01 Research/wiki/` when:

- the information has been synthesized
- the note should stay useful after the original session
- the content should link to related notes

Use `02 Trading/` when:

- the output is directly actionable for market work
- the note affects execution, risk, or narrative framing

Use `03 Systems/` when:

- the output is about tools, rules, templates, or workflows
- the note should guide future operating behavior

## Relevant Hermes Skills

The current Hermes runtime already includes skills that map to this workflow:

- `note-taking/obsidian` for vault interaction
- `research/llm-wiki` for markdown knowledge-base maintenance
- `autonomous-ai-agents/hermes-agent` for Hermes runtime usage and extension

## Current Paths

- runtime: `/home/dev/projects/hermes-runtime`
- state: `/home/dev/state/hermes`
- vault: `/home/dev/Documents/Obsidian Vault`
- wiki layer: `/home/dev/Documents/Obsidian Vault/01 Research/wiki`
