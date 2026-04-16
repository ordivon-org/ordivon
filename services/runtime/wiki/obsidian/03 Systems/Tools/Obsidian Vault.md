# Obsidian Vault

Obsidian is the human-facing workspace for the knowledge base and operating docs.

## Canonical Path

- `/home/dev/Documents/Obsidian Vault`

This is the only vault path that should be treated as canonical.

## Role

- human-readable workspace
- entry point for rules, research, trading notes, and systems docs
- visual layer over the markdown files Hermes reads and writes

## Current Structure

- `00 Inbox/` for quick capture
- `01 Research/` for sources and wiki material
- `02 Trading/` for actionable market notes
- `03 Systems/` for rules, tools, templates, and workflows
- `99 Rules/` for machine and operating policy

## Practical Rule

Obsidian is not the source of truth because of the app itself.

The source of truth is the markdown tree under this vault path.
Obsidian is the preferred interface for browsing and editing it.

## Relationship To Hermes

- Hermes should treat this path as the default vault
- notes should be linked with `[[wikilinks]]` when useful
- stable procedures belong in `03 Systems/`
- machine policy belongs in `99 Rules/`

## Related Docs

- [[03 Systems/Tools/Research Wiki]]
- [[03 Systems/Workflows/Hermes + Obsidian + Wiki Workflow]]
