# External Learning & Evolution — project research on PostgreSQL

ELE is the **cross-Owner learning method**, not a new execution Owner, provider
registry, formal LEGO registry, scheduler or permission service. The existing
Capability Catalog owns this PostgreSQL research projection; Git source files
remain under their natural Catalog/Knowledge Owners.

## What is actually migrated

The importer reads only these source families at an exact Git SourceCut:

| Family | Role |
| --- | --- |
| `catalogs/capabilities/providers/*.md` | Studied upstream and internal provider capabilities, mechanisms and boundaries |
| `catalogs/knowledge/lessons/*.md` | Detailed method / LEGO / external-project decompositions |
| `catalogs/capabilities/packages/*.md` | Package outcomes, applied methods and adoption boundaries |
| `catalogs/capabilities/evidence/*.json` | Pinned candidate / cross-Owner source observations, **not** adoption |
| `catalogs/knowledge/graphs/*.json` | Existing analysis/decomposition graphs |
| `catalogs/knowledge/evidence/{analysis,acceptance}/*.json` | Analysis and acceptance evidence, retaining their original scope |
| `catalogs/capabilities/authority-map-r1.md` and `RESEARCH_CAPABILITY_PACKAGE_R1.md` | Existing authority and package study |

Rolling daily GitHub radar, Host Work/Topic/Message, Runtime Job/Workspace,
service logs, package caches and active Owner operational state are **not**
silently imported or transferred. Other Owners retain their own domain data.

Markdown is split into exact numbered heading sections with an ancestry path
and source line ranges; code fences are not treated as headings. JSON evidence
is split into root fields and distinct `observations[]` objects when present.
The **entire original UTF-8 source body** is retained with an immutable SHA-256
digest. A section is a read projection, not a new assertion of truth.

## PostgreSQL representation

The `ele` schema is isolated from existing Host/Runtime tables:

- `ele.study_versions` — immutable (study ID, SHA-256) versions and exact source
  body, with source path, kind, title and Git SourceCut;
- `ele.study_sections` — source-bound structural decomposition with heading
  ancestry, original line range where applicable, and PostgreSQL native
  `to_tsvector('simple', ...)` indexing;
- `ele.study_heads` — which imported version is present in the latest
  **successful full Git import**; absent files are *soft-retired*, and prior
  versions stay queryable;
- `ele.current_studies` — joined current-import read view.

The importer uses one PostgreSQL transaction, an advisory transaction lock,
parameterized SQL, digest-keyed idempotent inserts and **readback before
commit**. Re-importing an unchanged tree adds no versions or sections.
Reverting a document to an earlier digest correctly repoints its head without
losing history. A partial or failed transaction leaves the previous projection
unchanged. There is **no SQLite fallback**.

**Truth boundary:** A provider study is an attributed, dated analysis. PostgreSQL
does not certify that upstream releases are still current, a tool is installed,
a Candidate is a DECLARED/ADMITTED LEGO, or a domain consumer has switched.
Confirm currentness through the upstream and natural Owner before action.

## Operator / Agent use

The intended database connection is supplied by the environment as
`ORDIVON_ELE_PG_DSN` (a normal psycopg 3 PostgreSQL DSN). Do not commit DSNs,
passwords, role secrets or copied Host/Runtime configuration. Prefer a
dedicated ELE database/credential when one is provisioned; a dedicated
`ele` schema in an existing PostgreSQL database is a bounded first
storage cut, not semantic ownership of that database's other tables.

From the repository root:

```sh
python3 catalogs/capabilities/ele/studies.py plan
# After supplying the ELE PostgreSQL DSN securely:
python3 catalogs/capabilities/ele/studies.py migrate
python3 catalogs/capabilities/ele/studies.py verify
python3 catalogs/capabilities/ele/studies.py stats
python3 catalogs/capabilities/ele/studies.py search --query 'recovery'
python3 catalogs/capabilities/ele/studies.py show --id provider:worktrunk
```

The importer requires the mature `psycopg 3` driver already used by
Ordivon's PostgreSQL-native Owners. It does not create a custom connection
pool, event bus, ORM, vector service or fulltext engine. English-token fulltext
uses PostgreSQL's `simple` configuration; the parameterized substring fallback
supports exact phrases and Chinese text. This is a research index, not an
embeddings-based semantic retrieval claim.

## Migration, consumer cutover, and safe subtraction

1. Record the selected source families and exact Git revision. Verify the
   complete corpus (including JSON validity and distinct study IDs) via
   `plan`. Before PG mutation, verify every selected original file's Git Blob
   against HEAD; reject dirty/uncommitted external analyses rather than assign
   them a false SourceCut.
2. Import into PostgreSQL and require `verify` to match **all** current source
   digests, study IDs and section counts. Run one real `search` and `show`.
3. Have actual Human/Agent consumers use this searchable projection for
   analysis; keep upstream project URLs, research qualifications and release
   decisions routed through existing Owners and Skills.
4. **Only after real consumers and exact references are migrated**, retire
   redundant Git files one at a time. Until then, original Markdown/JSON
   remains the authoritative edited source; PG is a read model, not a competing
   editable truth store. Git history continues to preserve earlier versions.
5. For production substitution, separately follow
   `external-capability-evaluation`, Research's qualification and the
   domain Owner's successor/readback and GitHub release process.

The database schema and all import operations are versioned in ordinary Git.
Do not perform age-only deletion of Host/Runtime entities or replace natural
Owner-specific data stores with ELE's analytical projection.
