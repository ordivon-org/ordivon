# Package: Research

Last census: 2026-09-29
Standing: **READY_FOR_REAL_WORK**
Current workload acceptance: **ACCEPTED_FOR_CURRENT_WORKLOAD**

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

Task-dependent examples already selected or proven useful include OpenAlex/Crossref for scholarly discovery/metadata, Firecrawl when broad current public-web context must be searched/scraped/mapped/crawled, MarkItDown as a lightweight candidate for ordinary heterogeneous-file-to-Markdown intake, Zotero when human reference-library management is useful, Docling for richer layout/document understanding, GROBID for scholarly PDF metadata/citations/TEI structure, LlamaIndex or Haystack only when a real context/RAG workload benefits from their ingestion/retrieval/pipeline abstractions, Snakemake for scientific DAGs, DVC for larger data/artifact versioning, Pandera for tabular contracts, DuckDB for local analytical SQL, MLflow for run tracking, Inspect AI for agent/model evaluation, RO-Crate tooling for packaging, and Quarto/Pandoc/CSL for manuscript production.

Firecrawl is an acquisition/context provider rather than a scientific-method owner: successful scraping does not establish source quality or evidential sufficiency. See `catalogs/capabilities/providers/firecrawl.md` and `catalogs/knowledge/lessons/firecrawl-web-context-kernel.md`.

MarkItDown is the lightweight normalization candidate, not a replacement for deeper parsers: escalate ordinary files to Docling when layout/table/OCR/document hierarchy matters, or to GROBID when scholarly metadata/reference/citation semantics matter. See `catalogs/capabilities/providers/markitdown.md` and `catalogs/knowledge/lessons/markitdown-document-normalization-kernel.md`.

LlamaIndex/Haystack are optional context-engineering frameworks, not Research knowledge authorities: source evidence remains with the authoritative corpus, indexes/chunks are derived retrieval projections, and retrieval quality must be evaluated separately from scientific/domain validity. See `catalogs/capabilities/providers/llamaindex.md`, `catalogs/capabilities/providers/haystack.md`, and `catalogs/knowledge/lessons/llamaindex-haystack-context-retrieval-kernel.md`.

These are replaceable external capabilities, not Research-owned components.

## Observed local capability and real evidence

Global/agent layer:

- advisory Skills include `paper-lookup`, `citation-management`, `literature-review`, `hypothesis-generation`, `experimental-design`, `exploratory-data-analysis`, `statistical-analysis`, `scientific-visualization`, `scientific-writing`, `scientific-critical-thinking`, and `peer-review`; exact availability/dependency state remains Skills-owner truth;
- project-local routing Skills separate new-Study admission (`research-study-birth`), method selection (`method-router`), provider/capability routing (`research-capability-routing`), and publication closure/perceptual conformance;
- Runtime execution, Temporal durable workflow, Snakemake scientific DAG, Artifact publication mechanics, and external providers remain independent natural owners.

Fresh Research-v2 owner census at revision `e9492290f69cce9711893667c2f76177cd46592d` reports Birth Policy `research-study-birth-r1` (`sha256:26fc766661c6cba508ffea5bd7c08885f5be231502ef0dd663d17925a0d5ee79`) and data-plane profile `research-data-plane-r1` (`sha256:647ef75e00fe7d9c7d14807bed08f6662175fd5d400e48ce0812cb6b057673d7`). Current defaults are owner-bound, not copied into the shared Research profile: DuckDB for rebuildable local analytical SQL, Polars LazyFrame for new dataframe scan/transform with pandas as compatibility provider, Apache Arrow for explicit/validated normalization, Parquet+zstd for rebuildable analytical derivatives, Arrow/Pandera/JSON Schema/method-native validation, Snakemake/DVC/MLflow on consumer-driven activation, and shared PostgreSQL only for transactional service state rather than analytical truth.

The reusable route contract lives at `.agents/skills/research-capability-routing/`. It consumes explicit problem classes plus natural-owner currentness observations and returns one exact route or a typed HOLD; it never treats catalog presence as availability, availability as authorization, or provider success as scientific completion.

The current-workload acceptance used real paper material rather than a toy citation demo:

- Crossref resolved all **12** DOI-bearing manuscript references;
- DOI content negotiation produced structured BibTeX and Research-v2 materialized `references.bib` plus `REFERENCES_RECEIPT.json`;
- the receipt records **12/12** DOI-set agreement;
- pinned official Quarto `1.11.1` / Pandoc consumed the bibliography with network disabled;
- the acceptance HTML contained real-reference sentinels;
- Research-v2 verification reached **44 passing tests**;
- a frozen publication-path replay produced identical rendered HTML SHA-256 values (`d4397b2a8c12ae521515c29934df79ffc38210d47a80fcaf004a891958a30845`).

Detailed dated evidence is in `docs/RESEARCH_CAPABILITY_PACKAGE_R1.md` and `evidence/acceptance/capability-packages-r1-20260913.md`.

## Concrete current gaps

The generic Research package does not have a demonstrated construction gap.

Remaining work belongs to the actual paper/submission boundary:

- normalize final citation fields/years according to the selected venue and authoritative bibliographic policy;
- bind the scientifically selected **current manuscript** to structured citations and venue-native output requirements;
- add ORCID/CRediT/ROR or other publication metadata when the submission boundary requires it;
- publish/deposit the exact replication package and obtain a persistent DOI only when the release artifact is ready and the external effect is intentionally authorized.

Literature ingestion, systematic-review screening, preregistration, domain-specific statistics, specialist scientific software, HPC and similar capabilities remain **on demand**, not installation debt.

Zotero is not a base dependency: use it when a live human-managed/collaborative library is valuable. The proven publication path already accepts an exact DOI-verified BibTeX/CSL projection.

## Operating rule

Stop generic Research construction. Continue real research:

`real research problem -> applicable scientific standard/method -> task-local mature tools/Skills -> execute -> verify scientific/target evidence -> publish/deposit when ready`

Reopen the package census only when a real research task exposes a capability that the current working set cannot adequately provide.
