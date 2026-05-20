# Tool Permission Levels (M0–M5)

From D2: MCP Permission Model debt processing. These levels apply to both
local tools and MCP-exposed tools.

| Level | Description | Example | Approval |
|-------|-------------|---------|----------|
| M0 | Disabled | Unknown MCP, high-risk tool | Blocked |
| M1 | Read-only local | read file, list resources | Implicit |
| M2 | Read-only external | read GitHub issue, search docs | Context |
| M3 | Local mutation | edit file, run formatter, generate draft | Context-dependent |
| M4 | External mutation | create PR, update Notion, draft email | User confirmation |
| M5 | Critical / irreversible | deploy, delete data, execute trade | Explicit human authorization |

## Rules

- Tool access ≠ execution authority
- Mutating tools (M3+) require stronger gates
- M5 tools require explicit human authorization
- Every MCP tool carries permission metadata
- External data from MCP is untrusted until source-bound
