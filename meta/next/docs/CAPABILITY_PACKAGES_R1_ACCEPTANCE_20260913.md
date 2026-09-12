# Capability Packages R1 — Local Census and Acceptance Receipt

Date: 2026-09-13
Initial census subject revision: `3a279b3eb2fca33dd736a3c6581e6551dd89afb4`

This is a dated operational snapshot for `docs/CAPABILITY_PACKAGES_R1.md`. It is **not** a registry, required stack, permanent topology, or a demand to install every selected tool. Later evidence in this same receipt supersedes earlier partial observations.

## Census rule

A PATH miss is not a capability miss. Availability is checked in the scope where the capability is actually owned:

- system package / canonical executable;
- project-local virtual environment;
- `/opt` or provider-owned installation;
- container image;
- `uvx` / package-runner acquisition;
- connected service/API;
- authority-gated external provider.

Snapshot labels used here are descriptive only:

- `READY_LOCAL` — immediately invokable from the current local substrate;
- `READY_SCOPED` — available in the owning project/provider scope rather than globally;
- `READY_ON_DEMAND` — mature provider selected and reacquirable/invokable when a real task needs it;
- `SELECTED_NOT_ACTIVATED` — ecosystem choice is known but no current workload justifies activation;
- `AUTHORITY_GATED` — mechanics exist but consequential external action correctly remains blocked without exact authority;
- `PARTIAL_ACCEPTANCE` — some real evidence exists, but the package's current acceptance workload is incomplete;
- `ACCEPTED_FOR_CURRENT_WORKLOAD` — the current real workload is served and remaining gaps belong to later task/submission boundaries rather than package construction.

## Important false-miss corrections

The first generic PATH probe produced several apparent gaps that were not real gaps:

- OpenTofu is installed as package `opentofu 1.12.6-1`; its executable is `/usr/bin/tofu`, not `opentofu`.
- Temporal CLI/server are provider-owned under `/opt/ordivon/external/temporal-*`; Operations records CLI `1.8.3` and server `1.31.2`, with the local server bound on loopback.
- Snakemake is intentionally Research-v2-local at `.venv/bin/snakemake`; the current lock contains Snakemake `9.26.1`.
- Playwright has an external provider installation under `/opt/ordivon/external/playwright-cli` even though no generic `playwright` command is on PATH.
- Semgrep is intentionally an on-demand Security-v2 provider (`uvx --from semgrep==1.177.0 semgrep`) rather than a globally installed binary.
- OpenSSF Scorecard is intentionally exercised through its official container image in Security v2 rather than required as a host binary.

Therefore future census work must classify *provider scope* before proposing an installation.

## Package snapshot

| Package | Standing on this workstation | Evidence / current providers | Real gap or next trigger | Action now |
| --- | --- | --- | --- | --- |
| Research | `READY_SCOPED` + `ACCEPTED_FOR_CURRENT_WORKLOAD` | Research v2 project-local Snakemake/DVC stack; six Research Skills; real 12-DOI bibliography; pinned Quarto `1.11.1` offline render; 44 passing tests | citation field normalization, structured citations in the scientifically selected current manuscript, publication metadata, and replication-package deposit are submission-bound tasks | **Stop generic Research construction.** Continue the real paper and activate only submission/domain capabilities it actually needs |
| Engineering | `READY_LOCAL` | Codex, Git/GitHub CLI, Python/Node/Go/Rust/Java, CMake/Ninja/Make, pytest/Ruff, containers, Runtime, Ansible, n8n and scoped Playwright | no demonstrated missing engineering class | use the next real software change as acceptance; no Engineering-v2 repo |
| Security | `READY_SCOPED` + `ACCEPTED_FOR_CURRENT_SOFTWARE_SLICE` | Gitleaks, OSV-Scanner, Trivy, Syft, OPA, Cosign plus Security-v2 on-demand Semgrep and containerized Scorecard; exact `ordivon-runtime@e2c25e03dde172eb958068698282454a75060f23` slice executed | no missing scanner class demonstrated; online freshness acquisition remains a Network/provider concern when current databases are required | **Do not reinstall or bulk-add scanners.** Select providers by subject/threat surface and keep semantic disposition separate from scanner severity |
| Artifact | `READY_LOCAL` | accepted Artifact-v2 provider, `artifact-work`, Typst, qpdf, FFmpeg, ImageMagick, Blender, DuckDB/GDAL, Syft/Trivy/Skopeo/Cosign | no generic gap demonstrated | use next real artifact request and native validator/target evidence |
| Media | `READY_LOCAL` for core production; `SELECTED_NOT_ACTIVATED` for optional trust/metadata layers | FFmpeg, ImageMagick, Blender + Artifact/Distribution/Research | no current media workload proving need for extra metadata/provenance tooling such as C2PA utilities | defer; activate on first real media production request |
| Game | `READY_LOCAL` | Godot, Blender, FFmpeg/ImageMagick, Codex, existing Veilwild/Game evidence + shared Engineering/Artifact/Security | package re-profile should happen through a playable candidate, not architecture work | use next real playable candidate |
| Data & Analytics | `READY_LOCAL` | Python, DuckDB, SQLite, GDAL/OGR, statistics/visualization Skills, Research/Artifact paths | no repeated ownership or lineage gap demonstrated; OpenLineage-class infrastructure is optional until a real multi-system lineage problem exists | use a real dataset as acceptance; no `ordivon-data-v2` |
| Distribution | `READY_SCOPED` + `AUTHORITY_GATED` | Distribution v2, Runtime evidence paths, n8n, OCI/Skopeo-class providers | real provider writes correctly remain gated by exact effect authority | wait for an explicitly authorized publish effect; prove provider read-back |
| Operations | `READY_SCOPED` | Temporal under `/opt`, n8n, Ansible, `/usr/bin/tofu`, Prometheus/node-exporter, osquery, OPA; Vector/Grafana/Loki are installed but some are intentionally inactive | no missing general operations framework demonstrated | validate through a useful real long-running workflow; do not activate dormant components merely for coverage |
| Network | `READY_LOCAL` | Network v2 plus tcpdump, mtr, dig/nslookup, iperf3, tracepath, ss, nft, WireGuard and OpenVPN | no current unresolved path problem after classifying the Trivy cold-update stall as provider acquisition/network rather than Security analysis | activate when a real reachability/throughput/path failure appears |

## No-install decisions from R1

This census does **not** justify installing Zotero, Kubernetes, Helm, a global Semgrep binary, C2PA tooling, ExifTool, MediaInfo, Wireshark/tshark, or any other absent executable merely to make a checklist green.

Examples:

- Research publication: the real bibliography is now materialized and consumed by pinned Quarto/Pandoc offline. A global Zotero install remains unnecessary unless human library management/collaboration becomes a real requirement.
- Security: a global Semgrep install would duplicate an existing on-demand provider path without evidence of a new finding class.
- Operations: OpenTofu was already installed; the apparent absence came from probing the wrong executable name.
- Network: tshark/Wireshark may be useful for future packet-level diagnosis, but current mature CLI probes cover the active network package and no packet-decoding workload was presented.

## First real acceptance status

### Research — accepted for the current workload

The Research package now has a real evidence chain beyond the earlier computational-only slice. Detailed evidence is recorded in `docs/RESEARCH_CAPABILITY_PACKAGE_R1.md`.

Observed:

- the current paper used 12 real DOI-backed references;
- Crossref resolved all 12 DOI identities;
- DOI content negotiation produced structured BibTeX;
- Research-v2 materialized `references.bib` plus `REFERENCES_RECEIPT.json`;
- pinned Quarto/Pandoc consumed the bibliography with network disabled;
- the acceptance HTML was 23,153 bytes and contained real-reference sentinels;
- repository verification reached 44 passing tests.

Accepted chain:

`real manuscript references -> DOI identity resolution -> structured bibliography -> offline Quarto/Pandoc consumption`

Remaining work is submission-specific, not justification for another generic Research framework.

Standing: `ACCEPTED_FOR_CURRENT_WORKLOAD`.

### Security — accepted software slice with one semantically disposed finding

The documentation-heavy `ordivon-next` repository was first useful as a negative-control object: Gitleaks was applicable, but OSV/Syft found no package sources/components and Trivy had no meaningful target. That is tool inapplicability to the subject, not package failure.

The real software acceptance subject was then switched to:

`ordivon-runtime@e2c25e03dde172eb958068698282454a75060f23`

Observed:

- Gitleaks scanned about 4.93 MB and reported no leaks;
- OSV-Scanner offline discovered the Cargo/Python package sources, including 279 Cargo packages, and reported no issues in the available offline vulnerability data;
- Syft generated a CycloneDX view containing 305 `file`/`library` components;
- Trivy offline secret/misconfiguration scanning reported one HIGH `AsymmetricPrivateKey` in `crates/ordivon-runtime-mcp/src/access_auth.rs`.

The Trivy finding was independently inspected. The key is inside a Rust `#[cfg(test)]` module, is explicitly named `TEST_PRIVATE_KEY`, and is used to generate JWTs for verifier tests. `.gitleaks.toml` documents and allowlists this exact generated test-only fixture as non-production credential material. Current disposition: **expected test fixture / scanner disagreement, not an exposed production secret**.

The first online Trivy attempt stalled while update connections remained `SYN-SENT`; that execution was cancelled and strict offline flags were used. This is retained as a Network/provider-freshness dependency, not misclassified as a Security analysis failure.

Standing: `ACCEPTED_FOR_CURRENT_SOFTWARE_SLICE`; current vulnerability freshness is bounded by the available offline data.

### Engineering / Artifact / Game / Media / Data / Distribution / Operations / Network

Do not manufacture synthetic demonstrations solely to graduate the inventory. Their next acceptance should be attached to the next real workload named in `CAPABILITY_PACKAGES_R1.md`.

## R1 decision

The local capability base is already broad enough to stop bulk capability installation.

Default loop from here:

`real task -> select package(s) -> discover mature owner/provider -> check scoped local availability -> activate/install only the missing capability -> execute -> verify with native/domain evidence -> retain only useful mappings/lessons`

Use `docs/CAPABILITY_CENSUS_TEMPLATE.md` for subsequent package censuses. Stop package construction once the current real outcome is served and verified; reopen only the missing capability family when a later task proves a gap.

The success criterion is not package count or tool count. It is increasing verified real-world output while keeping Ordivon-owned implementation and dormant local coupling small.
