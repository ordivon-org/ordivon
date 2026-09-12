# Package: Research

Last census: 2026-09-13
Standing: **READY_FOR_REAL_WORK**

## Outcome scope

Turn a research question into a credible, inspectable research result, paper, dataset, model, review, or other scientific output.

This card does not define a Research lifecycle. Study design and reporting must follow the applicable scientific/domain/venue standards.

## Mature external knowledge owners

Use the applicable subset, not all at once:

- FAIR principles for stewardship of digital research objects;
- PRISMA and extensions for systematic-review reporting when applicable;
- ACM SIGSOFT Empirical Standards for applicable empirical software-engineering studies;
- W3C PROV for provenance semantics;
- RO-Crate for research-object packaging where useful;
- CSL for citation styles;
- CRediT, ORCID and ROR for contributor/identity metadata;
- DataCite and Crossref for scholarly/research-output metadata and DOI records;
- venue/domain-specific reporting standards whenever they are more specific.

## Mature implementation choices

Task-dependent examples already selected or proven useful include OpenAlex/Crossref for scholarly discovery/metadata, Zotero for reference authority, Docling/GROBID for document intake/enrichment, Snakemake for scientific DAGs, DVC for larger data/artifact versioning, Pandera for tabular contracts, DuckDB for local analytical SQL, MLflow for run tracking, Inspect AI for agent/model evaluation, RO-Crate tooling for packaging, and Quarto/Pandoc/CSL for manuscript production.

These are replaceable external capabilities, not Research-owned components.

## Observed local capability

Global/agent layer:

- Skills: `literature-review`, `experimental-design`, `statistical-analysis`, `scientific-visualization`, `scientific-writing`, `peer-review`;
- Python + uv/uvx, Git/GitHub, DuckDB, PostgreSQL client, Typst;
- Quarto 1.10.18 is activated at `/root/tools/bin/quarto` with bundled Pandoc 3.10; a BibTeX/CSL citation-render smoke test passed on 2026-09-13;
- Runtime execution and Artifact capability are available as external enabling surfaces.

Existing Research project environment additionally contains an executable Snakemake/DVC/Pandera/MLflow/Optuna/Jupyter/RO-Crate-oriented stack and one real first-paper workflow. This project is evidence/capability supply, not the future top-level Research owner.

## Concrete current gaps

Only gaps exposed by the active paper/research workload count:

- the generic Quarto/Pandoc/CSL authoring path is now activated; the remaining real work is to bind the active paper to that path and its venue-native output requirements;
- bibliography/reference authority still needs Zotero or an exact exported BibTeX/CSL projection with DOI metadata verification when relevant;
- literature discovery, document ingestion, systematic-review screening, preregistration/deposition and domain statistics remain **on demand**, not installation debt.

## Acceptance workload

Use the currently active paper as the first package acceptance task. Research is accepted when an exact research revision can produce its required research evidence and target manuscript/reviewer artifacts with traceable sources, applicable scientific checks, and no invented local research framework.

Future task-specific gaps follow:

`real research task -> applicable scientific standard -> mature method/tool -> execute -> scientific/target validation`
