# Entropy Governance — Anti-Bloat System

Layer: L4.5 (between Architecture Boundaries L4A and Runtime Evidence L5)
Status: Phase EG-1 (design + initial deployment)
Owner: DG
Authority: source_of_truth

## 1. Problem

Software entropy grows automatically (Lehman's Second Law).
Without active counter-mechanisms, Ordivon will:

- Accumulate files without bound
- Grow cross-reference drift
- Develop checker blind spots
- Suffer documentation staleness
- Accept ungoverned complexity

## 2. Design Principles

### 2.1 Evidence-First

All entropy claims backed by telemetry data. No subjective "it feels bloated."
Every entropy gate references a specific metric, measured by an automated checker,
logged to a structured ledger.

### 2.2 Receipt/Debt/Gate Triad

```
Entropy Growth Detected → EntropyDebt created → EntropyGate escalates
```

Entropy is not "bad code." Entropy is a measurable property of the system.
When it exceeds a threshold, it creates **governance debt**, not moral failure.

### 2.3 BLOCKED/DEGRADED/READY Algebra

| Entropy State | Threshold | Meaning |
|--------------|-----------|---------|
| READY | Velocity < 3%/month | System is stable |
| DEGRADED | Velocity 3-10%/month | Growth is accelerating — review needed |
| BLOCKED | Velocity > 10%/month | Unsustainable growth — gate activated |

## 3. Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  Entropy Governance                       │
│                                                          │
│  ┌─────────────────┐     ┌─────────────────┐            │
│  │ Telemetry       │────▶│ Velocity        │            │
│  │ Measures:       │     │ Calculates:     │            │
│  │  - file count   │     │  d(metric)/dt   │            │
│  │  - import edges │     │  % growth/month │            │
│  │  - doc registry │     │  trend analysis │            │
│  │  - debt ledger  │     │                 │            │
│  │  - checker cov  │     └────────┬────────┘            │
│  └────────┬────────┘              │                     │
│           │                       ▼                     │
│           │              ┌─────────────────┐            │
│           │              │ Gate             │            │
│           │              │ Enforces:        │            │
│           │              │  - file ceiling  │            │
│           │              │  - import depth  │            │
│           │              │  - coverage min  │            │
│           │              │  - freshness SLO │            │
│           │              └────────┬────────┘            │
│           │                       │                     │
│           │                       ▼                     │
│           │              ┌─────────────────┐            │
│           │              │ Budget           │            │
│           │              │ Tracks:          │            │
│           │              │  - module quotas │            │
│           │              │  - add tax       │            │
│           │              │  - delete credit │            │
│           │              └─────────────────┘            │
│           │                                             │
│           ▼                                             │
│  ┌─────────────────────────────────────────┐            │
│  │          Learning Loop                   │            │
│  │  Gate violation → Lesson → CandidateRule │            │
│  │  → Policy Shadow → Activation Review     │            │
│  └─────────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────┘
```

## 4. Metrics

### 4.1 Size Metrics

| Metric | Source | Frequency |
|--------|--------|-----------|
| `total_files` | File system scan | Per run |
| `docs_files` | docs/ scan | Per run |
| `src_files` | src/ scan | Per run |
| `test_files` | tests/ scan | Per run |
| `checkers_count` | checkers/ scan | Per run |
| `total_lines` | Line count | Weekly |

### 4.2 Complexity Metrics

| Metric | Source | Frequency |
|--------|--------|-----------|
| `cross_boundary_imports` | Import analysis | Per run |
| `unique_import_sources` | Import dedup | Per run |
| `doc_registry_entries` | document-registry.jsonl | Per run |
| `cross_references` | Related docs/ledgers/receipts | Per run |
| `max_import_depth` | Import chain analysis | Weekly |

### 4.3 Health Metrics

| Metric | Source | Frequency |
|--------|--------|-----------|
| `stale_docs` | document-registry.jsonl | Per run |
| `docs_missing_freshness` | document-registry.jsonl | Per run |
| `debt_entries` | verification-debt-ledger.jsonl | Per run |
| `checker_findings` | Full baseline run | Per run |
| `checker_coverage_ratio` | Coverage gap analysis | Weekly |

### 4.4 Velocity

Velocity = (current_value - previous_value) / time_delta_days

Normalized to % growth per 30 days for comparability.

## 5. Entropy Gate Rules

### Gate 1: File Ceiling

```
total_files < 2500
```

If `total_files` exceeds 2500: **BLOCKED** — must archive/delete before adding.

### Gate 2: Import Depth

```
max_import_depth < 6
```

If any import chain exceeds depth 6: **BLOCKED** — must refactor module.

### Gate 3: Freshness SLO

```
stale_docs / doc_registry_entries < 0.10
```

If >10% of docs are stale: **DEGRADED** — backfill freshness.

### Gate 4: Coverage Minimum

```
checkers_count / sqrt(total_files) > 0.5
```

If checker-to-file ratio drops below threshold: **DEGRADED** — coverage gap.

### Gate 5: Growth Velocity

```
total_files_growth_rate < 10% per month
```

If monthly growth >10%: **BLOCKED** — unsustainable growth rate.

## 6. Agent-Friendly Properties

### 6.1 Structured Data

All telemetry stored as JSONL with `timestamp`, `metric_name`, `value`, `unit`.
Agents query via JSON parsing — no NLP required.

### 6.2 Deterministic

Telemetry is reproducible. Same code state → same metrics. No randomness.

### 6.3 Self-Describing

Every metric has `unit`, `threshold`, `interpretation` in the telemetry schema.
An agent can understand "total_files: 450, unit: files, threshold_warning: 1000"
without human explanation.

### 6.4 Actionable

Gate violations produce structured debt entries with:
- `violation_type`
- `current_value`
- `threshold`
- `remediation_hint`

An agent can read a BLOCKED gate and know exactly what to fix.

## 7. Integration with Ordivon Governance Loop

```
 ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
 │ Telemetry│───▶│ Velocity │───▶│   Gate   │───▶│  Budget  │
 │ (measure)│    │ (detect) │    │(prevent) │    │(allocate)│
 └──────────┘    └──────────┘    └────┬─────┘    └──────────┘
                                      │
                            ┌─────────▼─────────┐
                            │   Gate Violation   │
                            │   → Lesson         │
                            │   → CandidateRule  │
                            │   → Policy Shadow  │
                            │   → Review         │
                            └───────────────────┘
```

A BLOCKED gate doesn't just stop the PR. It creates:
1. A Lesson ("system hit file ceiling at 2500")
2. A CandidateRule proposal ("archive docs/archive/ before adding new docs/")
3. Shadow evaluation against the rule
4. Human review of whether the ceiling should be raised or enforced

## 8. Current Status

Phase EG-1: Design + initial telemetry deployment.
- Entropy Telemetry checker: measures and logs metrics
- Entropy Gate checker: enforces structural constraints

Future phases:
- EG-2: Entropy Budget (module-level quotas)
- EG-3: Automatic archival (stale docs auto-archived)
- EG-4: Predictive entropy (ML-based growth forecasting)
