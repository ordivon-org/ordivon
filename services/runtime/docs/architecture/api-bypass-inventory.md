# API Bypass Inventory

This list tracks direct `repo -> response` or router-local read paths that still bypass a dedicated capability.

## Current Bypasses

| Route | Current Path | Risk | Recommendation |
| --- | --- | --- | --- |
| `GET /api/v1/health` | router-only constant response | low | acceptable utility endpoint |
| `GET /api/v1/version` | router-only constant response | low | acceptable utility endpoint |

## Routes Already Using Capability

- `analyze`
- `recommendations`
- `dashboard`
- `reports`
- `audits`
- `evals`
- `validation`
- `reviews/pending`
- review submit/complete flows
