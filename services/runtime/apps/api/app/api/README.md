# API Route Tree

`apps/api/app/api/` contains versioned HTTP route trees.

## Current Focus

- `v1/`: the active public API surface

## Rules

- routes should stay thin
- transport logic belongs here
- business semantics should flow through capabilities, domains, or orchestrators
