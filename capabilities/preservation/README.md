# Ordivon Preservation capability

This is a thin, standard-native source/evidence package extracted from the historical
workstation-lab repository. It is not a preservation runtime framework.

External owners retain preservation semantics:

- ISO 14721:2025 (OAIS) provides the archival reference model.
- Archivematica 1.18.0 and its Storage Service own local AIP/transfer/storage workflows.
- Artefactual Fixity owns scheduled/bulk fixity client behavior.
- PREMIS/METS, PRONOM and E-ARK profiles retain their native semantics.
- systemd owns timer/process scheduling; Docker Compose owns local container composition.

Ordivon owns only the bounded local profile: exact provider/version/carrier selection,
the R7/R10 historical composition, the current R11 local operational overlay, immutable evidence, and independent verification.

The current Archivematica Docker composition is a validated local preservation profile.
It is not claimed to be an officially supported Archivematica production deployment,
an OAIS certification, a CoreTrustSeal certification, or an independent off-site
failure domain.

Creative Library is intentionally excluded. It is a presentation/read-model concern
with current Media consumers, not preservation-format authority.

## Current R11 host-port profile

The current local Docker Compose overlay is `config/archivematica-preservation-r11.compose.yml`. R11 preserves the accepted R10 restart/volume/image constraints and moves published host ports from 620xx to 420xx because Windows/WSL host networking dynamically excluded the former 620xx range during the 2026-09-27 recovery. Provider container ports and inter-container service names are unchanged. R10 remains frozen historical closeout evidence.
