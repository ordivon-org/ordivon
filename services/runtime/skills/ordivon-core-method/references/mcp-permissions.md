# MCP & Tool Permission Levels (M0–M5)

## Levels

| Level | Description | Example | Approval |
|-------|-------------|---------|----------|
| M0 | Disabled | Unknown MCP, untrusted server, high-risk tool | Blocked entirely |
| M1 | Read-only local | read file, list resources, inspect config | Implicit |
| M2 | Read-only external | read GitHub issue, search docs, query DB view | Context-dependent |
| M3 | Local mutation | edit file, run formatter, generate draft | Context-dependent |
| M4 | External mutation | create PR, update Notion, draft email | User confirmation |
| M5 | Critical / irreversible | deploy, delete data, execute trade, merge PR | Explicit human authorization |

## Rules

- Tool access ≠ execution authority. Availability is not permission.
- M5 tools require explicit human authorization before every use.
- MCP server discovery ≠ trust. External servers are untrusted until reviewed.
- Every MCP-exposed tool must carry permission metadata.
- External data from MCP is untrusted until source-bound.
- Mutating MCP calls (M4+) require receipt.
