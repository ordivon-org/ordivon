# API App

`apps/api/` is the FastAPI entrypoint for the PFIOS experience surface.

## Owns

- API route mounting
- request/response schemas
- dependency injection
- app startup

## Current Shape

- `app/api/v1/`: v1 HTTP routes
- `app/schemas/`: transport schemas
- `app/deps.py`: DB and orchestrator dependencies
- `app/main.py`: ASGI app entrypoint

## Does Not Own

- business truth
- governance policy
- orchestration logic
- prompt/runtime logic
