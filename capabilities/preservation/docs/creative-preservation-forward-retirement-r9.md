# Creative Preservation Forward Packager Retirement R9

Date: 2026-09-14

## Decision

The custom R4/R5 executable forward-preservation layer is retired.

Deleted from the forward working tree:

- `scripts/creative_forward_ingest.py`;
- `tests/test_creative_forward_ingest.py`;
- `requirements/creative-preservation-forward-r1.txt`;
- `requirements/creative-preservation-forward-r1.lock.txt`.

Deleted from local runtime state:

- `/root/.local/share/ordivon-workstation/creative-preservation-tools-r1`;
- `/var/lib/ordivon/creative-preservation/forward-r1/catalog`;
- `/var/lib/ordivon/creative-preservation/forward-r2/catalog`.

The catalogs were explicitly disposable read models. The dedicated Python environment existed only for the retired BagIt/SWHID packager.

## Preserved historical evidence

R4/R5 bags and handoff receipts remain frozen in their existing roots. Their historical Git revision retains the exact deleted implementation and dependency lock, so reproduction remains possible without keeping that implementation live.

```text
forward-r1: 4 bags / 4 receipts
forward-r2: 13 bags / 13 receipts
```

Historical R4/R5 docs and receipts are not rewritten into E-ARK. They remain evidence about what was actually executed at the time.

## Forward replacement

```text
owner-approved object + exact authoritative bytes
        ↓
E-ARK SIP 2.2.0 / CSIP 2.2.0
        ↓
Commons-IP 2.11.3 validation
        ↓
preservation ingest provider
```

BagIt may still be used by the current Archivematica engine adapter, but Ordivon no longer owns a BagIt handoff generator or a preservation catalog rebuilt from private receipts.

## Residual boundary

Owner-domain approval and exact-byte resolution remain domain responsibilities. New preservation ingest orchestration must first evaluate Enduro/provider-native workflows rather than reviving this script.
