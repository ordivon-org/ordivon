# Market Capital contracts

Current contracts are selected only through current configuration and current code references; directory presence alone does not confer authority.

## Current

- `semantic-core-v1.json` — current Market Capital semantic boundary.
- `external-boundary-v1.json` — current component-responsibility boundary.
- `external-financial-write-admission-v1.json` — current external-effect admission contract. It records whether a concrete provider/executor financial-write capability is implemented, bound, current, and admitted; it is not a generic production approval or Human authorization bit.

## Frozen historical compatibility

- `production-authorization.json` — **retired from current authority**. This file remains byte-preserved at its historical path because frozen 2026-09-13 migration evidence references its exact content digest. Current config, code, runners, monitoring, and tests must not load it as an authority source. Its `BLOCK_NOT_GRANTED` value is historical vocabulary only.

Historical byte preservation must not be interpreted as semantic retention. New work must bind the current external-financial-write-admission contract instead.
