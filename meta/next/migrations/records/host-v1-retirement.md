# Host v1 source retirement

- Source: `/root/projects/ordivon-host`
- Final archive commit: `c7aefcf011154e2bd38d7ba26824c23a7627b418`
- Closed: 2026-09-14
- New-model disposition: **ARCHIVED PRODUCT/RESEARCH CORPUS; PRODUCTION ALREADY RETIRED**

This record concerns **Host v1 only**. It does not retire `/root/projects/ordivon-host-v2`.

Operations evidence already established production v1 retirement: the legacy systemd service and listener are absent, installed Host executable/runtime material was removed, and durable state was independently preserved under `/var/lib/ordivon/retired/host-v1` with SQLite, PostgreSQL migration evidence, and rebuildable Parquet/DuckDB historical projections.

Host v2 is a clean-room PostgreSQL implementation and does not import the `ordivon_host` v1 package. Remaining references to Host v1 are historical, compatibility, migration, behavioral-oracle, or evidence references.

Do not deploy or extend Host v1. Any future decision about Host v2's role is separate from this v1 closeout.
