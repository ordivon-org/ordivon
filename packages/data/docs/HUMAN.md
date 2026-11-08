# Data — Human guide

## What this owner does

Data provides a read-only lens into real data products and joins mature
producer/consumer contracts. It does not convert every dataset into a new
central database or take data custody from Research/Finance/Artifact.

## Start from an actual product

1. Choose a real final question, user and data consumer: e.g. a Paper1
   reproducibility check, Finance public market-observation analysis or an
   Experimental Episode study.
2. Identify the source owner and its declared meaning, observation time,
   allowed uses and original evidence version. Rights and publication are
   separate from mere public readability.
3. Inspect the existing federation with
   `python3 packages/data/scripts/inspect_federation.py`. This only lists
   metadata; it does not prove that the data file still exists.
4. Run `--verify-local` to inspect available evidence. For an actual
   integrity admission gate use `--verify-local --require-verified`:
   exit 0 only when every distribution has a scoped, matching SHA-256;
   exit 2 for a detected digest conflict and exit 3 for unknown/unverified
   evidence (including an empty list). Neither result certifies data quality,
   license rights, source freshness, or the decision to publish.
   If a source is outside the repository, first
   identify its current valid path and owner, then explicitly pass
   `--allow-root /absolute/approved/root`. Never guess a replacement path.
5. For a Parquet dataset, run Artifact's existing Dataset verification with
   its bound object contract. For scientific/financial semantics, run the
   actual Research/Finance consumer validation.
6. Publish through the natural product owner using ODCS/ODPS, DCAT discovery,
   OpenLineage/PROV and versioned provenance. Record an exact consumer read-back.
7. Measure usefulness (not merely row count), update only invalidated
   partitions/models/decisions, and retire data only if consumers and actual
   retention/recovery requirements permit it.

## Formal-first review

Read [Data formal verification](FORMAL_VERIFICATION.md), run
`mise run data:formal:verify`, and separate kernel-checked *abstract* model
proofs from bounded CrossHair implementation search and actual source/consumer
read-back. Retire synthetic tests only after the relevant Python/Rust/SQL
implementation refinement is established, not from abstract proofs alone.

## Inspect actual producer-owned product metadata

Run `python3 packages/data/scripts/project_owned_products.py` for a live
**checkout-relative** ODPS-to-DCAT projection over Git-tracked products.
Use `--product` to select a particular owner's qualified document. The current
repository contains Capital and Experimental Episode ODPS records; Research's
historical record remains in the frozen federation and cannot be promoted to
a current live product by copying September's catalog.

The CLI provides product discovery only. It deliberately does not invent file
locations, access grants or physical integrity. A consumer needing only one
bound port may use `inspect_federation.py --verify-local --require-port
PRODUCT_ID PRODUCT_VERSION DISTRIBUTION_URN` with the exact version/port
declared by the owner. This distinguishes a verified input from the whole
multi-port product: `selectedPortIntegrityGate=PASS` does not change a
global `integrityGate=NOT_ESTABLISHED`. A readable product record
and an output port do not establish available bytes; real product release
still requires the producing owner's ODCS/ODPS contract and read-back.

## Explicit producer evidence, not inferred paths

If the source owner has an existing relative path and SHA-256 in its ODPS
`customProperties`, pass an explicit `--bind-local PRODUCT_ID PORT_NAME
PATH_PROPERTY SHA_PROPERTY OWNER_ROOT` to the projection CLI. This names
the qualified mapping; there is no automatic search for coincidentally
matching hashes or guessed file locations. The current Finance JSON and
Experimental Episode manifest can be verified from their Git-tracked source
bytes. The Episode Parquet index has only a reproducibility digest and no
currently accessible file in this repo; it remains UNKNOWN.

The new DCAT 3 projection uses `spdx:checksum` for SHA-256 and leaves
`dct:identifier` as the distribution's identity. Contradictory legacy and
SPDX digests are rejected; historical frozen digests remain readable.

A verified SHA-256 observation establishes only one current byte match.
It cannot establish provider rights, future pathname stability, a complete
product publication, or approval to delete source records.

## Version and status warnings

- ODPS 1.1 historical consumers must not be silently switched to ODPS 4.2.
- `VERIFIED` means only declared file digest == observed bytes, within scope.
- `FALSIFIED` means the same check observed a digest disagreement.
- `UNKNOWN` means file or claim could not be established (no URL, invalid
  URI, unavailable file, outside scope, no SHA-256 binding). It does not
  mean the dataset is false or dispensable.
- Existing archival master and replica share a machine failure domain; they
  are not independent offsite disaster protection.

## Where to look

`studies/data-lifecycle/` — lifecycle evidence and acceptance.
`capabilities/artifact/` — native dataset verifier, WARC/fixity.
`domains/capital/` — financial source adapters and owned products.
`studies/experimental-episodes/` — Episode PG analytical consumer.
`catalogs/capabilities/packages/data-analytics.md` — capability discovery,
not dataset ownership or a task scheduler.
