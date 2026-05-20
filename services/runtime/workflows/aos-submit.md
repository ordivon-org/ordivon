# AOS Submission Workflow

Submits governance objects through identity validation, admission, evidence collection, and receipt generation.

**Workflow ID:** `ordivon-aos-submit`
**Runtime:** Temporal
**Trigger:** AOS package submission

## Steps (DAG)

```
identity_validation
    ↓
admission
    ↓
registry_entry
    ↓
evidence_collection
    ↓
reconciliation_check (can_fail)
    ↓
governance_verify (can_fail)
    ↓
receipt
    ↓
publish_events
```

## Activities

| Step | Description | M-Level |
|------|-------------|---------|
| identity_validation | Validate object identity against schema | M1 |
| admission | Admit object to governance registry | M3 |
| registry_entry | Write entry to PG + JSONL registry | M3 |
| evidence_collection | Collect evidence by running verification commands | M1-M3 |
| reconciliation_check | Reconcile claims vs observations | M3 |
| governance_verify | Run full governance verification | M1 |
| receipt | Write governance receipt to disk + PG | M3 |
| publish_events | Publish to NATS JetStream | M3 |

## Output

- Governance receipt (R4)
- NATS events published
- Trace captured to `traces/aos-submit/`

## Authority

- identity_validation: automated
- admission: requires maintainer authorization
- receipt: draft until reviewed

## Receipt

After completion, generate R4 Governance Receipt.
