# E7: MCP Risk Assessment

## Input

A project has discovered an MCP server configuration:

```
Server: github-enterprise
Source: third-party (github.com/example/mcp-ghe)
Exposed tools:
  - read_issue (read-only)
  - create_issue (write)
  - list_repos (read-only)
  - merge_pr (write, no approval flow)
  - delete_branch (destructive)
  - update_protected_branch (modifies repo settings)
```

The server has no trust classification, no permission manifest, and no audit logging.

## Task

Assess the risk and recommend what should be done before connecting.
