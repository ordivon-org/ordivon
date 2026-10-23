# Structure R2 S2A — Control Plugin Relocation

Date: 2026-09-22
Status: **ACCEPTED / POST-MERGE VERIFIED**

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

## Verification

Candidate verification:

- `control-plugin:verify` — PASS (17 tests; Agent Plugins 1.0 schemas; Gateway-only MCP surface).
- `next:verify` — PASS.
- Structure R2 checker — PASS.
- architecture documentation drift checker — PASS.
- root `repo:ci` — PASS.
- owner-boundary scan — PASS at 1,952 active files / 18 seams / 23 references.
- repository architecture tests — 33 passed.

Serialized integration:

```text
candidate = 96db72e07832a2b0c653e13fe62903acb13b55cc
previous_main = 4d46d741994ce08c8282c62c5154aef57f20331a
main = 466f44387f1698481d1253982a004aad21ebfac2
integration = MERGE_COMMIT
```

Fresh post-merge verification from `main@466f44387f1698481d1253982a004aad21ebfac2`:

- `control-plugin:verify` — PASS.
- Structure R2 checker — PASS.
- `next:verify` — PASS.
- root `repo:ci` — PASS.
- owner-boundary scan — PASS at 1,952 active files / 18 seams / 23 references.
- repository architecture tests — 33 passed.

S2A is closed. S2B-S9 remain open.
