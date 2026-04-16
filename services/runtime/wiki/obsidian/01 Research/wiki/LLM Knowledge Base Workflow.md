# LLM Knowledge Base Workflow

Inspired by Karpathy's recent comments on LLM knowledge bases.

## Core Idea

Use the model to build and maintain a markdown knowledge base, not just answer isolated questions.

## Structure

- `raw/`: unprocessed source material
- `wiki/`: cleaned topic pages
- `trading/`: decisions, signals, dossiers, reviews

## Operational Pattern

1. Capture raw material.
2. Summarize into stable notes.
3. Link related notes with `[[wikilinks]]`.
4. Revisit and consolidate after major new information.
5. Use the knowledge base as the context layer for decision-making.

## Why It Matters

- Reduces repetitive prompting
- Preserves institutional memory
- Makes pattern comparison easier
- Supports post-trade learning loops

## Related

- [[02 Trading/Trading Knowledge Base]]
- [[03 Systems/Hermes + Obsidian Workflow]]
