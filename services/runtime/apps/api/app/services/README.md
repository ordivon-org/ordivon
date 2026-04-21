# API Services

`apps/api/app/services/` contains compatibility-era application services.

## Current Role

- transitional glue
- API-local composition helpers

## Boundary

These services should not grow into the main business layer.
Prefer capabilities, domains, execution adapters, and orchestrators for new work.
