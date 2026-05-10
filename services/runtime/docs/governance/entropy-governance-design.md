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

## 9. Anti-Mudball Governance Doctrine

> A governance system is not naturally immune to becoming a mudball.
> Without a control plane, deletion capacity, exception expiry, and
> metabolic mechanisms, it becomes a higher-order mudball.

### 9.1 The Governance Mudball

What Ordivon guards against is not ordinary code bloat but:

```text
governance mudball
```

Characteristics:

```text
Many checkers, weak control.
Many docs, unclear current truth.
Many receipts, weak real closure.
Many rules, no lifecycle.
Many reports, no human reading them.
Many exceptions, no expiry.
Many scanners, growing noise.
```

### 9.2 The Mudball Risk Formula

```text
Governance Mudball Risk =
  New checkers + New docs + New receipts + New ledgers
  + New templates + New protocols + New exceptions
  + New scanner findings
  -
  (Core simplicity + generated registry + TTL/tombstone
   + fixture/archive/tmp exclusion + report compression
   + current truth routing + hard NO-GO boundaries)
```

When the top half grows faster than the bottom half, mudball forms.

### 9.3 Small Hard Control Plane, Large Soft Evidence Plane

```text
Core:
  Small. Stable. Hard. Changes slowly.
  Holds only invariants:
  - Evidence != Approval
  - READY != Authorization
  - CandidateRule != Policy
  - Skill != Permission
  - Memory != Truth
  - Trace != Truth

Packs:
  Medium. Scenario-specific. Replaceable.

Adapters:
  Many. Volatile. Must not pollute Core.

Reports / receipts / ledgers:
  Generable. Compressible. Archivable. Tombstonable.
```

### 9.4 No Immortal Exceptions

Every exception must carry:

```text
owner
reason
scope
risk_stage
created_at
review_date
expiry
removal_plan
evidence_ref
```

Without these, an exception is governance debt.

### 9.5 Docs Are Maps, Not Walls

Philosophical invariants must not live only in prose. They must become:

```text
1. Schema constraint
2. Deterministic checker
3. Report wording invariant
4. Lifecycle rule
5. Registry rule
6. Test fixture
7. Closure predicate
```

Anything that cannot land in one of these 7 forms is commentary,
not a control surface.

### 9.6 Deletion Is a Positive Capability

Every phase closure receipt must include a Subtraction Receipt:

```text
Files deprecated
Rules downgraded
Artifacts archived
Exceptions removed
Duplicate definitions merged
Old receipts tombstoned
Current truth reduced
```

Without deletion/deprecation/tombstone capacity, every governance
system becomes an accumulation system.

### 9.7 The Four Questions for Every New Governance Object

Before any new object enters Core or becomes an active Pack:

```text
1. What new control capability does it add?
2. What entropy does it reduce?
3. What old burden does it delete?
4. Does it turn new complexity into long-term debt?
```

If these four cannot be answered, the object stays in
candidate / archive / internal dogfood only.

### 9.8 Compression

```text
Complexity is not failure; unmanaged complexity is failure.
Every exception must expire.
Every rule must have a death path.
Docs cannot substitute for control.
Detection cannot substitute for prevention.
History cannot pollute the present.
Governance expansion must be paired with governance deletion.
```

> Ordivon's enemy is not complexity — it is un-metabolized complexity.
> Not exceptions — immortal exceptions.
> Not documents — documents masquerading as control surfaces.
> Not detection — detection that cannot trigger feedback closure.
