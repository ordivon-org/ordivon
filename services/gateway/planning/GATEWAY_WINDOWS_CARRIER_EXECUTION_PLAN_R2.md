# Gateway Windows Carrier R2 execution plan

## Current truth

- Source/main: `bb666c7cace423f3f15a09a7c115a67e2382ca8d`
- Production WSL Gateway: v0.3.0, release `ad84462e...`, 16 tools, healthy.
- ChatGPT connector: 9 tools; catalog is stale.
- Existing Windows CandidateR1: historical `5bd241df...`, stopped, port 18999 not listening.
- R2 implementation replay: `7db79dfe...` plus current hardening changes; 54/54 tests and ruff pass.

## Immediate sequence

1. Commit R2 carrier hardening and credential materializer.
2. Materialize exact R2 SHA from the WSL workspace via Interactive-Highest Windows Git/PowerShell.
3. Materialize only the Windows Runtime bearer from its existing Windows owner file into the Gateway credential directory; do not expose secret content.
4. Rematerialize CandidateR1 in Manual mode against the exact R2 release.
5. Reapply and verify service SID ACLs.
6. Start CandidateR1 and prove /health, 16-tool MCP surface, Windows Runtime available, Host available, and Linux Runtime unavailable only because GW12 credential handoff remains blocked.
7. Stop WSL and prove Gateway + Windows Runtime remain usable; restart WSL and prove Host returns without Gateway restart.
8. Keep production :8899 unchanged until GW12, public auth, connector-currentness, and destructive lifecycle gates close.

## Explicit stop condition

Do not attempt to extract or relay the Linux Runtime bearer through model/tool output. GW12 remains blocked until an approved secure operator-owned credential handoff exists.
