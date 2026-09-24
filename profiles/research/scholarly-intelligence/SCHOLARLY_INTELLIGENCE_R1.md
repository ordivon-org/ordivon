# Scholarly Intelligence Architecture R1

Date: 2026-09-23
Status: **IMPLEMENTED PROFILE CANDIDATE / NO SCIENTIFIC AUTHORITY TRANSFER**

## Decision

Retain the accepted Research architecture:

```text
CLASSIFY -> BIND -> COMPOSE -> VERIFY -> RECORD
```

and add only a thin machine-readable Scholarly Intelligence projection over Study-owned state.

Do not create `capabilities/research`, a Research daemon, a shared scientific database, or a
universal claim/reviewer ontology.

## Core composition

```text
External scholarly authorities
          |
  Standard-Native binding
          |
          v
Scholarly Intelligence Projection
+---------------------------------+
| exact Study authority           |
| five opaque reference roles     |
| nine owner-native state axes    |
| explicit non-claims             |
+---------------------------------+
     |          |          |
   Infer      Compile     Verify
     \          |          /
      +---------+---------+
                |
          proposed work
                |
      Study/domain admission
                |
             Runtime
```

The projection is navigation and composition metadata. The Study remains scientific truth owner.

## Three structures, not one graph

Long-term Research work needs separate structures:

1. **knowledge/reference graph** for claims, evidence, concerns, standards and literature;
2. **execution DAG** for one bounded revision/campaign;
3. **provenance/event history** for derivation and state change.

Review -> rebuttal -> revision -> review is cyclic at the scholarly level. The complete Research
system must not be forced into one DAG.

## Minimal semantic waist

R1 recognizes five coordination roles:

```text
Requirement -> Claim <- Evidence
                  |
               Concern
                  |
              Resolution
```

These are address roles only. R1 does not define universal Requirement semantics, Claim truth,
Evidence sufficiency, reviewer correctness, concern severity, or resolution success.

## Multi-axis state

A Study projection exposes nine independent axes:

```text
requirements
evidence
inference
claims
argument
venue
review
publication
learning
```

Every axis binds an owner and an opaque owner-native state string. The shared layer never writes
a universal `READY` flag or normalizes domain verdicts.

## LEGO classes

Scholarly circuits reuse the generic Ordivon distinction:

- **Observe** — acquire bounded facts/references;
- **Infer** — derive bounded inferences without changing owner truth;
- **Compile** — transform representations;
- **Verify** — check explicit invariants;
- **Effect** — change durable/external reality.

Models and Agents are replaceable LEGO providers, not state authorities.

```text
Agent = ephemeral
Study state = durable
```

## Candidate future circuits

### Statistical inference

```text
Study evidence
 -> design / estimand / dependence
 -> uncertainty / sensitivity / robustness
 -> Study-owned ClaimPermission
 -> argument/language consumer
```

The desired output is an inference/claim boundary, not merely a p-value.

### Review intelligence

```text
venue criteria + manuscript projection
 -> independent reviewer circuits
 -> Study-owned Concern refs
 -> preserve disagreement
 -> Study-owned resolution decisions
```

Reviewer disagreement is evidence and must not be averaged into false consensus.

### Concern-to-gap

Candidate resolution categories:

```text
NO_GAP
TEXT_GAP
CITATION_GAP
REPORTING_GAP
ANALYSIS_GAP
ROBUSTNESS_GAP
ARTIFACT_GAP
EVIDENCE_GAP
IRREDUCIBLE_LIMITATION
```

They are architecture candidates only in R1. Promotion to shared executable policy requires
cross-Study dogfood.

### Evidence acquisition

Long-term invariant candidate:

```text
new experiment
  requires
unresolved Study-owned evidence gap
  unless
explicit Study/human override
```

R1 does not enforce this rule.

## External-owner alignment

Reuse existing owners rather than wrap them:

- ACM SIGSOFT Empirical Standards / venue rules: research requirements;
- W3C PROV: semantic provenance;
- OpenLineage: execution/data lineage;
- RO-Crate: research-object packaging;
- in-toto/SLSA: software/build provenance where applicable;
- Nanopublication/CiTO-style structures: optional claim/citation interchange;
- CARS / Argumentative Zoning / CoreSC / discourse/citation-intent methods: optional discourse providers;
- OpenReview-style events: review/rebuttal source adapters.

No mature external owner becomes universal simply because it exists.

## Storage direction

R1 deploys no storage service.

If repeated workloads justify durable shared analytics later:

- PostgreSQL: projections, event journal and opaque reference edges;
- Parquet + DuckDB: large scholarly/review feature corpora;
- pgvector: retrieval only, never authority;
- artifact/object storage: immutable carriers by digest.

Scientific datasets remain Study-owned.

## R1 acceptance invariants

A valid R1 profile must:

1. bind an exact Study authority and revision;
2. state `truthRole=non-authoritative-study-projection`;
3. keep all five semantic roles as opaque owner/id references;
4. expose all nine state axes with explicit owners;
5. preserve owner-native state strings;
6. contain explicit non-claims;
7. bind a Standard-Native profile or explicitly represent no binding;
8. not embed manuscript, dataset, model-score, review-text, decision or acceptance-probability payloads.

## Dogfood

R1 binds the accepted Paper1 Standard-Native dogfood receipt:

`meta/next/evidence/acceptance/standard-native-enterprise-r2-dogfood-20260914.json`

That evidence already demonstrates external authority decisions, stable requirement IDs, explicit
claim boundary, domain-owned verdicts, and rejection of universal verdict normalization.

R1 adds navigation projection semantics only.

## Next waves

- **SI-R2** — generate live Paper1/Paper2/Paper3 projections from their current authorities.
- **SI-R3** — dogfood Study-owned ClaimPermission across at least two independent Studies.
- **SI-R4** — dogfood Concern/Resolution routing using real or bounded simulated review evidence.
- **SI-R5** — add longitudinal DecisionEpisode retrieval/descriptive learning before causal claims.

## Non-claims

R1 does not establish Paper1 submission readiness, scientific truth, reviewer correctness, venue
acceptance probability, experiment necessity, or the need for a new Research service/database.
