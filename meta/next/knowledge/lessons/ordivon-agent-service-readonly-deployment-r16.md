# Ordivon Agent Service — Read-Only Deployment Canary R16

Status: **IMPLEMENTED / ACCEPTANCE PASS**
Date: 2026-09-18
Base main: `5413e02d8a184077b1cfde9b8726963758bbacb4`

## Purpose

Close the next propagation gap after R15: prove that Agent Service can cross the source-library -> daemon -> authenticated stateless MCP -> consumer boundary without exposing production mutation or provider effects.

## Surface

Default endpoint: `http://127.0.0.1:8894/mcp`.

Exactly four tools are admitted:

- `service.doctor`;
- `service.contract`;
- `architecture.identity`;
- `deployment.snapshot`.

All are read-only, idempotent, closed-world tools. There is no Session, Delegation, route, credential, delivery, Runtime mutation, Host mutation or provider-effect operation.

## Deployment bundle

- `scripts/agent_service_mcp.py` — authenticated loopback MCP facade;
- `config/agent-service-mcp-requirements.txt` — pinned canary dependencies;
- `systemd/ordivon-agent-service-canary-mcp.service` — hardened parallel unit;
- `tests/test_agent_service_mcp_canary_r16.py` — source/deployment contract tests.

The unit is intentionally parallel to `ordivon-agent-automation-mcp.service`; R16 does not replace or disable the legacy path.

## Current verification

Source tests: 5/5 PASS in an MCP 2.0 deployment venv.

Ephemeral real-network smoke on loopback port 18894:

- unauthenticated MCP POST -> HTTP 401;
- authenticated MCP 2026-07-28 `tools/list` -> HTTP 200;
- exact returned tool set = four R16 read-only tools;
- returned tool annotations report readOnlyHint=true and destructiveHint=false.

No production database, systemd installation, Runtime/Host mutation or provider effect was used by this smoke.

Final source verification: graph history 14 files / 92 nodes / zero hard collisions; graph regression 1/1 PASS; MCP deployment-v2 tests 5/5 PASS; repository suite 274 tests PASS with 5 expected MCP-environment skips under system Python. A later live 8894 systemd canary is a separate deployment action and does not imply production write/effect admission.
