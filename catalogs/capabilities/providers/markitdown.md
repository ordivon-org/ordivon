# Provider: Microsoft MarkItDown

Status: **PROTOTYPE-READY / LIGHTWEIGHT DEFAULT CANDIDATE / NOT GLOBALLY INSTALLED**
Role: lightweight heterogeneous-file-to-Markdown normalization provider for Agent/LLM ingestion.

## One-sentence understanding

**MarkItDown routes a file/stream/URI to a format-specific converter and normalizes the useful structure into token-efficient Markdown so downstream Agents can consume heterogeneous inputs through one lightweight interface.**

## Current upstream scope

MarkItDown is intentionally a Python library/CLI rather than a document platform. Its main repository describes the output as optimized for LLM/text-analysis consumption rather than high-fidelity human publishing.

Current built-in/optional coverage includes PDF, Word, PowerPoint, Excel, images, audio, HTML, CSV/JSON/XML and other text formats, ZIP containers, EPUB, Outlook messages, YouTube/transcripts and related inputs. Format-specific dependencies are optional extras rather than mandatory base dependencies.

It also exposes an MCP package and a third-party plugin mechanism. Plugins are disabled by default and discovered through Python entry points when enabled.

## Core primitives

### Input boundary

The input may be:

- local file;
- already-open byte stream;
- HTTP response / remote URI;
- data/other supported URI depending on the chosen API.

Use the narrowest input method that matches the task rather than the permissive universal `convert()` entry point.

### StreamInfo / type hints

Before conversion, the host assembles file-type hints such as extension, MIME/content type and content detection. These hints are passed to candidate converters.

Conceptually:

```text
input bytes + metadata
        ↓
file-type guesses / StreamInfo
        ↓
converter selection
```

### Converter registry

The central abstraction is a set of converters that each answer roughly:

```text
accepts(stream, stream_info)?
convert(stream, stream_info) -> DocumentConverterResult
```

Converters are ordered by priority. Plugins can register higher-priority replacements/enhancements; the official OCR plugin, for example, registers OCR-aware converters ahead of built-ins without changing the central router.

This is the important architecture: one stable intake surface, many replaceable format adapters.

### Normalized result

The common result is deliberately small:

- Markdown content;
- optional title/metadata;
- page-level content where supported.

The target is not lossless document editing. It is a compact representation that preserves useful headings, lists, links, tables and textual structure for downstream reasoning/indexing.

### Optional escalation providers

MarkItDown can optionally route suitable inputs to richer services such as Azure Document Intelligence or Azure Content Understanding when basic local conversion is insufficient.

This establishes a useful pattern:

`cheap local converter -> richer document understanding only when required`

## Ordivon routing rule

Use the thinnest document representation that satisfies the task:

```text
plain text / already-readable markup
    -> direct read

common heterogeneous file needing Agent-readable text
    -> MarkItDown

complex PDF/layout/table/OCR/document hierarchy
    -> Docling

scientific-paper metadata/citations/reference structure/TEI
    -> GROBID

formal markup/publishing format conversion
    -> Pandoc

native document editing/high-fidelity artifact production
    -> corresponding Artifact tool/provider
```

These providers overlap in accepted file extensions but solve different downstream problems. Route by required output semantics, not by input suffix alone.

## Boundary with Docling

MarkItDown is the lighter normalization layer. It aims to produce useful Markdown quickly through format-specific libraries.

Docling is preferable when the task requires a richer intermediate document model or advanced document understanding such as:

- PDF page layout;
- reading order;
- robust table structure;
- formulas/code/picture enrichment;
- explicit hierarchy;
- chunking/RAG serialization;
- lossless-ish structured JSON/DoclingDocument operations.

Do not run every ordinary DOCX/PPTX/XLSX through a heavy document-understanding pipeline merely because Docling can parse it.

## Boundary with GROBID

GROBID is specialized for technical/scientific PDFs and extracts scholarly semantics such as:

- article headers/metadata;
- authors/affiliations;
- references;
- citation contexts and resolution;
- section/figure/table/footnote structure;
- TEI XML.

If the research question depends on scholarly structure rather than just readable paper text, use GROBID instead of treating Markdown conversion as sufficient.

## Boundary with Pandoc

Pandoc is a universal markup/document format converter and publishing pipeline. It is preferable when the goal is transforming between authoring/publishing formats such as Markdown, HTML, LaTeX and DOCX while preserving formal document semantics needed for output generation.

MarkItDown is primarily an ingestion direction:

`heterogeneous input -> Markdown for analysis`

Pandoc is primarily a format-transformation direction:

`structured markup/document -> another structured/publishing format`

## Security boundary

MarkItDown performs I/O with the privileges of its current process. Its permissive conversion APIs may read local files or fetch remote resources.

Therefore:

- treat paths/URIs from untrusted users as untrusted capability requests;
- prefer `convert_local()` for local-file-only workloads;
- prefer caller-controlled HTTP fetching plus `convert_response()` when network policy matters;
- prefer `convert_stream()` when the caller already controls the bytes;
- restrict URI schemes, private/loopback/link-local/metadata destinations and filesystem scope in hosted/server environments;
- plugins are executable code and require normal dependency/source trust review.

Document conversion success does not prove extraction completeness or semantic correctness.

## Dependency policy

Do not install `[all]` by default solely for theoretical format coverage.

Prefer:

- an isolated environment/tool;
- only the extras required by observed workload;
- Python 3.12/3.13 when ecosystem compatibility is better than the workstation's newest Python;
- plugins only when their behavior is actually needed.

On this workstation, no global `markitdown` executable is currently observed. Python 3.14 is present globally, and upstream issue history shows some optional dependency combinations have lagged Python 3.14; if installed, use an isolated supported Python environment rather than modifying system Python.

## Prototype recipe

A minimal MarkItDown-like implementation needs only:

1. define `StreamInfo` containing extension/MIME/source hints;
2. define a converter interface with `accepts()` and `convert()`;
3. register converters with priorities;
4. inspect an input and build candidate type guesses;
5. try applicable converters in priority order;
6. convert a few representative formats, e.g. HTML, DOCX, PDF and CSV;
7. normalize their outputs to `markdown + optional metadata/pages`;
8. expose local-file and stream entry points separately;
9. add a plugin registration mechanism only after the base router works.

This is sufficient to reproduce the architecture. The value of the mature project is its maintained set of format adapters, dependency handling, tests and security hardening rather than a complicated core algorithm.

## Prototype readiness gate

**PASS.** Converter routing, type detection, normalized result, plugin priority, optional-dependency and security boundaries are explicit enough to implement a small functional prototype or consume MarkItDown directly.
