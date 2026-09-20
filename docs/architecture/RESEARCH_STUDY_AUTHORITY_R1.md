# ADR — Research composition profile and Study authority boundary

Date: 2026-09-21

Status: **ACCEPTED**

## Decision

Ordivon will **not** import `ordivon-research-v2` wholesale as a monorepo `capabilities/research` code owner.

The shared Research layer is treated as a **composition profile and authority-binding protocol**, not as a standalone runtime framework:

```text
CLASSIFY → BIND → COMPOSE → VERIFY → RECORD
```

Concrete scientific state remains owned by a concrete Study authority.

## Evidence for the decision

Live source inspection at Research-v2 revision `31498498d72cc00be6c4311d710a7f79b0a9bdf9` showed:

- the packaged production source under `src/ordivon_research` contains only an `__init__.py` description and no material Research runtime;
- substantial executable and verification logic lives in study-specific scripts, tests, Paper1/Paper3 research trees, publication tooling and historical regression oracles;
- the existing LEGO plan already forbids ownership of a generic workflow engine, a universal claims ontology and Runtime physical execution;
- the existing semantic-ownership contract already delegates provenance and interchange to W3C PROV, RO-Crate, Workflow Run RO-Crate, Nanopublications/CiTO and method/domain standards;
- current Research-v2 working state has 88 staged entries, all under `papers/`, so the repository is actively carrying concrete Paper1 scientific/publication work rather than acting as a clean shared capability source.

This means the repo boundary and the semantic authority boundary no longer coincide.

## External owners

The shared profile continues to bind external/method-native owners rather than copying their semantics.

Current checked authorities include:

- ACM SIGSOFT Empirical Standards for method-specific software-engineering research expectations;
- W3C PROV for provenance representation;
- RO-Crate 1.3 for research-object packaging;
- Workflow Run / Provenance Run RO-Crate 0.6 for workflow/run provenance;
- method-native tools such as Snakemake, Pandera, MLflow, Inspect AI, Quarto/Pandoc, Docling, GROBID, ASReview and domain-specific analysis tools when a concrete Study activates them.

The profile is metadata and routing. It does not become scientific truth authority.

## Study dispositions

### Paper1

The frozen EMSE R3 object is a Git worktree of Research-v2, not an independent repository:

- ref: `refs/heads/paper1/emse-r3-frozen`
- revision: `d9022b15bc34467e5843ef2a30f75c8f2b27f0e1`
- role: frozen study history, not forward authority

A read-only archive bundle was created without changing source worktree state or refs:

- bundle: `/root/ordivon-migration-backups/2026-09-21-paper1-frozen/paper1-emse-r3-frozen.bundle`
- SHA-256: `5368f6a280beefb947735d29d304e5bb4ceca7aa6e1e1a3848e97d42f1e9941a`

The current Paper1 working state remains in Research-v2 and is explicitly excluded from migration while staged scientific/publication changes are present.

### Paper2

`/root/projects/ordivon-paper2` remains a separate scientific source authority.

Observed source state:

- main: `fd0fef6b0ed4b792f784726d2632551d6d5fd2b0`
- source working tree: clean
- an active Runtime workspace exists for Paper2 full-text Coder A: `ws-paper2-fulltext-coder-a-r59-20260920`

Paper2 is not imported into the monorepo while full-text screening and later scientific gates remain active. Repository consolidation must not redefine eligibility, screening, adjudication, claim extraction or reproduction authority.

### Paper3

Paper3 is currently integrated into Research-v2 history and paths rather than exposed through a dedicated current Study repository/ref. Research-v2 main contains integrated Paper3 FSE work followed by later Paper1 work.

Therefore Paper3 extraction is **HOLD** until a clean, explicit frozen Study ref is produced. No branch/ref is created from the dirty Research-v2 working state by this ADR.

## Physical topology

For now:

```text
ordivon monorepo
  meta / architecture
    Research composition-profile decision
  [no capabilities/research runtime subtree]

external Study authorities
  Research-v2
    active Paper1 working state
    integrated Paper3 state
    historical/shared research assets

  Paper2
    independent active scientific authority

archive
  Paper1 frozen ref + verified bundle
```

A future `meta/research/` machine-readable profile may be admitted only after it can be generated from authority bindings without becoming a second copy of Study scientific state.

## Migration rules

1. Do not import the entire Research-v2 repository into `capabilities/research`.
2. Do not reset, filter, commit or ref-mutate Research-v2 while staged Study work is present.
3. Study repositories/refs may be imported only at explicit frozen scientific gates.
4. Source relocation must preserve Git/content identity and must not change scientific standing.
5. Publication/rendering tooling remains an Artifact/Media/toolchain concern unless a Study-local rule is scientifically material.
6. Research profile metadata must point to live external authorities; it must not copy method semantics.
7. A shared Research code abstraction is admitted only if at least two independent Studies demonstrate the same irreducible action-changing rule after external substitution.

## Supersedes

This ADR supersedes the earlier working assumption that Research-v2 should become a large `capabilities/research` source owner inside the monorepo. It does **not** supersede Research-v2 scientific history or any Study-specific evidence.
