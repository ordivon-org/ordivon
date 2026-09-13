# Cloudflare Edge provider maintenance boundary

Date admitted: 2026-09-13

Maintained source: `providers/cloudflare/`

## Operations owns

- source maintenance and dependency upgrades;
- local installation/materialization of client and control scripts;
- systemd service/timer bytes and lifecycle;
- provider policy/config materialization;
- release/rollback/GC controller maintenance;
- mechanical health/SLO observation and evidence plumbing.

## Operations does not own

- Cloudflare Worker/R2/request/receipt truth;
- permission to perform a consumer-requested external effect;
- Task/domain completion or semantic verification;
- generic cross-provider ontology or provider broker semantics.

## Provenance

The provider was extracted from `ordivon-world@4f908b237d45a8e8759bfdf3ec41dab8e4b73948`, briefly staged as `/root/projects/ordivon-cloudflare-provider`, and absorbed into Operations from staging revision `44f0cc3eb19e665f61b942bf24915ea06c493eb2`. The staging repository is not a retained top-level project.

Historical private release/GC receipts remain under `/root/backups/ordivon-world/` for continuity; their path does not confer current World ownership.
