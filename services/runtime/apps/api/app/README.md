# API Application Package

`apps/api/app/` is the concrete FastAPI application package.

## Current Structure

- `api/`: versioned API route tree
- `schemas/`: transport schemas
- `deps.py`: dependency wiring
- `main.py`: ASGI app entrypoint
- `services/`: compatibility-era app services

## Boundary

This package owns HTTP assembly and transport concerns.
It does not own business truth or governance policy.
