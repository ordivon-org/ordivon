# Research Wiki

The wiki is the durable markdown knowledge layer inside the vault.

## Current Position

For this machine, the wiki is not a separate repo or separate vault.

It is the structured knowledge portion of:

- `/home/dev/Documents/Obsidian Vault/01 Research/wiki`

## Purpose

- convert raw sources into stable markdown knowledge
- preserve cross-linked notes that improve over time
- separate durable synthesis from temporary capture

## Operating Flow

1. Raw material lands in `01 Research/raw/` or `01 Research/sources/`
2. Hermes extracts and summarizes the material
3. durable notes are written into `01 Research/wiki/`
4. trading-relevant conclusions may be promoted into `02 Trading/`
5. procedural lessons may be promoted into `03 Systems/`

## Relationship To Hermes Skills

The upstream Hermes skill most aligned with this layer is:

- `research/llm-wiki`

That skill assumes a markdown wiki with conventions, cross-links, and durable updates.
This vault uses the same idea, but scoped to the current folder structure instead of a separate `~/wiki` directory.

## Current Rule

- raw sources are allowed to be messy
- wiki pages should be durable and readable
- avoid duplicating the same concept across multiple pages
- when a note becomes procedural rather than informational, move or rewrite it into `03 Systems/`
