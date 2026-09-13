# MarkItDown Document Normalization Kernel — extracted design lessons

Status: **REGISTERED / PROTOTYPE-READY**
Registered: 2026-09-14

## One-sentence model

**MarkItDown is a thin anti-corruption layer between heterogeneous files and Agent context: detect the input, dispatch to the narrowest mature format converter, and collapse the result into a small common Markdown representation.**

## Mechanism 1: normalize at the boundary, not throughout the system

Agents should not need separate reasoning paths for every common input format.

A useful boundary is:

```text
PDF / DOCX / PPTX / XLSX / HTML / image / audio / ZIP / ...
                       ↓
              format adapters
                       ↓
             common Agent context
                 Markdown + metadata
```

This reduces downstream combinatorial complexity without claiming the normalized form is lossless.

## Mechanism 2: common output should be intentionally smaller than source formats

Word, PowerPoint, PDF and Excel contain far more representational detail than most analysis tasks need.

The normalization target should preserve task-relevant semantic structure such as:

- headings;
- paragraphs;
- lists;
- links;
- tables where practical;
- titles/metadata;
- page boundaries when useful.

Do not preserve every visual/style primitive merely because it existed in the source.

This is the document analogue of Browser Use exposing browser affordances and Firecrawl cleaning web pages before Agent reasoning.

## Mechanism 3: use a converter registry rather than one giant parser

Each format has its own mature parser ecosystem and edge cases. A stable router plus replaceable format converters is easier to maintain than a universal monolithic parser.

Conceptually:

```text
ConverterRegistry
├─ PdfConverter
├─ DocxConverter
├─ PptxConverter
├─ XlsxConverter
├─ HtmlConverter
└─ plugins...
```

The router owns selection and common result shape; converters own format specifics.

## Mechanism 4: converter priority enables clean specialization

A specialized converter/plugin may supersede a generic converter for the same input type.

Example pattern:

```text
OCR-enhanced PDF converter     priority high
basic PDF converter            priority normal
```

This is better than inserting OCR/LLM conditions throughout a central parser.

The general Ordivon lesson is:

**specialization should override at provider/adapter selection boundaries, not fork the whole pipeline.**

## Mechanism 5: dependencies should follow workload

Broad format support creates dependency sprawl. MarkItDown therefore makes many format libraries optional extras.

Retain the rule:

`observed input family -> install corresponding adapter dependencies`

not:

`possible future input family -> preinstall everything`

This is particularly important on constrained workstations and fast-moving Python ecosystems.

## Mechanism 6: escalate semantic depth only when required

Document ingestion has levels:

```text
raw readable text
   ↓
light structural Markdown
   ↓
rich document model/layout understanding
   ↓
domain-specific semantic extraction
```

Representative routing:

- direct read -> plain text/Markdown;
- MarkItDown -> light generic normalization;
- Docling -> rich layout/document representation;
- GROBID -> scholarly semantics;
- domain extraction/OCR/cloud analyzers -> only when workload demands them.

Do not apply the deepest parser by default.

## Mechanism 7: input format does not determine provider by itself

The same PDF might be processed differently depending on the question:

- “summarize this PDF” -> MarkItDown may be enough;
- “recover this scanned table accurately” -> Docling/OCR;
- “extract article references and citation contexts” -> GROBID;
- “produce a publication-quality converted document” -> document/publishing tool, not MarkItDown.

Route by **required semantics and fidelity**, not extension.

## Mechanism 8: ingestion and authoring are opposite directions

Do not confuse:

```text
source document -> Agent-readable context
```

with:

```text
structured content -> high-quality target document
```

MarkItDown is mainly the former. Pandoc/Artifact pipelines often serve the latter.

This prevents a common architecture error: trying to use one converter both as an ingestion normalizer and a document-authoring truth layer.

## Mechanism 9: permissive convenience APIs expand authority

A convenience method that accepts files, URIs and streams can silently become a filesystem/network capability.

General rule:

**Expose the narrowest intake authority the workload needs.**

Examples:

```text
local only -> local-file API
controlled bytes -> stream API
controlled network -> caller fetches, converter parses response
```

This is an SSRF/path-traversal containment principle, not just a MarkItDown-specific concern.

## Mechanism 10: conversion success is not semantic completeness

A converter returning Markdown means it produced an output, not that it faithfully captured every:

- table;
- equation;
- image;
- footnote;
- reading-order relation;
- citation relation;
- scanned region.

For consequential work, verify the representation against the information actually required by the task.

## Relationship to Ordivon's Knowledge layer

MarkItDown reinforces representation plurality rather than a universal storage format.

Markdown is useful as a **working representation for Agent context**, but it should not become Ordivon's universal source of truth.

```text
native file      -> authoritative artifact
Markdown         -> derived Agent-readable projection
DoclingDocument  -> richer derived document representation when needed
TEI/GROBID       -> scholarly derived representation when needed
```

Keep the native source and provenance when downstream claims depend on it.

## What Ordivon should retain

1. Normalize heterogeneous files at the Agent intake boundary.
2. Use a small common result shape for ordinary reasoning.
3. Keep format-specific logic behind replaceable converters.
4. Let specialized converters override generic ones by explicit priority.
5. Install parser dependencies according to observed workloads.
6. Escalate from light parsing to rich/domain parsing only when needed.
7. Route by required semantics/fidelity, not filename extension.
8. Keep ingestion separate from document authoring/publishing.
9. Limit local/network authority by choosing the narrowest conversion API.
10. Treat converted Markdown as a derived projection, not evidence of extraction completeness.

## What Ordivon should not copy

- another universal document ontology;
- a mandatory all-formats dependency bundle;
- custom PDF/DOCX/PPTX parsers already provided by mature libraries;
- automatic LLM/OCR calls for every document;
- a new document database merely because Markdown is convenient;
- a global rule that replaces Docling, GROBID or Pandoc with MarkItDown.

## Minimal prototype

```text
Input
  ↓
StreamInfo / type detection
  ↓
priority-ordered ConverterRegistry
  ↓
format-specific converter
  ↓
DocumentConverterResult
  ├─ markdown
  ├─ title/metadata
  └─ pages (optional)
```

Four converters and two input modes are enough to demonstrate the architecture.

## Project-study acceptance

### One-sentence test

PASS: MarkItDown is a lightweight format-router that normalizes heterogeneous inputs into Markdown for Agent/text-analysis consumption.

### Prototype test

PASS: input detection, converter selection, adapter priority, normalized output and authority boundaries are explicit enough to implement a minimal clone or use the mature library directly.

## Verdict

**PASS — LIGHTWEIGHT INGESTION PROVIDER + EXTRACT NORMALIZATION/ESCALATION RULES.**

Do not install every optional dependency by default. Installation should follow a real document-intake workload, ideally in an isolated Python environment.
