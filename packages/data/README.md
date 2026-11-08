# Data — Cross-owner data-product interoperability

**Natural responsibility:** inspect, compose and verify reproducible data-product
interoperability without taking custody of Research, Finance, Runtime, Artifact,
Preservation or external-provider truth. This is a source package, **not** a
second warehouse, scheduler, data registry, or universal data-product ontology.

## Existing production and evidence

- Research owns scientific dataset definitions, estimands and study outputs.
- Capital/Finance owns financial market observations and business inferences.
- Artifact owns dataset file bytes, integrity and bounded Parquet conformance.
- Experimental Episode Study owns its reproducible data analysis projection.
- Runtime owns Job/Attempt/Workspace/physical execution evidence.
- Preservation owns archival/fixity effects; Security owns credential/policy enforcement.
- The existing DCAT 3 federation is a **read-only discovery projection** over
  domain-owned ODPS/ODCS products. Neither this package nor DCAT changes authority.

## Bounded modules — no empty symmetry directories

| Semantic LEGO candidate | Natural owner / actual binding | Current standing |
| --- | --- | --- |
| Source acquisition | Domain API/REST/WebSocket, Research scholarly clients | existing domain-specific implementations |
| Immutable file capture | Artifact WARC and Runtime input/artifact receipt | existing bounded implementations |
| Dataset interoperability | Artifact Dataset Contract + independent DuckDB/PyArrow readers | existing bounded implementation |
| Product contract | Domain-owned ODCS 3.2 / consumed ODPS 1.1 | existing products and tests |
| Catalog discovery | DCAT 3 projection in the Data Lifecycle study | read-only CLI in this package |
| Provenance and lineage | W3C PROV / OpenLineage in existing product evidence | selected cross-domain consumers |
| Validation and modeling | Domain-native Pandera/statistics/SQL, Artifact readers | do not promote a generic checker to domain truth |
| Materialization | DuckDB/Parquet/PG/domain store | domain-specific, workload-bound |
| Outcome and feedback | Research/Finance consumers | selected bounded evidence; general loop partial |
| Retention and retirement | Preservation + domain record/consumer authority | no autonomous deletion of owner evidence |

Do **not** implement a generic ETL engine, a second SQL interface, data ontology,
source registry, scheduler, or opaque custom verification scheme.

## Executable read-only seam

```sh
python3 packages/data/scripts/inspect_federation.py
python3 packages/data/scripts/inspect_federation.py --verify-local
# Optional artifact-integrity admission gate: rejects UNKNOWN and zero observations.
# The frozen historical catalog currently cannot pass this gate without corrected source-owned URIs.
python3 packages/data/scripts/inspect_federation.py --verify-local --require-verified
# Read a specific externally owned path only after confirming it and its owner:
python3 packages/data/scripts/inspect_federation.py --verify-local --allow-root /absolute/approved/data/root
mise run data:verify
```

The CLI reads the existing compact DCAT JSON-LD projection; it does **not**
implement RDF/JSON-LD schema validation, register data, or materialize data.
Only exact SHA-256-bound, readable local file distributions inside explicitly
allowed roots can become VERIFIED. A digest mismatch becomes FALSIFIED.
Missing data, malformed file URI authority, missing accessURL, and files
outside the explicit scope remain UNKNOWN rather than FALSE.

Historical federated catalog uses `file://studies/...`, whose authority
component is `studies`. The CLI deliberately treats that as an unsupported
file URI rather than silently rewriting the frozen evidence. The source owner
should emit canonical URIs in a **new** versioned DCAT projection, preserving
the historical R2 acceptance.

## Current producer-owned ODPS discovery (no new registry)

`python3 packages/data/scripts/project_owned_products.py` projects the
currently **Git-tracked** producer-owned ODPS v1.1 records into a deterministic
DCAT 3 JSON-LD view. The two presently tracked documents belong to Capital
and Experimental Episode; the frozen three-product September federation still
contains Research's external product. The generated view is **not** a claim
that all three current products are accessible, installed, or publishable.

```sh
python3 packages/data/scripts/project_owned_products.py > /tmp/owner-products.jsonld
python3 packages/data/scripts/inspect_federation.py --catalog /tmp/owner-products.jsonld --verify-local
# To project a specific external owner's qualified ODPS 1.1 document:
python3 packages/data/scripts/project_owned_products.py --product /approved/path/odps.json
```

The projection consumes upstream ODPS product IDs, versions, output ports and
declared ODRL policy IDs without rewriting the owners' files. Output-port IDs
and versions are **optional** under ODPS 1.1; a port version may differ from
its containing product version. Missing port IDs never acquire invented
stable IDs. A generated Distribution has no physical `dcat:accessURL` or
file digest without an explicit owner binding, so the verifier returns
`UNKNOWN`, not false `VERIFIED`. Producer source bytes are SHA-256 bound
into the content-derived catalog identity. No central catalog daemon, new
database or persisted product state is added.

## Optional qualified owner-file binding

The default projection does NOT infer physical availability. For an actual local
file, use explicit producer ODPS `customProperties` as the authority for the
relative source path and SHA-256. The operator selects the exact product, port,
property names and owner root; the adapter hashes the opened regular file and
rejects any mismatch or escape from the explicit root. Only then does it emit
a local file URI and W3C DCAT 3 `spdx:checksum`, retaining `dct:identifier`
for the producer's port identity. Legacy `sha256:` identifiers remain
readable for the historical frozen catalog. That local URI is **not portable** to other
workspaces or an implicit redistribution permission.

```sh
repo="$(git rev-parse --show-toplevel)"
python3 packages/data/scripts/project_owned_products.py \
  --bind-local d14d7457-c9aa-59e0-8bf5-7783cea39c1c \
    public-shadow-json sourceRelativePath sourceSha256 "$repo/domains/capital" \
  --bind-local 4b2a0b92-e9d6-5f31-8157-a1c16e4ef34b \
    episode-corpus-manifest-json corpusManifestRelativePath corpusManifestSha256 "$repo" \
  > /tmp/ordivon-qualified-products.jsonld

python3 packages/data/scripts/inspect_federation.py \
  --catalog /tmp/ordivon-qualified-products.jsonld --verify-local
```

For this source cut, the producer-owned Finance JSON and Episode manifest are
both Git-tracked with matching SHA-256 declarations and can be VERIFIED.
The rebuildable Episode Parquet file is **not** present in Git, so remains
UNKNOWN. The strict `--require-verified` gate appropriately refuses to
declare the *whole* catalog publishable with that unbound port. The optional
binding is a current observation: consumers must read back the file against
its declared digest before using it, since mutable pathnames can change.
Never persist this ephemeral local URI as the canonical cross-host identity.

## Verification and user instructions

- Native: `mise run data:verify` (Owner's CLI and exact existing study contracts).
- [Human workflow](docs/HUMAN.md)
- [Agent workflow](docs/AGENT.md)
- [Directory audit and decisions](docs/AUDIT_2026-11-07.md)
- [Capability and thought LEGO inventory](docs/LEGO_CENSUS.md)
- [Property-first formal verification / test disposition](docs/FORMAL_VERIFICATION.md)
- Opt-in kernel/symbolic check: `mise run data:formal:verify` (Lean + CrossHair/Z3)

**Data product standard version law:** ODPS 1.1 is consumed by current historical
products; ODPS 4.2 (released 2026-10-26) has a different document root and
access model. It is a migration **candidate**, not a compatible in-place bump.
Maintain consumer parity and native conformance evidence before moving a product.
