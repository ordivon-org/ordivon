---
name: clean-test-skill
description: A clean skill with proper boundaries and no risky language.
allowed-tools: Read, Grep, Glob
owner: test-owner
---

# Clean Test Skill

This skill reads files and searches code. It does not request credentials.

## Tools

- Read: reads file contents
- Grep: searches file contents
- Glob: finds files by pattern

## Boundaries

This skill capability is not permission. Tool access does not authorize
merge, deploy, release, execution, or external action. Owner/reviewer
must confirm canonical gates and authorize all high-impact actions.

## Verification

Run: python -m pytest tests/ -q
