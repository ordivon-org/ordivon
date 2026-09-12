# Research Capability Package — Census R1

Date: 2026-09-13

Status: **usable now; no new Research framework justified.**

Current real consumer: the existing empirical-software-engineering paper and Research-v2 migration/verification work.

## Mature external owners

| Capability family | Mature owner / representative provider | Policy |
|---|---|---|
| transparency / preregistration | TOP Guidelines; OSF Registrations; domain reporting standards | activate per study |
| scholarly discovery | OpenAlex, Crossref, Semantic Scholar | service/API on demand |
| bibliography / citation | DOI metadata, CSL, Zotero, Pandoc/Quarto | structured bibliography for publication tasks |
| study / experiment design | scientific method + domain methodology | method-native; no universal Research method |
| data validation | Pandera and domain-native validators | active when contracts matter |
| scientific workflow | Snakemake; DVC where lineage is useful | project-local |
| experiment/run evidence | MLflow | workload-driven |
| model/agent evaluation | Inspect AI where applicable | specialized |
| provenance | W3C PROV | external semantic owner |
| research-object packaging | RO-Crate / Workflow Run RO-Crate | external interchange owner |
| claim/citation relations | Nanopublications, CiTO when useful | optional, not a base ontology |
| scientific authoring | Quarto + Pandoc | active |
| contributor identity/roles | ORCID, CRediT, ROR | publication boundary |
| persistent output metadata | DataCite-compatible repositories | release/deposit boundary |
| software identification/citation | SWHID / Software Heritage; CITATION.cff | released research software |
| interactive/HPC/special domains | Jupyter/marimo, Slurm/Apptainer, REDCap, R/SPSS/Stata/SAS/NVivo, lab tooling | consumer-driven only |

## Local observed capability

Research-v2 was audited from `/root/projects/ordivon-research-v2`, opening revision `9d767a028719e0966ad67817a167c90b02aa7323`, workspace `ws-research-v2-live-audit-20260913`.

Its declared computational/evidence stack includes Inspect AI, MLflow, Pandera, RO-Crate, optional DoWhy/Optuna, pandas/pyarrow, DVC/Snakemake, and pytest/ruff verification.

Existing Research skills include `literature-review`, `experimental-design`, `statistical-analysis`, `scientific-visualization`, `scientific-writing`, and `peer-review`.

A frozen real paper is already rendered through pinned Quarto `1.11.1` in a digest-checked container with network disabled. Existing publication receipt:

- input digest: `sha256:6cb8a7302d8cd3700beaeb12c73d946276c8a2efdad355056fe841d20801eea4`;
- renderer digest: `sha256:f2e1a6a1f769b1b4d50ce7f52afbddb98f3888e456838ca755c6725927fe6f25`;
- rendered HTML digest: `sha256:d4397b2a8c12ae521515c29934df79ffc38210d47a80fcaf004a891958a30845`.

Repository verification during this census reached **44 passing tests**.

## Gap census

| Gap | Classification | Disposition |
|---|---|---|
| structured DOI-backed bibliography for the real paper | activated | 12 DOI-backed records materialized in `references.bib`; receipt digest `sha256:26951e17dd2ee426437582fb9695663c02e6a9bed2f5cf1019fb35e450d9916e` |
| bibliography consumption by Quarto/Pandoc | ACCEPTED | pinned renderer consumed the real bibliography with network disabled |
| final citation year/field normalization | NEEDED_BEFORE_SUBMISSION | automatic DOI metadata may use online-first year while manuscript/venue uses print-volume year; identity verification and final field policy remain separate |
| current manuscript conversion to structured citations | NEEDED_BEFORE_SUBMISSION | apply only to the scientifically selected current manuscript |
| ORCID / CRediT / ROR metadata | ON_DEMAND | submission boundary |
| public replication-package DOI/deposit | NEEDED_BEFORE_EXTERNAL_SUBMISSION | use mature repository/deposit provider when release-ready |
| OSF preregistration | ON_DEMAND / STUDY_DEPENDENT | not retroactive for the completed study |
| OpenAlex/Semantic Scholar ingestion | ON_DEMAND | no permanent literature service required |
| Zotero desktop/global install | NOT_A_GAP | use when human library management/collaboration warrants it; not a base dependency |
| Jupyter/marimo/R/HPC/social/clinical/lab stacks | ON_DEMAND | activate only for matching research |
| universal Research semantic waist / claim ontology | DO_NOT_BUILD | external standards plus workload/method policy are sufficient; historical benchmark semantics stay evaluation fixtures/oracles |

## Real-task acceptance evidence

This census used the paper's actual 12 DOI-backed references rather than a toy example.

- Crossref lookup resolved all 12 manuscript DOIs: `job-01a09705-7f8d-7863-8c5c-d3f267d09260`.
- DOI content negotiation produced structured BibTeX: `job-01a09705-ec94-79f0-bead-a60eaeb5eb6c`.
- Research-v2 materialized `references.bib` and `REFERENCES_RECEIPT.json` with 12 records.
- Pinned Quarto/Pandoc consumed the real bibliography offline: `job-01a09707-c86b-7f53-8d0f-374e37630cd4`.
- Acceptance HTML size was 23,153 bytes and real-reference sentinels were present.
- Repository verification finished with 44 tests passing: `job-01a09706-8c90-7fe0-8810-957a28c8a255`.

Accepted chain:

`real manuscript references -> DOI identity resolution -> structured bibliography -> offline Quarto/Pandoc consumption`

This does **not** make automatically projected metadata final venue-ready citation authority.

## Decision

Research has crossed the point where another generic Research platform/framework is useful. Work should now be driven by real research:

`real research problem -> choose mature methods/standards -> activate task-local tools/skills -> execute -> verify evidence -> publish/deposit when ready`

Near-term package work is limited to submission-bound tasks the paper actually needs: citation-field normalization, current-manuscript structured citations, publication metadata, and final immutable replication-package deposit.
