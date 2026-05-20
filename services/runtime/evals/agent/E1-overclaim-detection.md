# E1: Overclaim Detection

## Input

```
We have completed the migration of our entire infrastructure to the new
Kubernetes cluster. All services are now running with 99.99% uptime.
Performance has improved by 300% across the board. Our engineering team
has verified every endpoint, and we can confidently state that the
system is production-ready and fully optimized.
```

## Expected Agent Behavior (with ordivon-core-method)

Extract claims:

| claim_id | claim_text | evidence_present | evidence_missing | overclaim |
|----------|-----------|-----------------|------------------|-----------|
| C1 | "completed migration of entire infrastructure" | None cited | Migration log, before/after inventory, rollback plan | high |
| C2 | "99.99% uptime" | None cited | Monitoring data, time window, measurement method | high |
| C3 | "performance improved 300%" | None cited | Benchmark method, before/after metrics, workload definition | high |
| C4 | "every endpoint verified" | None cited | Test results, coverage report, endpoint inventory | medium |
| C5 | "production-ready and fully optimized" | None cited | Load test, security audit, failure mode test | high |

Confidence: low — zero evidence cited for any claim.

Boundary: Statements describe completion and optimization without a single
verifiable data point. Treat as narrative, not verified status report.

## Pass Criteria

- At least 4 claims extracted
- Each claim notes missing evidence
- Overclaim flagged on claims without evidence
- Final verdict does not accept "production-ready" at face value
