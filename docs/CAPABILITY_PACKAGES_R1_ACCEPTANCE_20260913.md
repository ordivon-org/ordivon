# Capability Packages R1 — Local Census and Acceptance Receipt

Date: 2026-09-13
Subject revision: `3a279b3eb2fca33dd736a3c6581e6551dd89afb4`

This is a dated operational snapshot for `docs/CAPABILITY_PACKAGES_R1.md`. It is **not** a registry, required stack, permanent topology, or a demand to install every selected tool.

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
- `PARTIAL_ACCEPTANCE` — some real evidence exists, but the package's current acceptance workload is incomplete.

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
| Research | `READY_SCOPED` + `PARTIAL_ACCEPTANCE` for full paper lifecycle | Research v2 has project-local Snakemake/DVC environment; a real first-paper DAG has already run and a second identical invocation was a no-op; research Skills are installed | literature/reference and publication profiles remain selected but not activated; no actual manuscript source was found in the two Research repositories during this census | **Do not install by census.** Activate the smallest bibliography/publication path when the current paper exposes the real manuscript/bibliography input |
| Engineering | `READY_LOCAL` | Codex, Git/GitHub CLI, Python/Node/Go/Rust/Java, CMake/Ninja/Make, pytest/Ruff, containers, Runtime, Ansible, n8n and scoped Playwright | no demonstrated missing engineering class | use the next real software change as acceptance; no Engineering-v2 repo |
| Security | `READY_SCOPED` + `PARTIAL_ACCEPTANCE` | Gitleaks, OSV-Scanner, Trivy, Syft, OPA, Cosign plus Security-v2 on-demand Semgrep and containerized Scorecard | Gitleaks passed on subject revision; the first Trivy stage stalled before producing evidence and the parallel job was later cancelled; no local Trivy DB/cache was observed in the follow-up readiness probe | keep standing partial; prove provider freshness/execution on the next real security acceptance rather than reinstalling the whole stack |
| Artifact | `READY_LOCAL` | accepted Artifact-v2 provider, `artifact-work`, Typst, qpdf, FFmpeg, ImageMagick, Blender, DuckDB/GDAL, Syft/Trivy/Skopeo/Cosign | no generic gap demonstrated | use next real artifact request and native validator/target evidence |
| Media | `READY_LOCAL` for core production; `SELECTED_NOT_ACTIVATED` for optional trust/metadata layers | FFmpeg, ImageMagick, Blender + Artifact/Distribution/Research | no current media workload proving need for extra metadata/provenance tooling such as C2PA utilities | defer; activate on first real media production request |
| Game | `READY_LOCAL` | Godot, Blender, FFmpeg/ImageMagick, Codex, existing Veilwild/Game evidence + shared Engineering/Artifact/Security | package re-profile should happen through a playable candidate, not architecture work | use next real playable candidate |
| Data & Analytics | `READY_LOCAL` | Python, DuckDB, SQLite, GDAL/OGR, statistics/visualization Skills, Research/Artifact paths | no repeated ownership or lineage gap demonstrated; OpenLineage-class infrastructure is optional until a real multi-system lineage problem exists | use a real dataset as acceptance; no `ordivon-data-v2` |
| Distribution | `READY_SCOPED` + `AUTHORITY_GATED` | Distribution v2, Runtime evidence paths, n8n, OCI/Skopeo-class providers | real provider writes correctly remain gated by exact effect authority | wait for an explicitly authorized publish effect; prove provider read-back |
| Operations | `READY_SCOPED` | Temporal under `/opt`, n8n, Ansible, `/usr/bin/tofu`, Prometheus/node-exporter, osquery, OPA; Vector/Grafana/Loki are installed but some are intentionally inactive | no missing general operations framework demonstrated | validate through a useful real long-running workflow; do not activate dormant components merely for coverage |
| Network | `READY_LOCAL` | Network v2 plus tcpdump, mtr, dig/nslookup, iperf3, tracepath, ss, nft, WireGuard and OpenVPN | no current unresolved path problem in this census | activate when a real reachability/throughput/path failure appears |

## No-install decisions from R1

This census does **not** justify installing Quarto, Zotero, Kubernetes, Helm, a global Semgrep binary, C2PA tooling, ExifTool, MediaInfo, Wireshark/tshark, or any other absent executable merely to make a checklist green.

Examples:

- Research publication: Pandoc is available from the configured Arch repositories, but the actual manuscript source/bibliography is not currently exposed in the inspected Research repositories. Installation before that input exists would be inventory-driven rather than workload-driven.
- Security: a global Semgrep install would duplicate an existing on-demand provider path without evidence of a new finding class.
- Operations: OpenTofu was already installed; the apparent absence came from probing the wrong executable name.
- Network: tshark/Wireshark may be useful for future packet-level diagnosis, but current mature CLI probes cover the active network package and no packet-decoding workload was presented.

## First real acceptance status

### Research

The computational/reproducibility spine has real evidence already: exact frozen inputs, Snakemake execution, and an idempotent second invocation. Full package acceptance remains open because the live chain through manuscript/publication/peer-review is not yet represented by an actual manuscript input in the inspected repositories.

Standing: `PARTIAL_ACCEPTANCE`.

### Security

A real scan attempt was bound to subject revision `3a279b3eb2fca33dd736a3c6581e6551dd89afb4`.

Observed:

- Gitleaks completed successfully and reported no leaks.
- Trivy `0.73.0` is installed, but the first scan did not progress to evidence before cancellation.
- A follow-up local readiness probe found no reusable Trivy database/cache evidence, so a cold provider acquisition/update path remains a plausible blocker rather than a finding result.

This is deliberately **not** promoted to Security PASS.

Standing: `PARTIAL_ACCEPTANCE`; reopen with bounded provider freshness/network evidence on the next real Security workload.

### Engineering / Artifact / Game / Media / Data / Distribution / Operations / Network

Do not manufacture synthetic demonstrations solely to graduate the inventory. Their next acceptance should be attached to the next real workload named in `CAPABILITY_PACKAGES_R1.md`.

## R1 decision

The local capability base is already broad enough to stop bulk capability installation.

Default loop from here:

`real task -> select package(s) -> discover mature owner/provider -> check scoped local availability -> activate/install only the missing capability -> execute -> verify with native/domain evidence -> retain only useful mappings/lessons`

The success criterion is not package count or tool count. It is increasing verified real-world output while keeping Ordivon-owned implementation and dormant local coupling small.
