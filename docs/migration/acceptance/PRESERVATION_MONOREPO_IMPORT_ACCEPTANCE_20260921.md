# Preservation Monorepo Import Acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: identity-preserving import of the extracted standard-native Preservation capability into `capabilities/preservation`.

## Source identity

- Historical source container: `/root/workstation-lab`
- Historical observed head: `c45aa22ca9b4632dd98fdacef539bf167db61ab0`
- Extracted source repository: `/root/ordivon-migration-backups/2026-09-21-preservation-extract/preservation.git`
- Extracted source revision: `2b9c9a4955d232870d2737864abeae662a6ec08e`
- Extracted source tree: `9a5c4e7dadbd80647bbbbc994d68d3349ae7e4ba`
- Import merge: `c87bf19dfddb4a55f307a740584502d5afc3aa00`
- Target path: `capabilities/preservation`
- Bundle: `/root/ordivon-migration-backups/2026-09-21-preservation-extract/preservation.bundle`
- Bundle SHA-256: `5f13af9df698ee1b3819628726b6815a43da3a09f51537ac0ac6d46cf7d7cdfc`

The extracted source tree and imported monorepo subtree are identical.

## Authority boundary

Preservation is a bounded local profile, not a new Ordivon preservation runtime framework.

External owners retain preservation semantics: ISO 14721:2025/OAIS, Archivematica 1.18.0 and Storage Service, Artefactual Fixity 0.8.0, PREMIS/METS, PRONOM, E-ARK, systemd and Docker Compose.

Ordivon retains only exact provider/version/carrier selection, the validated R7/R10 local composition, immutable evidence, and independent verification.

Creative Library is explicitly excluded because it is a Media-facing presentation/read-model concern.

## Deterministic source acceptance

Executed from the candidate monorepo path `capabilities/preservation/`:

- owner prefix: PASS;
- source/subtree tree identity: PASS;
- `SOURCE_BOUNDARY.json`: PASS;
- 20 JSON evidence objects parsed successfully;
- systemd service/timer static verification: PASS;
- systemd security/authority semantics checks: PASS;
- forward source secret/private-key scan: PASS;
- `git diff --check`: PASS.

## Provider-native composition acceptance

The R10 file is an overlay, not a standalone Compose project. Correct validation composed the external Archivematica 1.18 base with `config/archivematica-preservation-r10.compose.yml`.

The merged Compose configuration passed native parsing and semantic checks:

- all nine target services use `restart: unless-stopped`;
- ClamAV remains image-digest pinned;
- Storage Service retains the R7 secondary-store and read-only upstream `unar/lsar` bindings.

Observed carrier state:

- Storage Service, Dashboard, MCP Client, MCP Server, Gearman, ClamAV and Elasticsearch: running;
- Artefactual Fixity executable: present;
- upstream XADMaster 1.10.8 `unar/lsar`: present.

The external Archivematica checkout contains provider-local dirty/untracked files. That observation is not promoted to Ordivon source truth and does not alter the extracted capability tree.

## Non-claims

This acceptance does not claim official Archivematica production support for the Docker profile, OAIS certification, CoreTrustSeal certification, an independent/off-site failure domain, or a newly re-run destructive recovery drill.

Historical R6-R10 evidence remains evidence about those exact prior operations.

## Boundary

`ACCEPTED_SOURCE_ONLY` does not perform production cutover, credential migration, external-provider mutation, or workstation-lab retirement.
