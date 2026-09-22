# Structure R2 S2A — Control Plugin Relocation

Date: 2026-09-22
Status: **CANDIDATE — requires verification/integration**

## Scope

Relocate only the portable Agent Plugins 1.0 `ordivon-control-plane` package skeleton from
`meta/next/plugins/ordivon-control-plane` to the repository-level extension boundary
`extensions/ordivon-control-plane`.

## Preserved boundaries

- Plugin remains MCP-only by default.
- `mcp.json` still declares exactly one Ordivon Gateway endpoint.
- Plugin owns package bytes only; Runtime, Host, Skill, and domain truth remain external.
- Next retains release/materialization mechanics for now.
- Canonical Skill bytes remain at the pre-S2B path.
- No deployment or public endpoint changes occur in S2A.

## Mechanical change

The Next materializer resolves the Plugin from repo-level `extensions/` and records
`extensions/ordivon-control-plane` in release receipts. Structure R2 now mechanically rejects
an S2A deployed claim if the old source remains or the new target is missing.

## Required verification

- `next:verify`
- Structure R2 checker/tests
- composition architecture checker
- root `repo:ci`
- post-merge repetition before final acceptance
