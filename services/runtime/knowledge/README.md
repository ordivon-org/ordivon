# Knowledge

`knowledge/` is the code-facing home for derived learning assets.

It now covers:

- knowledge object definitions
- lesson extraction
- feedback hint generation
- retrieval
- recurring issue aggregation
- wiki-facing knowledge assets

Knowledge is not the source of truth for current holdings, orders, approvals, or task state. Those belong in `state/`.

## Read These Files First

- `models.py`
  - `KnowledgeEntry`
  - `KnowledgeRef`
- `adapters.py`
  - builder logic from persisted lesson/outcome inputs
- `extraction.py`
  - `LessonExtractionService`
- `feedback.py`
  - `KnowledgeFeedbackService`
  - `KnowledgeFeedbackPacket` and `KnowledgeHint`
- `retrieval.py`
  - `KnowledgeRetrievalService`
  - recurring issue aggregation

## Current Real Flow

The most important knowledge path today is:

`review complete -> lesson rows -> outcome snapshot -> knowledge entry derivation -> feedback packet -> governance/intelligence consumption -> retrieval/aggregation`

## Current Subareas

- `wiki/`
  - human-readable knowledge assets and module cards
- `retrieval/`
  - reserved assets around retrieval support
- `indexes/`
  - future indexing helpers
- `memory/`
  - future reusable guidance assets
- `ingestion/`
  - future inbound knowledge pipelines

## Important Boundary

Knowledge remains:

- derived
- evidence-backed
- non-authoritative compared to state truth

It may guide governance and intelligence, but it must not silently rewrite policy or state.
