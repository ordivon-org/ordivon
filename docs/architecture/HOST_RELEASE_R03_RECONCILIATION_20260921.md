# Host Release R03 Reconciliation — 2026-09-21

Status: **ACCEPTED**

R03 reconciles the live Host deployment without collapsing independent identity axes.

| Axis | Live identity |
|---|---|
| Git source/release | `69e8fc5f231c2c95cd5c5aac3f184e53989ecb04` |
| Source subtree | `services/host` |
| Git tree object | `4203ec1818446748a150a8e5825c4f89ee1268ec` |
| Subtree archive SHA-256 | `sha256:278b472fbe82a0fa4cb1db93646d48f6412ae3397bf86ef9dc43dcb4f6d64387` |
| Package version | `ordivon-host-v2 0.1.0` |
| MCP serverInfo | `ordivon-host-v2 / 0.1.0` |
| MCP protocol | `2025-11-25` |
| PostgreSQL schema | `5` |
| Live tool count | `10` |
| Tool-catalog digest | `sha256:80d5cdc944479874e8b114429cdfbef61f5f630742ba1396c34ae2de96ebd571` |

The monorepo-aware installer emitted `source_subtree=services/host` and installed the immutable release at
`/opt/ordivon/host-v2/releases/69e8fc5f231c2c95cd5c5aac3f184e53989ecb04`.
The prior observed immutable release `a95a8e112edfbe85582ff8e6fa25bb268038ea48` remains available as rollback material.

After restart, `ordivon-host-v2.service` was active/running with zero restarts. Host integrity reported PostgreSQL schema 5 and every doctor check healthy.

The package version, MCP server version, database schema, Git revision and tool-catalog digest are intentionally **not interchangeable**. The machine-readable receipt beside this document is the canonical reconciliation evidence.
