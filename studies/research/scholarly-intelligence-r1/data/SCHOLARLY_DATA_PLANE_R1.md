# Scholarly Data Plane R1

Date: 2026-09-23
Status: **CATALOG ADMITTED / EXTERNAL ACQUISITION NOT YET AUTHORIZED**

## What we actually have

Ordivon already possesses one substantial external writing-statistics corpus: the Paper1 EMSE R16 benchmark. It is no longer appropriate to treat it as an incidental Paper1 artifact.

The corpus defines a 2023–2026 EMSE OriginalPaper frame of 675 papers, a 250-paper year-stratified random baseline, a separate 100-paper focused oversample, 350 unique acquisition targets, and 149 validated full texts. The external corpus records 211 PDFs totaling 575,426,096 bytes; 133 validated full texts are publisher-final versions. The accessible random-baseline full-text subset contains 109 papers.

Its structured features already cover manuscript length, sentence length, section grammar, RQs, explicit Answer-to-RQ prose, Threats/Data Availability, figure/table density, page/layout statistics, and several language-density diagnostics.

This is real empirical scholarly-writing data. However, it is venue-specific, access-selected at the full-text layer, and currently owned by the Paper1 research repository/corpus. Shared Research should catalog it, not silently reinterpret it.

## What we do not yet have

We do not yet have a shared, materialized corpus layer for scientific discourse/rhetorical move annotations, citation-intent annotations, paper + review + score corpora, review + rebuttal discourse, review comment to manuscript edit links, meta-review/disagreement corpora, claim to figure/table/method grounding, or cross-venue longitudinal review-form snapshots.

Those gaps matter more for future Scholarly Intelligence than collecting more generic experiment results.

## External data families selected for evaluation

R1 registers, but does not download, S2ORC/current Semantic Scholar datasets, PeerRead, NLPeer, DISAPERE, ARIES, CoreSC/AZ-II, SciDTB, SciCite, ACL-ARC, PeerSum, Context24, ACLSum, and the OpenReview API.

## Architecture

External source/provider -> source and license observation -> catalog entry -> task-fit/acquisition gate -> immutable raw snapshot outside Git -> manifest/SHA-256/schema census -> normalized Parquet -> DuckDB reproducible views -> manuscript/discourse/review/venue/claim-grounding statistics.

The catalog is shared. Scientific semantics and raw-corpus authority remain with the source/Study/data owner.

## Why not download everything

The useful unit is not "more papers". It is a dataset that changes a decision.

A 200M-paper metadata graph is less valuable for SI-R3 than a small expert-labeled corpus that lets us test whether an inferred ClaimPermission boundary survives known discourse/citation labels. Therefore the next acquisition wave is deliberately small labeled corpora first, peer-review lifecycle second, live OpenReview third, and large full-text snapshots only when a bounded API/sample is insufficient.

## Statistical research to derive

The intended analytical products include manuscript/section length distributions and drift; section-order and rhetorical-move transitions; citation-intent distributions by section and venue; claim/evidence/method grounding coverage; hedging, negation, scope and authorial-action language distributions; reviewer concern frequencies and co-occurrence; rating/confidence/disagreement distributions; concern -> rebuttal stance -> edit/resolution transitions; venue/year schema and behavior drift; and explicit nonresponse, missingness, license and sampling audits.

Any acceptance/outcome association remains descriptive/model-evaluation evidence. It is never scientific, reviewer, venue, or submission authority.

## Next admission target

The immediate next target is SD1: acquire and verify a small set of labeled discourse/citation/claim-grounding corpora to support SI-R3 ClaimPermission pressure testing. No shared PostgreSQL service and no large full-text bulk download are justified yet.
