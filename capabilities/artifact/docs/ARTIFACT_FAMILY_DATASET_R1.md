# Artifact E2E — Dataset Family R1

## Standing

`SHADOW_PROFILE_LIVE_PROVEN`

Dataset is the second non-Office proof of the standards-first Artifact taxonomy. It deliberately exercises a non-visual semantic regime after Still Image. It does not modify `profile-v1.schema.json`, Temporal production routing or existing production Artifact profiles.

## External authority structure

A dataset requires three distinct authority layers that must not be collapsed:

1. **Family/Profile** — which serialization and bounded interoperability rules are acceptable for this class of dataset;
2. **Concrete Dataset Contract** — the exact columns, logical types, nullability, key and row-bound expectations for this particular data object;
3. **Native format evidence** — facts independently observed from the serialized object by mature implementations.

The Dataset Contract is therefore not a substitute for the Parquet schema embedded in the file, and the embedded Parquet schema is not a substitute for the Dataset Contract. Acceptance requires them to agree.

## First bounded profile: `dataset-parquet-flat-r1`

Classification:

- family: `dataset`;
- representation: `columnar`;
- format: Apache Parquet;
- registered media type: `application/vnd.apache.parquet`;
- purpose: interchange + analysis;
- target authority: independent-reader matrix.

The IANA Media Types Registry currently registers `application/vnd.apache.parquet` to the Apache Parquet Project. The Apache Parquet specification defines the native physical types and logical annotations; for example, STRING is a logical annotation on `BYTE_ARRAY`, not a new physical primitive type.

R1 is intentionally narrow:

- flat columns only;
- `int64`, UTF-8 string, `float64`, boolean;
- exact column order/name/type/nullability from one bound Dataset Contract;
- no lists, maps, structs or other nested types;
- no non-finite float values;
- one declared non-null primary key used for canonical row comparison;
- row order itself is not authoritative in R1;
- schema evolution is outside R1.

## Dataset Contract

`artifact-delivery/shadow-contracts/dataset-contract-v1.schema.json` defines the current shadow contract carrier.

The contract contains only object-specific acceptance facts:

- ordered columns;
- bounded logical type;
- nullability;
- primary-key columns;
- optional minimum/maximum row counts.

The family profile remains reusable; a new dataset does not require a new Artifact family profile merely because its columns differ.

The smoke contract is:

`artifact-delivery/shadow-contracts/dataset-parquet-flat-smoke-r1.json`

with:

```text
id      int64    REQUIRED   primary key
name    string   REQUIRED
score   float64  OPTIONAL
active  boolean  REQUIRED
```

## Independent reader binding

### DuckDB 1.5.5

Frozen local carrier:

- `/opt/ordivon/external/duckdb/1.5.5-1/duckdb`
- binary SHA-256 `02f1b93ff8b0dc40f3600b04d55b5f2ca4e968ef22e8c1a3cc49dcf34f880a06`
- Arch package `duckdb 1.5.5-1`
- package SHA-256 `81a5ec42e26876ba0161fde1a29b6b7bf822ccbbc08bb063a05842016a728136`
- detached package signature verified through the Arch keyring.

DuckDB contributes two distinct evidence surfaces:

- `parquet_schema()` for native Parquet physical type, repetition and logical annotation;
- `read_parquet()` for logical rows.

A crucial negative result was retained: generic SQL `DESCRIBE SELECT * FROM read_parquet(...)` reports projected SQL nullability and cannot be promoted to native Parquet REQUIRED/OPTIONAL authority. R1 therefore uses `parquet_schema()` for repetition evidence.

### PyArrow 25.0.1

Frozen local carrier:

- `/opt/ordivon/external/pyarrow/25.0.1/python`
- wheel `pyarrow-25.0.1-cp314-cp314-manylinux_2_28_x86_64.whl`
- official PyPI release-file SHA-256 `9171748cdf796972d85a4b60157c279913e242992e350c90c7450182a9838b2a`.

The official manylinux wheel was used instead of reconstructing the Arch Arrow C++ dependency closure. It carries the Arrow native runtime required by PyArrow and runs without modifying the host Python environment.

Direct `files.pythonhosted.org` transfer was only ~40–50 KiB/s. Acquisition was therefore retried through one fresh, scoped Surfshark path and reached about 4.35 MiB/s. The downloaded wheel digest exactly matched PyPI release metadata. The VPN was an acquisition carrier only; Dataset verification is fully local/offline afterward.

PyArrow contributes:

- `ParquetFile.schema` / `schema_arrow` evidence;
- physical and logical column facts;
- independent logical row decoding.

## Verification flow

```text
Parquet artifact ─────────────┐
                             │
Dataset Contract ───────┐     │
                        ▼     ▼
                contract/schema binding
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
      DuckDB parquet_schema   PyArrow ParquetSchema
      DuckDB read_parquet     PyArrow table read
             │                     │
             └──────────┬──────────┘
                        ▼
              independent agreement
                        │
          primary-key + row-bound checks
                        │
                        ▼
                  bounded PASS/FAIL
```

No Ordivon Parquet parser was introduced.

## Live proof

The live smoke artifact had:

- artifact SHA-256 `32370bdf9c76e2f27597116618431fb5fd951e3ab2d7c9a74f41e65e8662aa52`;
- contract canonical digest `bb339bfbbe334a7bc50ff25282ab78d15935b220d3e3f1b1c2f2ed50a9d7de3b`;
- three rows;
- canonical row digest `2ae3600a21041f871c48499eee42252746640b1701085a6bd4be20150167ce77` from **both** DuckDB and PyArrow.

Both implementations independently observed the same native schema:

```text
id      INT64       REQUIRED
name    BYTE_ARRAY  REQUIRED   STRING
score   DOUBLE      OPTIONAL
active  BOOLEAN     REQUIRED
```

and the smoke contract's `id` key was non-null and unique.

## Falsifiers proven

Six focused tests currently pass:

1. valid bounded flat Parquet + matching Dataset Contract → PASS;
2. Parquet remains valid/readable but the contract changes `score` from nullable to required → FAIL;
3. both readers decode and agree on rows but the declared primary key is duplicated → FAIL;
4. truncated/corrupted Parquet → reader evidence fails closed;
5. non-finite float enters a profile that explicitly excludes it → FAIL;
6. a Dataset Contract declares a nullable primary-key column → FAIL before reader evidence can be promoted.

These demonstrate three separate truths:

```text
FileReadable != ContractSatisfied
ReadersAgree != KeyIntegrity
FormatValid != DatasetSemanticsValid
```

## Claim boundary

A Dataset PASS establishes only the bounded Artifact facts selected by the profile and concrete contract:

- serialization can be decoded by both selected mature implementations;
- native schema facts agree with the contract;
- reader interpretations agree on canonical logical rows;
- declared key integrity holds;
- row bounds hold.

It does **not** establish:

- factual truth or provenance of values;
- statistical quality or representativeness;
- domain correctness;
- units, ontologies or scientific validity not encoded by the contract;
- bias/fairness claims;
- schema evolution compatibility;
- nested Parquet semantics;
- warehouse/catalog transactions or database ACID constraints.

## Architectural consequence

Still Image and Dataset now independently force the same separation:

```text
Family/Profile       = reusable class-level acceptance semantics
Object Contract      = artifact-instance/object-specific acceptance facts
Capability Binding   = replaceable mature tools that produce evidence
Evidence             = observations bound to exact bytes and contract
```

For Still Image, an explicit object contract is often minimal or unnecessary because many facts are profile-level. For Dataset, it is indispensable. This means a future `profile-v2` must support an optional/typed object-contract reference rather than trying to put every artifact-specific fact inside the family profile itself.
