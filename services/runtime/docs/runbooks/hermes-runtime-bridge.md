# Hermes Runtime Bridge Runbook

## Purpose

This runbook starts the standalone Hermes bridge that `financial-ai-os` now calls when `PFIOS_REASONING_PROVIDER=hermes`.

PFIOS expects the bridge to expose:

- `GET /pfios/v1/health`
- `POST /pfios/v1/tasks`

## Start Hermes Bridge

From [hermes_cli/pfios_bridge.py](/c:/Users/16663/Desktop/dev/projects/hermes-runtime/hermes_cli/pfios_bridge.py):

```powershell
cd C:\Users\16663\Desktop\dev\projects\hermes-runtime
$env:HERMES_PFIOS_API_TOKEN="local-dev-token"
$env:HERMES_PFIOS_PROVIDER="gemini"
$env:HERMES_PFIOS_MODEL="google/gemini-3.1-pro-preview"
uvicorn hermes_cli.pfios_bridge:app --host 127.0.0.1 --port 9120
```

## Start PFIOS Against Hermes

Set the matching environment in `financial-ai-os`:

```powershell
cd C:\Users\16663\Desktop\dev\projects\financial-ai-os
$env:PFIOS_REASONING_PROVIDER="hermes"
$env:PFIOS_HERMES_BASE_URL="http://127.0.0.1:9120/pfios/v1"
$env:PFIOS_HERMES_API_TOKEN="local-dev-token"
$env:PFIOS_HERMES_DEFAULT_PROVIDER="gemini"
$env:PFIOS_HERMES_DEFAULT_MODEL="google/gemini-3.1-pro-preview"
uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
```

## Verify

Health:

```powershell
curl http://127.0.0.1:8000/api/v1/health
```

Analyze:

```powershell
curl -Method POST http://127.0.0.1:8000/api/v1/analyze-and-suggest `
  -ContentType "application/json" `
  -Body '{"query":"Analyze BTC momentum","symbols":["BTC/USDT"]}'
```

Traceability:

- `GET /api/v1/agent-actions/latest`
- `GET /api/v1/agent-actions/{action_id}`
- `GET /api/v1/agent-actions/trace/recommendations/{recommendation_id}`

## Expected Outcomes

- every Hermes-backed analyze run creates one `agent_actions` row
- analysis metadata includes `agent_action_id`
- audit payloads include `agent_action_id`
- dashboard summary exposes runtime status and latest agent action

## Fallback

To return to the previous local mock behavior, set:

```powershell
$env:PFIOS_REASONING_PROVIDER="mock"
```
